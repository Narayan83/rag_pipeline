"""Hierarchical chunking, proposition chunking, and legal structure parsing."""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Chunk:
    text: str
    role: str
    chunk_kind: str
    hierarchy_path: str
    metadata: dict = field(default_factory=dict)
    children: list["Chunk"] = field(default_factory=list)


@dataclass
class ExtractedTable:
    text: str
    hierarchy_path: str
    metadata: dict
    chunk_index: int | None = None


_HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
_TABLE_LINE = re.compile(r"^\s*\|.+\|\s*$")
_ACT = re.compile(
    r"(?i)^(?:the\s+)?[A-Z0-9][A-Za-z0-9 ,.'()\-]{6,}(?:act|rules|rule|order|ordinance|code)\b.*$"
)
_GO = re.compile(r"(?i)^(?:g\.?\s*o\.?|government order)\b.*$")
_SECTION = re.compile(
    r"(?i)^(?:section\s+)?(\d+[A-Za-z]?(?:\(\d+\))?)\s*[\.\-\)]\s+\S+"
)
_SECTION_WORD = re.compile(r"(?i)^section\s+(\d+[A-Za-z]?)\b[:\.\-\s]*(.*)$")
_SUB = re.compile(r"(?i)^(?:sub-?section\s+)?\((\d+[A-Za-z]?)\)\s+\S+")
_PROVISO = re.compile(r"(?i)^provided\s+(?:that|further|also)\b")
_PART_LINE = re.compile(
    r"(?i)^(?:#{1,6}\s*)?PART[\s\-]*([IVX]+|\d+)\b(?:[\s\-]*\(([A-Z0-9])\))?"
)
_OBS_LINE = re.compile(
    r"(?i)^(?:#{1,6}\s*)?(?:reference\s+number\s*:\s*)?OBS[-\s]?(\d+)\b"
)
_PARA_LINE = re.compile(
    r"(?i)^(?:#{1,6}\s*)?para(?:graph)?\s+(\d+)\s*[:.\-]"
)


def proposition_chunks(text: str) -> list[str]:
    """Split narrative into short claims. Tables must not be passed here."""
    cleaned = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
    claims: list[str] = []
    for sentence in sentences:
        parts = re.split(r"\s+(?:and|but|while)\s+", sentence, flags=re.IGNORECASE)
        for part in parts:
            piece = part.strip(" ,;")
            if len(piece.split()) >= 3:
                if piece[-1] not in ".!?":
                    piece += "."
                claims.append(piece)
    return claims or ([cleaned.strip()] if cleaned.strip() else [])


def _blocks(markdown: str) -> list[tuple[str, str]]:
    lines = markdown.splitlines()
    blocks: list[tuple[str, str]] = []
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            blocks.append(("text", "\n".join(buffer).strip()))
            buffer.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        heading = _HEADING.match(line.strip())
        if heading:
            flush()
            blocks.append(("heading", heading.group(2).strip()))
            i += 1
            continue
        if _TABLE_LINE.match(line):
            flush()
            table = [line]
            i += 1
            while i < len(lines) and _TABLE_LINE.match(lines[i]):
                table.append(lines[i])
                i += 1
            blocks.append(("table", "\n".join(table)))
            continue
        if not line.strip():
            flush()
        else:
            buffer.append(line)
        i += 1
    flush()
    return [(kind, text) for kind, text in blocks if text.strip()]


def _path(parts: list[str]) -> str:
    return " > ".join(part for part in parts if part)


def _table_grid(markdown: str) -> dict:
    parsed: list[list[str]] = []
    for line in markdown.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(set(cell.replace(" ", "")) <= set("-:") for cell in cells):
            continue
        parsed.append(cells)
    if not parsed:
        return {"headers": [], "rows": []}
    width = max(len(row) for row in parsed)
    headers = parsed[0] + [""] * (width - len(parsed[0]))
    rows = [(row + [""] * (width - len(row)))[:width] for row in parsed[1:]]
    return {"headers": headers, "rows": rows}


def _prose_parent(text: str, path: str, metadata: dict) -> Chunk:
    parent = Chunk(text, "parent", "section", path, metadata)
    for claim in proposition_chunks(text):
        parent.children.append(Chunk(claim, "child", "proposition", path, {}))
    return parent


def _plain_line(line: str) -> str:
    return re.sub(r"^#{1,6}\s*", "", line).strip()


def _part_label(line: str) -> str | None:
    if _TABLE_LINE.match(line):
        return None
    match = _PART_LINE.match(line.strip())
    if not match:
        return None
    suffix = f"-({match.group(2).upper()})" if match.group(2) else ""
    return f"PART-{match.group(1).upper()}{suffix}"


def _is_part_ii(label: str) -> bool:
    return bool(re.match(r"PART-II\b", label))


def _obs_ref(line: str) -> str | None:
    if _TABLE_LINE.match(line):
        return None
    match = _OBS_LINE.match(line.strip())
    return f"OBS-{match.group(1)}" if match else None


def _para_ref(line: str) -> str | None:
    if _TABLE_LINE.match(line):
        return None
    match = _PARA_LINE.match(line.strip())
    return f"PARA-{match.group(1)}" if match else None


def _peel_tables(text: str) -> tuple[str, list[dict]]:
    prose: list[str] = []
    tables: list[dict] = []
    for kind, block in _blocks(text):
        if kind == "table":
            tables.append({"text": block, "metadata": _table_grid(block)})
        else:
            prose.append(block)
    return "\n\n".join(prose).strip(), tables


