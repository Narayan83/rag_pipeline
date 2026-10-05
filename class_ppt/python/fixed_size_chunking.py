"""Fixed-size chunking.

Teaching goal:
Split text into equally sized windows. This is predictable and fast, but it can
cut across sentence or topic boundaries.

This example uses whitespace-delimited words as a lightweight stand-in for
model tokens. In production, count tokens with the tokenizer used by your
embedding / generation model.
"""
from __future__ import annotations

from pathlib import Path


def fixed_size_chunks(text: str, chunk_size: int = 60) -> list[str]:
    """Return non-overlapping chunks containing at most `chunk_size` words."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")

    words = text.split()
    return [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]


def main() -> None:
    text = Path(__file__).with_name("sample_policy.txt").read_text(encoding="utf-8")
    for i, chunk in enumerate(fixed_size_chunks(text, chunk_size=55), start=1):
        print(f"\n--- chunk {i} ---\n{chunk}")


if __name__ == "__main__":
    main()
