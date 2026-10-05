"""Educational late-chunking / contextual-pooling demo.

Idea:
1. Encode the WHOLE document so every token representation sees surrounding text.
2. Define chunk spans afterwards.
3. Mean-pool the contextual token vectors that overlap each span.

This is a compact teaching implementation, not a production library.
Install: pip install transformers torch
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import torch
from transformers import AutoModel, AutoTokenizer


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    text: str


def paragraph_spans(text: str) -> list[Span]:
    spans: list[Span] = []
    for match in re.finditer(r"\S(?:.*?\S)?(?=\n\s*\n|\Z)", text, flags=re.DOTALL):
        spans.append(Span(match.start(), match.end(), match.group(0)))
    return spans


def late_chunk_embeddings(
    text: str,
    spans: list[Span],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> torch.Tensor:
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    model = AutoModel.from_pretrained(model_name)
    model.eval()

    batch = tokenizer(
        text,
        return_tensors="pt",
        return_offsets_mapping=True,
        truncation=True,
        max_length=min(getattr(tokenizer, "model_max_length", 512), 512),
    )
    offsets = batch.pop("offset_mapping")[0]

    with torch.no_grad():
        token_vectors = model(**batch).last_hidden_state[0]

    pooled: list[torch.Tensor] = []
    for span in spans:
        mask = []
        for token_start, token_end in offsets.tolist():
            is_special = token_start == token_end == 0
            overlaps = token_end > span.start and token_start < span.end
            mask.append((not is_special) and overlaps)
        mask_tensor = torch.tensor(mask, dtype=torch.bool)
        if not mask_tensor.any():
            pooled.append(torch.zeros(token_vectors.shape[-1]))
        else:
            pooled.append(token_vectors[mask_tensor].mean(dim=0))

    return torch.stack(pooled)


def main() -> None:
    text = Path(__file__).with_name("sample_policy.txt").read_text(encoding="utf-8")
    spans = paragraph_spans(text)
    vectors = late_chunk_embeddings(text, spans)
    print("chunks:", len(spans))
    print("embedding matrix:", tuple(vectors.shape))
    for i, span in enumerate(spans[:3], start=1):
        print(f"\n--- span {i} ---\n{span.text[:180]}")


if __name__ == "__main__":
    main()
