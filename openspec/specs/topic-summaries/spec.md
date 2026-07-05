# topic-summaries Specification

## Purpose
TBD - created by archiving change phase2-topic-summaries-graph. Update Purpose after archive.
## Requirements
### Requirement: 每個主題生成 Overview 概念

系統 SHALL 對 bundle 中每個主題(子目錄)綜合其成員概念,生成一個 Overview 概念,回答該主題的全局問題。Overview MUST 標記為衍生物,不得被當作真相。

#### Scenario: 主題生成 Overview
- **WHEN** 某主題有多個成員概念
- **THEN** 系統 MUST 產生一個該主題的 Overview 概念,`generated` 為 `true`

#### Scenario: Overview 進入檢索
- **WHEN** Overview 已生成並 ingest
- **THEN** 全局查詢(如「這主題涵蓋什麼」)MUST 能檢索到該 Overview

### Requirement: Overview 可確定性重建

Overview MUST 可由成員概念重新生成;成員內容改變後重跑 SHALL 更新對應 Overview,而不產生重複。

#### Scenario: 重跑更新而非重複
- **WHEN** 對同一 bundle 再次生成摘要
- **THEN** 每個主題 MUST 仍只有一個 Overview(更新,不新增重複)

### Requirement: 不修改成員概念

生成摘要的過程 MUST 為對成員概念唯讀:不得改動任何非 generated 的成員概念檔(維持真相 append-only)。

#### Scenario: 成員概念保持不變
- **WHEN** 執行摘要生成
- **THEN** 成員概念 `.md`(generated:false)MUST 保持不變

