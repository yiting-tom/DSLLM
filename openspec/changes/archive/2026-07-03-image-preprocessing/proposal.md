## Why

實測:大圖以 base64 送自架 K2.7(OpenAI 相容端點)會炸——payload 撞 gateway body 上限、vision token 爆量。Claude Code 不炸是因為 client 先把長邊縮到 ~1568px。此外圖片模式沒有 pptx 的文字錨點,densify 純靠 vision 讀字,尺寸/料號/小字會錯。需要把「送出前的圖片前處理」確定性地烤進 pipeline,而非改用 agentic 方案(非確定、成本浮動、要 shell 存取公司資料)。

## What Changes

- **縮圖 + 重編碼**:送 K2.7 前把每張圖長邊降到上限(預設 1600px)、壓進位元組預算(PNG 優先,超標退 JPEG);`image_data_uri` mime 自動偵測。→ 治 crash。
- **自適應密集頁切塊**:來源過大/過密的頁不硬縮,改切成數塊(有重疊防切字),同一張 slide 的多塊在 densify 一次餵入。→ 保留小字細節。
- **自動裁邊**:去掉投影片四周空白,讓內容佔滿像素預算 → 縮圖後有效解析度更高。
- **OCR 文字錨點(選配、可插拔)**:圖片模式對每張圖跑 OCR(PaddleOCR 優先,退 tesseract,皆無則略過),把結果填進 `Slide.text`,補回 pptx 模式才有的精確文字錨點;densify 既有的「校正錨點」槽自動採用,prompt 不改。
- **BREAKING**(內部):`Slide.image_png: bytes` → `Slide.images: list[bytes]`(支援切塊)。

## Capabilities

### New Capabilities
- `image-preprocessing`: 送 vision 前的確定性圖片前處理——縮圖/重編碼、自適應切塊、裁邊、選配 OCR 錨點。

### Modified Capabilities
<!-- image-folder-input 的 Slide 結構有微調,但其行為需求不變 -->

## Impact

- 程式:新增 `imageprep.py`、`ocr.py`;`extract.py`(Slide 改 `images`、兩條路徑套前處理、圖片模式跑 OCR)、`prompts.py`(densify/synthesize 迭代多圖)、`synthesize.py`(判斷改 `.images`)、`config.py`(新旗鈕)。
- 相依:Pillow(已有);OCR 為選配(PaddleOCR / tesseract,未裝則自動略過)。
- 不影響:cluster / build / RAG;K2.7 仍走原自架端點(不出內網)。
