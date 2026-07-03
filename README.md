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

## 旋鈕(env)

| 變數 | 預設 | 說明 |
|---|---|---|
| `OKF_RENDER_DPI` | 220 | slide 渲染 DPI;截圖/小字多可拉到 300 |
| `OKF_MAX_CONCURRENCY` | 8 | 平行呼叫數 |
| `OKF_SYNTH_REFEED_IMAGES` | true | C 階段是否重餵圖:true=忠實度最高(較貴)、false=純文字 reduce(便宜、品質被 densify 卡上限) |

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

## 待辦 / 已知限制

- **關鍵數值需抽樣人工核對**:prompt 已要求低信心標註,vision 讀尺寸/bin map 仍會錯。
- 跨 **deck** 聚合(Stage C 級 corpus reduce)尚未做;目前 merge 只在單一 deck 內。
- 資訊上限 = 投影片畫面所有的東西;真的沒有的內容,標 stub 交給 SME,不填充。
