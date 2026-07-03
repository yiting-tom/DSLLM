## ADDED Requirements

### Requirement: 從圖片資料夾建立 Deck

系統 SHALL 能把「一個主題子資料夾內的投影片圖片」建成一份 Deck,每個圖片檔對應一張 slide,不需讀取任何 `.pptx`。

#### Scenario: 主題資料夾轉成 Deck
- **WHEN** 指定一個含 N 張投影片圖片的主題資料夾
- **THEN** 系統 MUST 產生一份含 N 張 slide 的 Deck,每張帶該圖片內容

#### Scenario: 忽略非圖片檔
- **WHEN** 主題資料夾內混有非圖片檔(如 `.txt`、`.DS_Store`)
- **THEN** 系統 MUST 只取圖片檔(png/jpg/jpeg/webp),忽略其餘

### Requirement: 圖片依檔名自然排序為頁序

slide 頁序 SHALL 由圖片**檔名自然排序**決定(數字視為數值,使 `2` 排在 `10` 前),讓 densify/cluster 能正確引用頁號。

#### Scenario: 自然排序
- **WHEN** 資料夾含 `slide_2.png` 與 `slide_10.png`
- **THEN** `slide_2.png` MUST 排在 `slide_10.png` 之前

### Requirement: 根資料夾下逐主題處理

系統 SHALL 接受一個根資料夾,將其下**每個含圖片的子資料夾視為一個主題(一份 deck)**獨立處理;deck 名稱取子資料夾名。

#### Scenario: 多主題
- **WHEN** 根資料夾下有 3 個各含圖片的子資料夾
- **THEN** 系統 MUST 各自處理成 3 份 deck,並以子資料夾名為 deck 名

#### Scenario: 單主題(根即主題)
- **WHEN** 指定的資料夾本身直接含圖片、無子資料夾
- **THEN** 系統 MUST 將其當作單一主題處理

### Requirement: 不依賴 pptx 工具鏈

圖片模式 MUST 能在未安裝 python-pptx / LibreOffice / poppler 的環境執行;pptx 相關相依只在使用 pptx 模式時才載入。

#### Scenario: 無 pptx 工具鏈仍可跑圖片模式
- **WHEN** 環境未安裝 python-pptx / pdf2image,執行圖片模式
- **THEN** 系統 MUST 正常建立 Deck,不因缺 pptx 相依而失敗
