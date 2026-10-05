# Chunking Methods — Teaching Code

All examples use the same `sample_policy.txt` so learners can compare boundaries directly.

## Dependency-free examples

```bash
python fixed_size_chunking.py
python sliding_window_chunking.py
python sentence_paragraph_chunking.py
python recursive_chunking.py
python hierarchical_chunking.py
python parent_child_chunking.py
python structure_aware_chunking.py
python agentic_chunking.py
python proposition_chunking.py
python compare_chunkers.py
```

## Embedding-based examples

```bash
python -m pip install -r requirements.txt
python semantic_chunking.py
python late_chunking_demo.py
```

`semantic_chunking.py` uses `sentence-transformers/all-MiniLM-L6-v2` to compare adjacent sentence embeddings. `late_chunking_demo.py` encodes the document first and pools token representations into chunk spans afterwards.

## Teaching notes

- The fixed-size examples count whitespace-separated words rather than exact model tokens, keeping the baseline easy to read. In production, use the tokenizer for your embedding / generation model.
- `agentic_chunking.py` is provider-agnostic: replace the included heuristic boundary decider with an LLM call.
- `proposition_chunking.py` uses a deliberately simple offline decomposer. High-quality proposition extraction normally needs a stronger NLP or LLM component.
- `late_chunking_demo.py` is intentionally compact and truncates long inputs according to the model context window. Production systems should handle long documents with an appropriate long-context strategy.
