## Context

densify(逐頁榨取)與 synthesize(寫概念)都會把圖片中的表格轉成 markdown。VLM 有「表格應填滿」的先驗,空白 cell 觸發補值/錯位。pptx 走 python-pptx 拿精確 cell 不受影響;此問題限圖片/PDF(OCR)。此步只改 prompt(最便宜),結構化表格抽取另案。

## Goals / Non-Goals

**Goals:**
- densify/synthesize prompt 明確規範空白 cell、對齊、不猜測。

**Non-Goals:**
- 不做結構化表格抽取(pdfplumber for born-digital PDF / PP-Structure for 掃描)——後續步驟。
- 不改程式流程、資料結構、pptx 路徑。

## Decisions

- **只改 `DENSIFY_SYSTEM` 與 `SYNTHESIZE_SYSTEM`**:兩處都會輸出表格(densify 榨頁、synthesize 寫概念 body),都要加規則,否則 synthesize 可能重新腦補。
- **規則措辭**:空白用 `—` 保留;禁止以鄰值/推測填補;逐欄對齊、空格不致後值左移;看不清標 `?`。沿用既有「(低信心)」紀律。
- **不新增程式/參數**:降風險,可立即上線;效果靠後續空格表 A/B 驗證。

## Risks / Trade-offs

- **prompt 不保證根治**:VLM 仍可能偶爾補值 → 這是第一道防線;根治靠結構化表格抽取(下一步)+ 低信心旗標。
- **措辭過嚴的副作用**:可能把「合併儲存格」誤判為空 → 措辭保留彈性(空白才用 `—`,合併格照原樣描述)。

## Migration Plan

- 純 prompt 變更,無資料遷移。回滾 = revert 單一 commit。
