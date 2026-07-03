## Context

`densify`/`synthesize` 用 `Slide.image_data_uri()`(寫死 `image/png`)把整張圖 base64 塞進 JSON 送自架 K2.7。大圖 → 撞 gateway body 上限 + vision token 爆。且圖片模式無精確文字錨點。修正走**確定性前處理**(非 agentic:agentic 對批次是非確定、成本浮動、要 shell 存取公司資料)。

## Goals / Non-Goals

**Goals:**
- 送出前縮圖/重編碼 → 不炸。
- 密集頁自適應切塊 → 保留小字。
- 裁邊 → 提升有效解析度。
- 圖片模式選配 OCR → 補回精確文字錨點。

**Non-Goals:**
- 不改用 agentic / claude-code-router 當批次主幹(留給互動/救援)。
- 不做對比/去歪斜/二值化(僅低畫質來源才需要;預設不做)。
- 不改 cluster/build/RAG。

## Decisions

- **`Slide.image_png: bytes` → `Slide.images: list[bytes]`**:切塊需要一張 slide 對多圖。新增 `Slide.image_uris()` 回傳 data URI 清單;`densify_user`/`synthesize_user` 迭代之。`synthesize` 的存在判斷改看 `.images`。
- **新增 `imageprep.py`**:`normalize(raw) -> list[bytes]` 為單一入口:裁邊 → 判斷「切塊 or 縮圖」→ 逐塊 `_encode`(PNG 優先,超 `MAX_IMAGE_BYTES` 退 JPEG 降質)。`data_uri(bytes)` 依魔數判 mime。
- **切塊策略**:來源長邊 > `TILE_TRIGGER_PX` 才切;`cols=ceil(w/MAX_IMAGE_PX)`、`rows=ceil(h/MAX_IMAGE_PX)`,塊間約 5% 重疊防切字;`cols*rows > MAX_TILES` 則放棄切塊、退回單張縮圖並 log(避免爆量)。
- **裁邊**:用 PIL 與四角推估底色做 bbox 差異裁切 + 少量 padding;bbox 空(近乎全白)則不裁。
- **OCR 可插拔**:`ocr.py` 依 `OKF_OCR`(auto/off/paddle/tesseract)挑引擎;auto = 有 Paddle 用 Paddle、否則 tesseract、否則回空字串。中英混建議 PaddleOCR(tesseract CJK 弱)。只在**圖片模式**跑(pptx 模式已有 python-pptx 文字);結果填 `Slide.text`,densify prompt 既有錨點槽自動採用,prompt 不改。
- **縮圖 vs 切塊的張力**:縮圖治傳輸、切塊保細節,兩者互斥;以 `TILE_TRIGGER_PX` 為界自適應二選一。

## Risks / Trade-offs

- **切塊丟跨塊脈絡** → 重疊 + 同一次 densify 一起餵多塊,讓模型看到全部塊。
- **切塊/OCR 增加成本** → 切塊有 `MAX_TILES` 上限;OCR 選配。
- **OCR 也會錯**(CJK/小字/旋轉) → 仍套低信心紀律,OCR 只當錨點不當真相。
- **Slide 結構改動** → 影響面限 extract/prompts/synthesize,已列入 tasks 一併改。

## Migration Plan

- Slide 欄位改名為內部改動;一次改齊 extract/prompts/synthesize。前處理預設開啟但參數保守;OCR 預設 auto(未裝引擎=略過,行為等同現況)。回滾:revert 單一 commit。
