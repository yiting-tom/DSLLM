## Why

Phase 1 的扁平向量 RAG 只服務「點問題」(某個具體概念)。全局問題(「這主題涵蓋什麼」「整體流程」)與關係問題(「哪些概念相關」)答不好——前者需要粗顆粒摘要,後者需要概念間的連結。這是架構文件的 Phase 2:graph + 主題摘要,讓粗細打通。

## What Changes

- **主題摘要(Topic Overview)**:對每個主題(bundle 子目錄)產生一個 Overview 概念,綜合該主題所有成員概念;標 `generated: true`(衍生物,不污染真相),進 RAG 後回答全局問題。
- **概念圖(hub-and-spoke)**:Overview 的 `related` 以 **id** 連到該主題全部成員概念,形成主題級 graph。**不修改成員概念檔**(維持真相 append-only)。
- **graph 展開檢索**:query 加 `--expand`,命中概念後沿 `related` 補入相關概念,讓答案帶上鄰居脈絡。
- Overview 為衍生物,可由成員概念**確定性重建**(改動主題內容後重跑即更新)。

## Capabilities

### New Capabilities
- `topic-summaries`: 對每個主題生成 Overview 概念(generated:true),回答全局問題。
- `concept-graph`: 以 id `related` 連結建立主題級 graph,並支援 graph 展開檢索。

### Modified Capabilities
<!-- 無 spec 級行為變更的既有 capability;成員概念不被修改 -->

## Impact

- 程式:新增 `summarize.py`(生成 Overview)、`prompts.py`(摘要 prompt)、`build.py`(寫 generated 概念)、`rag/store.py`(依 id 取概念)、`rag/query.py`(`--expand`)。
- 契約:沿用 frontmatter,Overview 帶 `generated:true` + `related:[ids]`;成員概念不動。
- 不影響:extract / densify / cluster / synthesize / ingest 既有行為。
