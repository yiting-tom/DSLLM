#!/usr/bin/env python3
"""pptx → OKF bundle 批次轉換 CLI(densify → cluster → synthesize → merge)。

用法:
    OKF_LLM_BASE_URL=http://k2:8000/v1 OKF_LLM_MODEL=kimi-k2.7 \
    python run.py ./decks --out ./bundle

    先驗證前兩段品質(不燒 Stage C 的 vision token):
    python run.py ./decks --dump-only

    ./decks 可為單一 .pptx 或含多份 .pptx 的目錄。
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from tqdm import tqdm

from pptx_to_okf import config, build
from pptx_to_okf.extract import extract
from pptx_to_okf.densify import densify
from pptx_to_okf.cluster import cluster
from pptx_to_okf.synthesize import synthesize


def find_decks(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*.pptx") if not p.name.startswith("~$"))


def process_deck(deck_path: Path, out: Path) -> int:
    deck = extract(deck_path)                       # 抽文字/表格/備註 + 渲染每頁圖
    dumps = densify(deck)                           # A：逐頁 vision → 純文字
    clustered = cluster(deck_path.stem, dumps)      # B：純文字聚類 + glossary
    concepts = synthesize(deck, dumps, clustered)   # C：分組寫 OKF + 跨群合併
    build.write_bundle(deck_path, concepts, out)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    build.append_log(out, deck_path.name, len(concepts), ts)
    return len(concepts)


def dump_deck(deck_path: Path, debug_dir: Path) -> int:
    """只跑到 Stage A/B:把逐頁 densify 文字與分組結果落地,供人工檢視。不呼叫 Stage C。"""
    deck = extract(deck_path)
    dumps = densify(deck)
    clustered = cluster(deck_path.stem, dumps)

    d = debug_dir / deck_path.stem
    d.mkdir(parents=True, exist_ok=True)
    for idx in sorted(dumps):
        (d / f"slide_{idx:03d}.txt").write_text(dumps[idx], encoding="utf-8")
    (d / "cluster.json").write_text(
        json.dumps(clustered, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    groups = clustered["groups"]
    tqdm.write(f"[DUMP] {deck_path.name}: {len(dumps)} 頁 → {len(groups)} 群  ({d})")
    for i, g in enumerate(groups):
        tqdm.write(f"    [{i}] ({g.get('type','?')}) {g.get('title','')}  slides={g.get('source_slides',[])}")
    return len(groups)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, help=".pptx 檔或含 pptx 的目錄")
    ap.add_argument("--out", type=Path, default=Path(config.BUNDLE_ROOT))
    ap.add_argument("--dump-only", action="store_true",
                    help="只跑 densify+cluster,落地文字與分組供檢視,不跑 Stage C")
    ap.add_argument("--debug-dir", type=Path, default=Path("./debug"))
    args = ap.parse_args()

    decks = find_decks(args.input)
    if not decks:
        print(f"找不到 pptx:{args.input}", file=sys.stderr)
        return 1
    if args.dump_only:
        print(f"[dump-only] 共 {len(decks)} 份 deck → {args.debug_dir}")
    else:
        print(f"共 {len(decks)} 份 deck → {args.out}  (refeed_images={config.SYNTH_REFEED_IMAGES})")

    ok = fail = 0
    for deck_path in tqdm(decks, desc="decks"):
        try:
            if args.dump_only:
                dump_deck(deck_path, args.debug_dir)
            else:
                n = process_deck(deck_path, args.out)
                tqdm.write(f"[OK] {deck_path.name} → {n} concepts")
            ok += 1
        except Exception:                          # 單份失敗不中斷整批
            fail += 1
            tqdm.write(f"[FAIL] {deck_path.name}\n{traceback.format_exc()}")
    dest = args.debug_dir if args.dump_only else args.out
    print(f"完成:{ok} 成功 / {fail} 失敗。輸出在 {dest}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
