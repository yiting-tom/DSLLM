## 1. extract 支援圖片資料夾

- [x] 1.1 `extract.py`:pptx 相依(`pptx` / `pdf2image`)改為函式內延遲載入,使 module 可在無 pptx 工具鏈時 import
- [x] 1.2 `extract.py`:加 `IMAGE_EXTS` 與自然排序 key
- [x] 1.3 `extract.py`:實作 `extract_image_dir(topic_dir) -> Deck`(每圖一 slide,Pillow 延遲載入轉 PNG bytes)

## 2. run.py 圖片模式

- [x] 2.1 `run.py`:加 `--images` 旗標
- [x] 2.2 `run.py`:圖片模式下把 `input` 當根資料夾,列出每個「含圖片的子資料夾」為 deck;若 input 自身含圖片則當單一主題
- [x] 2.3 `run.py`:process/dump 流程改用可插拔 extractor,圖片模式走 `extract_image_dir`

## 3. 驗證與文件

- [x] 3.1 `py_compile` 全通過
- [x] 3.2 冒煙測試:temp 根資料夾放 2 主題×數張 PNG(檔名亂序)→ `extract_image_dir` 產出正確頁序、image_png 非空;無 pptx 相依也能 import
- [x] 3.3 更新 `README.md`(圖片模式用法 + 資料夾結構說明)
- [x] 3.4 `docs/ARCHITECTURE.md`:註明圖片資料夾為過渡輸入模式
