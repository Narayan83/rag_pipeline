"""Retrieval tools. top_k and max context length come from config.yaml."""
from __future__ import annotations

import re

from app.clients import embed_text
from app.config import load_config
from app.db import connect


def top_k() -> int:
    return int(load_config()["retrieval"]["top_k"])


def max_context_length() -> int:
    return int(load_config()["retrieval"]["max_context_length"])


def normalize_document_type(document_type: str | None) -> str | None:
    if not document_type:
        return None
    lowered = document_type.strip().lower()
    if lowered in {"ir", "ir_document"}:
        return "ir_document"
    if lowered in {"criteria", "criteria_document", "rule", "rule_document"}:
        return "criteria_document"
    return document_type


def list_documents(document_type: str | None = None) -> list[dict]:
    document_type = normalize_document_type(document_type)
    sql = """
        SELECT id, document_type, document_name, markdown_path, created_at,
               state, department, office_name, district, audit_period,
               ir_number, document_title, instrument_kind, year, auditee
        FROM (
            SELECT id, 'ir_document' AS document_type, document_name,
                   NULL::text AS markdown_path, created_at, state, department,
                   office_name, district, audit_period, ir_number, document_title,
                   'inspection_report' AS instrument_kind, year, auditee
            FROM ir_master
            UNION ALL
            SELECT id, 'criteria_document', document_name, markdown_path, created_at,
                   state, department, NULL::text, NULL::text, NULL::text, ir_number,
                   document_title, instrument_kind, year, NULL::text
            FROM criteria_master
        ) documents
    """
    params: list = []
    if document_type:
        sql += " WHERE document_type = %s"
        params.append(document_type)
    sql += " ORDER BY document_type, document_name"
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    for row in rows:
        row["created_at"] = row["created_at"].isoformat()
    return rows


_STOPWORDS = frozenset({
    "the", "and", "for", "with", "from", "that", "this", "what", "when", "where",
    "which", "who", "how", "are", "was", "were", "has", "have", "had", "not",
    "but", "you", "your", "about", "into", "over", "than", "then", "them",
    "they", "its", "can", "could", "would", "should", "does", "did", "any",
    "all", "per", "via", "please", "tell", "give", "show", "find", "there",
    "their", "our", "using", "used", "only", "also",
})


def _query_words(query: str) -> list[str]:
    words: list[str] = []
    for word in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]{2,}", query.replace("%", "")):
        if word.lower() in _STOPWORDS:
            continue
        words.append(word)
        if len(words) >= 8:
            break
    return words


def _keyword_filter(query: str, column: str = "chunk") -> tuple[str, list, str]:
    """Match and rank by how many query words appear in the column."""
    words = _query_words(query)
    if not words:
        return "TRUE", [], "0"
    patterns = [f"%{word}%" for word in words]
    clause = " OR ".join(f"{column} ILIKE %s" for _ in words)
    score = " + ".join(f"CASE WHEN {column} ILIKE %s THEN 1 ELSE 0 END" for _ in words)
    return clause, patterns, score


def _metadata_clause(query: str) -> tuple[str, list]:
    """Narrow retrieval when the question names a state, department, or IR number."""
    lowered = query.lower()
    clauses: list[str] = []
    params: list = []
    for needle, label in (
        ("andhra pradesh", "Andhra Pradesh"),
        ("maharashtra", "Maharashtra"),
        ("haryana", "Haryana"),
        ("punjab", "Punjab"),
        ("aurangabad", "Maharashtra"),
        ("amritsar", "Punjab"),
        ("vijayawada", "Andhra Pradesh"),
    ):
        if needle in lowered:
            clauses.append("d.state = %s")
            params.append(label)
            break
    for needles, label in (
        (("energy", "power", "apcpdcl"), "Energy"),
        (("finance", "allowance", "special pay"), "Finance"),
        (("stamp", "registrar", "registration"), "Registration and Stamps"),
        (("esi", "hospital", "medical"), "Medical and Health"),
    ):
        if any(needle in lowered for needle in needles):
            clauses.append("d.department = %s")
            params.append(label)
            break
    ir_match = re.search(r"IR-[0-9A-F]{6,}", query, re.IGNORECASE)
    if ir_match:
        clauses.append("d.ir_number = %s")
        params.append(ir_match.group(0).upper())
    if not clauses:
        return "", []
    return " AND " + " AND ".join(clauses), params


