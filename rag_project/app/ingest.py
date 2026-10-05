"""Turn source documents into stored chunks and tables.

Inspection reports are chunked from the source text.
Criteria documents are written to markdown first, then chunked from that file.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from app.chunking import Chunk, ExtractedTable, chunk_criteria, chunk_ir
from app.clients import embed_texts, ocr_to_markdown
from app.config import load_config, project_path
from app.db import connect
from app.metadata import extract_metadata

_SOURCE_SUFFIXES = {".pdf", ".docx", ".md", ".txt"}
_ocr_available = True


def docx_to_markdown(path: Path) -> str:
    document = Document(str(path))
    parts: list[str] = []
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        style = (paragraph.style.name if paragraph.style else "") or ""
        if style.lower().startswith("heading") or style.lower() == "title":
            level = 1
            digits = "".join(ch for ch in style if ch.isdigit())
            if digits:
                level = min(int(digits), 6)
            parts.append(f"{'#' * level} {text}")
        else:
            parts.append(text)
    for table in document.tables:
        rows = [[cell.text.strip().replace("\n", " ") for cell in row.cells] for row in table.rows]
        if not rows:
            continue
        width = max(len(row) for row in rows)
        lines = []
        for index, row in enumerate(rows):
            padded = row + [""] * (width - len(row))
            lines.append("| " + " | ".join(padded) + " |")
            if index == 0:
                lines.append("| " + " | ".join("---" for _ in padded) + " |")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def pdf_to_markdown_local(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"## Page {number}\n\n{text.strip()}")
    return "\n\n".join(pages)


def local_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        return docx_to_markdown(path)
    if path.suffix.lower() == ".pdf":
        return pdf_to_markdown_local(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def read_document(path: Path, save_markdown: bool) -> tuple[str, str | None, str]:
    """Read a source file. Markdown is written only when save_markdown is true."""
    global _ocr_available
    try:
        if not _ocr_available:
            raise RuntimeError("OCR skipped after an earlier connection failure")
        text = ocr_to_markdown(str(path), path.name)
        method = "ocr"
    except Exception as exc:
        if "timed out" in str(exc) or "OCR skipped" in str(exc):
            _ocr_available = False
        text = local_text(path)
        method = f"local_fallback ({exc})"
        if not text.strip():
            raise RuntimeError(f"No text extracted for {path.name}: {exc}") from exc
    markdown_path = None
    if save_markdown:
        markdown_dir = project_path("markdown_dir")
        markdown_dir.mkdir(parents=True, exist_ok=True)
        target = markdown_dir / f"{path.stem}.md"
        target.write_text(text, encoding="utf-8")
        markdown_path = str(target)
    return text, markdown_path, method


def _source_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(
        path for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in _SOURCE_SUFFIXES
    )


def _insert_rows(
    chunk_table: str,
    table_table: str,
    document_id: int,
    chunks: list[Chunk],
    tables: list[ExtractedTable],
    method: str,
    with_children: bool,
) -> dict:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {table_table} WHERE document_id = %s", (document_id,))
            if with_children:
                cur.execute(
                    f"DELETE FROM {chunk_table} WHERE document_id = %s AND role = 'child'",
                    (document_id,),
                )
            cur.execute(f"DELETE FROM {chunk_table} WHERE document_id = %s", (document_id,))

            def insert_chunk(item: Chunk, parent_id: int | None) -> int:
                if chunk_table == "ir_chunks":
                    cur.execute(
                        """
                        INSERT INTO ir_chunks
                            (document_id, chunk, chunk_kind, part, observation_ref,
                             hierarchy_path, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                        RETURNING id
                        """,
                        (
                            document_id, item.text, item.chunk_kind,
                            item.metadata.get("part"), item.metadata.get("observation_ref"),
                            item.hierarchy_path,
                            json.dumps({**item.metadata, "extraction": method}),
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO criteria_chunks
                            (document_id, parent_id, chunk, role, chunk_kind, hierarchy_path, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                        RETURNING id
                        """,
                        (
                            document_id, parent_id, item.text, item.role, item.chunk_kind,
                            item.hierarchy_path,
                            json.dumps({**item.metadata, "extraction": method}),
                        ),
                    )
                return cur.fetchone()["id"]

            parent_ids: list[int] = []
            stored = 0
            for item in chunks:
                parent_ids.append(insert_chunk(item, None))
                stored += 1
                if with_children:
                    for child in item.children:
                        insert_chunk(child, parent_ids[-1])
                        stored += 1
            for table in tables:
                chunk_id = parent_ids[table.chunk_index] if table.chunk_index is not None else None
                cur.execute(
                    f"""
                    INSERT INTO {table_table}
                        (document_id, chunk_id, table_markdown, hierarchy_path, metadata)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        document_id, chunk_id, table.text, table.hierarchy_path,
                        json.dumps(table.metadata),
                    ),
                )
                stored += 1
        conn.commit()
    return {"stored": stored, "chunks": len(chunks), "tables": len(tables)}


def ingest_ir(path: Path) -> dict:
    """Chunk an inspection report directly from the source. No markdown file is written."""
    text, _markdown_path, method = read_document(path, save_markdown=False)
    chunks, tables = chunk_ir(text, path.name)
    meta = extract_metadata(text, path.name, "ir_document")
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ir_master (
                    document_name, source_path, state, department, office_name, district,
                    audit_period, ir_number, document_title, year, auditee
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_name)
                DO UPDATE SET source_path = EXCLUDED.source_path,
                              state = EXCLUDED.state,
                              department = EXCLUDED.department,
                              office_name = EXCLUDED.office_name,
                              district = EXCLUDED.district,
                              audit_period = EXCLUDED.audit_period,
                              ir_number = EXCLUDED.ir_number,
                              document_title = EXCLUDED.document_title,
                              year = EXCLUDED.year,
                              auditee = EXCLUDED.auditee
                RETURNING id
                """,
                (
                    path.name, str(path), meta["state"], meta["department"], meta["office_name"],
                    meta["district"], meta["audit_period"], meta["ir_number"],
                    meta["document_title"], meta["year"], meta["auditee"],
                ),
            )
            document_id = cur.fetchone()["id"]
        conn.commit()
    stored = _insert_rows("ir_chunks", "ir_tables", document_id, chunks, tables, method, False)
    return {
        "document": path.name,
        "document_type": "ir_document",
        "document_id": document_id,
        "parts": sum(1 for chunk in chunks if chunk.chunk_kind == "part"),
        "observations": sum(1 for chunk in chunks if chunk.chunk_kind == "observation"),
        "tables": stored["tables"],
        "stored": stored["stored"],
        "extraction": method,
        "markdown": None,
    }


