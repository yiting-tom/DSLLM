# A1-1 front matter 欄位抽取

對應圖:[`a_1_summary_pack`](../diagrams/l2_a/a_1_summary_pack.mermaid) EXTRACT subgraph。單次 call,JSON mode 強制 schema 輸出。

- **輸入**:全部 section 文字(sections.json)+ 圖表描述 + 表格描述(已 A4 正規化)
- **輸出**:JSON,經程式驗證後組裝 YAML front matter;doc_id 由程式配發(`OKF-{年}-{流水號}`),不由模型生成

## System prompt

```
你是半導體製程文件的欄位抽取器。從文件內容抽取結構化欄位,以 JSON 輸出。

規則:
1. 只依據文件內容,不得推測或補充文件中不存在的資訊。
2. process_stations / tools / defect_modes / related_params 的值必須使用下方詞彙表的標準術語(canonical);文件中出現別名時轉換為標準術語。
3. 文件中找不到某欄位的依據時,該欄位輸出空值(null 或空陣列),不要猜。
4. date_range 從文件中的日期線索判定(標題、頁首、內文事件日期);格式 YYYY-MM-DD;僅單一日期時 from 與 to 相同。

標準詞彙表(canonical):
{vocabulary_canonical_list_by_category}

doc_type 只能是以下之一:
{doc_type_enum}
```

## User prompt

```
文件標題:{doc_title}

=== 文件內容 ===
{all_sections_text}

=== 圖表描述 ===
{figure_descriptions}

=== 表格描述 ===
{table_descriptions}
```

## 輸出 JSON schema(response_format 強制)

```json
{
  "type": "object",
  "properties": {
    "doc_type":        {"type": ["string", "null"]},
    "date_range":      {"type": ["object", "null"], "properties": {"from": {"type": "string"}, "to": {"type": "string"}}},
    "process_stations": {"type": "array", "items": {"type": "string"}},
    "tools":           {"type": "array", "items": {"type": "string"}},
    "defect_modes":    {"type": "array", "items": {"type": "string"}},
    "related_params":  {"type": "array", "items": {"type": "string"}}
  },
  "required": ["doc_type", "date_range", "process_stations", "tools", "defect_modes", "related_params"]
}
```

## 產出驗證(程式,非 LLM)

| 檢核 | 失敗處理 |
|---|---|
| 值皆為 canonical | 查 alias 表自動修正;修不了 → 該欄位留空 + 記 warning |
| doc_type 在枚舉清單內 | 同上 |
| date_range 格式合法 | 同上 |

warning 進 B2 report,形成人工修補入口。