def _cosine_score(alias: str = "c") -> str:
    return f"""
        (
          SELECT SUM(a * b) / NULLIF(SQRT(SUM(a * a)) * SQRT(SUM(b * b)), 0)
          FROM unnest({alias}.embedding, %s::float8[]) AS u(a, b)
        )
    """


def search_chunks(
    query: str,
    document_type: str | None = None,
    limit: int | None = None,
    apply_metadata: bool = True,
) -> list[dict]:
    """Search IR chunks and criteria child chunks, then return the stored passage."""
    limit = limit or top_k()
    document_type = normalize_document_type(document_type)
    found = _search_family(query, document_type, limit, apply_metadata)
    if found or not apply_metadata:
        return found
    if _metadata_clause(query)[0]:
        return search_chunks(query, document_type, limit, apply_metadata=False)
    return []


def _search_family(query: str, document_type: str | None, limit: int, apply_metadata: bool) -> list[dict]:
    vector = _safe_embed(query)
    rows: list[dict] = []
    if document_type in (None, "ir_document"):
        rows.extend(_search_ir_chunks(query, vector, limit, apply_metadata))
    if document_type in (None, "criteria_document"):
        rows.extend(_search_criteria_chunks(query, vector, limit, apply_metadata))
    rows.sort(key=lambda row: row.get("score") or -1, reverse=True)
    return _dedupe(rows, limit)


def _search_ir_chunks(query: str, vector: list[float] | None, limit: int, apply_metadata: bool) -> list[dict]:
    meta_sql, meta_params = _metadata_clause(query) if apply_metadata else ("", [])
    with connect() as conn:
        with conn.cursor() as cur:
            rows: list = []
            if vector:
                cur.execute(
                    f"""
                    SELECT c.id, NULL::int AS parent_id, c.chunk AS matched_child,
                           c.chunk_kind AS child_kind, c.chunk, c.chunk_kind,
                           c.hierarchy_path, c.metadata AS parameters,
                           d.document_name, 'ir_document' AS document_type,
                           d.state, d.department, d.ir_number,
                           {_cosine_score()} AS score
                    FROM ir_chunks c
                    JOIN ir_master d ON d.id = c.document_id
                    WHERE c.embedding IS NOT NULL
                    {meta_sql}
                    ORDER BY score DESC NULLS LAST
                    LIMIT %s
                    """,
                    [vector, *meta_params, limit * 4],
                )
                rows = cur.fetchall()
            if not rows:
                clause, word_params, score_sql = _keyword_filter(query, "c.chunk")
                cur.execute(
                    f"""
                    SELECT c.id, NULL::int AS parent_id, c.chunk AS matched_child,
                           c.chunk_kind AS child_kind, c.chunk, c.chunk_kind,
                           c.hierarchy_path, c.metadata AS parameters,
                           d.document_name, 'ir_document' AS document_type,
                           d.state, d.department, d.ir_number,
                           ({score_sql}) AS score
                    FROM ir_chunks c
                    JOIN ir_master d ON d.id = c.document_id
                    WHERE ({clause})
                    {meta_sql}
                    ORDER BY score DESC
                    LIMIT %s
                    """,
                    [*word_params, *word_params, *meta_params, limit * 4],
                )
                rows = cur.fetchall()
    return rows


