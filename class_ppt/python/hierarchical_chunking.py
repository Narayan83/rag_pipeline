"""Hierarchical chunking for Markdown-like documents.

Build a tree of heading -> subsection -> paragraph nodes. Retrieval systems can
index leaf nodes while retaining paths to larger parent context.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class Node:
    title: str
    level: int
    text: str = ""
    children: list["Node"] = field(default_factory=list)

    def walk(self, path: tuple[str, ...] = ()):
        current_path = path + ((self.title,) if self.title else ())
        yield current_path, self
        for child in self.children:
            yield from child.walk(current_path)


def parse_markdown_hierarchy(text: str) -> Node:
    root = Node(title="DOCUMENT", level=0)
    stack = [root]

    for block in re.split(r"\n\s*\n", text.strip()):
        block = block.strip()
        heading = re.match(r"^(#{1,6})\s+(.+)$", block)
        if heading:
            level = len(heading.group(1))
            node = Node(title=heading.group(2).strip(), level=level)
            while stack[-1].level >= level:
                stack.pop()
            stack[-1].children.append(node)
            stack.append(node)
        else:
            paragraph = Node(title="", level=stack[-1].level + 1, text=block)
            stack[-1].children.append(paragraph)
    return root


def leaf_chunks(root: Node) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []
    for path, node in root.walk():
        if node.text:
            chunks.append({"path": " > ".join(path), "text": node.text})
    return chunks


def main() -> None:
    text = Path(__file__).with_name("sample_policy.txt").read_text(encoding="utf-8")
    root = parse_markdown_hierarchy(text)
    for item in leaf_chunks(root):
        print(f"\n[{item['path']}]\n{item['text']}")


if __name__ == "__main__":
    main()