def convert_criteria_to_markdown(path: Path) -> dict:
    """Write the criteria markdown file and upsert criteria_master. Does not chunk."""
    text, markdown_path, method = read_document(path, save_markdown=True)
    meta = extract_metadata(text, path.name, "criteria_document")
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO criteria_master (
                    document_name, source_path, markdown_path, state, department,
                    ir_number, document_title, instrument_kind, year
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_name)
                DO UPDATE SET source_path = EXCLUDED.source_path,
                              markdown_path = EXCLUDED.markdown_path,
                              state = EXCLUDED.state,
                              department = EXCLUDED.department,
                              ir_number = EXCLUDED.ir_number,
                              document_title = EXCLUDED.document_title,
                              instrument_kind = EXCLUDED.instrument_kind,
                              year = EXCLUDED.year
                RETURNING id
                """,
                (
                    path.name, str(path), markdown_path, meta["state"], meta["department"],
                    meta["ir_number"], meta["document_title"], meta["instrument_kind"], meta["year"],
                ),
            )
            document_id = cur.fetchone()["id"]
        conn.commit()
    return {
        "document": path.name,
        "document_type": "criteria_document",
        "document_id": document_id,
        "extraction": method,
        "markdown": markdown_path,
    }


def chunk_criteria_from_markdown(document_id: int, method: str = "stored_markdown") -> dict:
    """Chunk one criteria document from the markdown file already on disk."""
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT document_name, markdown_path FROM criteria_master WHERE id = %s",
                (document_id,),
            )
            document = cur.fetchone()
    if document is None or not document["markdown_path"]:
        raise RuntimeError(f"Criteria document {document_id} has no markdown file")
    text = Path(document["markdown_path"]).read_text(encoding="utf-8", errors="ignore")
    chunks, tables = chunk_criteria(text, Path(document["document_name"]).stem)
    stored = _insert_rows(
        "criteria_chunks", "criteria_tables", document_id, chunks, tables, method, True
    )
    return {
        "document": document["document_name"],
        "document_type": "criteria_document",
        "document_id": document_id,
        "parents": len(chunks),
        "children": sum(len(chunk.children) for chunk in chunks),
        "tables": stored["tables"],
        "stored": stored["stored"],
        "extraction": method,
    }


def ingest_criteria(path: Path) -> dict:
    staged = convert_criteria_to_markdown(path)
    chunked = chunk_criteria_from_markdown(staged["document_id"], staged["extraction"])
    return {**chunked, "markdown": staged["markdown"]}


def ingest_all() -> list[dict]:
    results = []
    ir_dir = project_path("ir_documents")
    criteria_dir = project_path("criteria_documents")
    ir_dir.mkdir(parents=True, exist_ok=True)
    criteria_dir.mkdir(parents=True, exist_ok=True)
    for path in _source_files(ir_dir):
        results.append(ingest_ir(path))
    staged = [convert_criteria_to_markdown(path) for path in _source_files(criteria_dir)]
    for item in staged:
        chunked = chunk_criteria_from_markdown(item["document_id"], item["extraction"])
        results.append({**chunked, "markdown": item["markdown"]})
    return results


def _embed_pending(cur, sql: str, batch_size: int) -> None:
    cur.execute(sql)
    pending = cur.fetchall()
    print("chunks to embed", len(pending))
    for start in range(0, len(pending), batch_size):
        group = pending[start:start + batch_size]
        texts = [row["text"][:6000] for row in group]
        vectors = None
        for attempt in range(4):
            try:
                vectors = embed_texts(texts)
                break
            except Exception as exc:
                print("embed retry", attempt + 1, exc)
                if attempt == 3:
                    raise
                time.sleep(3)
        table = group[0]["table_name"]
        for row, vector in zip(group, vectors):
            cur.execute(
                f"UPDATE {table} SET embedding = %s WHERE id = %s",
                (vector, row["id"]),
            )
        print("embedded", start + len(group), "/", len(pending))


def refresh_metadata_and_embeddings(batch_size: int = 16) -> None:
    """Refresh master metadata and fill embeddings on rows that do not have one yet."""
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, document_name, source_path FROM ir_master")
            for document in cur.fetchall():
                source = Path(document["source_path"] or "")
                if not source.is_file():
                    continue
                text = local_text(source)
                meta = extract_metadata(text, document["document_name"], "ir_document")
                cur.execute(
                    """
                    UPDATE ir_master
                    SET state = %s, department = %s, office_name = %s, district = %s,
                        audit_period = %s, ir_number = %s, document_title = %s,
                        year = %s, auditee = %s
                    WHERE id = %s
                    """,
                    (
                        meta["state"], meta["department"], meta["office_name"], meta["district"],
                        meta["audit_period"], meta["ir_number"], meta["document_title"],
                        meta["year"], meta["auditee"], document["id"],
                    ),
                )
                print("metadata", document["document_name"], meta["state"], meta["department"])
            cur.execute("SELECT id, document_name, markdown_path FROM criteria_master")
            for document in cur.fetchall():
                markdown = Path(document["markdown_path"] or "")
                if not markdown.is_file():
                    continue
                text = markdown.read_text(encoding="utf-8", errors="ignore")
                meta = extract_metadata(text, document["document_name"], "criteria_document")
                cur.execute(
                    """
                    UPDATE criteria_master
                    SET state = %s, department = %s, ir_number = %s, document_title = %s,
                        instrument_kind = %s, year = %s
                    WHERE id = %s
                    """,
                    (
                        meta["state"], meta["department"], meta["ir_number"], meta["document_title"],
                        meta["instrument_kind"], meta["year"], document["id"],
                    ),
                )
                print("metadata", document["document_name"], meta["state"], meta["instrument_kind"])
            _embed_pending(
                cur,
                """
                SELECT id, chunk AS text, 'ir_chunks' AS table_name
                FROM ir_chunks
                WHERE embedding IS NULL
                """,
                batch_size,
            )
            conn.commit()
            _embed_pending(
                cur,
                """
                SELECT id, chunk AS text, 'criteria_chunks' AS table_name
                FROM criteria_chunks
                WHERE embedding IS NULL
                  AND (
                    role = 'child'
                    OR NOT EXISTS (
                        SELECT 1 FROM criteria_chunks child WHERE child.parent_id = criteria_chunks.id
                    )
                  )
                """,
                batch_size,
            )
            conn.commit()


if __name__ == "__main__":
    load_config()
    for item in ingest_all():
        print(item)
