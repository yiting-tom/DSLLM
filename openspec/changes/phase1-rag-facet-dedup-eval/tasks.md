## 1. facet 過濾

- [ ] 1.1 `store.py`:`SqliteStore.topk` 加 `where: dict | None` 參數,`type`/`generated`/`confidence` 用 SQL 等值過濾、`tags` 在 Python 端判含,過濾在排序前套用
- [ ] 1.2 `store.py`:`Store` Protocol 的 `topk` 簽章同步加 `where`
- [ ] 1.3 `query.py`:CLI 加 `--type` / `--tag` / `--no-low-confidence` / `--facts-only`(排除 generated)旗標,轉成 `where` 傳入
- [ ] 1.4 冒煙測試:無 facet 結果不變;`--type` 只回該 type;`--no-low-confidence` 濾掉低信心;k 名額仍湊滿

## 2. 疑似重複標旗標

- [ ] 2.1 `config.py`:加 `DEDUP_THRESHOLD`(env `OKF_DEDUP_THRESHOLD`,預設 0.92)
- [ ] 2.2 `store.py`:`topk` 支援排除自身 id(dedup 時不比到自己)
- [ ] 2.3 `ingest.py`:本批全嵌入後,逐一 upsert 前對「當下庫」取最相似既有項,≥ 門檻則記一筆 flag(新 id、既有 id、分數、雙方標題)
- [ ] 2.4 `ingest.py`:輸出 `flags.jsonl` + 終端摘要;確認全程唯讀、不改任何 `.md`
- [ ] 2.5 冒煙測試(假 embedder):餵兩個近乎重複的 concept → 產生一筆 flag 且 bundle 不變;不相似則無 flag

## 3. golden eval harness

- [ ] 3.1 建 `pptx_to_okf/eval/` 模組:確定性假 embedder(供離線自測)
- [ ] 3.2 `eval/runner.py`:讀 `eval.yaml`(`question` / `expect_ids` / `expect_keywords`),對每題跑 `rag.query.search`,判命中(期望 id 在 top-k,或關鍵字命中)
- [ ] 3.3 `eval/runner.py`:算 recall@k、逐題排名、低信心命中標註;輸出報告 + 整體指標
- [ ] 3.4 `eval/runner.py`:支援注入 `embed_fn`(預設真 embedding,`--fake` 用假 embedder)
- [ ] 3.5 建 `eval.yaml` 範例(2–3 題假資料,標明供領域專家替換為真題)
- [ ] 3.6 冒煙測試:假 embedder + 小 bundle 跑完整 eval,產出報告與 recall@k

## 4. 收尾

- [ ] 4.1 `py_compile` 全通過;三塊冒煙測試綠燈
- [ ] 4.2 更新 `README.md`(facet 旗標、dedup flags、eval 用法)
- [ ] 4.3 `docs/ARCHITECTURE.md` 元件狀態表:facet / dedup-flag / eval 標 ✅
