## Context

Phase 1 有 OKF 概念 + 扁平向量 RAG。Phase 2 加「粗顆粒摘要 + 概念連結」讓全局/關係問題可答。守住架構原則:OKF=真相、衍生物標 `generated`、連結用穩定 id、Phase 1 append-only(不改成員真相)。

## Goals / Non-Goals

**Goals:**
- 每主題一個 Overview(generated),回答全局問題。
- Overview `related` 連成員 → 主題級 graph。
- query `--expand` 沿連結展開。

**Non-Goals:**
- 不做成員↔成員細粒度/跨主題語意連結(未來)。
- 不改成員概念(唯讀)。
- 不改 embedding/store 骨架。

## Decisions

- **hub-and-spoke,不改成員**:graph 只由 Overview→成員單向連結構成。避免把衍生連結寫回成員真相(架構陷阱②:真相/衍生分離),也不動成員 content_hash。跨概念細連結留待有 authored/LLM-judged 連結時再說。
- **Overview 檔位置與識別**:寫 `<topic>/_overview.md`(非 OKF 保留名 index.md/log.md)。重跑更新靠**固定檔名覆寫**(同主題同檔),達成「不重複」。id 對 Overview 用**內容穩定衍生**(`ov_` + hash(subpath))以便重跑穩定;成員 id 不變。
- **摘要生成**:`summarize.py` 用 `chunk.load_chunks` 讀概念、依子目錄分組;每組把成員 title/description/body 餵 LLM → 產 Overview body + description。`related` = 成員 id(程式填,不靠 LLM)。可注入 `chat_fn` 供離線測試。
- **build 寫 generated 概念**:`build.write_overview(root, subpath, title, description, body, related)` 設 `generated:true`、`type: Topic Overview`、`related` 給定、`provenance` 標為衍生(指成員)。
- **store 依 id 取概念**:`SqliteStore.get(id)`。`query.search(..., expand=True)`:對每個 hit 的 metadata `related`,取回並附加(dedup、標記 via_related)。
- **ingest 照舊**:Overview 有 `id`/`content_hash` → 一般概念般被 ingest;`generated:true` 在 metadata,facet `--facts-only` 可排除。

## Risks / Trade-offs

- **相似≠相關**:hub 連結是「同主題成員」,語意明確(不用相似度猜);跨主題因果連結未做 → 之後補。
- **Overview 品質受成員品質影響** → 標 generated + 低信心紀律照舊;可重建。
- **覆寫式更新**:同主題檔名固定 → 主題重命名會殘留舊 Overview(需清理);記於文件。

## Migration Plan

- 純新增;摘要是獨立步驟(`python -m pptx_to_okf.summarize ./bundle`),不跑就與 Phase 1 相同。`--expand` 預設關。回滾 = 刪 `_overview.md` + revert。
