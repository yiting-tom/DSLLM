## ADDED Requirements

### Requirement: 送出前縮圖與重編碼

系統 SHALL 在把 slide 圖編碼成 base64 送 vision 前,將其長邊縮到設定上限(預設 1600px),並壓進位元組預算(PNG 優先,超標改 JPEG 逐級降質);已在上限內者不放大。

#### Scenario: 大圖被縮到上限內
- **WHEN** 一張長邊 3000px 的圖進入前處理
- **THEN** 輸出圖片長邊 MUST ≤ 設定上限,且位元組 MUST ≤ 預算

#### Scenario: 小圖不放大
- **WHEN** 一張長邊 800px 的圖進入前處理
- **THEN** 系統 MUST NOT 將其放大

### Requirement: data URI mime 自動偵測

`image_data_uri` SHALL 依實際位元組(PNG/JPEG 魔數)產生對應 mime,使 JPEG 退路能正確送出。

#### Scenario: JPEG 退路 mime 正確
- **WHEN** 前處理因超預算而輸出 JPEG
- **THEN** data URI 的 mime MUST 為 `image/jpeg`

### Requirement: 自適應密集頁切塊

當來源圖過大或過密(長邊超過切塊門檻)時,系統 SHALL 將其切成多塊(塊間帶重疊以免切斷文字),而非硬縮成單張;一張 slide 的多塊 MUST 能在同一次 densify 呼叫一起餵入。切塊數 MUST 有上限,超過則退回縮圖並記錄。

#### Scenario: 密集頁切成多塊
- **WHEN** 一張遠超門檻的大圖進入前處理
- **THEN** 系統 MUST 產出多塊(每塊在尺寸/位元組預算內),而非單一被重縮的圖

#### Scenario: 一般頁不切
- **WHEN** 一張未達門檻的頁進入前處理
- **THEN** 系統 MUST 只輸出單一(必要時縮過的)圖

### Requirement: 自動裁邊

系統 SHALL 去除圖片四周的均勻空白邊(保留少量 padding),讓內容佔滿像素預算;若整張近乎空白則 MUST 原樣保留,不得裁成空。

#### Scenario: 去除空白邊
- **WHEN** 一張四周有大片白邊的投影片
- **THEN** 輸出 MUST 裁掉多數白邊、內容區保留

### Requirement: 選配可插拔的 OCR 文字錨點

圖片模式 SHALL 可對每張圖跑 OCR,並把文字填入該 slide 的文字錨點,供 densify 校正精確字串;OCR 引擎 MUST 可插拔(PaddleOCR 優先、退 tesseract),兩者皆不可用時 MUST 靜默略過而不使流程失敗。

#### Scenario: 有 OCR 引擎時填入錨點
- **WHEN** 環境有可用 OCR 引擎且處理一張含文字的圖
- **THEN** 該 slide 的文字錨點 MUST 帶入 OCR 結果

#### Scenario: 無 OCR 引擎時不失敗
- **WHEN** 環境未安裝任何 OCR 引擎
- **THEN** 流程 MUST 正常完成,slide 文字錨點留空
