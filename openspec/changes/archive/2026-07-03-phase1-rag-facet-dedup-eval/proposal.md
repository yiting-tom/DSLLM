## Why

Phase 1 的向量 RAG(ingest/query)已可用,但還缺三塊才算收尾:檢索無法依結構化欄位過濾、大量餵資料時無法察覺重複、且沒有量測庫品質的手段。第三點是 process 債——增量、模型驅動的知識庫會靜默劣化,沒有 eval 就是盲飛。

## What Changes

- **facet 過濾**:`rag.query` / store 支援依 frontmatter metadata(`type` / `tags` / `confidence` / `generated`)篩選檢索結果(例如「只查 Failure Mode」「排除低信心」「只查真相不含衍生摘要」)。
- **疑似重複標旗標**:`rag.ingest` 對每個新 concept 用既有向量檢索最相似項,相似度超過門檻時**不自動合併**,只寫入一份 flags 報告交人審(架構 §7 陷阱④:自動合併有損、不可逆、順序相依,Phase 1 一律 append-only)。
- **golden eval harness**:讀 `eval.yaml`(問題 → 期望命中的 concept id / 關鍵字),跑 `rag.query`,輸出 recall@k、命中排名、低信心命中標註;先用假 embedder 自測,真題由領域專家日後填入。

## Capabilities

### New Capabilities
- `rag-facet-filter`: 檢索時依 frontmatter metadata 做結構化過濾與排除。
- `rag-dedup-flagging`: ingest 時偵測疑似重複並產出人工審查報告,不自動修改知識庫。
- `rag-eval-harness`: 以 golden 問答集量測檢索品質(recall@k、低信心命中),可用假 embedder 離線自測。

### Modified Capabilities
<!-- 無:openspec/specs/ 為空,皆為新 capability -->

## Impact

- 程式:`pptx_to_okf/rag/store.py`(topk 加 filter)、`rag/query.py`(CLI 加 facet flag)、`rag/ingest.py`(加 dedup 掃描與 flags 輸出);新增 `pptx_to_okf/eval/` 模組與 `eval.yaml` 範例。
- 契約:沿用既有 frontmatter metadata,不改 OKF 寫入格式;dedup 只讀不寫知識庫(只寫 flags 報告)。
- 相依:無新外部相依(sqlite 暴力 cosine、既有 OpenAI 相容 embedding 端點)。
- 不影響:離線轉換 pipeline(extract/densify/cluster/synthesize/build)不動。
