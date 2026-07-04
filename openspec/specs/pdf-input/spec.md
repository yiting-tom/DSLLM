# pdf-input Specification

## Purpose
TBD - created by archiving change pdf-input. Update Purpose after archive.
## Requirements
### Requirement: 從 PDF 建立 Deck

系統 SHALL 能把一個 PDF 檔建成一份 Deck,每頁對應一張 slide,每頁渲染成圖並經既有圖片前處理。

#### Scenario: PDF 轉成 Deck
- **WHEN** 指定一個 N 頁的 PDF
- **THEN** 系統 MUST 產生一份含 N 張 slide 的 Deck,每張帶該頁渲染圖

#### Scenario: 頁序正確
- **WHEN** 處理多頁 PDF
- **THEN** slide 的 index MUST 依 PDF 實際頁序遞增

### Requirement: 文字層優先、OCR 退回

每頁的文字錨點,系統 SHALL 優先抽取該頁 PDF 文字層;當該頁文字層為空(掃描/影像型 PDF)時 MUST 退回 OCR(若有引擎),皆無則留空。

#### Scenario: born-digital PDF 用文字層
- **WHEN** 某頁有非空文字層
- **THEN** 該 slide 的文字錨點 MUST 來自文字層,不必跑 OCR

#### Scenario: 無文字層退回 OCR
- **WHEN** 某頁文字層為空且有可用 OCR 引擎
- **THEN** 該 slide 的文字錨點 MUST 來自 OCR

#### Scenario: 皆無時不失敗
- **WHEN** 某頁無文字層且無 OCR 引擎
- **THEN** 流程 MUST 正常完成,該 slide 文字錨點留空

### Requirement: PDF 輸入的 CLI

`run.py` SHALL 提供 PDF 模式:input 為單一 `.pdf` 檔,或含多個 `.pdf` 的資料夾(每檔一份 deck,deck 名取檔名)。

#### Scenario: 單一 PDF
- **WHEN** 以 PDF 模式指定一個 `.pdf` 檔
- **THEN** 系統 MUST 將其處理成一份 deck

#### Scenario: 資料夾多 PDF
- **WHEN** 以 PDF 模式指定含多個 `.pdf` 的資料夾
- **THEN** 系統 MUST 各自處理成一份 deck

