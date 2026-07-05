"""Phase 2:對每個主題(bundle 子目錄)生成 Overview 概念(generated:true)。

    python -m pptx_to_okf.summarize ./bundle

- 綜合該主題成員概念 → 一份總覽,回答全局問題。
- Overview `related` = 成員 id(hub-and-spoke graph)。
- 成員概念唯讀不改;同主題固定檔名覆寫 → 重跑更新不重複。
"""
from __future__ import annotations

import argparse
from pathlib import Path

from . import build, llm, prompts
from .rag.chunk import load_chunks


def _topic_of(path: str, root: Path) -> str | None:
    rel = Path(path).relative_to(root)
    return rel.parts[0] if len(rel.parts) > 1 else None      # 只處理子目錄主題


def summarize(bundle_root: str | Path, chat_fn=llm.chat, min_members: int = 2) -> list[Path]:
    root = Path(bundle_root)
    groups: dict[str, list] = {}
    for c in load_chunks(root):
        if c.metadata.get("generated") or c.metadata.get("slug") == "_overview":
            continue                                          # 不摘要衍生物
        topic = _topic_of(c.path, root)
        if topic:
            groups.setdefault(topic, []).append(c)

    written: list[Path] = []
    for topic, members in sorted(groups.items()):
        if len(members) < min_members:
            print(f"  跳過主題 {topic}(僅 {len(members)} 概念)")
            continue
        payload = [{"type": m.metadata.get("type", ""), "title": m.metadata.get("title", ""),
                    "body": m.text} for m in members]
        ov = llm.parse_object(chat_fn(prompts.SUMMARY_SYSTEM, prompts.summary_user(topic, payload)))
        related = [m.id for m in members]
        out = build.write_overview(
            root, topic, ov.get("title", f"{topic} 總覽"),
            ov.get("description", ""), ov.get("body_markdown", ""), related,
        )
        written.append(out)
        print(f"  [OVERVIEW] {topic}: {len(members)} 概念 → {out.name}  (related {len(related)})")
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle", type=Path, help="OKF bundle 目錄")
    args = ap.parse_args()
    outs = summarize(args.bundle)
    print(f"完成:{len(outs)} 個主題 Overview → {args.bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