def _search_criteria_chunks(query: str, vector: list[float] | None, limit: int, apply_metadata: bool) -> list[dict]:
    meta_sql, meta_params = _metadata_clause(query) if apply_metadata else ("", [])
    with connect() as conn:
        with conn.cursor() as cur:
            rows: list = []
            if vector:
                cur.execute(
                    f"""
                    SELECT c.id, c.parent_id, c.chunk AS matched_child, c.chunk_kind AS child_kind,
                           COALESCE(p.chunk, c.chunk) AS chunk,
                           COALESCE(p.chunk_kind, c.chunk_kind) AS chunk_kind,
                           COALESCE(p.hierarchy_path, c.hierarchy_path) AS hierarchy_path,
                           COALESCE(p.metadata, c.metadata) AS parameters,
                           d.document_name, 'criteria_document' AS document_type,
                           d.state, d.department, d.ir_number,
                           {_cosine_score()} AS score
                    FROM criteria_chunks c
                    LEFT JOIN criteria_chunks p ON p.id = c.parent_id
                    JOIN criteria_master d ON d.id = c.document_id
                    WHERE c.role = 'child' AND c.embedding IS NOT NULL
                    {meta_sql}
                    ORDER BY score DESC NULLS LAST
                    LIMIT %s
                    """,
                    [vector, *meta_params, limit * 4],
                )
                rows = cur.fetchall()
            if not rows:
                clause, word_params, score_sql = _keyword_filter(query, "c.chunk")
                cur.execute(
                    f"""
                    SELECT c.id, c.parent_id, c.chunk AS matched_child, c.chunk_kind AS child_kind,
                           COALESCE(p.chunk, c.chunk) AS chunk,
                           COALESCE(p.chunk_kind, c.chunk_kind) AS chunk_kind,
                           COALESCE(p.hierarchy_path, c.hierarchy_path) AS hierarchy_path,
                           COALESCE(p.metadata, c.metadata) AS parameters,
                           d.document_name, 'criteria_document' AS document_type,
                           d.state, d.department, d.ir_number,
                           ({score_sql}) AS score
                    FROM criteria_chunks c
                    LEFT JOIN criteria_chunks p ON p.id = c.parent_id
                    JOIN criteria_master d ON d.id = c.document_id
                    WHERE c.role = 'child' AND ({clause})
                    {meta_sql}
                    ORDER BY score DESC
                    LIMIT %s
                    """,
                    [*word_params, *word_params, *meta_params, limit * 4],
                )
                rows = cur.fetchall()
    return rows


def search_tables(
    query: str,
    document_type: str | None = None,
    limit: int | None = None,
    apply_metadata: bool = True,
) -> list[dict]:
    """Search ir_tables and criteria_tables. Tables are stored whole."""
    limit = limit or top_k()
    document_type = normalize_document_type(document_type)
    clause, word_params, score_sql = _keyword_filter(query, "t.table_markdown")
    if clause == "TRUE":
        return []
    meta_sql, meta_params = _metadata_clause(query) if apply_metadata else ("", [])
    families = []
    if document_type in (None, "ir_document"):
        families.append(("ir_tables", "ir_master", "ir_document"))
    if document_type in (None, "criteria_document"):
        families.append(("criteria_tables", "criteria_master", "criteria_document"))
    rows: list = []
    with connect() as conn:
        with conn.cursor() as cur:
            for table_name, master_name, family in families:
                cur.execute(
                    f"""
                    SELECT t.id, d.document_name, %s AS document_type, t.hierarchy_path,
                           t.table_markdown, t.metadata AS parameters,
                           d.state, d.department, d.ir_number,
                           ({score_sql}) AS score
                    FROM {table_name} t
                    JOIN {master_name} d ON d.id = t.document_id
                    WHERE ({clause})
                    {meta_sql}
                    ORDER BY score DESC
                    LIMIT %s
                    """,
                    [family, *word_params, *word_params, *meta_params, limit],
                )
                rows.extend(cur.fetchall())
    rows.sort(key=lambda row: row.get("score") or 0, reverse=True)
    if not rows and apply_metadata and meta_sql:
        return search_tables(query, document_type, limit, apply_metadata=False)
    results = []
    for row in rows:
        results.append({
            "id": row["id"],
            "document_name": row["document_name"],
            "document_type": row["document_type"],
            "hierarchy_path": row["hierarchy_path"],
            "chunk": row["table_markdown"],
            "chunk_kind": "table",
            "parameters": row["parameters"],
            "state": row.get("state"),
            "department": row.get("department"),
            "ir_number": row.get("ir_number"),
        })
    return results[:limit]


