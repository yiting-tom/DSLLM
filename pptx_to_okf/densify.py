"""Stage A:逐頁 vision → 純文字 dump。平行執行。"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from . import config, llm, prompts
from .extract import Deck


def _one(slide) -> tuple[int, str]:
    text = llm.chat(prompts.DENSIFY_SYSTEM, prompts.densify_user(slide))
    return slide.index, text.strip()


def densify(deck: Deck) -> dict[int, str]:
    """回傳 {slide_index: 純文字 dump}。"""
    dumps: dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=config.MAX_CONCURRENCY) as ex:
        for idx, text in ex.map(_one, deck.slides):
            dumps[idx] = text
    return dumps
