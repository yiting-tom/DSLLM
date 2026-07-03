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
    def topk(self, vector: list[float], k: int) -> list[dict]: ...


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


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

    def topk(self, vector: list[float], k: int = 5) -> list[dict]:
        rows = self.db.execute("SELECT id, text, metadata, vector FROM chunks").fetchall()
        scored = []
        for cid, text, meta, vec in rows:
            scored.append({
                "id": cid, "text": text,
                "metadata": json.loads(meta),
                "score": _cosine(vector, json.loads(vec)),
            })
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:k]
