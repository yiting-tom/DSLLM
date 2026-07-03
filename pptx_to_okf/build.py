"""build:把 concept dict 寫成 OKF bundle(markdown + YAML frontmatter)。

依 docs/ARCHITECTURE.md §3 的 frontmatter 契約寫入:
id / generated / content_hash / confidence / provenance / related / model。
"""
from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import config

# OKF 保留檔名,不可當 concept 用
RESERVED = {"index.md", "log.md"}

# body 出現這個標記 → 內含未核對數值,強制 confidence: low(§7 陷阱⑤)
LOW_CONF_MARKER = "低信心"


def _slug(s: str) -> str:
    s = re.sub(r"[^\w一-鿿-]+", "-", s.strip().lower())
    return re.sub(r"-+", "-", s).strip("-") or "concept"


def _new_id() -> str:
    """永不變的穩定 ID(§7 陷阱①:連結用 id 不用 slug)。"""
    return "cpt_" + secrets.token_hex(4)


def _content_hash(body: str) -> str:
    return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()


def _confidence(c: dict, body: str) -> str:
    conf = (c.get("confidence") or "high").lower()
    if LOW_CONF_MARKER in body:          # 自動降級,不信任模型自評
        conf = "low"
    return "low" if conf == "low" else "high"


def _frontmatter(fm: dict) -> str:
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

        # 來源可回溯:指到原檔 + 投影片號(合併時累積,§7 陷阱⑤)
        slides = c.get("source_slides") or []
        anchor = f"#slide={','.join(map(str, slides))}" if slides else ""
        resource = f"file://{deck_path.name}{anchor}"

        body = (c.get("body_markdown") or "").strip()
        fm = {
            "id": _new_id(),
            "type": c.get("type") or "Concept",          # OKF 唯一必填
            "title": c.get("title", ""),
            "slug": _slug(c.get("slug") or c.get("title", "concept")),
            "description": c.get("description", ""),
            "generated": False,                          # 真相,非衍生物(§7 陷阱②)
            "content_hash": _content_hash(body),         # 索引增量重算用(§7 陷阱③)
            "confidence": _confidence(c, body),
            "resource": resource,                        # OKF 建議欄位
            "provenance": [resource],                    # 我們的契約,list 供跨 deck 累積
            "tags": c.get("tags", []),
            "related": [],                               # Phase 2 才填 id 連結
            "model": config.LLM_MODEL,
            "timestamp": ts,
        }

        out = root / subpath / name
        out.parent.mkdir(parents=True, exist_ok=True)
        # 同名去重:附序號(Phase 1 append-only,不自動合併,§7 陷阱④)
        n = 1
        while out.exists():
            out = out.with_name(f"{out.stem}-{n}.md")
            n += 1
        out.write_text(f"---\n{_frontmatter(fm)}\n---\n\n{body}\n", encoding="utf-8")
        written.append(out)
    return written


def append_log(root: str | Path, deck_name: str, n_concepts: int, ts: str) -> None:
    """OKF log.md:記錄每次轉換來源、時間與模型版本,供去重/追版本/可重現。"""
    log = Path(root) / "log.md"
    line = f"- {ts} — `{deck_name}` → {n_concepts} concepts  (model: {config.LLM_MODEL})\n"
    if not log.exists():
        log.write_text("# 轉換紀錄\n\n", encoding="utf-8")
    with log.open("a", encoding="utf-8") as f:
        f.write(line)
