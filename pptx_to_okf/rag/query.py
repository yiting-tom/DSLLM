"""RAG 檢索(給 eval / 線上服務用):

    python -m pptx_to_okf.rag.query "delamination 的成因?"

回傳 top-k concept(含 score 與 metadata)。低信心結果會標註。
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .. import config
from . import embed as _embed
from .store import SqliteStore, Store


def search(query: str, store: Store, k: int = 5, embed_fn=_embed.embed_texts) -> list[dict]:
    qv = embed_fn([query])[0]
    return store.topk(qv, k)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", type=str)
    ap.add_argument("--db", type=Path, default=Path(config.RAG_DB))
    ap.add_argument("-k", type=int, default=5)
    args = ap.parse_args()

    store = SqliteStore(args.db)
    for r in search(args.query, store, args.k):
        m = r["metadata"]
        warn = "  ⚠️低信心" if m.get("confidence") == "low" else ""
        print(f"[{r['score']:.3f}] ({m.get('type','?')}) {m.get('title','')}  <{m.get('id')}>{warn}")
        print(f"        來源 {m.get('resource','')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
