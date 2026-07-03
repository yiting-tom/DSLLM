"""embedding:OpenAI 相容端點(self-host bge-m3 / Qwen3-Embedding)。"""
from __future__ import annotations

import httpx
from openai import OpenAI

from .. import config

_client: OpenAI | None = None


def _c() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=config.EMBED_BASE_URL,
            api_key=config.EMBED_API_KEY,
            http_client=httpx.Client(verify=config.SSL_VERIFY, timeout=120),
        )
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    out: list[list[float]] = []
    for i in range(0, len(texts), config.EMBED_BATCH):
        batch = texts[i:i + config.EMBED_BATCH]
        resp = _c().embeddings.create(model=config.EMBED_MODEL, input=batch)
        out.extend(d.embedding for d in resp.data)
    return out
