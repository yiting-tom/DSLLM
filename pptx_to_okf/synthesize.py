"""Stage C:按分組把該群 slides(圖+文字)寫成 OKF concept,群間平行;最後跨群合併去重。"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from . import config, llm, prompts
from .extract import Deck


def _one_group(group: dict, slides_by_idx: dict, dumps: dict[int, str], glossary: str) -> list[dict]:
    content = prompts.synthesize_user(
        group, slides_by_idx, dumps, glossary, config.SYNTH_REFEED_IMAGES
    )
    return llm.parse_array(llm.chat(prompts.SYNTHESIZE_SYSTEM, content))


def synthesize(deck: Deck, dumps: dict[int, str], clustered: dict) -> list[dict]:
    slides_by_idx = {s.index: s for s in deck.slides}
    glossary = clustered.get("glossary", "")
    groups = clustered["groups"]

    concepts: list[dict] = []
    with ThreadPoolExecutor(max_workers=config.MAX_CONCURRENCY) as ex:
        futures = [ex.submit(_one_group, g, slides_by_idx, dumps, glossary) for g in groups]
        for f in futures:
            concepts.extend(f.result())
    return _merge(concepts)


def _merge(concepts: list[dict]) -> list[dict]:
    """跨群合併明顯重複的 concept(便宜的純文字 pass)。"""
    if len(concepts) < 2:
        return concepts
    try:
        clusters = llm.parse_array(llm.chat(prompts.MERGE_SYSTEM, prompts.merge_user(concepts)))
    except Exception:
        return concepts  # 合併失敗不致命,回未合併版

    merged_idx: set[int] = set()
    result: list[dict] = []
    for grp in clusters:
        grp = [i for i in grp if isinstance(i, int) and 0 <= i < len(concepts) and i not in merged_idx]
        if len(grp) < 2:
            continue
        base = dict(concepts[grp[0]])
        bodies = [concepts[i].get("body_markdown", "") for i in grp]
        srcs: list[int] = []
        for i in grp:
            srcs.extend(concepts[i].get("source_slides", []))
            merged_idx.add(i)
        base["body_markdown"] = "\n\n".join(b for b in bodies if b)
        base["source_slides"] = sorted(set(srcs))
        result.append(base)
    # 沒被合併的原樣保留
    result.extend(c for i, c in enumerate(concepts) if i not in merged_idx)
    return result
