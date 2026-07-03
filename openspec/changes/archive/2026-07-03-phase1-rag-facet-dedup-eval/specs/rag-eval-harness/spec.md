## ADDED Requirements

### Requirement: 從 golden 問答集量測檢索品質

eval harness SHALL 讀取一份 golden 集(每題含問題文字,與期望命中的 concept id 或關鍵字),對每題跑檢索,計算 recall@k 與期望項的命中排名。

#### Scenario: 期望 id 出現在 top-k
- **WHEN** 某題的期望 concept id 出現在檢索 top-k
- **THEN** 該題 MUST 計為命中,並記錄其排名

#### Scenario: 期望項未命中
- **WHEN** 某題的期望項未出現在 top-k
- **THEN** 該題 MUST 計為未命中,並列入報告供檢視

#### Scenario: 彙總指標
- **WHEN** 跑完整個 golden 集
- **THEN** 系統 MUST 輸出整體 recall@k 與逐題結果

### Requirement: 標註低信心命中

當某題的命中結果 metadata 為 `confidence=low`,eval 報告 MUST 明確標註,提醒該答案可能含未核對數值。

#### Scenario: 命中低信心 concept
- **WHEN** top-k 命中的 concept `confidence=low`
- **THEN** 報告該題 MUST 帶低信心標記

### Requirement: 可用假 embedder 離線自測

eval harness 與 ingest/query MUST 允許注入自訂 embedding 函式,使其可用確定性的假 embedder 在無 embedding 端點時跑通,供 CI / 開發自測。

#### Scenario: 注入假 embedder
- **WHEN** 以假 embedder 執行 eval
- **THEN** 流程 MUST 正常跑完並產出報告,不需連任何外部端點
