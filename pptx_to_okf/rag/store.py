"""向量庫(Phase 1:sqlite 暴力 cosine,零 infra)。

Store 是抽象介面;規模上來後換 Qdrant/pgvector 只要換這個實作。
append-only:靠 (id, content_hash) 判斷是否需要重嵌(架構 §7 陷阱③)。
"""
from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Protocol


class Store(Protocol):
    def has(self, cid: str, content_hash: str) -> bool: ...
    def upsert(self, cid: str, content_hash: str, text: str, metadata: dict, vector: list[float]) -> None: ...
    def topk(self, vector: list[float], k: int,
             where: dict | None = None, exclude_id: str | None = None) -> list[dict]: ...


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _match(m: dict, where: dict | None) -> bool:
    """facet 過濾:where 為 None 時全通過(行為不變)。"""
    if not where:
        return True
    if (t := where.get("type")) and m.get("type") != t:
        return False
    if (tags := where.get("tags_any")) and not (set(tags) & set(m.get("tags") or [])):
        return False
    if where.get("exclude_low_confidence") and m.get("confidence") == "low":
        return False
    if where.get("facts_only") and m.get("generated"):
        return False
    return True


class SqliteStore:
    def __init__(self, path: str | Path):
        self.db = sqlite3.connect(str(path))
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS chunks("
            "id TEXT PRIMARY KEY, content_hash TEXT, text TEXT, metadata TEXT, vector TEXT)"
        )
        self.db.commit()

    def has(self, cid: str, content_hash: str) -> bool:
        row = self.db.execute(
            "SELECT 1 FROM chunks WHERE id=? AND content_hash=?", (cid, content_hash)
        ).fetchone()
        return row is not None

    def upsert(self, cid: str, content_hash: str, text: str, metadata: dict, vector: list[float]) -> None:
        self.db.execute(
            "INSERT INTO chunks(id, content_hash, text, metadata, vector) VALUES(?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET content_hash=excluded.content_hash, "
            "text=excluded.text, metadata=excluded.metadata, vector=excluded.vector",
            (cid, content_hash, text, json.dumps(metadata, ensure_ascii=False), json.dumps(vector)),
        )
        self.db.commit()

    def topk(self, vector: list[float], k: int = 5,
             where: dict | None = None, exclude_id: str | None = None) -> list[dict]:
        rows = self.db.execute("SELECT id, text, metadata, vector FROM chunks").fetchall()
        scored = []
        for cid, text, meta, vec in rows:
            if cid == exclude_id:
                continue
            m = json.loads(meta)
            if not _match(m, where):          # 過濾在排序前套用,k 名額給符合者
                continue
            scored.append({
                "id": cid, "text": text, "metadata": m,
                "score": _cosine(vector, json.loads(vec)),
            })
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:k]
