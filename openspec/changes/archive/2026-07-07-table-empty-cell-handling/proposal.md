## Why

實測發現:表格若有空白 cell,模型會**亂補值**(用鄰列/鄰欄值或憑空填)或**數值錯位**(丟失欄位對齊,值塞到隔壁欄)。這是 VLM 讀表通病,只發生在圖片/PDF(OCR)模式(pptx 有 python-pptx 精確 cell,免疫)。先以最便宜的 prompt 硬化擋一波,結構化表格抽取(pdfplumber / PP-Structure)留待後續步驟。

## What Changes

- **densify / synthesize prompt 增加表格忠實轉錄規則**:
  - 空白 cell **必須保留空**(用 `—`),**禁止補值、禁止推測**;
  - **逐列逐欄對齊**,每個值確認對應正確的欄;不確定的格標 `?`;
  - 不確定行列數時,寧可少填不要腦補撐滿。
- 純 prompt 變更,不動程式流程與資料結構。

## Capabilities

### New Capabilities
- `faithful-table-transcription`: 從圖片/OCR 轉錄表格時,保留空白 cell、維持欄位對齊、不補值不推測。

### Modified Capabilities
<!-- 無 spec 級行為變更;densify/synthesize 既有能力不改介面 -->

## Impact

- 程式:僅 `prompts.py`(`DENSIFY_SYSTEM`、`SYNTHESIZE_SYSTEM` 加表格規則)。
- 不影響:extract / cluster / build / RAG。pptx 模式本就精確,不受影響。
- 驗證:需一張有空白 cell 的表做前/後對照(圖片或掃描 PDF)。
