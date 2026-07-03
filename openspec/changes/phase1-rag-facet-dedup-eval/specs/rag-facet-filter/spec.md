## ADDED Requirements

### Requirement: 依 metadata 過濾檢索結果

檢索介面 SHALL 接受一組 facet 條件,並在回傳 top-k 前,只保留 metadata 符合全部條件的 chunk。支援的欄位 MUST 至少包含 `type`、`tags`、`confidence`、`generated`。

#### Scenario: 依 type 過濾
- **WHEN** 查詢帶 `type=Failure Mode`
- **THEN** 回傳結果 MUST 只包含 metadata `type` 為 `Failure Mode` 的 concept

#### Scenario: 依 tags 過濾（任一命中）
- **WHEN** 查詢帶 `tags=molding`
- **THEN** 回傳結果 MUST 只包含 `tags` 陣列含 `molding` 的 concept

#### Scenario: 無 facet 時行為不變
- **WHEN** 查詢未帶任何 facet
- **THEN** 回傳結果 MUST 與未加過濾功能前相同

### Requirement: 排除低信心與衍生內容

檢索介面 SHALL 提供開關,分別排除 `confidence=low` 與 `generated=true` 的 chunk,讓呼叫端能只取「高信心的真相」。

#### Scenario: 排除低信心
- **WHEN** 查詢帶「排除低信心」開關
- **THEN** 回傳結果 MUST 不含 `confidence` 為 `low` 的 concept

#### Scenario: 排除衍生摘要
- **WHEN** 查詢帶「只取真相」開關
- **THEN** 回傳結果 MUST 不含 `generated` 為 `true` 的 concept

### Requirement: 過濾在相似度排序前套用

facet 過濾 MUST 在計算 top-k 之前套用,使 k 個名額全部給符合條件者,而非先取 k 再過濾導致結果數量不足。

#### Scenario: 過濾後仍湊滿 k
- **WHEN** 庫中有足量符合 facet 的 concept 且要求 k=5
- **THEN** 回傳 MUST 為 5 筆符合條件且相似度最高者
