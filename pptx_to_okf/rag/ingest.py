"""RAG ingest(append-only、增量):OKF bundle → 向量庫。

    python -m pptx_to_okf.rag.ingest ./bundle

- content_hash 沒變的 concept 直接跳過(不重嵌),實現架構 §7 陷阱③。
- 每個新 concept 對「當下庫」取最相似既有項,≥ 門檻只寫 flags 報告、不自動合併
  (架構 §7 陷阱④:唯讀,絕不改 bundle)。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .. import config
from . import embed as _embed
from .chunk import load_chunks
from .store import SqliteStore, Store


def ingest(bundle_root: str | Path, store: Store, embed_fn=_embed.embed_texts,
           dedup_threshold: float | None = None) -> tuple[int, int, list[dict]]:
    """回傳 (新嵌入數, 總 concept 數, 疑似重複 flags)。全程唯讀不改 bundle。"""
    if dedup_threshold is None:
        dedup_threshold = config.DEDUP_THRESHOLD

    chunks = load_chunks(bundle_root)
    todo = [c for c in chunks if not store.has(c.id, c.content_hash)]  # 增量
    flags: list[dict] = []

    for i in range(0, len(todo), config.EMBED_BATCH):
        batch = todo[i:i + config.EMBED_BATCH]
        vectors = embed_fn([c.text for c in batch])
        for c, v in zip(batch, vectors):
            # 比對「當下庫」(含本批已 upsert 者)→ 抓庫內與批內重複
            near = store.topk(v, 1, exclude_id=c.id)
            if near and near[0]["score"] >= dedup_threshold:
                flags.append({
                    "new_id": c.id, "new_title": c.metadata.get("title", ""),
                    "dup_id": near[0]["id"], "dup_title": near[0]["metadata"].get("title", ""),
                    "score": round(near[0]["score"], 4),
                })
            store.upsert(c.id, c.content_hash, c.text, c.metadata, v)

    return len(todo), len(chunks), flags


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle", type=Path, help="OKF bundle 目錄")
    ap.add_argument("--db", type=Path, default=Path(config.RAG_DB))
    ap.add_argument("--flags", type=Path, default=None, help="疑似重複報告輸出(預設 <db>.flags.jsonl)")
    args = ap.parse_args()

    store = SqliteStore(args.db)
    n_new, n_total, flags = ingest(args.bundle, store)

    flags_path = args.flags or args.db.with_suffix(".flags.jsonl")
    if flags:
        with open(flags_path, "w", encoding="utf-8") as f:
            for fl in flags:
                f.write(json.dumps(fl, ensure_ascii=False) + "\n")

    print(f"ingest 完成:{n_new} 新嵌入 / {n_total} concepts → {args.db}")
    if flags:
        print(f"⚠️ {len(flags)} 組疑似重複(未自動合併,交人審)→ {flags_path}")
        for fl in flags[:10]:
            print(f"    {fl['score']}  新 {fl['new_title']}<{fl['new_id']}> ≈ 既有 {fl['dup_title']}<{fl['dup_id']}>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
