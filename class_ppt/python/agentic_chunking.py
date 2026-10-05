"""Agentic / LLM-assisted chunking scaffold.

A real agentic chunker can ask an LLM whether two neighboring segments belong
in the same conceptual chunk. To keep this file runnable without an API key,
we inject a boundary-decider function and ship a deterministic heuristic demo.
Replace `heuristic_decider` with your own LLM call.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import re

BoundaryDecider = Callable[[str, str], bool]
# Return True when a NEW chunk should begin between left and right.


def candidate_segments(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def heuristic_decider(left: str, right: str) -> bool:
    """Demo policy: headings and topic keywords trigger a new chunk."""
    if right.lstrip().startswith("#"):
        return True
    topic_words = {"eligibility", "annual", "sick", "parental", "approval", "purpose"}
    right_lower = right.lower()
    return any(word in right_lower[:80] for word in topic_words)


def build_llm_prompt(left: str, right: str) -> str:
    """Example prompt to send to the LLM used as the boundary-decider."""
    return f"""Decide whether a new semantic chunk should begin between A and B.
Return only NEW_CHUNK or SAME_CHUNK.

A:
{left}

B:
{right}
"""


def agentic_chunks(text: str, decide_boundary: BoundaryDecider) -> list[str]:
    segments = candidate_segments(text)
    if not segments:
        return []

    chunks: list[list[str]] = [[segments[0]]]
    for segment in segments[1:]:
        previous = chunks[-1][-1]
        if decide_boundary(previous, segment):
            chunks.append([segment])
        else:
            chunks[-1].append(segment)
    return ["\n\n".join(group) for group in chunks]


def main() -> None:
    text = Path(__file__).with_name("sample_policy.txt").read_text(encoding="utf-8")
    for i, chunk in enumerate(agentic_chunks(text, heuristic_decider), start=1):
        print(f"\n--- agentic-style chunk {i} ---\n{chunk}")


if __name__ == "__main__":
    main()
