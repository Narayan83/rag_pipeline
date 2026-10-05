"""Structure-aware chunking for Markdown.

The parser keeps headings, code fences, tables, and paragraphs as distinct block
types, then packs blocks without splitting the most meaningful structures.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class Block:
    kind: str
    text: str


def markdown_blocks(text: str) -> list[Block]:
    lines = text.splitlines()
    blocks: list[Block] = []
    buffer: list[str] = []
    in_code = False

    def flush_paragraph() -> None:
        nonlocal buffer
        if buffer:
            blocks.append(Block("paragraph", "\n".join(buffer).strip()))
            buffer = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            flush_paragraph()
            code = [line]
            in_code = not in_code
            i += 1
            while i < len(lines):
                code.append(lines[i])
                if lines[i].strip().startswith("```"):
                    in_code = False
                    i += 1
                    break
                i += 1
            blocks.append(Block("code", "\n".join(code)))
            continue

        if re.match(r"^#{1,6}\s+", line):
            flush_paragraph()
            blocks.append(Block("heading", line.strip()))
        elif line.startswith("|") and "|" in line[1:]:
            flush_paragraph()
            table = [line]
            i += 1
            while i < len(lines) and lines[i].startswith("|"):
                table.append(lines[i])
                i += 1
            blocks.append(Block("table", "\n".join(table)))
            continue
        elif not line.strip():
            flush_paragraph()
        else:
            buffer.append(line)
        i += 1

    flush_paragraph()
    return blocks


def pack_blocks(blocks: list[Block], max_chars: int = 500) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    length = 0

    for block in blocks:
        extra = len(block.text) + (2 if current else 0)
        if current and length + extra > max_chars:
            chunks.append("\n\n".join(current))
            current, length = [], 0
        current.append(block.text)
        length += extra

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def main() -> None:
    text = Path(__file__).with_name("sample_policy.txt").read_text(encoding="utf-8")
    blocks = markdown_blocks(text)
    print("Detected block kinds:", [b.kind for b in blocks])
    for i, chunk in enumerate(pack_blocks(blocks), start=1):
        print(f"\n--- chunk {i} ---\n{chunk}")


if __name__ == "__main__":
    main()