def _part_sections(text: str) -> list[tuple[str, str]]:
    label = "PREAMBLE"
    buffer: list[str] = []
    sections: list[tuple[str, str]] = []

    def flush() -> None:
        body = "\n".join(buffer).strip()
        if body:
            sections.append((label, body))

    for line in text.splitlines():
        part = _part_label(line)
        if part:
            flush()
            buffer = []
            label = part
            continue
        buffer.append(line)
    flush()
    if len(sections) >= 2 and sections[0][0] == "PREAMBLE":
        following_label, following_body = sections[1]
        sections[1] = (following_label, f"{sections[0][1]}\n\n{following_body}".strip())
        sections = sections[1:]
    return sections


def _observation_pieces(body: str) -> list[tuple[str | None, str]]:
    has_obs = any(_obs_ref(line) for line in body.splitlines())
    has_para = any(_para_ref(line) for line in body.splitlines())
    splitter = _obs_ref if has_obs else _para_ref if has_para else None
    if splitter is None:
        return [(None, body)]
    pieces: list[tuple[str | None, str]] = []
    ref: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        text = "\n".join(buffer).strip()
        if text:
            pieces.append((ref, text))

    for line in body.splitlines():
        marker = splitter(line)
        if marker:
            flush()
            buffer = []
            ref = marker
        buffer.append(line)
    flush()
    return pieces


def _is_label_only(text: str) -> bool:
    """True for a part subtitle such as '(Audit Findings)', not for a real passage."""
    prose, tables = _peel_tables(text)
    if tables or re.search(r"(?i)\bnil\b", prose):
        return False
    lines = [line.strip() for line in prose.splitlines() if line.strip()]
    if not lines:
        return True
    return all(re.fullmatch(r"\(?[A-Za-z][A-Za-z\s/,&\-]{0,80}\)?", line) for line in lines)


def chunk_ir(text: str, document_name: str) -> tuple[list[Chunk], list[ExtractedTable]]:
    """Part I and the other non-finding parts are one chunk each.

    Part II is split into one chunk per observation. Tables are returned
    separately so they can be stored in ir_tables.
    """
    sections = _part_sections(text)
    has_parts = any(label != "PREAMBLE" for label, _body in sections)
    chunks: list[Chunk] = []
    tables: list[ExtractedTable] = []
    for label, body in sections:
        pieces = _observation_pieces(body) if (_is_part_ii(label) or not has_parts) else [(None, body)]
        if any(ref for ref, _piece in pieces):
            pieces = [(ref, piece) for ref, piece in pieces if ref or not _is_label_only(piece)]
        elif label == "PART-II" and _is_label_only(body):
            continue
        for ref, piece in pieces:
            prose, peeled = _peel_tables(piece)
            if not prose and not peeled:
                continue
            heading = label if label != "PREAMBLE" else "Document"
            if ref:
                heading = f"{heading} | {ref}" if label != "PREAMBLE" else ref
            chunk_text = f"{heading}\n\n{prose}".strip() if prose else heading
            path = _path([document_name, label if label != "PREAMBLE" else "", ref or ""])
            index = len(chunks)
            chunks.append(Chunk(
                chunk_text,
                "parent",
                "observation" if ref else "part",
                path,
                {
                    "part": None if label == "PREAMBLE" else label,
                    "observation_ref": ref,
                    "heading": heading,
                },
            ))
            for table in peeled:
                tables.append(ExtractedTable(
                    table["text"],
                    path,
                    {**table["metadata"], "part": None if label == "PREAMBLE" else label, "observation_ref": ref},
                    index,
                ))
    return chunks, tables


def chunk_criteria(markdown: str, document_name: str) -> tuple[list[Chunk], list[ExtractedTable]]:
    """Act, section, sub-section, and proviso stay as chunks. Tables are separate."""
    parents: list[Chunk] = []
    tables: list[ExtractedTable] = []
    act = document_name
    section = ""
    subsection = ""
    proviso = ""
    prose: list[str] = []

    def level_meta() -> dict:
        return {"act": act, "section": section, "subsection": subsection, "proviso": proviso}

    def flush_prose() -> None:
        if not prose:
            return
        path = _path([act, section, subsection, proviso]) or document_name
        parents.append(_prose_parent("\n\n".join(prose), path, level_meta()))
        prose.clear()

    for kind, text in _blocks(markdown):
        first = text.splitlines()[0].strip()
        if kind == "table":
            flush_prose()
            path = _path([act, section, subsection, proviso]) or document_name
            index = len(parents) - 1 if parents and parents[-1].hierarchy_path == path else None
            tables.append(ExtractedTable(text, path, {**level_meta(), **_table_grid(text)}, index))
            continue
        changed = False
        if kind == "heading" or _ACT.match(first) or _GO.match(first):
            if not _SECTION_WORD.match(first) and not _SUB.match(first) and not _PROVISO.match(first):
                if re.search(r"(?i)\bact\b|\brules\b|\border\b", first) or _GO.match(first) or kind == "heading":
                    flush_prose()
                    act = first[:240]
                    section = subsection = proviso = ""
                    changed = True
                    prose.append(text)
        if _SECTION_WORD.match(first) or (_SECTION.match(first) and not _SUB.match(first)):
            label = (_SECTION_WORD.match(first) or _SECTION.match(first)).group(1)
            flush_prose()
            section = f"Section {label}"
            subsection = proviso = ""
            changed = True
            prose.append(text)
        elif _SUB.match(first):
            flush_prose()
            subsection = f"Sub-section {first[:40]}"
            proviso = ""
            changed = True
            prose.append(text)
        elif _PROVISO.match(first):
            flush_prose()
            proviso = "Proviso"
            changed = True
            prose.append(text)
        elif not changed:
            prose.append(text)
    flush_prose()
    return parents, tables


def chunk_rule(markdown: str, document_name: str) -> tuple[list[Chunk], list[ExtractedTable]]:
    return chunk_criteria(markdown, document_name)
