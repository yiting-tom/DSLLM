# rag-dedup-flagging Specification

## Purpose
TBD - created by archiving change phase1-rag-facet-dedup-eval. Update Purpose after archive.
## Requirements
### Requirement: ingest 時偵測疑似重複

ingest 每處理一個新 concept,SHALL 用既有向量索引檢索最相似的既有 concept;當最高相似度 ≥ 設定門檻時,MUST 將該組(新 concept id、疑似重複的既有 id、相似度)記為一筆 flag。

#### Scenario: 相似度超過門檻
- **WHEN** 新 concept 與某既有 concept 的餘弦相似度 ≥ 門檻
- **THEN** 系統 MUST 產生一筆 flag,含雙方 id、相似度分數與各自標題

#### Scenario: 相似度未達門檻
- **WHEN** 新 concept 與所有既有 concept 相似度皆 < 門檻
- **THEN** 系統 MUST NOT 為它產生任何 flag

### Requirement: 絕不自動修改知識庫

dedup 偵測 MUST 為唯讀:不得刪除、合併或改寫任何 concept，只輸出一份人工審查報告(架構 §7 陷阱④,Phase 1 一律 append-only)。

#### Scenario: 偵測到重複也不動 bundle
- **WHEN** 偵測到疑似重複
- **THEN** OKF bundle 內的 `.md` 檔 MUST 保持不變,系統僅寫出 flags 報告

#### Scenario: 報告可供人工裁決
- **WHEN** ingest 結束
- **THEN** 系統 MUST 產出一份可讀的 flags 報告(含每組疑似重複),供人工決定合併或保留

### Requirement: 門檻可設定

相似度門檻 SHALL 可透過設定調整,預設值 MUST 為保守的高門檻,以免把不同但相近的知識(如根因不同的相似缺陷)誤報成重複。

#### Scenario: 調整門檻
- **WHEN** 呼叫端設定較低門檻
- **THEN** 系統 MUST 依新門檻判定並回報更多疑似重複組

