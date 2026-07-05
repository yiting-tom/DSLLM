"""RAG 檢索(給 eval / 線上服務用):

    python -m pptx_to_okf.rag.query "delamination 的成因?" --type "Failure Mode" --no-low-confidence

回傳 top-k concept(含 score 與 metadata)。低信心結果會標註。
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .. import config
from . import embed as _embed
from .store import SqliteStore, Store


def search(query: str, store: Store, k: int = 5, embed_fn=_embed.embed_texts,
           where: dict | None = None, expand: bool = False) -> list[dict]:
    qv = embed_fn([query])[0]
    hits = store.topk(qv, k, where=where)
    if not expand:
        return hits
    # graph 展開:沿命中概念的 related 補入鄰居(dedup、標 via_related)
    seen = {h["id"] for h in hits}
    extra = []
    for h in hits:
        for rid in (h["metadata"].get("related") or []):
            if rid in seen:
                continue
            nb = store.get(rid)
            if nb:
                seen.add(rid)
                nb = {**nb, "score": h["score"], "via_related": h["id"]}
                extra.append(nb)
    return hits + extra


def _where_from_args(args) -> dict:
    where: dict = {}
    if args.type:
        where["type"] = args.type
    if args.tag:
        where["tags_any"] = args.tag
    if args.no_low_confidence:
        where["exclude_low_confidence"] = True
    if args.facts_only:
        where["facts_only"] = True
    return where


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", type=str)
    ap.add_argument("--db", type=Path, default=Path(config.RAG_DB))
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--type", type=str, help="只查此 type")
    ap.add_argument("--tag", action="append", help="tags 任一命中(可重複)")
    ap.add_argument("--no-low-confidence", action="store_true", help="排除低信心")
    ap.add_argument("--facts-only", action="store_true", help="排除衍生摘要(generated)")
    ap.add_argument("--expand", action="store_true", help="graph 展開:沿 related 補入鄰居")
    args = ap.parse_args()

    store = SqliteStore(args.db)
    for r in search(args.query, store, args.k, where=_where_from_args(args), expand=args.expand):
        m = r["metadata"]
        warn = "  ⚠️低信心" if m.get("confidence") == "low" else ""
        via = f"  ↳via {r['via_related']}" if r.get("via_related") else ""
        print(f"[{r['score']:.3f}] ({m.get('type','?')}) {m.get('title','')}  <{m.get('id')}>{warn}{via}")
        print(f"        來源 {m.get('resource','')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
