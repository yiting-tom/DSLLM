"""確定性假 embedder,供離線自測 / CI(無 embedding 端點時)。

用字元雜湊 → 固定維度向量。分數無語意意義,只驗流程,不驗品質。
"""
from __future__ import annotations

DIM = 64


def fake_embed(texts: list[str]) -> list[list[float]]:
    vecs = []
    for t in texts:
        v = [0.0] * DIM
        for ch in t:
            v[ord(ch) % DIM] += 1.0
        vecs.append(v)
    return vecs
