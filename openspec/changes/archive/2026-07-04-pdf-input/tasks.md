## 1. extract 支援 PDF

- [x] 1.1 `extract.py`:加 `_pdf_page_text(pdf, page)`(poppler `pdftotext -f -l` subprocess,回文字層)
- [x] 1.2 `extract.py`:實作 `extract_pdf(pdf_path, first_page=None, last_page=None) -> Deck`(pdf2image 延遲載入渲染;每頁 normalize;text=文字層,空則 OCR)

## 2. run.py PDF 模式

- [x] 2.1 `run.py`:加 `--pdf` 旗標
- [x] 2.2 `run.py`:PDF 模式下 input 為 `.pdf`→單 deck;資料夾→收集 `*.pdf` 每檔一 deck;走 `extract_pdf`

## 3. 驗證與文件

- [x] 3.1 `py_compile` 全通過
- [x] 3.2 機械冒煙(不燒 LLM):對真 PDF 前幾頁跑 `extract_pdf` → slide 數對、image 非空;文字層空的頁 OCR 有填 `Slide.text`
- [x] 3.3 更新 README + ARCHITECTURE(PDF 模式 + 三種輸入的錨點表)
