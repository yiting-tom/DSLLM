## ADDED Requirements

### Requirement: 保留空白 cell,不補值

從圖片/OCR 轉錄表格時,系統(透過 densify/synthesize prompt)SHALL 要求模型將空白 cell 保留為空(以 `—` 標示),MUST NOT 以鄰列/鄰欄值或推測值填補。

#### Scenario: 空白 cell 保持空
- **WHEN** 表格中某 cell 在來源上為空白
- **THEN** 輸出對應 cell MUST 為空(`—`),不得出現補入的值

#### Scenario: 不以鄰值填補
- **WHEN** 某空白 cell 的同列/同欄相鄰有值
- **THEN** 系統 MUST NOT 把相鄰值複製到該空白 cell

### Requirement: 維持欄位對齊

轉錄表格時 SHALL 逐列逐欄對齊,確保每個值落在正確的欄;遇到空白 cell 不得使後續值左移錯位。

#### Scenario: 空白 cell 不造成錯位
- **WHEN** 某列中間有空白 cell
- **THEN** 該列後續各值 MUST 仍對應到其原本的欄,不左移

### Requirement: 不確定處標記而非猜測

看不清或不確定的 cell,系統 SHALL 標為 `?`(或沿用低信心標記),MUST NOT 以猜測值呈現。

#### Scenario: 看不清的 cell
- **WHEN** 某 cell 內容無法清楚辨識
- **THEN** 輸出 MUST 標 `?` 或標註低信心,而非填入猜測值
