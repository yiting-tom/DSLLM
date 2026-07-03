"""golden eval harness:量測檢索品質(recall@k、低信心命中)。

    python -m pptx_to_okf.eval.runner eval.yaml --db ./rag.db          # 真 embedding
    python -m pptx_to_okf.eval.runner eval.yaml --db ./rag.db --fake   # 假 embedder 自測

eval.yaml 每題:
    - question: "delamination 的成因?"
      expect_ids: [cpt_xxxx]        # 期望命中的 concept id(擇一)
      expect_keywords: ["分層"]      # 或關鍵字(標題/來源/內文含即命中)
"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from .. import config
from ..rag import embed as _embed
from ..rag.query import search
from ..rag.store import SqliteStore, Store
from .fake import fake_embed


def _is_hit(item: dict, r: dict) -> bool:
    m = r["metadata"]
    if m.get("id") in (item.get("expect_ids") or []):
        return True
    hay = f"{m.get('title','')}\n{m.get('resource','')}\n{r.get('text','')}"
    return any(kw in hay for kw in (item.get("expect_keywords") or []))


def run(eval_path: str | Path, store: Store, k: int = 5, embed_fn=_embed.embed_texts) -> dict:
    items = yaml.safe_load(Path(eval_path).read_text(encoding="utf-8")) or []
    rows = []
    for it in items:
        hits = search(it["question"], store, k, embed_fn)
        rank = next((i + 1 for i, r in enumerate(hits) if _is_hit(it, r)), None)
        low = bool(rank and hits[rank - 1]["metadata"].get("confidence") == "low")
        rows.append({"question": it["question"], "hit": rank is not None, "rank": rank, "low_conf": low})
    n = len(rows) or 1
    return {
        "k": k,
        "recall_at_k": sum(r["hit"] for r in rows) / n,
        "total": len(rows),
        "hits": sum(r["hit"] for r in rows),
        "rows": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("eval", type=Path, help="golden 問答集 yaml")
    ap.add_argument("--db", type=Path, default=Path(config.RAG_DB))
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--fake", action="store_true", help="用假 embedder(離線自測,分數無語意)")
    args = ap.parse_args()

    embed_fn = fake_embed if args.fake else _embed.embed_texts
    rep = run(args.eval, SqliteStore(args.db), args.k, embed_fn)

    mode = " (假 embedder,僅驗流程)" if args.fake else ""
    print(f"recall@{rep['k']} = {rep['recall_at_k']:.3f}  ({rep['hits']}/{rep['total']}){mode}")
    for r in rep["rows"]:
        mark = f"rank {r['rank']}" if r["hit"] else "MISS"
        warn = "  ⚠️低信心命中" if r["low_conf"] else ""
        print(f"    [{mark}]{warn}  {r['question']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
