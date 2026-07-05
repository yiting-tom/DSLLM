"""讀 OKF bundle 的 .md → Chunk(id / text / content_hash / metadata)。
一個 concept = 一個 chunk(md 本身就是天然邊界)。"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

RESERVED = {"index.md", "log.md"}

# 帶進 metadata 供檢索過濾/加權/graph 展開的 frontmatter 欄位
META_KEYS = ("id", "type", "title", "slug", "tags", "confidence",
            "generated", "resource", "provenance", "related")


@dataclass
class Chunk:
    id: str
    text: str
    content_hash: str
    metadata: dict
    path: str


def _parse(md: str) -> tuple[dict, str]:
    if md.startswith("---"):
        parts = md.split("---", 2)
        if len(parts) == 3:
            return yaml.safe_load(parts[1]) or {}, parts[2].strip()
    return {}, md.strip()


def _content_hash(body: str) -> str:
    return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()


def load_chunks(bundle_root: str | Path) -> list[Chunk]:
    root = Path(bundle_root)
    chunks: list[Chunk] = []
    for p in sorted(root.rglob("*.md")):
        if p.name in RESERVED:
            continue
        fm, body = _parse(p.read_text(encoding="utf-8"))
        cid = fm.get("id")
        if not cid:                      # 沒 id 的不是合規 concept,跳過
            continue
        # 嵌入文字:標題+摘要前置,語意訊號更強
        text = "\n".join(x for x in (fm.get("title", ""), fm.get("description", ""), body) if x)
        meta = {k: fm.get(k) for k in META_KEYS if k in fm}
        chunks.append(Chunk(
            id=cid,
            text=text,
            content_hash=fm.get("content_hash") or _content_hash(body),
            metadata=meta,
            path=str(p),
        ))
    return chunks
