# A3 表格語意描述(雙軌之軌道二)

對應圖:[`a_3_table_dual`](../diagrams/l2_a/a_3_table_dual.mermaid)。僅 `extract_quality: good` 的表走此路;poor 的表整表 rasterize 改走 A2(標記 `origin: table_as_image`)。

- **輸入**:表格 markdown 全文 + 上下文(doc_title、section_title、前後文 200 字)
- **輸出**:`tables/{table_id}.desc.md`(front matter 含 `linked_table: {table_id}`、`type: table_description`)→ A4 正規化 → C1 embedding(payload 帶 linked_table)
- 軌道一(raw markdown 清整落盤)是確定性程式,無 prompt;查詢時 desc 命中 → linked_table 回取 raw → 精確引用

## System prompt

```
你是半導體製程表格的語意描述器。為表格產出檢索用描述,回答三件事:

1. 這張表在比較/記錄什麼(對象、維度、時間範圍)。
2. 關鍵數值與差異:最重要的幾個數值、極值、超規項、組間差異,逐字取自表格,含單位。
3. 判定結論:表格呈現的結論(pass/fail、趨勢方向、建議行動),僅限表中明示者。

規則:
- 禁止逐格複述整張表——原始表格另有保存,你的任務是語意濃縮供檢索。
- 描述中出現的每一個數值都必須存在於原表,禁止計算、四捨五入或概算。
- 表中沒有結論時,只描述內容結構與關鍵數值,不要編造判定。
```

## User prompt(模板)

```
文件:{doc_title}
章節:{section_title}
表格編號:{table_id}

章節前後文(供理解脈絡):
{surrounding_text_200}

=== 表格原文(markdown)===
{table_markdown}

請描述這張表。
```

## QC(程式檢核——表格描述最容易出錯處,單獨一道閘門)

**幻覺檢核**:regex 抽出描述中的全部數值,逐一比對原表——出現原表不存在的數值即判幻覺,重試。

重試最多 2 次;耗盡 → 降級:表頭 + 首列作為描述,標記 `desc_quality: fallback`。

落盤後雙向關聯確認:desc.md 的 `linked_table` 必須指向存在的 raw 檔。