def calculate_table(query: str) -> str | None:
    """Sum a numeric column from table metadata stored in the database."""
    if not re.search(r"\b(total|sum|average|avg|how much|collected)\b", query, re.IGNORECASE):
        return None
    tables = search_tables(query, limit=3)
    notes: list[str] = []
    for table in tables:
        params = table.get("parameters") or {}
        headers = params.get("headers") or []
        grid = params.get("rows") or []
        if not headers or not grid:
            continue
        chosen = [
            index for index, header in enumerate(headers)
            if header and header.lower() in query.lower()
        ]
        if not chosen:
            continue
        values = []
        for row in grid:
            if not row or re.match(r"(?i)\s*total\b", str(row[0])):
                continue
            if chosen[0] < len(row):
                number = _to_float(row[chosen[0]])
                if number is not None:
                    values.append(number)
        if not values:
            continue
        notes.append(
            f"Calculated from the stored table in {table['document_name']} "
            f"({table['hierarchy_path']}): {headers[chosen[0]]} total = {sum(values):g} "
            f"across {len(values)} rows."
        )
    return "\n".join(notes) if notes else None


def _to_float(value) -> float | None:
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group(0)) if match else None


def _dedupe(rows: list[dict], limit: int) -> list[dict]:
    chosen: list[dict] = []
    seen: set[tuple] = set()
    for row in rows:
        parent_key = (row["document_type"], row.get("parent_id") or row["id"])
        if parent_key in seen:
            continue
        seen.add(parent_key)
        chosen.append(_public_chunk(row))
        if len(chosen) >= limit:
            break
    return chosen


def gather_evidence(query: str) -> tuple[str, list[dict]]:
    """Top chunks and tables for a question, packed to max_context_length."""
    chunks = search_chunks(query)
    seen = {(item["document_type"], item["id"]) for item in chunks}
    for table in search_tables(query):
        key = (table["document_type"], table["id"])
        if key not in seen:
            chunks.append(table)
            seen.add(key)
    context = pack_context(chunks)
    calculated = calculate_table(query)
    if calculated:
        context = f"{calculated}\n\n{context}" if context else calculated
    return context, chunks


def pack_context(chunks: list[dict]) -> str:
    """Join chunks until max_context_length characters is reached."""
    budget = max_context_length()
    parts: list[str] = []
    used = 0
    for chunk in chunks:
        block = (
            f"[{chunk.get('document_type')} | {chunk.get('document_name')} | "
            f"{chunk.get('hierarchy_path')} | {chunk.get('chunk_kind')}]\n"
            f"{chunk.get('chunk', '')}"
        )
        if used + len(block) > budget:
            remaining = budget - used
            if remaining > 80:
                parts.append(block[:remaining])
            break
        parts.append(block)
        used += len(block) + 2
    return "\n\n".join(parts)


def _safe_embed(query: str) -> list[float] | None:
    try:
        return embed_text(query)
    except Exception:
        return None


def _public_chunk(row: dict) -> dict:
    score = row.get("score")
    return {
        "id": row.get("parent_id") or row["id"],
        "document_name": row["document_name"],
        "document_type": row["document_type"],
        "chunk": row["chunk"],
        "matched_child": row.get("matched_child"),
        "chunk_kind": row["chunk_kind"],
        "hierarchy_path": row["hierarchy_path"],
        "parameters": row.get("parameters"),
        "state": row.get("state"),
        "department": row.get("department"),
        "ir_number": row.get("ir_number"),
        "score": float(score) if score is not None else None,
    }
