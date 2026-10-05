"""Semantic chunking with Sentence Transformers.

Adjacent sentences are embedded. A new chunk begins when similarity drops below
`similarity_threshold` or the current chunk becomes too large.

Install: pip install sentence-transformers numpy
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    return [s.strip() for s in _SENTENCE_END.split(cleaned) if s.strip()]


def semantic_chunks(
    text: str,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    similarity_threshold: float = 0.42,
    max_sentences: int = 5,
) -> list[str]:
    sentences = split_sentences(text)
    if not sentences:
        return []

    model = SentenceTransformer(model_name)
    embeddings = model.encode(sentences, normalize_embeddings=True)

    chunks: list[list[str]] = [[sentences[0]]]
    for i in range(1, len(sentences)):
        # With normalized vectors, dot product equals cosine similarity.
        similarity = float(np.dot(embeddings[i - 1], embeddings[i]))
        current = chunks[-1]

        if similarity < similarity_threshold or len(current) >= max_sentences:
            chunks.append([sentences[i]])
        else:
            current.append(sentences[i])

    return [" ".join(group) for group in chunks]


def main() -> None:
    text = Path(__file__).with_name("sample_policy.txt").read_text(encoding="utf-8")
    chunks = semantic_chunks(text)
    for i, chunk in enumerate(chunks, start=1):
        print(f"\n--- semantic chunk {i} ---\n{chunk}")


if __name__ == "__main__":
    main()
