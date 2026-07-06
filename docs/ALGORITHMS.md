# 演算法細節

對照實際程式碼的逐階段演算法參考。高階設計與技術債見 [`ARCHITECTURE.md`](ARCHITECTURE.md)。
所有可調參數集中在 `pptx_to_okf/config.py`(env 覆寫)。

管線總覽:
```
輸入(pptx / 圖片資料夾 / PDF)
  → extract           每頁 → Slide{images:list[bytes], text:文字錨點}
  → A densify         逐頁 vision → 純文字(平行)
  → B cluster         全 deck 純文字 → 概念群(≤3頁)+ glossary
  → C synthesize      每群 圖+文字 → OKF 概念(平行)
  → merge             跨群去重
  → build             寫 OKF .md(frontmatter 契約)
  → [RAG] chunk → embed → store;ingest(增量+dedup);query(facet/expand)
  → [Phase 2] summarize 主題 Overview + hub-and-spoke graph
```

---

## 1. 輸入抽取(`extract.py`)

三種模式都產出相同的 `Deck{path, slides:[Slide]}`;`Slide{index, title, text, tables, notes, images:list[bytes]}`。
`text` 是**文字錨點**(densify 用來校正精確字串),來源依模式不同。`images` 是**前處理後**的圖(§2),一張或密集頁多塊。

| 模式 | 函式 | 圖來源 | 文字錨點來源 |
|---|---|---|---|
| pptx | `extract(pptx)` | soffice→pdf→png(`_render_slides_to_png`,`RENDER_DPI`) | python-pptx 抽文字/表格/講者備註 |
| 圖片資料夾 | `extract_image_dir(dir)` | 資料夾內原圖 | `ocr.ocr_image`(§3) |
| PDF | `extract_pdf(pdf, first, last)` | pdf2image 渲染(`RENDER_DPI`) | `_pdf_page_text`(poppler `pdftotext`)→空則 OCR |

- pptx / pdf2image 相依**延遲載入**(函式內 import),使圖片模式在無 pptx 工具鏈的環境仍可執行。
- **頁序**:圖片資料夾用 `_natkey`(自然排序,數字段轉 int → `2` 排在 `10` 前);PDF/pptx 用原生頁序。
- `_pdf_page_text`:`pdftotext -f p -l p`;subprocess 逾時或無 exe 回空字串 → 觸發 OCR 退回(掃描/jsPDF 型 PDF)。

---

## 2. 圖片前處理(`imageprep.py`)

送 vision 前的確定性正規化,治「大圖 base64 撞 body 上限 / vision token 爆」。單一入口:

```
normalize(raw) -> list[bytes]:
    im = open(raw)
    if TRIM_MARGINS: im = _trim(im)              # 裁邊
    parts = _tile(im) if max(im.size) > TILE_TRIGGER_PX else [im]
    if parts is None: parts = [im]               # 塊太多 → 退回單張縮圖
    return [_encode(_resize_to_max(p)) for p in parts]
```

- **`_trim`**:以四角(0,0)像素為底色,`ImageChops.difference` 求 bbox → 裁 + 8px padding;bbox 空(近全白)不裁。
- **`_resize_to_max`**:長邊縮到 `MAX_IMAGE_PX`(1600);已在內不放大。
- **`_tile`**(自適應密集頁切塊):`cols=⌈w/MAX_IMAGE_PX⌉`, `rows=⌈h/MAX_IMAGE_PX⌉`;`cols·rows>MAX_TILES`(6)回 `None`(放棄切塊);否則切格,每格帶 **5% 重疊**防切斷文字,row-major 回傳。
- **`_encode`**:先存 PNG(文字銳利);`len>MAX_IMAGE_BYTES`(1.5MB)→ JPEG 逐級降質(q90→60)取第一個進預算者。
- **`data_uri`**:依位元組魔數判 mime(`\xff\xd8`→jpeg,否則 png),配合 JPEG 退路。`Slide.image_uris()` 對每張圖產 data URI。

