# Schema 契約(單一事實來源)

對應圖:[`d_2_schema_sync`](../diagrams/l2_d/d_2_schema_sync.mermaid)、[`d_0_mcp_tools`](../diagrams/l2_d/d_0_mcp_tools.mermaid)、[`d_1_filter_tool`](../diagrams/l2_d/d_1_filter_tool.mermaid)、[`c_1_4_ingest`](../diagrams/l2_c/c_1_4_ingest.mermaid)。

| 檔案 | 內容 |
|---|---|
| [`schema.yaml`](schema.yaml) | 欄位契約 SSOT:bundle 級欄位 + chunk 級 payload 欄位 + 改版約定 |
| [`MCP_TOOLS.md`](MCP_TOOLS.md) | 五個 MCP tool 的完整簽名(JSON schema)、共通生命週期、錯誤與回傳格式 |

## 消費關係

```
schema.yaml ──單一 parser 模組──┬→ A1  front matter 欄位定義與驗證
                                ├→ B1  INDEX entry 模板 + B2 sanity check 合規檢核
                                ├→ C4  vdb payload 定義 + 寫入驗證
                                └→ D0/D1  tool filter 參數 JSON schema + 錯誤訊息欄位清單
```

核心約定:

- **任何人不得在單一消費者私自加欄位**——必須進 schema.yaml、schema_ver 升版、PR review。
- **B1 entry 與 C4 payload 欄位語意完全等價**:索引導航結果與 filter 結果永遠可互相印證。
- 欄位值一律 canonical(A4 寫入端收斂);raw table 與 code block 是保護區,不做替換。

## 枚舉值與 vocabulary.yaml

站點 / 機台 / defect 類欄位的合法值 = `vocabulary.yaml` 對應 category 的 canonical,以 `enum_source: vocabulary#<category>` 動態引用——**術語新增不需改 schema**。

vocabulary.yaml 結構(A4 契約):

```yaml
terms:
  - canonical: CMP            # 儲存一律用這個(寫入端收斂)
    aliases: [化學機械研磨, chemical mechanical polishing, 研磨站]
    category: process_station
  - canonical: delamination
    aliases: [脫層, 剝離, delam]
    category: defect_mode
```

載入時驗證(衝突即 build fail):canonical 不重複、alias 不跨 term 衝突。編譯成 alias → canonical 對照表 + 預編譯 regex(長 alias 優先匹配,中文直接匹配、英文加 word boundary)。查詢端展開:BM25 路把命中詞展開成 `(canonical OR alias1 OR ...)`,dense 路原句不變。

## 改版流程

| 變更類型 | 流程 |
|---|---|
| 新增選填欄位(向後相容) | 直接發布;新 bundle 開始帶新欄位,舊資料查詢時該欄位視為空 |
| 必填欄位 / 枚舉結構變更(破壞性) | 四步依序:① A pipeline 更新 → ② C 批次回填(c_4 schema 改版路徑,ledger 找出舊 bundle)→ ③ B2 手動觸發全量重建 → ④ MCP tool schema 熱更新 |

回填完成的判定:ledger 中全部 bundle 的 `schema_ver` == 新版。未完成前,MCP filter 對新欄位標記 `partial` 並在回應中警示 Kimi 結果可能不完整。

## 與既有 pipeline 的關係

ARCHITECTURE.md §3 的 `cpt_*` frontmatter 是既有 pptx_to_okf pipeline 的**概念級**契約;本目錄的 schema.yaml 是新架構(L0–L2 圖組)的 **bundle 級**契約,兩者不同層、並存。
