# B2 Step 5 — TOPICS.md 跨 bundle 關聯

對應圖:[`b2_2_rebuild_flow`](../diagrams/l2_b2/b2_2_rebuild_flow.mermaid) STEP5。**整條 index 重建流程唯一的 LLM call**——分層與 entry 生成全是確定性程式,LLM 只做程式做不到的事:發現跨文件關聯。

- **輸入**:全部 bundle 的 front matter(metas 清單)——**不含全文**,幾百份也只是一次小 call
- **輸出**:`TOPICS.md`,主題聚類 + 每個 topic 的 doc_id 清單
- **驗證**:b2_4 檢核 5——TOPICS.md 引用的 doc_id 逐一驗證存在(這是幻覺唯一可能混進 index 的地方);失敗則整版不上線

## System prompt

```
你是半導體製程知識庫的主題整理器。輸入是全部文件的結構化欄位(標題、類型、站點、機台、defect 模式、日期),請找出跨文件的主題關聯,產出主題地圖。

規則:
1. 每個 topic 是一個工程上有意義的主題(同一 defect 模式的系列分析、同一機台的長期監控、同一站點的 SOP 體系等)。
2. topic 名稱用輸入欄位中出現的標準術語組合,禁止發明新術語。
3. 每個 topic 列出所屬文件的 doc_id——只能使用輸入清單中存在的 doc_id,逐一核對,禁止杜撰。
4. 一份文件可屬多個 topic;孤立文件(無關聯)不硬塞,歸入「未分類」。
5. topic 依所含文件數降冪排列。

輸出格式(markdown):
# TOPICS

## {topic 名稱}({文件數})
{一句話說明此主題的範圍}
- OKF-YYYY-NNNN {doc_title}
- ...
```

## User prompt

```
以下是全部 {n} 份文件的結構化欄位(JSON lines):

{metas_jsonl}
```

## 驗證與失敗處理

| 檢核 | 處理 |
|---|---|
| 引用的 doc_id 全部真實存在(b2_4 檢核 5) | 任一不存在 → sanity check 失敗,新版不切換,沿用舊版 + 告警 |
| topic 數異常(暴增/暴減 vs 上一版) | b2_5 report 標記,人工檢視 prompt |
