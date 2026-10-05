"""Fixed-size chunking with overlap (sliding window).

Overlap protects facts that sit near a chunk boundary, but it increases the
number of chunks and duplicates some text in the vector store.
"""
from __future__ import annotations

from pathlib import Path


def sliding_window_chunks(
    text: str,
    chunk_size: int = 60,
    overlap: int = 12,
) -> list[str]:
    """Return word windows of `chunk_size` with `overlap` words repeated."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")

    words = text.split()
    step = chunk_size - overlap
    chunks: list[str] = []

    for start in range(0, len(words), step):
        window = words[start : start + chunk_size]
        if not window:
            break
        chunks.append(" ".join(window))
        if start + chunk_size >= len(words):
            break
    return chunks


def main() -> None:
    text = Path(__file__).with_name("sample_policy.txt").read_text(encoding="utf-8")
    for i, chunk in enumerate(sliding_window_chunks(text, 55, 12), start=1):
        print(f"\n--- chunk {i} ---\n{chunk}")


if __name__ == "__main__":
    main()