> **張力**:縮圖治傳輸、切塊保細節,互斥;以 `TILE_TRIGGER_PX` 為界二選一。

---

## 3. OCR(`ocr.py`,選配可插拔)

僅圖片/無文字層 PDF 用,當文字錨點。

- **引擎選擇**(`_pick_engine`,只初始化一次):`OKF_OCR` = `off`→無;`auto`→有 PaddleOCR 用 Paddle、否則 pytesseract、否則無;`paddle`/`tesseract`→指定。皆不可用時 `ocr_image` 回空字串(不使流程失敗)。
- **PaddleOCR 3.x**:`PaddleOCR(use_textline_orientation=True, lang=OCR_LANG or "ch")`;`predict(np_array)` → 每頁 `rec_texts` 串接。
- **tesseract**:`image_to_string(lang=OCR_LANG or "chi_tra+eng")`。
- 任何例外回空字串(OCR 失敗不致命)。中英混建議 PaddleOCR(tesseract CJK 弱)。

---

## 4. Stage A — densify(`densify.py`)

**逐頁**把單張(或該頁多塊)圖 + 文字錨點榨成純文字。

```
densify(deck) -> {slide_index: dump_text}
  ThreadPool(MAX_CONCURRENCY) 平行,每頁一次 LLM 呼叫
  訊息 = DENSIFY_SYSTEM + densify_user(slide)
```

- `densify_user`:文字區塊(標題/檔案抽到的文字當錨點/表格/備註)+ 該 slide 全部 `image_uris()`(密集頁多塊一起餵)。
- **紀律**:只描述畫面實際內容、不腦補;看不清數值標「(低信心,需人工核對)」。
- 平行度受 `MAX_CONCURRENCY`(8);vision 呼叫走 IO,ThreadPool 即可。

---

## 5. Stage B — cluster(`cluster.py`)

全 deck 的**純文字**(便宜)一次餵入 → 聚成概念群 + 共用 glossary。

```
cluster(deck_name, dumps) -> {"glossary": str, "groups":[{title,type,source_slides,rationale}]}
  out = LLM(CLUSTER_SYSTEM, cluster_user(name, dumps, MAX_SLIDES_PER_GROUP))
  groups = out.groups or [一頁一群]           # 保底:模型沒分組時退化
  return {glossary, groups: _cap(groups, MAX_SLIDES_PER_GROUP)}
```

- **每群頁數上限**雙保險:prompt 要求 ≤ `MAX_SLIDES_PER_GROUP`(3);程式 `_cap` 強制——超上限的群按 slide 序切成 ≤cap 子群(標題加 `(1)`、`(2)`)。
- 概念群邊界是**知識單元**,非投影片:相鄰同主題合併、一頁多主題可拆(`source_slides` 可重疊)。
- type 優先取 `TYPE_VOCABULARY`(Process Step / Failure Mode / Material Spec …)。

---

## 6. Stage C — synthesize + merge(`synthesize.py`)

**每群**把該群 slides 的圖 + densify 文字 + glossary 寫成 OKF 概念,群間平行;再跨群去重。

```
synthesize(deck, dumps, clustered) -> concepts:
  concepts = 平行(每群 _one_group)            # ThreadPool(MAX_CONCURRENCY)
  return _merge(concepts)

_one_group(group): LLM(SYNTHESIZE_SYSTEM, synthesize_user(group, slides, dumps, glossary, SYNTH_REFEED_IMAGES))
```

- `synthesize_user`:每個成員 slide 的 densify 文字(當檢查清單/錨點)+(若 `SYNTH_REFEED_IMAGES`)該 slide 圖再餵一次(補回逐頁 densify 漏的跨頁視覺脈絡)。輸出 JSON 陣列(可 1 群多概念)。
- **`_merge`**(跨群去重):把所有概念的 title/description 餵 `MERGE_SYSTEM` → 回應合併 index 群;合併時串接 body、累積 `source_slides`;未合併者原樣保留。失敗則回未合併版(不致命)。
- 群間獨立 → 平行 + 最後合併,**不用序列 rolling**(避免 drift)。

