"""Proposition-based chunking: decompose text into small, atomic claims.

True proposition extraction is usually best performed by a capable NLP / LLM
component. This teaching version provides an injectable decomposer and a simple
heuristic fallback so the file can run offline.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import re

Decomposer = Callable[[str], list[str]]


def sentences(text: str) -> list[str]:
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def heuristic_decompose(sentence: str) -> list[str]:
    """Split some compound sentences into smaller claims; intentionally simple."""
    parts = re.split(r"\s+(?:and|but|while)\s+", sentence, flags=re.IGNORECASE)
    return [p.strip(" ,.;") + "." for p in parts if len(p.split()) >= 3]


def proposition_chunks(text: str, decompose: Decomposer = heuristic_decompose) -> list[str]:
    propositions: list[str] = []
    for sentence in sentences(text):
        pieces = decompose(sentence)
        propositions.extend(pieces or [sentence])
    return propositions


def main() -> None:
    text = Path(__file__).with_name("sample_policy.txt").read_text(encoding="utf-8")
    for i, proposition in enumerate(proposition_chunks(text), start=1):
        print(f"{i:02d}. {proposition}")


if __name__ == "__main__":
    main()
