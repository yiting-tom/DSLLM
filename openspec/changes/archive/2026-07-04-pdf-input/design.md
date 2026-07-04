## Context

`extract()`（pptx）已用 pdf2image 把 pptx→pdf→png。PDF 輸入更直接:直接 render PDF 頁。text 錨點:pptx 有 python-pptx、圖片有 OCR;PDF born-digital 有文字層、掃描型無(如本次測試檔:jsPDF 產、83 頁、文字層 0 字)。故 PDF 需「文字層優先、OCR 退回」。

## Goals / Non-Goals

**Goals:**
- PDF → Deck,重用既有後段與圖片前處理。
- 文字層優先、無則 OCR。
- 單檔或多檔資料夾。

**Non-Goals:**
- 不解析 PDF 內嵌向量圖/表為結構(表格抽取屬後續 layout analyzer)。
- 不改 densify/cluster/synthesize/build。

## Decisions

- **`extract_pdf(pdf_path, first_page=None, last_page=None) -> Deck`**:pdf2image `convert_from_path` 渲染(延遲載入);每頁 → `Slide(images=imageprep.normalize(png), text=文字層或OCR)`。`first_page/last_page` 供大檔(如 83 頁)分段/測試,預設全部。
- **文字層抽取走 poppler `pdftotext -f p -l p`(subprocess)**:poppler 已是相依,免再裝 PyMuPDF/pypdf。空白則 `ocr.ocr_image`。
- **run.py `--pdf`**:input 是 `.pdf` → 單 deck;是資料夾 → 收集其中 `*.pdf` 每檔一 deck。與 `--images` 並列;沿用 `--dump-only`/`--out`。
- **DPI**:PDF 渲染沿用 `RENDER_DPI`;送出前一律過 `imageprep.normalize`(縮圖/切塊),故高 DPI 不會撐爆。

## Risks / Trade-offs

- **大 PDF(83 頁)成本高** → `first_page/last_page` 可分段;文件提醒。
- **文字層品質參差**(有些 PDF 文字層亂序/亂碼) → 仍當錨點不當真相,densify 以圖為主校正;必要時可強制走 OCR(未來旗鈕)。
- **pdf2image 需 poppler** → 與 pptx 模式同相依,無新增系統相依。

## Migration Plan

- 純新增;pptx/圖片模式不動。回滾 = revert 單一 commit。
