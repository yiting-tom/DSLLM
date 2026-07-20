# 系統圖組(L0 → L1 → L2,全套 21 張)

三層下鑽式的架構圖:**L0 認識全貌 → L1 按分區分工 → 需要實作細節時下鑽 L2**。跨圖的銜接點在圖內以虛線加註標明(例如 l1_a 輸出指向 B/C、l1_b 的 vocab miss 回填指向 A4、l1_d 的查詢 log 指向 E)。可按「L0 對齊共識 → L1 分工 → L2 實作」直接發給團隊。

```
diagrams/
├── l0/       全景架構圖(1 張)
├── l1/       四張分區細部圖(A 轉換 / B 索引 / C hybrid RAG / D 整合層)
├── l2_a/     A 區實作圖(5 張,含錯誤路徑、QC 檢核、fallback 降級)
├── l2_b2/    B2 全量重建實作圖(5 張)
├── l2_c/     C 區實作圖(5 張:寫入端 2、查詢端 2、一致性維護 1)
└── l2_d/     D 區實作圖(5 張:tool 介面、filter、schema、路由、出處)
```

---

## L0 — 全景([`l0/l0_overview.mermaid`](l0/l0_overview.mermaid))

一張看懂全系統:左半是建置時的三條 pipeline(A 轉換 → 分流給 B 索引和 C 寫入 vdb),右半是查詢時的 D 整合層(四個 MCP tool),E 評估體系以虛線貫穿。D2 的 schema 共用約定也在這層標出。

---

## L1 — 四張分區細部圖(`l1/`)

| 圖 | 範圍 | 重點 |
|---|---|---|
| [`l1_a_okf_pipeline`](l1/l1_a_okf_pipeline.mermaid) | OKF 轉換 | 三路解析(文字/圖片/表格)→ A2 描述化與 A3 雙軌各成 subgraph → 三路匯入 A4 正規化(含 vocab miss log 的產出點)→ A1 生成 SUMMARY.md → 最終 bundle 目錄結構直接畫在輸出節點裡 |
| [`l1_b_index_pipeline`](l1/l1_b_index_pipeline.mermaid) | 階層索引 | B1 驗證與 entry 生成 → 三層確定性分層 → B3 唯一 LLM call → B2 重建發布壓縮成一個 subgraph,細節見 `l2_b2/` |
| [`l1_c_hybrid_rag`](l1/l1_c_hybrid_rag.mermaid) | hybrid RAG | 寫入端(C1 上下文拼接、C4 payload 組裝,同筆記錄寫入)與查詢端(A4 alias 展開、D2 pre-filter 分支、C2 雙路檢索 + RRF、C3 rerank、表格描述回取 linked_table 原文)兩大 subgraph |
| [`l1_d_integration`](l1/l1_d_integration.mermaid) | 整合層 | Kimi 路由到四條查詢路徑:索引導航、hybrid RAG(含改寫重查迴圈與 grep fallback)、metadata filter 列舉、綜觀組合(filter 列範圍 + 逐份讀 SUMMARY)→ 匯入 D4 出處標注;查詢 log 流向 E 評估 |

---

## L2 — A 區實作圖(`l2_a/`)

按資料流順序排列,每張都補上 L1 沒有的實作細節——特別是**錯誤路徑、QC 檢核、fallback 降級**這三類實作時會踩到的東西:

