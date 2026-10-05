"""Sentence- and paragraph-aware chunking using only the Python standard library."""
from __future__ import annotations

import re
from pathlib import Path

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> list[str]:
    """A compact teaching sentence splitter; use an NLP tokenizer for complex text."""
    return [s.strip() for s in _SENTENCE_END.split(text.strip()) if s.strip()]


def paragraph_chunks(text: str, max_words: int = 90) -> list[str]:
    """Pack whole paragraphs when possible; split oversized paragraphs by sentence."""
    if max_words <= 0:
        raise ValueError("max_words must be > 0")

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    def flush() -> None:
        nonlocal current, current_words
        if current:
            chunks.append("\n\n".join(current))
            current, current_words = [], 0

    for paragraph in paragraphs:
        words = paragraph.split()
        if len(words) <= max_words:
            if current and current_words + len(words) > max_words:
                flush()
            current.append(paragraph)
            current_words += len(words)
            continue

        flush()
        sentence_group: list[str] = []
        sentence_words = 0
        for sentence in split_sentences(paragraph):
            n = len(sentence.split())
            if sentence_group and sentence_words + n > max_words:
                chunks.append(" ".join(sentence_group))
                sentence_group, sentence_words = [], 0
            sentence_group.append(sentence)
            sentence_words += n
        if sentence_group:
            chunks.append(" ".join(sentence_group))

    flush()
    return chunks


def main() -> None:
    text = Path(__file__).with_name("sample_policy.txt").read_text(encoding="utf-8")
    for i, chunk in enumerate(paragraph_chunks(text), start=1):
        print(f"\n--- chunk {i} ---\n{chunk}")


if __name__ == "__main__":
    main()
