# pptx → OKF

半導體投影片批次轉成 [OKF(Open Knowledge Format)](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) bundle,供線上模型(RAG 或直掛)使用。離線轉換用 self-host **Kimi K2.7**(多模態)。

專為「**沒講者備註、內容多是截圖/圖形拼成的解釋圖**」的 deck 設計 → vision 為主,python-pptx 只當校正錨點。

## 架構:densify → cluster → synthesize → merge

```
.pptx
 └─ extract   抽文字/表格/備註 + 每頁渲染成高 DPI 圖(soffice→pdf→png)
 └─ A densify   逐頁一圖送 K2.7,榨出該頁全部可見資訊 → 純文字（平行、高 DPI）
 └─ B cluster   全 deck 純文字很便宜,一次看完 → 聚類成 concept 群 + 共用 glossary
 └─ C synthesize 每群把該群 slides 的圖+文字一起丟回模型 → 寫成 OKF（群間平行）
 └─ merge      跨群合併明顯重複的 concept（便宜的純文字 pass）
 └─ build      寫成 OKF：每 concept 一個 .md（YAML frontmatter,type 必填）
```

**為什麼這樣切**
- 逐頁 densify → vision 注意力集中在單張,小字/尺寸/bin 座標讀得最準;DPI 可拉高。
- densify 後變便宜文字 → cluster/synthesize 都 bounded,**50+ 頁不爆**。
- 分組後群間獨立 → **平行,不用序列 rolling**(避免 drift);重複留到最後一次 merge。
- 全程「不腦補」紀律:看不清的數值標「(低信心,需人工核對)」,不虛構 spec。

## 安裝

```bash
brew install libreoffice poppler          # soffice + pdf2image 相依
pip install -r requirements.txt
```

## 執行

```bash
export OKF_LLM_BASE_URL=http://<k2.7-host>:8000/v1   # OpenAI 相容端點
export OKF_LLM_MODEL=kimi-k2.7
export SSL_VERIFY=false                              # 內網自簽 CA 時
python run.py ./decks --out ./bundle
```

產物 `./bundle/`:`<主題>/<slug>.md` + `log.md`(轉換紀錄)。

### 圖片模式(過渡:審核未過不能讀 pptx 時)

先把投影片轉成圖片,用圖片跑;**不需 pptx 工具鏈**(python-pptx / LibreOffice / poppler 都不用)。

```bash
python run.py ./topics --images --out ./bundle
```
資料夾結構:根目錄下每個子資料夾 = 一個主題,內含該主題投影片圖片(png/jpg/jpeg/webp),依**檔名自然排序**當頁序;若根目錄自身直接含圖片則當單一主題。

```
topics/
├── wire-bond/      01.png 02.png 03.png ...
└── delamination/   01.jpg 02.jpg ...
```
審核通過後改回 `python run.py ./decks`(pptx 模式)即可,後段完全相同。

### PDF 模式

```bash
python run.py "./paper.pdf" --pdf --out ./bundle      # 單一 PDF
python run.py ./pdfs --pdf --out ./bundle             # 資料夾:每個 *.pdf 一份 deck
```
每頁渲染成圖 + 文字錨點(**born-digital 用文字層,掃描/影像型退回 OCR**)。需 poppler(`brew install poppler`)。

### 三種輸入的文字錨點來源

| 輸入 | 圖 | 文字錨點 |
|---|---|---|
| pptx | soffice 渲染 | python-pptx(文字/表格/備註) |
| PDF | poppler 渲染 | 文字層 → 空則 OCR |
| 圖片資料夾 | 原圖 | OCR |

### 圖片前處理(送 K2.7 前,兩種模式都套)

大圖以 base64 送自架 K2.7(OpenAI 相容端點)會撞 body 上限 / vision token 爆。送出前確定性前處理(**非 agentic**):
- **縮圖 + 重編碼**:長邊降到 `OKF_MAX_IMAGE_PX`(1600,≈vision 實際用的解析度,對小字幾乎無損);超位元組預算退 JPEG。
- **自適應密集頁切塊**:過大/過密的頁不硬縮,切成數塊(重疊防切字)一起餵 densify → 保留小字。
- **自動裁邊**:去空白邊,讓內容佔滿像素預算。
- **OCR 文字錨點(選配)**:圖片模式對每圖跑 OCR(PaddleOCR 優先,退 tesseract,皆無則略過),填入 densify 的校正錨點——補回 pptx 模式才有的精確文字。中英混建議裝 `paddleocr`。