| 圖 | 主題 | L1 沒有的實作細節 |
|---|---|---|
| [`a_0_parsing`](l2_a/a_0_parsing.mermaid) | 格式解析 | 三種格式各自的抽取規則成獨立 subgraph(pptx 以 slide 為 section、docx 以 Heading 切、pdf 用字級啟發式);掃描 PDF 的 OCR 分支(繁中 OCR 情境)、損毀檔拒收路徑。輸出定義為三份中間表示(`sections.json` / `figures.json` / `tables.json`)= 後續三條路的 API 契約 |
| [`a_2_vlm_desc`](l2_a/a_2_vlm_desc.mermaid) | VLM 描述化 | 前置過濾(裝飾圖不進 VLM,省成本)、產出 QC(長度、禁用模糊詞、純外觀描述三條規則觸發重試)、重試耗盡後降級(caption + 前後文 fallback,標記品質供 review) |
| [`a_3_table_dual`](l2_a/a_3_table_dual.mermaid) | 表格雙軌 | `extract_quality` 判定(抽取失敗的表整表轉圖走 A2);軌道二的幻覺檢核(regex 抽出描述中的數值逐一比對原表,不存在即重試)——表格描述最容易出錯處,單獨一道閘門。底部附查詢時 desc → linked_table → 精確引用的取用關係 |
| [`a_4_vocabulary`](l2_a/a_4_vocabulary.mermaid) | 術語正規化 | 「寫入端收斂、查詢端展開」雙端完整畫出;vocabulary 載入時的衝突驗證(alias 跨 term 衝突直接 build fail)、長 alias 優先的 regex 編譯、保護區跳過(raw table 和 code block 不替換)、vocab miss 偵測 → B2 report → 回填的完整閉環 |
| [`a_1_summary_pack`](l2_a/a_1_summary_pack.mermaid) | SUMMARY 生成與打包 | A1 共兩次 LLM call(JSON mode 欄位抽取 + 摘要生成,可 batch 併發),各自的驗證與 fallback;bundle 打包的 manifest + hash 完整性檢核,通過才發 `bundle_created` 事件,同時餵給 B(rebuild counter)和 C(embedding 寫入) |

---

## L2 — B2 全量重建實作圖(`l2_b2/`)

| 圖 | 主題 | 重點 |
|---|---|---|
| [`b2_2_rebuild_flow`](l2_b2/b2_2_rebuild_flow.mermaid) | 重建流程主體(**建議先看**) | 五個 step 各自成 subgraph:Step 1~4 純程式,Step 5 是唯一 LLM call(橘色標記);驗證階段三向分支:通過 / 自動正規化 / 進 error report |
| [`b2_1_triggers`](l2_b2/b2_1_triggers.mermaid) | 觸發機制 | 三軌觸發(計數、cron、手動)匯流後經 rebuild lock 防並行;counter 歸零與 lock 釋放的完整生命週期 |
| [`b2_3_atomic_swap`](l2_b2/b2_3_atomic_swap.mermaid) | 原子性切換 | symlink 用 `mv -T` rename 保證原子性;附三個開發參考 subgraph:目錄結構、查詢端(MCP tool)讀取行為、手動回滾程序 |
| [`b2_4_sanity_check`](l2_b2/b2_4_sanity_check.mermaid) | sanity check | 五道檢核串成 fail-fast 鏈,任一失敗即短路並寫入失敗明細;檢核 5(TOPICS.md 引用驗證)橘色標出——整條 pipeline 唯一擋 LLM 幻覺的閘門 |
| [`b2_5_drift_monitor`](l2_b2/b2_5_drift_monitor.mermaid) | 漂移監控 | report 生成後三條回饋:error report → 修 bundle、vocabulary miss → 回填 A4 並手動觸發重建(閉環回 b2_1)、topic 異常 → 檢視 prompt;選配長期趨勢儀表板 |

### B2 設計要點(為什麼是「全量重建」)

**問題**:INDEX.md 由模型生成,增量追加會漂移——每次追加的風格、詳略、術語用法逐漸不一致,舊 entry 也不會因新知識加入而更新分類。

**解法**:把 index 降級為「front matter 的確定性彙整產物」,當成可拋棄的東西定期從 bundle 全量重生:

1. **雙軌觸發**——計數(每 +20 bundle)保證成長期不落後,cron(每週日 02:00)保證低頻期定期校正;vocabulary.yaml 或 schema 改版必須手動觸發,否則新舊 entry 正規化不一致。
2. **從 front matter 重建,不重讀全文**——A1 已把結構化欄位存進每個 bundle 的 front matter,所以掃描、驗證、分層(站點 → 文件類型 → 日期排序)、模板渲染全是零 LLM 成本的確定性程式;**唯一 LLM call 是 TOPICS.md 的跨 bundle 關聯(只餵 front matter)**。幾百個 bundle 重建也只要幾秒到幾分鐘,順帶消滅 entry 層級的幻覺風險。
3. **原子性切換**——不原地覆寫,目錄版本 + `current` symlink 切換;MCP tool 永遠讀 `current`,重建失敗就繼續用舊版,永遠查不到半成品。保留最後 5 版供回滾。
4. **sanity check 擋壞版本上線**——entry 數 = bundle 數(扣已知排除)、entry 數不比上一版掉 >2%、schema/canonical 術語齊全、抽樣反查 bundle 一致、TOPICS.md 引用的 doc_id 逐一驗證存在(最後一項是幻覺唯一可能混進來的地方)。
5. **漂移長期監控**——每次重建產出 diff 摘要(bundle 數、entry 數、error 明細、topic 變化、vocabulary misses);vocabulary misses 自然形成 A4 詞表的回填來源,閉環。

