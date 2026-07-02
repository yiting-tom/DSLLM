"""Stage B:用每頁純文字聚類成 concept 群 + 共用 glossary。"""
from __future__ import annotations

from . import config, llm, prompts


def _cap(groups: list[dict], cap: int) -> list[dict]:
    """強制每群 ≤ cap 張:超過的群按 slide 序切成多個子群(模型不一定聽話,這是保底)。"""
    out: list[dict] = []
    for g in groups:
        slides = sorted({int(i) for i in g.get("source_slides", [])})
        if len(slides) <= cap:
            g["source_slides"] = slides
            out.append(g)
            continue
        chunks = [slides[i:i + cap] for i in range(0, len(slides), cap)]
        for k, ch in enumerate(chunks, 1):
            ng = dict(g)
            ng["source_slides"] = ch
            ng["title"] = f"{g.get('title', '')} ({k})"
            out.append(ng)
    return out


def cluster(deck_name: str, dumps: dict[int, str]) -> dict:
    """回傳 {"glossary": str, "groups": [ {title,type,source_slides,rationale}, ... ]}。"""
    cap = config.MAX_SLIDES_PER_GROUP
    out = llm.parse_object(llm.chat(
        prompts.CLUSTER_SYSTEM,
        prompts.cluster_user(deck_name, dumps, cap),
    ))
    groups = out.get("groups") or []
    # 保底:模型完全沒分組時,退化成一頁一組,避免整份 deck 掉光
    if not groups:
        groups = [{"title": f"Slide {i}", "type": "Concept", "source_slides": [i]} for i in sorted(dumps)]
    return {"glossary": out.get("glossary", ""), "groups": _cap(groups, cap)}
