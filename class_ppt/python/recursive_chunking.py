"""Recursive separator-based chunking.

The algorithm tries coarse separators first (sections / paragraphs), then falls
back to finer separators (lines / sentences / spaces) until pieces fit.
"""
from __future__ import annotations

from pathlib import Path

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def _hard_split(text: str, max_chars: int) -> list[str]:
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]


def recursive_chunks(
    text: str,
    max_chars: int = 420,
    separators: list[str] | None = None,
) -> list[str]:
    """Split text recursively while preferring natural boundaries."""
    if max_chars <= 0:
        raise ValueError("max_chars must be > 0")
    separators = separators or DEFAULT_SEPARATORS

    def split_piece(piece: str, level: int) -> list[str]:
        piece = piece.strip()
        if not piece:
            return []
        if len(piece) <= max_chars:
            return [piece]
        if level >= len(separators):
            return _hard_split(piece, max_chars)

        sep = separators[level]
        if sep == "":
            return _hard_split(piece, max_chars)

        raw_parts = piece.split(sep)
        if len(raw_parts) == 1:
            return split_piece(piece, level + 1)

        # First recursively fix any oversized part.
        parts: list[str] = []
        for raw in raw_parts:
            raw = raw.strip()
            if not raw:
                continue
            parts.extend(split_piece(raw, level + 1) if len(raw) > max_chars else [raw])

        # Then greedily merge adjacent parts back up to max_chars.
        merged: list[str] = []
        current = ""
        joiner = sep if sep != ". " else ". "
        for part in parts:
            candidate = part if not current else current + joiner + part
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    merged.append(current)
                current = part
        if current:
            merged.append(current)
        return merged

    return split_piece(text, 0)


def main() -> None:
    text = Path(__file__).with_name("sample_policy.txt").read_text(encoding="utf-8")
    for i, chunk in enumerate(recursive_chunks(text), start=1):
        print(f"\n--- chunk {i} ({len(chunk)} chars) ---\n{chunk}")


if __name__ == "__main__":
    main()