**開發順序建議**:b2_2 的 Step 1~4(純程式,可獨立測試)→ b2_3 版本目錄與 symlink → b2_4 檢核 → b2_1 觸發 → Step 5 與 b2_5。每一步都有可驗證的產出。

---

## L2 — C 區實作圖(`l2_c/`)

前兩張是寫入端、中間兩張是查詢端、最後一張是一致性維護:

| 圖 | 主題 | 重點 |
|---|---|---|
| [`c_0_chunking`](l2_c/c_0_chunking.mermaid) | chunk 切割 | 三種內容型態分流:section 文字按長度決定整段成 chunk 或段內切割(384~512 tokens、overlap 64、尾段過短併入前段防碎片);圖表和表格描述**永不切割**(一單元一 chunk)。三條開發約定寫在圖底:section 邊界不可跨、描述不切、overlap 只存在於段內 |
| [`c_1_4_ingest`](l2_c/c_1_4_ingest.mermaid) | 寫入端(C1+C4) | C1 的 embed_text 拼接模板按 content_kind 分三版(text / 圖 / 表各自的脈絡標記);C4 payload 分必填與條件欄位並戳 schema 版本號;dense + sparse 雙路向量化後批次 upsert;寫入後以「point 數 == chunk 數」驗證,成功落帳到 **ingest_ledger**——這本帳是 c_4 對帳和 schema 改版回填的依據 |
| [`c_2_hybrid_query`](l2_c/c_2_hybrid_query.mermaid) | hybrid 查詢 | 從 MCP tool 參數驗證開始(filter 值 alias 自動轉 canonical、欄位不存在則回錯誤附可用欄位清單,讓 Kimi 自我修正);query 雙路處理(dense 原句、BM25 展開 aliases);pre-filter 候選數為零回傳放寬建議而非硬失敗;雙路 top-50 + RRF 融合。調參起始值(k=60、各路 50)和觀察指標寫在備註區 |
| [`c_3_rerank_resolve`](l2_c/c_3_rerank_resolve.mermaid) | rerank 與解析 | rerank 後多一道低信心判定(最高分低於門檻附 `low_confidence` 旗標,提示 Kimi 改寫或走 grep fallback,對應 l1_d 重查迴圈);結果解析按 content_kind 分流:表格描述回取 raw markdown、各型態 attach 出處欄位、同 section 相鄰命中合併拼回脈絡;回傳格式中的 citation 欄位直接服務 D4 |
| [`c_4_sync`](l2_c/c_4_sync.mermaid) | 增量同步(運維面) | 四種事件(新增/更新/刪除/schema 改版)各自處理路徑:更新一律「先刪後寫」、刪除一律以 okf_id filter 整批刪;每日 cron 三方對帳(bundle 目錄 vs ledger vs vdb)兜底,任何漂移自動修復並在 B2 report 留痕。核心原則:**vdb 永遠是 bundle 的投影,衝突時以 bundle 為準重建** |

---

## L2 — D 區實作圖(`l2_d/`)

