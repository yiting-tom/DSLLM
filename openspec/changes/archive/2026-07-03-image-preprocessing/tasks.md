## 1. imageprep 模組

- [x] 1.1 `config.py`:加 `MAX_IMAGE_PX`(1600)、`MAX_IMAGE_BYTES`(1.5MB)、`TILE_TRIGGER_PX`(2600)、`MAX_TILES`(6)、`TRIM_MARGINS`(true)
- [x] 1.2 `imageprep.py`:`_encode`(PNG 優先,超預算退 JPEG 降質)、`data_uri`(魔數判 mime)
- [x] 1.3 `imageprep.py`:`_trim`(裁邊,近全白不裁)、`_tile`(重疊切塊,超 MAX_TILES 退縮圖)
- [x] 1.4 `imageprep.py`:`normalize(raw) -> list[bytes]` 串起 裁邊→切塊/縮圖→編碼

## 2. Slide 改多圖 + 套前處理

- [x] 2.1 `extract.py`:`Slide.image_png` → `Slide.images: list[bytes]`;加 `image_uris()`;移除舊 `image_data_uri`
- [x] 2.2 `extract.py`:pptx 路徑每頁 PNG 過 `normalize`;`extract_image_dir` 每圖過 `normalize`
- [x] 2.3 `prompts.py`:`densify_user` / `synthesize_user` 迭代 `slide.image_uris()`(多塊一起餵)
- [x] 2.4 `synthesize.py`:refeed 存在判斷改看 `.images`

## 3. OCR 錨點(選配)

- [x] 3.1 `config.py`:加 `OCR`(auto/off/paddle/tesseract)、`OCR_LANG`
- [x] 3.2 `ocr.py`:可插拔 `ocr_image(raw)`(PaddleOCR→tesseract→空字串)
- [x] 3.3 `extract.py`:圖片模式對每圖跑 OCR,填 `Slide.text`(auto 且無引擎則靜默略過)

## 4. 驗證與文件

- [x] 4.1 `py_compile` 全通過
- [x] 4.2 冒煙(Pillow):大圖→切多塊且各在預算內;一般圖→單張且長邊≤上限;小圖不放大;白邊被裁;JPEG 退路 mime 正確;無 OCR 引擎不失敗
- [x] 4.3 更新 README + ARCHITECTURE;把殘留的 `193k` 改為 `200k`(K2.7 context)
