## Context

Phase 1 已有 `pptx_to_okf/rag/`:`chunk`(OKF `.md` → Chunk)、`embed`(OpenAI 相容)、`store`(SqliteStore 暴力 cosine)、`ingest`/`query` CLI。本 change 在此之上補三塊,不改 OKF 寫入格式與離線轉換 pipeline。核心約束沿用架構決策:OKF 是唯一真相、RAG 是可重建的衍生索引、Phase 1 一律 append-only。

## Goals / Non-Goals

**Goals:**
- 檢索可依 frontmatter metadata 過濾(type/tags/confidence/generated)。
- ingest 時偵測疑似重複並產人工報告,唯讀不動 bundle。
- 可跑的 golden eval harness,支援假 embedder 離線自測。

**Non-Goals:**
- 不做自動合併/策展(Phase 3)。
- 不換向量庫(仍 SqliteStore;Qdrant/pgvector 屬後續)。
- 不建 graph / 摘要(Phase 2)。
- 不提供正式 golden 題庫(領域專家日後填;本 change 只給格式與 runner)。

## Decisions

- **facet 過濾在 store 層做,不在 query 層事後濾**:`SqliteStore.topk` 加 `where: dict` 參數,先過濾候選再排序 top-k,確保 k 名額給符合者(對應 spec「過濾在排序前套用」)。替代方案(先取 k 再濾)會導致結果不足,否決。SQL 端先做 `type`/`generated`/`confidence` 的等值過濾,`tags`(JSON 陣列)在 Python 端判含。
- **dedup 重用既有 store 的相似度檢索,不另建索引**:ingest 對每個新 chunk 呼叫 `topk(vector, 1, exclude_self)` 取最相似既有項比門檻。零額外儲存。順序上「先嵌入既有、逐一 upsert 時比對已在庫者」——為求確定性,先把本批全部嵌入,再依序 upsert 並在 upsert 前比對「當下庫內容」。
- **dedup 唯讀 + 報告落地**:輸出 `flags.jsonl`(每行一組疑似重複)+ 終端摘要。絕不改 `.md`(架構 §7 陷阱④)。
- **門檻保守預設**:`OKF_DEDUP_THRESHOLD` 預設 0.92(高),寧漏報不誤報,避免把根因不同的相似缺陷併掉。
- **eval 注入式 embedder**:`ingest`/`query`/`search` 已支援 `embed_fn` 參數;eval runner 沿用,確定性假 embedder 放 `eval` 模組供自測與 CI。
- **eval 格式用 YAML**:`eval.yaml` 每題 `{ question, expect_ids?: [...], expect_keywords?: [...] }`;命中定義為期望 id 出現在 top-k,或(無 id 時)標題/來源含關鍵字。

## Risks / Trade-offs

- **暴力 cosine 的 dedup 是 O(N²)**(每個新 chunk 掃全庫)→ 大量餵時變慢。緩解:Phase 1 資料量小可接受;規模化時隨向量庫一起換 ANN。於程式標註此限制。
- **假 embedder 的 eval 分數無語意意義**→ 只驗流程不驗品質。緩解:報告明示「假 embedder 模式」,真品質數字要接真 embedding 端點跑。
- **dedup 門檻難一刀切**(不同 type 的相似度分佈不同)→ 可能漏報或誤報。緩解:門檻可調 + 只旗標不動庫,人工是最終裁決。
- **facet 的 tags 在 Python 端過濾**→ 大庫時比 SQL 慢。緩解:資料量小可接受;需要時再建 tag 表。

## Migration Plan

- 純新增與可選參數,無破壞性變更;`topk` 的 `where` 預設 None → 既有呼叫行為不變。
- 無資料遷移;`rag.db` 結構不變。
- 回滾:三塊互相獨立,可各自 revert。