---

## 7. build — OKF frontmatter 契約(`build.py`)

`write_bundle(deck_path, concepts, root)` 每概念寫一個 `.md`。frontmatter:

| 欄位 | 演算法 |
|---|---|
| `id` | `_new_id` = `cpt_` + `secrets.token_hex(4)`(永不變隨機 ID) |
| `content_hash` | `sha256:` + sha256(body) |
| `confidence` | `_confidence`:取模型自評,**但 body 含「低信心」標記則強制 `low`**(不信任自評) |
| `resource`/`provenance` | `file://<deck>#slide=<csv>`;provenance 為 list(合併/跨 deck 累積) |
| `slug`/檔名 | `_slug`(kebab,保留中日韓);檔名撞名附 `-N` 去重;避開保留名 `index.md`/`log.md` |
| `generated` | 一般概念 `false` |
| `related` | 一般概念空 `[]`(Phase 2 的 Overview 才填) |
| `model` | `config.LLM_MODEL` |

- Phase 1 **append-only**:同名附序號,不自動合併(重複交 dedup 旗標,§10)。
- `append_log`:`log.md` 記每次來源、概念數、模型版本(可追/可重現)。

---

## 8. RAG chunk(`rag/chunk.py`)

`load_chunks(bundle)` 掃 `*.md`(略過保留名、無 `id` 者)→ `Chunk{id, text, content_hash, metadata, path}`。

