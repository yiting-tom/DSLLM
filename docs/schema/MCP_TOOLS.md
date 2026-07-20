# MCP Tool 介面契約

對應圖:[`d_0_mcp_tools`](../diagrams/l2_d/d_0_mcp_tools.mermaid)、[`d_1_filter_tool`](../diagrams/l2_d/d_1_filter_tool.mermaid)、[`c_2_hybrid_query`](../diagrams/l2_c/c_2_hybrid_query.mermaid)、[`c_3_rerank_resolve`](../diagrams/l2_c/c_3_rerank_resolve.mermaid)。

filter 欄位名與枚舉值一律取自 [`schema.yaml`](schema.yaml)(`filterable: true` 的欄位)。

## 共通生命週期(每次 tool call)

```
JSON schema 驗證 → alias → canonical 正規化(A4)→ 路由執行
→ 回應大小截斷(truncated: true + 取得餘下內容的方法)→ 落 log(供 E2)
```

設計原則:

- **錯誤回傳必附修正指引和正確用法範例**——模型看得懂才能 agentic 重試。
- read 類 tool 唯讀 `current/` symlink,永不觸碰版本目錄(b2_3)。
- tool description 寫明各 tool 適用的查詢類型(輔助 d_3 路由)。

錯誤回傳格式:

```json
{
  "error_code": "unknown_filter_field",
  "message": "filter 欄位 'station' 不存在",
  "hint": "可用欄位:process_station, tool, doc_type, date_from, date_to, defect_mode",
  "example": {"filters": {"process_station": "CMP"}}
}
```

---

## 1. `read_topics()`

跨 bundle 主題總覽(B2 Step 5 產物)。

```json
{"name": "read_topics", "inputSchema": {"type": "object", "properties": {}}}
```

回傳:`current/TOPICS.md` 全文。

## 2. `read_index(station?, doc_type?)`

階層式索引導航。不帶參數 = 根目錄總覽(站點層)。

```json
{
  "name": "read_index",
  "inputSchema": {
    "type": "object",
    "properties": {
      "station":  {"type": "string", "description": "process_station canonical 值;alias 會自動轉換"},
      "doc_type": {"type": "string", "enum": ["SOP", "異常分析報告", "週報", "月報", "教材", "會議記錄", "規格書"]}
    }
  }
}
```

回傳:對應層 `INDEX.md`。

## 3. `read_bundle(okf_id, part)`

指定文件的精確讀取(出處回溯也走這裡)。

```json
{
  "name": "read_bundle",
  "inputSchema": {
    "type": "object",
    "properties": {
      "okf_id": {"type": "string", "pattern": "^OKF-\\d{4}-\\d{4}$"},
      "part":   {"type": "string", "description": "summary | {section_id} | {figure_id} | {table_id}"}
    },
    "required": ["okf_id", "part"]
  }
}
```

回傳:指定內容(summary = SUMMARY.md;table_id 回 raw markdown)。

## 4. `hybrid_search(query, filters?, top_k=8)`

語意檢索(c_2 雙路 + RRF → c_3 rerank)。

```json
{
  "name": "hybrid_search",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query":   {"type": "string"},
      "filters": {
        "type": "object",
        "properties": {
          "process_station": {"type": "string"},
          "tool":            {"type": "string"},
          "doc_type":        {"type": "string"},
          "date_from":       {"type": "string", "format": "date"},
          "date_to":         {"type": "string", "format": "date"},
          "defect_mode":     {"type": "string"}
        }
      },
      "top_k": {"type": "integer", "default": 8}
    },
    "required": ["query"]
  }
}
```

回傳格式(c_3):

```json
{
  "results": [{
    "text": "...",
    "score": 0.87,
    "citation": {"okf_id": "OKF-2026-0143", "doc_title": "...", "section_id": "s3", "figure_id": null, "table_id": "t2"},
    "raw_table": "|參數|值|\n|...|(僅 content_kind=table_desc,由 linked_table 回取)"
  }],
  "meta": {
    "low_confidence": false,
    "applied_filters": {"process_station": "CMP"},
    "total_candidates": 50
  }
}
```

行為要點:

- filter 值是 alias → 自動轉 canonical;欄位不存在 → 錯誤 + 可用欄位清單。
- pre-filter 候選數 = 0 → 回空結果 + **逐一放寬條件的建議**(非硬失敗,讓 Kimi 決定重試策略)。
- dense 原句 / BM25 展開 aliases,各 top-50,RRF 融合(k=60 起始值)。
- rerank 最高分低於門檻 → 照回傳但附 `low_confidence: true`(提示改寫或 grep fallback)。
- 同 bundle 相鄰 chunk 合併,拼回完整脈絡。

## 5. `filter_documents(filters, mode, page?, page_size=50)`

metadata 精確列舉——結果 = **全部符合條件的文件,不多不少**(非 top-k;前提是 c_4 對帳成立)。

```json
{
  "name": "filter_documents",
  "inputSchema": {
    "type": "object",
    "properties": {
      "filters": {"$ref": "#/hybrid_search/filters"},
      "mode":    {"type": "string", "enum": ["list", "count"]},
      "page":      {"type": "integer", "default": 1},
      "page_size": {"type": "integer", "default": 50}
    },
    "required": ["filters", "mode"]
  }
}
```

回傳:

```json
{
  "mode": "list",
  "items": [{"okf_id": "...", "doc_title": "...", "doc_type": "...", "date_range": {"from": "...", "to": "..."}, "process_stations": ["CMP"]}],
  "total": 37,
  "next_page": 2,
  "group_counts": {"by_station": {"CMP": 21}, "by_doc_type": {"異常分析報告": 14}},
  "applied_filters": {"process_station": "CMP", "date_from": "2025-10-01"}
}
```

行為要點:

- **零條件直接拒絕**(防全量掃描)。
- **以 okf_id 去重**:vdb 存 chunk、列舉單位是文件,scroll 全量 + group by okf_id,不做這步數字全錯。
- 依 date_range 降冪;超過 page_size 分頁(items + total + next_page)。
- 回應附 `applied_filters`(canonical 化後的實際條件),供 Kimi 確認語意無偏移。
- `total` 可直接用於「共幾份」類回答。
