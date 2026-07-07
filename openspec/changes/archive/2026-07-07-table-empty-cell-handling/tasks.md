## 1. prompt 硬化

- [x] 1.1 `prompts.py`:`DENSIFY_SYSTEM` 加表格規則(空白保留 `—`、禁補值/推測、逐欄對齊不左移、看不清標 `?`)
- [x] 1.2 `prompts.py`:`SYNTHESIZE_SYSTEM` 加同一組表格規則(避免寫概念時重新腦補)
- [x] 1.3 措辭保留彈性:合併儲存格照原樣描述,只有「真的空白」才用 `—`

## 2. 驗證與文件

- [x] 2.1 `py_compile` 通過;確認兩個 SYSTEM prompt 都含表格規則
- [x] 2.2 更新 `docs/ALGORITHMS.md`(densify/synthesize 段註明表格空白/對齊規則)
- [ ] 2.3(需 key)挑一張有空白 cell 的表做前/後 A/B,確認補值/錯位下降
