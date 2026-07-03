"""RAG ingest(append-only、增量):OKF bundle → 向量庫。

    python -m pptx_to_okf.rag.ingest ./bundle

content_hash 沒變的 concept 直接跳過(不重嵌),實現架構 §7 陷阱③。
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .. import config
from . import embed as _embed
from .chunk import load_chunks
from .store import SqliteStore, Store


def ingest(bundle_root: str | Path, store: Store, embed_fn=_embed.embed_texts) -> tuple[int, int]:
    """回傳 (新嵌入數, 總 concept 數)。"""
    chunks = load_chunks(bundle_root)
    todo = [c for c in chunks if not store.has(c.id, c.content_hash)]  # 增量
    for i in range(0, len(todo), config.EMBED_BATCH):
        batch = todo[i:i + config.EMBED_BATCH]
        vectors = embed_fn([c.text for c in batch])
        for c, v in zip(batch, vectors):
            store.upsert(c.id, c.content_hash, c.text, c.metadata, v)
    return len(todo), len(chunks)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle", type=Path, help="OKF bundle 目錄")
    ap.add_argument("--db", type=Path, default=Path(config.RAG_DB))
    args = ap.parse_args()

    store = SqliteStore(args.db)
    n_new, n_total = ingest(args.bundle, store)
    print(f"ingest 完成:{n_new} 新嵌入 / {n_total} concepts → {args.db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
