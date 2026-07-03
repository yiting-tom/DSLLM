#!/usr/bin/env python3
"""pptx / 圖片資料夾 → OKF bundle 批次轉換 CLI(densify → cluster → synthesize → merge)。

pptx 模式:
    python run.py ./decks --out ./bundle          # 單一 .pptx 或含 pptx 的目錄

圖片模式(過渡方案,審核未過不能讀 pptx 時用;不需 pptx 工具鏈):
    python run.py ./topics --images --out ./bundle
    # ./topics 下每個子資料夾 = 一個主題,內含該主題投影片圖片;若 ./topics 自身含圖片則當單一主題

先驗證前兩段品質(不燒 Stage C 的 vision token):加 --dump-only
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
from pptx_to_okf.extract import extract, extract_image_dir, IMAGE_EXTS
from pptx_to_okf.densify import densify
from pptx_to_okf.cluster import cluster
from pptx_to_okf.synthesize import synthesize


def find_decks(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*.pptx") if not p.name.startswith("~$"))


def _has_images(d: Path) -> bool:
    return d.is_dir() and any(p.is_file() and p.suffix.lower() in IMAGE_EXTS for p in d.iterdir())


def find_topics(root: Path) -> list[Path]:
    """圖片模式:root 自身含圖片 → 單一主題;否則取每個含圖片的子資料夾。"""
    if _has_images(root):
        return [root]
    return sorted(d for d in root.iterdir() if _has_images(d))


def process_deck(deck_path: Path, out: Path, extractor) -> int:
    deck = extractor(deck_path)                     # pptx 或圖片資料夾 → Deck
    dumps = densify(deck)                           # A：逐頁 vision → 純文字
    clustered = cluster(deck_path.stem, dumps)      # B：純文字聚類 + glossary
    concepts = synthesize(deck, dumps, clustered)   # C：分組寫 OKF + 跨群合併
    build.write_bundle(deck_path, concepts, out)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    build.append_log(out, deck_path.name, len(concepts), ts)
    return len(concepts)


def dump_deck(deck_path: Path, debug_dir: Path, extractor) -> int:
    """只跑到 Stage A/B:把逐頁 densify 文字與分組結果落地,供人工檢視。不呼叫 Stage C。"""
    deck = extractor(deck_path)
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
    ap.add_argument("input", type=Path, help=".pptx/pptx 目錄,或(--images)含主題子資料夾的根目錄")
    ap.add_argument("--images", action="store_true",
                    help="圖片模式:input 為根目錄,每子資料夾一主題;不需 pptx 工具鏈")
    ap.add_argument("--out", type=Path, default=Path(config.BUNDLE_ROOT))
    ap.add_argument("--dump-only", action="store_true",
                    help="只跑 densify+cluster,落地文字與分組供檢視,不跑 Stage C")
    ap.add_argument("--debug-dir", type=Path, default=Path("./debug"))
    args = ap.parse_args()

    if args.images:
        if not args.input.is_dir():
            print(f"圖片模式的 input 需為資料夾:{args.input}", file=sys.stderr)
            return 1
        jobs, extractor, kind = find_topics(args.input), extract_image_dir, "主題"
    else:
        jobs, extractor, kind = find_decks(args.input), extract, "deck"

    if not jobs:
        print(f"找不到{'圖片主題資料夾' if args.images else ' pptx'}:{args.input}", file=sys.stderr)
        return 1
    if args.dump_only:
        print(f"[dump-only] 共 {len(jobs)} 份{kind} → {args.debug_dir}")
    else:
        print(f"共 {len(jobs)} 份{kind} → {args.out}  (refeed_images={config.SYNTH_REFEED_IMAGES})")

    ok = fail = 0
    for job in tqdm(jobs, desc=kind):
        try:
            if args.dump_only:
                dump_deck(job, args.debug_dir, extractor)
            else:
                n = process_deck(job, args.out, extractor)
                tqdm.write(f"[OK] {job.name} → {n} concepts")
            ok += 1
        except Exception:                          # 單份失敗不中斷整批
            fail += 1
            tqdm.write(f"[FAIL] {job.name}\n{traceback.format_exc()}")
    dest = args.debug_dir if args.dump_only else args.out
    print(f"完成:{ok} 成功 / {fail} 失敗。輸出在 {dest}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
