# Prompt 定義(全部 LLM / VLM call site)

整條 pipeline 的模型呼叫點只有下面這些;其餘全是確定性程式。每個 prompt 檔含:模板全文、輸入來源、輸出契約、QC 規則、重試與降級路徑。

## 建置時(離線)

| 檔案 | 呼叫點 | 模型 / 模式 | QC | 重試耗盡降級 |
|---|---|---|---|---|
| [`a1_field_extraction.md`](a1_field_extraction.md) | A1 第一次 call:front matter 欄位抽取 | K2.7,JSON mode(強制 schema) | 程式驗證:canonical / 枚舉 / 日期格式 | alias 自動修正;修不了 → 欄位留空 + warning |
| [`a1_summary.md`](a1_summary.md) | A1 第二次 call:摘要正文生成 | K2.7 | 數值 / doc_id 存在於素材、長度 150~300 | 重試 2 次 → 首 section 前 200 字 + fallback 標記 |
| [`a2_figure_description.md`](a2_figure_description.md) | A2:圖表 VLM 描述化 | K2.7 vision(vLLM batch) | 長度 ≥30、禁用模糊詞、禁純外觀描述 | 重試 2 次(調 temp + 附失敗原因)→ caption + 前後文 |
| [`a3_table_description.md`](a3_table_description.md) | A3 軌道二:表格語意描述 | K2.7 | regex 抽數值逐一比對原表(擋幻覺) | 重試 2 次 → 表頭 + 首列 + fallback 標記 |
| [`b2_topics.md`](b2_topics.md) | B2 Step 5:TOPICS.md 跨 bundle 關聯(**重建流程唯一 LLM call**) | K2.7,只餵 front matter | b2_4 檢核 5:引用的 doc_id 逐一驗證存在 | 驗證失敗 → 沿用舊版 TOPICS.md + 告警 |

A1 兩次 call 可 batch 併發;所有 fallback / warning 都會出現在 B2 report,形成人工修補入口。

## 查詢時(線上)

| 檔案 | 用途 |
|---|---|
| [`d3_router_skill.md`](d3_router_skill.md) | Kimi 的 system prompt / skill 全文:路由決策樹(d_3)+ 出處標注與自我檢核(d_4) |

## 非 LLM 的文字模板

| 檔案 | 用途 |
|---|---|
| [`c1_embed_templates.md`](c1_embed_templates.md) | C1 embed_text 拼接模板(按 content_kind 三版)——進 embedding 的正規形,非 prompt |

## 共通約定

- prompt 中的欄位名 / 枚舉值一律引用 [`../schema/schema.yaml`](../schema/schema.yaml),術語一律 canonical([`vocabulary` 契約](../schema/README.md))。
- LLM 產物 → A4 正規化(alias → canonical)之後才落盤。
- 重試上限一律 2 次;降級必標 `desc_quality: fallback` / 記 review 清單,絕不無聲吞掉。
