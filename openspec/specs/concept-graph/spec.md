# concept-graph Specification

## Purpose
TBD - created by archiving change phase2-topic-summaries-graph. Update Purpose after archive.
## Requirements
### Requirement: Overview 以 id 連結成員(hub-and-spoke)

每個 Overview 概念的 `related` SHALL 以成員概念的**穩定 id** 列出該主題全部成員,形成主題級 graph。連結 MUST 用 id(非 slug/title),以免改名/合併後失效。

#### Scenario: Overview 連到成員
- **WHEN** 生成某主題 Overview
- **THEN** 其 `related` MUST 包含該主題所有成員概念的 id

#### Scenario: 連結用 id
- **WHEN** 檢視 Overview 的 `related`
- **THEN** 每個項目 MUST 是既有概念的 id

### Requirement: graph 展開檢索

檢索 SHALL 提供展開選項:命中概念後,沿其 `related` 補入相關概念一併回傳,讓答案帶鄰居脈絡。

#### Scenario: 展開帶入鄰居
- **WHEN** 以展開模式查詢且命中一個帶 `related` 的概念
- **THEN** 回傳結果 MUST 額外包含該概念 `related` 指向的概念

#### Scenario: 未展開時行為不變
- **WHEN** 未啟用展開
- **THEN** 回傳結果 MUST 與 Phase 1 檢索相同

