# C1 embed_text 拼接模板

對應圖:[`c_1_4_ingest`](../diagrams/l2_c/c_1_4_ingest.mermaid) C1 subgraph。**非 LLM prompt**——這是進 embedding(dense BGE-M3 + sparse BM25)的文字正規形;chunk 裸文字缺脈絡,拼上文件/章節標記後語意才完整。

輸入皆已 A4 正規化(canonical),BM25 斷詞直接吃同一份 embed_text。

## 三版模板(按 content_kind)

### text(section 文字 chunk)

```
【{doc_title}|{section_title}】
{chunk_text}
```

### fig_desc(圖表描述)

```
【{doc_title}|{section_title}|圖 {figure_id}】
{description_text}
```

### table_desc(表格描述)

```
【{doc_title}|{section_title}|表 {table_id}】
{description_text}
```

## 約定

- `doc_title` / `section_title` 取自 bundle 的 SUMMARY.md front matter 與 sections.json,不即席生成。
- raw table 不進 embedding——只存路徑(payload.linked_table)供 c_3 回取。
- 模板變更 = 全量 re-embed,等同破壞性改版,走 c_4 schema 改版路徑。
- rerank(c_3)的 (query, passage) 對也用同一份 embed_text,兩處看到的文字一致。