## 旋鈕(env)

| 變數 | 預設 | 說明 |
|---|---|---|
| `OKF_RENDER_DPI` | 220 | slide 渲染 DPI;送出前才降到 `MAX_IMAGE_PX`,故渲染仍可高 |
| `OKF_MAX_CONCURRENCY` | 8 | 平行呼叫數 |
| `OKF_SYNTH_REFEED_IMAGES` | true | C 階段是否重餵圖:true=忠實度最高(較貴)、false=純文字 reduce |
| `OKF_MAX_IMAGE_PX` | 1600 | 送 vision 前圖片長邊上限 |
| `OKF_MAX_IMAGE_BYTES` | 1500000 | 單圖位元組預算(超則退 JPEG) |
| `OKF_TILE_TRIGGER_PX` | 2600 | 長邊超此 → 密集頁切塊 |
| `OKF_MAX_TILES` | 6 | 切塊上限,超過退回縮圖 |
| `OKF_TRIM_MARGINS` | true | 自動裁邊 |
| `OKF_OCR` | auto | OCR 引擎:auto / off / paddle / tesseract |

> K2.7 context = 200k;densify 逐頁一圖、cluster 走純文字,皆遠在其內。

## RAG(Phase 1:向量檢索,append-only)

架構見 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md):OKF 是唯一真相,RAG 是可重建的衍生索引。

```bash
export OKF_EMBED_BASE_URL=http://<embed-host>:8001/v1   # OpenAI 相容
export OKF_EMBED_MODEL=bge-m3
python -m pptx_to_okf.rag.ingest ./bundle --db ./rag.db   # 增量,content_hash 沒變就跳過
python -m pptx_to_okf.rag.query "delamination 的成因?" --db ./rag.db
```

- 一個 concept `.md` = 一個 chunk(天然邊界);低信心 concept 檢索時會標註。
- 向量庫 Phase 1 用內建 sqlite 暴力 cosine(零 infra);規模上來換 Qdrant/pgvector,只需換 `rag/store.py`。
- **直掛**(替代路線):量小時把 `bundle/` 接 MCP filesystem / retrieval tool,模型按需讀 `.md`。

### facet 過濾
```bash
python -m pptx_to_okf.rag.query "分層問題" --type "Failure Mode" --no-low-confidence --facts-only
# --type 指定類別 · --tag 可重複 · --no-low-confidence 排除低信心 · --facts-only 排除衍生摘要
```

### 疑似重複(dedup flagging)
ingest 對每個新 concept 比對最相似既有項,`≥ OKF_DEDUP_THRESHOLD`(預設 0.92)只寫報告、**不自動合併**(唯讀,交人審):
```bash
python -m pptx_to_okf.rag.ingest ./bundle --db ./rag.db   # 疑似重複 → <db>.flags.jsonl
```

### eval harness
```bash
python -m pptx_to_okf.eval.runner eval.yaml --db ./rag.db          # 真 embedding
python -m pptx_to_okf.eval.runner eval.yaml --db ./rag.db --fake   # 假 embedder 離線自測
```
`eval.yaml` 每題 `question` + `expect_ids`/`expect_keywords`;輸出 recall@k、逐題排名、低信心命中標註。真題由領域專家填。

## Phase 2:主題摘要 + graph(全局/關係問題)

```bash
python -m pptx_to_okf.summarize ./bundle                      # 每主題生 Overview(generated)
python -m pptx_to_okf.rag.ingest ./bundle --db ./rag.db       # Overview 一併 ingest
python -m pptx_to_okf.rag.query "這主題整體涵蓋什麼" --db ./rag.db --expand
```

- **主題摘要**:每個子目錄綜合成一個 `_overview.md`(`generated: true`,衍生物,**不改成員真相**),回答全局問題;同主題固定檔名覆寫 → 重跑更新不重複。
- **graph(hub-and-spoke)**:Overview 的 `related` 以 **id** 連到成員 → `--expand` 命中後沿連結帶出鄰居脈絡。
- 只想查真相不要摘要:query 加 `--facts-only`。

## 待辦 / 已知限制

- **關鍵數值需抽樣人工核對**:prompt 已要求低信心標註,vision 讀尺寸/bin map 仍會錯。
- 跨 **deck** 聚合(Stage C 級 corpus reduce)尚未做;目前 merge 只在單一 deck 內。
- 資訊上限 = 投影片畫面所有的東西;真的沒有的內容,標 stub 交給 SME,不填充。
