"""Run the dependency-free chunkers side by side on the same document."""
from __future__ import annotations

from pathlib import Path

from agentic_chunking import agentic_chunks, heuristic_decider
from fixed_size_chunking import fixed_size_chunks
from hierarchical_chunking import leaf_chunks, parse_markdown_hierarchy
from parent_child_chunking import build_parent_child_chunks
from recursive_chunking import recursive_chunks
from sentence_paragraph_chunking import paragraph_chunks
from sliding_window_chunking import sliding_window_chunks
from structure_aware_chunking import markdown_blocks, pack_blocks


def main() -> None:
    text = Path(__file__).with_name("sample_policy.txt").read_text(encoding="utf-8")

    methods = {
        "fixed": fixed_size_chunks(text, 55),
        "overlap": sliding_window_chunks(text, 55, 12),
        "paragraph": paragraph_chunks(text),
        "recursive": recursive_chunks(text),
        "structure-aware": pack_blocks(markdown_blocks(text)),
        "agentic-scaffold": agentic_chunks(text, heuristic_decider),
        "hierarchical-leaves": [x["text"] for x in leaf_chunks(parse_markdown_hierarchy(text))],
    }
    parents, children = build_parent_child_chunks(text)
    methods["parent-child (children)"] = [c.text for c in children]

    for name, chunks in methods.items():
        lengths = [len(c.split()) for c in chunks]
        print(f"{name:24s}: {len(chunks):2d} chunks | words/chunk = {lengths}")

    print(f"parent-child parents      : {len(parents):2d} parent chunks")


if __name__ == "__main__":
    main()
