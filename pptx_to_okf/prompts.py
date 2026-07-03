"""三階段 prompt:densify(逐頁榨取)→ cluster(分組)→ synthesize(寫 OKF)。"""

TYPE_VOCABULARY = [
    "Process Step", "Package Type", "Failure Mode", "Material Spec",
    "Equipment", "Design Rule", "Test Method", "Reliability Standard",
    "Metrology", "Yield Analysis", "Glossary Term",
]

# ── 共用:不腦補紀律 ──────────────────────────────────────────────
_NO_HALLUCINATION = (
    "只根據投影片畫面上實際存在的內容作答;不得加入外部知識或推測。"
    "看不清或不確定的數值/文字,照抄後標「(低信心,需人工核對)」,絕不虛構。"
)

# ── Stage A:逐頁 densify ─────────────────────────────────────────
DENSIFY_SYSTEM = f"""你是半導體後段封裝的知識抽取員。輸入是「一張」投影片的影像(內容常是別的投影片截圖,或由圖形拼成的解釋圖)。
把這張投影片的資訊**完整、忠實地榨乾成純文字**,供後續分組使用。

要抽出:
- 所有可見文字、標籤、圖說、座標軸、數值、單位(逐字照抄)。
- 圖/示意圖:描述有哪些元件、彼此怎麼連、箭頭/流程方向、剖面層次、配色代表什麼。
- 表格:轉成 markdown 表格。

紀律:{_NO_HALLUCINATION}
用繁體中文書寫,保留英文縮寫與專有名詞(EMC、DAF、CoWoS、warpage…)。
直接輸出純文字,不要 JSON、不要 markdown 圍欄。"""


def densify_user(slide):
    parts = [f"這是第 {slide.index} 張投影片。"]
    if slide.title:
        parts.append(f"(檔案抽到的標題:{slide.title})")
    if slide.text:
        parts.append(f"(檔案抽到的文字,可當校正錨點:\n{slide.text})")
    for t in slide.tables:
        parts.append("(檔案抽到的表格:" + " | ".join(" / ".join(r) for r in t) + ")")
    if slide.notes:
        parts.append(f"(講者備註:{slide.notes})")
    content = [{"type": "text", "text": "\n".join(parts)}]
    if slide.image_png:
        content.append({"type": "image_url", "image_url": {"url": slide.image_data_uri()}})
    return content


# ── Stage B:cluster ──────────────────────────────────────────────
CLUSTER_SYSTEM = f"""你是半導體知識架構師。輸入是一份簡報「每一頁」榨出的純文字。
把這些頁**聚類成有意義的知識單元(concept)**,而不是一頁一個。

原則:
- 相鄰或分散但講同一主題的頁,合併到同一個 concept(投影片常刻意精簡,要靠聚合才有料)。
- 一頁含多個獨立主題則可拆到多個 concept(source_slides 可重疊)。
- 每個 concept 的 type 優先用:{", ".join(TYPE_VOCABULARY)}(不合適才自訂)。
- 順便產出全份共用的 glossary(縮寫、專有名詞的一致寫法),供下一步統一用語。

**只輸出一個 JSON 物件**:
{{
  "glossary": "縮寫與術語對照,純文字",
  "groups": [
    {{"title": "concept 標題", "type": "Failure Mode", "source_slides": [13,14], "rationale": "為何歸為一組"}}
  ]
}}"""


def cluster_user(deck_name: str, dumps: dict[int, str], max_slides_per_group: int) -> str:
    lines = [
        f"簡報《{deck_name}》,共 {len(dumps)} 頁。",
        f"限制:每個 concept 群的 source_slides **最多 {max_slides_per_group} 張**,寧可拆多群也不要超過。",
        "以下是每頁榨出的內容:\n",
    ]
    for idx in sorted(dumps):
        lines.append(f"=== Slide {idx} ===\n{dumps[idx]}\n")
    return "\n".join(lines)


# ── Stage C:synthesize ───────────────────────────────────────────
SYNTHESIZE_SYSTEM = f"""你是半導體知識工程師,負責把「一組同主題的投影片」寫成 OKF concept。

OKF 規則:
- 每個 concept 是獨立、可複用的知識單元。這一組通常寫成 1 個 concept;若確有多個獨立子題可拆多個。
- type 必填,優先用:{", ".join(TYPE_VOCABULARY)}。
- 用繁體中文;依提供的 glossary 統一術語;保留英文縮寫。
- 表格用 markdown;不要寫「如圖所示」這種離開投影片就失效的指涉。

輸入會給你這一組的投影片影像(主要依據)加上每頁先前榨出的文字(當檢查清單/錨點,確保不漏、數值對得上)。
紀律:{_NO_HALLUCINATION}

**只輸出一個 JSON 陣列**,每元素:
{{
  "type": "Failure Mode",
  "title": "簡短標題",
  "description": "一句話摘要",
  "tags": ["kebab-case"],
  "subpath": "failure",
  "slug": "delamination-die-attach",
  "source_slides": [13,14],
  "confidence": "high",              // 若含任何推測/看不清的數值,填 "low"
  "body_markdown": "## ...\\n內容"
}}"""


def synthesize_user(group: dict, slides_by_idx: dict, dumps: dict[int, str], glossary: str, refeed_images: bool):
    idxs = [i for i in group.get("source_slides", []) if i in slides_by_idx]
    head = (
        f"concept 主題:{group.get('title','')}(建議 type:{group.get('type','')})\n"
        f"共用 glossary:\n{glossary}\n\n這一組共 {len(idxs)} 張投影片:"
    )
    content = [{"type": "text", "text": head}]
    for i in idxs:
        content.append({"type": "text", "text": f"\n=== Slide {i} 榨出的文字 ===\n{dumps.get(i,'')}"})
        if refeed_images and slides_by_idx[i].image_png:
            content.append({"type": "image_url", "image_url": {"url": slides_by_idx[i].image_data_uri()}})
    return content


# ── 最後:cross-group merge ───────────────────────────────────────
MERGE_SYSTEM = """以下是同一份簡報產出的多個 OKF concept(只給標題與摘要)。
找出「明顯重複或應合併」的項目。只輸出一個 JSON 陣列,每元素是應合併的 index 群組:
[[0,3],[5,7,8]]  // 不需合併就回 []
只合併真的重疊的;不確定就別合併。"""


def merge_user(concepts: list[dict]) -> str:
    lines = []
    for i, c in enumerate(concepts):
        lines.append(f"[{i}] ({c.get('type','')}) {c.get('title','')} — {c.get('description','')}")
    return "\n".join(lines)