| 圖 | 主題 | 重點 |
|---|---|---|
| [`d_0_mcp_tools`](l2_d/d_0_mcp_tools.mermaid) | MCP tool 介面總覽 | 五個 tool 的完整簽名(`read_topics` / `read_index` / `read_bundle` / `hybrid_search` / `filter_documents`)+ 每次 tool call 的共通生命週期:JSON schema 驗證 → alias 正規化 → 路由執行 → 回應大小截斷 → 落 log。關鍵設計原則:**錯誤回傳必附修正指引和正確用法範例**,這是 agentic 系統能自我修正的前提 |
| [`d_1_filter_tool`](l2_d/d_1_filter_tool.mermaid) | filter tool 實作 | 三個容易漏掉的細節:零條件直接拒絕(防全量掃描)、以 okf_id 去重(vdb 存 chunk 但列舉單位是文件,不做這步數字全錯)、回應附 `applied_filters` 讓 Kimi 確認正規化後的條件沒有偏移語意。圖底寫明存在理由:「不多不少」的保證,前提是 c_4 對帳成立 |
| [`d_2_schema_sync`](l2_d/d_2_schema_sync.mermaid) | schema 同步 | `schema.yaml` 作為單一事實來源,四個消費者(A1 front matter / B1 entry / C4 payload / D0 tool 參數)import 同一份 parser。改版分向後相容和破壞性兩路,破壞性改版有四步順序和回填期間的 partial 警示機制。枚舉值動態引用 vocabulary.yaml 的 canonical,術語新增不需改 schema |
| [`d_3_routing`](l2_d/d_3_routing.mermaid) | 路由決策樹 | **skill prompt 的邏輯藍圖**:四層判斷依序過(列舉 → 指名 → 綜觀 → 精確代號)落到五條路徑之一,之後進入每輪必做的自我評估迴圈——失敗原因分四類各有對應動作(拆子問題 / 改寫 / grep fallback / 鬆綁 filter),四輪上限後誠實回報部分結果而非硬編。備註區含 prompt 撰寫要點,包括要求模型每次 tool call 前說明選擇理由(E2 分析路由錯誤的素材) |
| [`d_4_citation`](l2_d/d_4_citation.mermaid) | 出處標注 | 四條組合規則(逐論點標注、數值取 raw_table、矛盾明示、推測聲明)+ 送出前三項自我檢核,其中「**標注的 id 必須出現在本輪 tool 結果中**」是擋幻覺引用的最後閘門,和 b2_4 的檢核 5 同型設計。問答 log 流向 E 體系,一魚三吃(出題素材 / 引用正確率 / 微調樣本) |

---

## 跨圖銜接點速查

| 從 | 到 | 銜接 |
|---|---|---|
| l1_a(A1 打包) | l1_b / l1_c | `bundle_created` 事件同時餵 B(rebuild counter)與 C(embedding 寫入) |
| l1_b(B2 report) | l1_a(A4) | vocabulary miss 回填詞表,回填後手動觸發重建(閉環) |
| l1_c 查詢端 | l1_a(A4)/ l1_d(D2) | alias 展開、pre-filter 分支 |
| l1_d(查詢 log) | E 評估 | 所有查詢路徑的 log 匯入 E |
| a_3(表格描述) | c_3(結果解析) | desc 命中 → linked_table 回取 raw markdown → 精確引用 |
| c_1_4(ingest_ledger) | c_4(對帳)/ d_1 | 落帳是三方對帳的依據;d_1「不多不少」保證的前提 |
| c_3(low_confidence) | l1_d / d_3(重查迴圈) | 低信心旗標提示 Kimi 改寫或走 grep fallback |
| c_4(對帳修復) | l1_b(B2 report) | 漂移自動修復後在 B2 report 留痕 |
| c_3(citation 欄位) | d_4(出處標注) | 回傳格式直接服務 D4 組合規則 |
| d_2(schema.yaml) | A1 / B1 / C4 / D0 | 單一事實來源,四個消費者共用同一份 parser |
| d_4(id 存在檢核) | b2_4(檢核 5) | 同型設計:LLM 產物引用的 id 逐一驗證存在,擋幻覺 |
| d_3 / d_4(log) | E 評估 | 路由理由供 E2 分析;問答 log 一魚三吃 |
| l1_b(B2 subgraph) | `l2_b2/` 五張 | L1 壓縮成一個 subgraph,實作細節下鑽 |

## 狀態

全套 21 張已完成:L0 × 1、L1 × 4、L2 × 16(A 五張、B2 五張、C 五張、D 五張)。後續需要針對某張圖產出對應的程式骨架,指定圖即可。