- **一個概念 = 一個 chunk**(md 本身是天然邊界)。
- 嵌入文字 `text` = `title\n description\n body`(標題/摘要前置,語意訊號強)。
- `metadata` 帶 `META_KEYS`(id/type/title/slug/tags/confidence/generated/resource/provenance/**related**)——`related` 必須帶,否則 graph 展開拿不到連結。
- `content_hash` 沿用 frontmatter 內既存值(與 build 對齊 → §9 增量)。

---

## 9. embed / store(`rag/embed.py`, `rag/store.py`)

- **embed**:OpenAI 相容 `/embeddings`,`EMBED_BATCH`(64)分批。
- **store**(Phase 1:`SqliteStore`,零 infra,可換 Qdrant/pgvector):
  - `_cosine(a,b)` 純 Python 餘弦。
  - `topk(vec, k, where, exclude_id)`:掃全表 → `_match` facet 過濾 → 排序取前 k。**過濾在排序前**,k 名額給符合者。
  - `_match(m, where)`:`type` 等值、`tags_any` 交集、`exclude_low_confidence`(排除 `confidence==low`)、`facts_only`(排除 `generated`)。
  - `get(id)`:依 id 取單一概念(graph 展開用)。
  - 複雜度:`topk`/`get` O(N)(暴力);規模化改 ANN。

---

## 10. ingest — 增量 + dedup 旗標(`rag/ingest.py`)

```
ingest(bundle, store, embed_fn, dedup_threshold=DEDUP_THRESHOLD) -> (n_new, n_total, flags):
  todo = [c for c in load_chunks(bundle) if not store.has(c.id, c.content_hash)]   # 增量
  for batch in todo/EMBED_BATCH:
     vecs = embed_fn([c.text ...])
     for c,v:
        near = None if c.metadata.generated else store.topk(v,1,exclude_id=c.id)   # 衍生物不查重
        if near and near[0].score >= dedup_threshold: flags.append({new,dup,score})
        store.upsert(...)                                                          # 唯讀不改 bundle
```

- **增量**:`(id, content_hash)` 已在庫 → 跳過(不重嵌)。實現「內容沒變不重算」。
- **dedup 旗標**:對「當下庫」(含本批已 upsert)取最相似;`≥DEDUP_THRESHOLD`(0.92,保守高門檻)只寫 `flags.jsonl` **交人審、絕不自動合併**。**generated 概念不查重**(摘要本就像成員,必誤報)。
- 複雜度 O(N²)(每個新 chunk 掃全庫);Phase 1 資料量小可接受。

---

## 11. query — facet + graph 展開(`rag/query.py`)

```
search(q, store, k, embed_fn, where, expand) -> hits:
  hits = store.topk(embed_fn([q])[0], k, where)
  if not expand: return hits
  for h in hits:                                   # hub-and-spoke 展開
     for rid in h.metadata.related:
        nb = store.get(rid); if nb and 未見過: 附加(標 via_related)
  return hits + extra
```

- CLI facet:`--type` / `--tag`(可重複)/ `--no-low-confidence` / `--facts-only`。
- `--expand`:命中概念後沿 `related`(id)補入鄰居 → 全局問題命中 Overview 再帶出成員。

---

## 12. Phase 2 — 主題摘要 + graph(`summarize.py`, `build.write_overview`)

```
summarize(bundle, chat_fn, min_members=2) -> [overview 檔]:
  groups = load_chunks(bundle) 依 _topic_of(子目錄) 分組,排除 generated / _overview
  for topic, members(≥min_members):
     ov = LLM(SUMMARY_SYSTEM, summary_user(topic, members))          # {title,description,body}
     write_overview(root, topic, ..., related=[m.id for m in members])
```

- **`write_overview`**:寫 `<topic>/_overview.md`;`generated:true`、`type: Topic Overview`、`related`=成員 id(**hub→spoke**)、`id = ov_ + sha1(subpath)[:8]`(隨主題**穩定**)。
- **固定檔名覆寫** → 重跑更新、不重複。
- **成員概念唯讀不改**(維持真相 append-only);Overview 是衍生物,可由成員**確定性重建**。
- `min_members=2`:單概念主題不生 Overview(無綜合價值)。
- graph = Overview 的 `related`;查詢用 `--expand`(§11)沿之展開。跨主題/成員↔成員細連結未做(未來)。

---

## 13. eval(`eval/runner.py`, `eval/fake.py`)

```
run(eval.yaml, store, k, embed_fn) -> {recall_at_k, rows:[{hit,rank,low_conf}]}
```

- 每題 `search(question, k)`;**命中**定義:期望 `expect_ids` 之一出現在 top-k,或 `expect_keywords` 出現在命中項的 title/resource/text。
- 指標:recall@k、逐題命中排名、命中項 `confidence==low` 標記。
- **假 embedder**(`fake.fake_embed`,字元雜湊→定維向量)供離線/CI 自測(只驗流程、分數無語意)。真品質需接真 embedding 端點。

---

## 參數速查(`config.py`)

| 參數 | 預設 | 用途 |
|---|---|---|
| `RENDER_DPI` | 220 | pptx/PDF 渲染 DPI(送出前才降到 `MAX_IMAGE_PX`) |
| `MAX_CONCURRENCY` | 8 | densify/synthesize 平行度 |
| `MAX_SLIDES_PER_GROUP` | 3 | 每概念群頁數上限 |
| `SYNTH_REFEED_IMAGES` | true | Stage C 是否重餵圖 |
| `MAX_IMAGE_PX` / `MAX_IMAGE_BYTES` | 1600 / 1.5MB | 圖片長邊 / 位元組預算 |
| `TILE_TRIGGER_PX` / `MAX_TILES` | 2600 / 6 | 密集頁切塊門檻 / 上限 |
| `TRIM_MARGINS` | true | 自動裁邊 |
| `OCR` / `OCR_LANG` | auto / (引擎預設) | OCR 引擎 / 語言 |
| `EMBED_BATCH` | 64 | 嵌入分批 |
| `DEDUP_THRESHOLD` | 0.92 | 疑似重複門檻 |

> **平行 vs 序列**:densify、synthesize 群間 = 平行(ThreadPool);cluster、merge、summarize = 序列(單/少次呼叫)。
