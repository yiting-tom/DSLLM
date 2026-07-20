# A2 圖表 VLM 描述化

對應圖:[`a_2_vlm_desc`](../diagrams/l2_a/a_2_vlm_desc.mermaid)。前置過濾(裝飾圖/logo/底圖不進 VLM)之後,內容圖逐張呼叫,vLLM batch。

- **輸入**:圖片 + 上下文(doc_title、section_title、figure_id、caption、該 section 前後文字 200 字)
- **輸出**:`figures/{figure_id}.desc.md`(front matter 含 `desc_quality: vlm | fallback`)→ A4 正規化 → C1 embedding

## System prompt

```
你是半導體製程圖表的描述器。為圖表產出「數據結論式」描述,供語意檢索與工程師快速理解。描述必須包含四項:

1. 監控對象:圖表在追蹤什麼(參數名、機台、站點、wafer 批次等)。
2. 數據行為:趨勢、分布、異常點的具體行為(上升/下降/震盪/超規,從何時到何時)。
3. 事件標記:圖上標注的事件(調機、換耗材、異常發生點)及其對應變化。
4. 可讀數值:座標軸/標注中可辨識的具體數值,逐字轉錄,含單位。

規則:
- 禁止模糊詞:「某參數」「某時間」「似乎」「大概」。看不清就寫「不可辨識」,不要猜。
- 禁止純外觀描述(只講顏色、線條、座標軸長相而無資訊結論)。
- 圖中文字看不清楚時,參考 caption 與前後文推斷指涉對象,但數值不可推斷。
- 長度至少 30 字,以資訊密度為先,不硬湊。
```

## User prompt(模板)

```
文件:{doc_title}
章節:{section_title}
圖表編號:{figure_id}
Caption:{caption}

章節前後文(供理解脈絡,不要照抄):
{surrounding_text_200}

請描述這張圖。
```

## QC(程式檢核,三規則)

| 規則 | 觸發 |
|---|---|
| 長度 < 30 字 | 重試 |
| 含禁用模糊詞:某參數 / 某時間 / 似乎 | 重試 |
| 純外觀描述(僅顏色線條座標,無結論) | 重試 |

重試(最多 2 次):調 temperature + **在 prompt 附上失敗原因**。耗盡 → 降級:存 caption + 前後文作為描述,標記 `desc_quality: fallback`,記入 review 清單。

被前置過濾跳過的圖記 `skip_reason` 進 skip log,供抽查過濾規則是否誤殺。
