"""③ 把 concept dict 寫成 OKF bundle(markdown + YAML frontmatter)。"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

# OKF 保留檔名,不可當 concept 用
RESERVED = {"index.md", "log.md"}


def _slug(s: str) -> str:
    s = re.sub(r"[^\w一-鿿-]+", "-", s.strip().lower())
    return re.sub(r"-+", "-", s).strip("-") or "concept"


def _frontmatter(c: dict, resource: str, ts: str) -> str:
    fm = {
        "type": c.get("type") or "Concept",          # OKF 唯一必填欄位
        "title": c.get("title", ""),
        "description": c.get("description", ""),
        "resource": resource,
        "tags": c.get("tags", []),
        "timestamp": ts,
    }
    return yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()


def write_bundle(deck_path: Path, concepts: list[dict], root: str | Path) -> list[Path]:
    root = Path(root)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    written: list[Path] = []
    for c in concepts:
        subpath = _slug(c.get("subpath", "misc"))
        name = f"{_slug(c.get('slug') or c.get('title', 'concept'))}.md"
        if name in RESERVED:
            name = f"c-{name}"
        # 來源可回溯:指到原檔 + 投影片號
        slides = c.get("source_slides") or []
        anchor = f"#slide={','.join(map(str, slides))}" if slides else ""
        resource = f"file://{deck_path.name}{anchor}"

        out = root / subpath / name
        out.parent.mkdir(parents=True, exist_ok=True)
        # 同名去重:附序號
        n = 1
        while out.exists():
            out = out.with_name(f"{out.stem}-{n}.md")
            n += 1
        body = (c.get("body_markdown") or "").strip()
        out.write_text(f"---\n{_frontmatter(c, resource, ts)}\n---\n\n{body}\n", encoding="utf-8")
        written.append(out)
    return written


def append_log(root: str | Path, deck_name: str, n_concepts: int, ts: str) -> None:
    """OKF log.md:記錄每次轉換來源與時間,供去重/追版本。"""
    log = Path(root) / "log.md"
    line = f"- {ts} — `{deck_name}` → {n_concepts} concepts\n"
    if not log.exists():
        log.write_text("# 轉換紀錄\n\n", encoding="utf-8")
    with log.open("a", encoding="utf-8") as f:
        f.write(line)
