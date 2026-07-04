## Why

論文/tutorial 等來源多為 PDF,是最常見的輸入格式,目前不支援。PDF 頁面本質等同投影片:born-digital PDF 有文字層可當精確錨點(比 OCR 準);掃描/影像型 PDF(如 jsPDF 匯出)無文字層,需退回 OCR。加入 PDF 輸入即補齊三種來源的錨點策略。

## What Changes

- 新增 **PDF 輸入模式**:一個 PDF 檔 = 一份 deck,每頁 = 一張 slide。
- 每頁**渲染成圖**(poppler/pdf2image)過既有圖片前處理(縮圖/切塊/裁邊)。
- **文字錨點**:優先抽 PDF 文字層(pdftotext);該頁文字層為空 → 退回 OCR。填入 `Slide.text`,densify 既有錨點槽自動採用。
- `run.py` 加 `--pdf` 模式:input 為單一 `.pdf` 或含多個 `.pdf` 的資料夾(每檔一份 deck)。
- 後段 densify→cluster→synthesize→build 完全重用。

## Capabilities

### New Capabilities
- `pdf-input`: 從 PDF 建立 Deck(每頁渲染成圖 + 文字層/OCR 錨點),無需 pptx 工具鏈。

### Modified Capabilities
<!-- 無 spec 級行為變更的既有 capability -->

## Impact

- 程式:`extract.py`(新增 `extract_pdf`,延遲載入 pdf2image;文字層走 poppler `pdftotext`)、`run.py`(加 `--pdf`)、`config.py`(可選頁範圍供大檔測試)。
- 相依:pdf2image + poppler(pptx 模式已用);文字層抽取用 poppler `pdftotext`(已有)。
- 不影響:pptx / 圖片模式、densify 以後全部不變。
