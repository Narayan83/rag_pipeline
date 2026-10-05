"""OCR, embedding, and chat clients for the internal endpoints."""
from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import load_config


def _timeout() -> httpx.Timeout:
    read = float(load_config()["services"]["request_timeout_seconds"])
    return httpx.Timeout(connect=5.0, read=read, write=30.0, pool=5.0)


def _first_vector(payload: Any) -> list[float] | None:
    if isinstance(payload, list) and payload and isinstance(payload[0], (int, float)):
        return [float(x) for x in payload]
    if isinstance(payload, dict):
        for key in ("embedding", "vector", "embeddings"):
            found = _first_vector(payload.get(key))
            if found:
                return found
        data = payload.get("data")
        if isinstance(data, list) and data:
            found = _first_vector(data[0])
            if found:
                return found
        for value in payload.values():
            found = _first_vector(value)
            if found:
                return found
    return None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """POST raw JSON. `input` is one chunk or a list of chunks."""
    services = load_config()["services"]
    endpoint = services["embed_url"].rstrip("/") + "/v1/embeddings"
    body = {"model": services["embed_model"], "input": texts}
    with httpx.Client(timeout=_timeout()) as client:
        response = client.post(endpoint, json=body)
        response.raise_for_status()
        payload = response.json()
    rows = payload.get("data") or []
    vectors = [_first_vector(row) for row in rows]
    if len(vectors) != len(texts) or any(vector is None for vector in vectors):
        raise RuntimeError("embedding service did not return one vector per chunk")
    return vectors  # type: ignore[return-value]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]


def ocr_to_markdown(file_path: str, filename: str) -> str:
    """Render each PDF page and transcribe it with the OCR chat model."""
    import base64
    from pathlib import Path

    import pymupdf

    path = Path(file_path)
    if path.suffix.lower() != ".pdf":
        raise RuntimeError("OCR endpoint expects page images; non-PDF files use local text")
    services = load_config()["services"]
    endpoint = services["ocr_url"].rstrip("/") + "/v1/chat/completions"
    document = pymupdf.open(path)
    pages: list[str] = []
    with httpx.Client(timeout=_timeout()) as client:
        for index, page in enumerate(document, start=1):
            image = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).tobytes("png")
            encoded = base64.b64encode(image).decode()
            payload = {
                "model": services["ocr_model"],
                "temperature": 0,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}},
                        {"type": "text", "text": "Transcribe this page to markdown. Keep headings and tables."},
                    ],
                }],
            }
            response = client.post(endpoint, json=payload)
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"] or ""
            if text.strip():
                pages.append(f"## Page {index}\n\n{text.strip()}")
    if not pages:
        raise RuntimeError("OCR returned no text")
    return "\n\n".join(pages)


def _markdown_from_response(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "")
    if "json" in content_type:
        payload = response.json()
        if isinstance(payload, str):
            return payload
        for key in ("markdown", "md", "text", "content", "result"):
            value = payload.get(key) if isinstance(payload, dict) else None
            if isinstance(value, str) and value.strip():
                return value
        return json.dumps(payload, ensure_ascii=False)
    return response.text


def summarize(question: str, context: str) -> str:
    """Ask the chat endpoint to answer from the retrieved chunks only."""
    services = load_config()["services"]
    url = services["llm_url"].rstrip("/") + "/v1/chat/completions"
    payload = {
        "model": services["llm_model"],
        "temperature": 0.1,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You answer questions about inspection reports and criteria documents "
                    "(Acts, Rules, and Government Orders). Use only the supplied chunks. "
                    "If they do not contain the answer, say so. Cite the document "
                    "name and hierarchy path for each point you use."
                ),
            },
            {
                "role": "user",
                "content": f"Question:\n{question}\n\nRetrieved chunks:\n{context}",
            },
        ],
    }
    with httpx.Client(timeout=_timeout()) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    return data["choices"][0]["message"]["content"] or ""
