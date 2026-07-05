## 1. 生成 Overview 概念

- [x] 1.1 `prompts.py`:`SUMMARY_SYSTEM` + `summary_user(topic, members)`(綜合成員 → Overview body/description,不腦補)
- [x] 1.2 `build.py`:`write_overview(root, subpath, title, description, body, related, ts)` 寫 `<topic>/_overview.md`(generated:true、type Topic Overview、related=成員 id、id=ov_+hash(subpath) 穩定覆寫)
- [x] 1.3 `summarize.py`:`load_chunks` 讀概念、依子目錄分組(排除既有 _overview 與 generated);每組呼叫 LLM 生 Overview;`related`=成員 id;可注入 `chat_fn`
- [x] 1.4 `summarize.py`:CLI `python -m pptx_to_okf.summarize ./bundle`

## 2. graph 展開檢索

- [x] 2.1 `rag/store.py`:`get(id)` 依 id 取單一概念(含 metadata)
- [x] 2.2 `rag/query.py`:`search(..., expand=False)`;expand 時對每個 hit 的 `related` 取回附加(dedup、標 via_related);CLI 加 `--expand`

## 3. 驗證與文件

- [x] 3.1 `py_compile` 全通過
- [x] 3.2 冒煙(fake chat + fake embed):小 bundle → 每主題一個 _overview(generated:true、related=成員 id);重跑不重複;成員檔不變
- [x] 3.3 冒煙:ingest 後 `--expand` 命中 Overview 會帶出成員;未 expand 行為不變
- [x] 3.4 更新 README + ARCHITECTURE(Phase 2 狀態、摘要/展開用法)
