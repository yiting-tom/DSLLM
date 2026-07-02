"""共用的 LLM client 與防禦式 JSON 解析。"""
from __future__ import annotations

import json
import httpx
from openai import OpenAI

from . import config

_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY,
            http_client=httpx.Client(verify=config.SSL_VERIFY, timeout=600),
        )
    return _client


def chat(system: str, content, temperature: float = 0.2) -> str:
    """content 可為 str 或 OpenAI 多模態 blocks list。"""
    resp = client().chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1].removeprefix("json").strip()
    return text


def parse_array(text: str) -> list:
    text = _strip_fence(text)
    s, e = text.find("["), text.rfind("]")
    if s == -1 or e == -1:
        raise ValueError(f"輸出不含 JSON 陣列:{text[:200]}")
    return json.loads(text[s:e + 1])


def parse_object(text: str) -> dict:
    text = _strip_fence(text)
    s, e = text.find("{"), text.rfind("}")
    if s == -1 or e == -1:
        raise ValueError(f"輸出不含 JSON 物件:{text[:200]}")
    return json.loads(text[s:e + 1])
