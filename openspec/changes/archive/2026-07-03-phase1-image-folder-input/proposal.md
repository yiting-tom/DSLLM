## Why

公司讀檔審核未通過前,不能直接讀 `.pptx`。過渡方案:先把投影片轉成圖片,用圖片跑第一階段;審核通過後再接回 pptx。因此 Phase 1 需要一個「圖片資料夾」輸入模式,且**不得依賴 pptx 工具鏈**(python-pptx / LibreOffice / poppler 可能都還沒裝)。

## What Changes

- 新增輸入模式:user 指定一個**根資料夾**,底下每個**子資料夾 = 一個主題**,子資料夾內放該主題投影片的圖片;一個主題子資料夾等同現在的「一份 deck」。
- 圖片依**檔名自然排序**當作 slide 頁序;支援 png/jpg/jpeg/webp。
- 圖片模式直接把圖當 slide 餵進既有 densify→cluster→synthesize→build,**跳過** `extract` 的 pptx/soffice 渲染。
- **BREAKING**(內部):`extract.py` 的 pptx 相依(python-pptx / pdf2image)改為延遲載入,使圖片模式在未裝 pptx 工具鏈時也能執行。

## Capabilities

### New Capabilities
- `image-folder-input`: 從「根資料夾 / 每主題一子資料夾 / 內含投影片圖片」建立 Deck 並轉成 OKF,無需 pptx 工具鏈。

### Modified Capabilities
<!-- 無 spec 級行為變更的既有 capability -->

## Impact

- 程式:`extract.py`(新增 `extract_image_dir`;pptx 相依改延遲載入)、`run.py`(加 `--images` 模式,逐主題子資料夾處理)。
- 相依:圖片模式只需 Pillow;不需 python-pptx / LibreOffice / poppler。
- 不影響:densify / cluster / synthesize / merge / build 與既有 pptx 模式不變。
