## Context

現有 `extract.extract(pptx)` 產出 `Deck{slides:[Slide{image_png,text,tables,notes}]}`,後段 densify→cluster→synthesize→build 只吃 `Slide.image_png`(文字/表格/備註在此類 deck 幾乎為空)。圖片模式只要能產出同樣的 `Deck` 即可完全重用後段。關鍵約束:審核未過的環境**可能沒有 pptx 工具鏈**,故 `extract.py` 目前在 module 頂層 import `pptx` / `pdf2image` 必須改成延遲載入。

## Goals / Non-Goals

**Goals:**
- 圖片資料夾 → Deck,重用既有後段。
- 根資料夾逐主題(子資料夾)處理。
- 圖片模式不需 pptx 工具鏈。

**Non-Goals:**
- 不改 densify/cluster/synthesize/build。
- 不做圖片前處理(裁切/去邊/OCR);原圖直接餵 vision。
- 不移除 pptx 模式(審核過後要用)。

## Decisions

- **新增 `extract_image_dir(topic_dir) -> Deck`**,與 `extract()` 並列。每個圖片檔 → 一張 `Slide`,`index` 依自然排序,`title/text/tables/notes` 留空(dataclass 預設)。
- **圖片統一轉 PNG bytes**:用 Pillow 載入後 `convert("RGB")` 存成 PNG,存進 `Slide.image_png`。因 `Slide.image_data_uri()` 目前寫死 `image/png`,統一成 PNG 最省事且避免 mime 不符;副作用是 webp/jpg 會重編碼(可接受)。
- **pptx 相依延遲載入**:把 `from pptx import Presentation` 與 `from pdf2image import convert_from_path` 移進 `extract()` / `_render_slides_to_png()` 內部;Pillow 也在 `extract_image_dir` 內延遲載入。使 `import extract` 在只有圖片模式的環境不炸。
- **run.py 加 `--images`**:`input` 視為根資料夾;取其下每個「含圖片的子資料夾」為一份 deck;若 `input` 自身直接含圖片則當單一主題。deck 名 = 資料夾名。沿用既有 `--dump-only` / `--out`。
- **自然排序**:自訂 key 把檔名數字段轉 int,避免 `10` 排在 `2` 前。

## Risks / Trade-offs

- **重編碼成 PNG 會放大檔案 / 稍慢** → 可接受;必要時未來加「原格式直傳 + mime 偵測」。
- **圖片解析度由來源決定**,不像 pptx 模式可控 DPI → 提醒使用者轉檔時用足夠解析度(小字可讀)。
- **子資料夾判定**:只認「直接含圖片」的子資料夾,巢狀更深不遞迴 → 明確、避免誤抓;文件標註。

## Migration Plan

- 純新增 + 既有 import 改延遲載入,pptx 模式行為不變。
- 無資料遷移。回滾:revert 單一 commit 即可。
