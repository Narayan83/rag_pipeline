"""Parent-child chunking.

Create small child chunks for precise retrieval, but keep a link to a larger
parent chunk that can be supplied to the LLM after a child matches.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class ParentChunk:
    parent_id: str
    text: str


@dataclass(frozen=True)
class ChildChunk:
    child_id: str
    parent_id: str
    text: str


def _word_windows(text: str, size: int = 35) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)]


def build_parent_child_chunks(text: str) -> tuple[list[ParentChunk], list[ChildChunk]]:
    sections = [s.strip() for s in re.split(r"(?=^##\s+)", text, flags=re.MULTILINE) if s.strip()]
    parents: list[ParentChunk] = []
    children: list[ChildChunk] = []

    for p_index, section in enumerate(sections, start=1):
        parent_id = f"P{p_index:02d}"
        parents.append(ParentChunk(parent_id, section))
        for c_index, child_text in enumerate(_word_windows(section), start=1):
            children.append(ChildChunk(f"{parent_id}-C{c_index:02d}", parent_id, child_text))

    return parents, children


def expand_hit(child: ChildChunk, parents: list[ParentChunk]) -> str:
    """Return the full parent text after a child is retrieved."""
    by_id = {p.parent_id: p.text for p in parents}
    return by_id[child.parent_id]


def main() -> None:
    text = Path(__file__).with_name("sample_policy.txt").read_text(encoding="utf-8")
    parents, children = build_parent_child_chunks(text)

    print("Children to index:")
    for child in children[:5]:
        print(child)

    print("\nExpanded context for first hit:\n")
    print(expand_hit(children[0], parents))


if __name__ == "__main__":
    main()
