"""集中設定,全部走環境變數,方便對接團隊的 self-host 端點。"""
import os

# K2.7 (OpenAI 相容端點,vLLM/SGLang 預設格式)
LLM_BASE_URL = os.environ.get("OKF_LLM_BASE_URL", "http://localhost:8000/v1")
LLM_API_KEY = os.environ.get("OKF_LLM_API_KEY", "EMPTY")   # 內網通常隨便填
LLM_MODEL = os.environ.get("OKF_LLM_MODEL", "kimi-k2.7")

# 內網自簽 CA:與你 SMDR2 的 SSL_VERIFY 慣例一致
SSL_VERIFY = os.environ.get("SSL_VERIFY", "true").lower() not in ("false", "0", "no")

# slide 渲染解析度(DPI)。內容多是截圖/圖形解釋圖 → 拉高讓小字可讀。
# 逐頁 densify(一頁一圖)不怕吃 context,可用 200~300。
RENDER_DPI = int(os.environ.get("OKF_RENDER_DPI", "220"))

# ── 圖片前處理(送 K2.7 前;K2.7 context 200k)──────────────────
MAX_IMAGE_PX = int(os.environ.get("OKF_MAX_IMAGE_PX", "1600"))       # 長邊上限(≈vision 實際用的解析度)
MAX_IMAGE_BYTES = int(os.environ.get("OKF_MAX_IMAGE_BYTES", "1500000"))  # 單圖位元組預算,超則退 JPEG
TILE_TRIGGER_PX = int(os.environ.get("OKF_TILE_TRIGGER_PX", "2600"))  # 長邊超此 → 密集頁切塊(不硬縮)
MAX_TILES = int(os.environ.get("OKF_MAX_TILES", "6"))                # 切塊上限,超過退回縮圖
TRIM_MARGINS = os.environ.get("OKF_TRIM_MARGINS", "true").lower() not in ("false", "0", "no")

# OCR 文字錨點(僅圖片模式;可插拔選配)。auto=有 Paddle 用 Paddle、否則 tesseract、否則略過
OCR = os.environ.get("OKF_OCR", "auto").lower()                      # auto | off | paddle | tesseract
OCR_LANG = os.environ.get("OKF_OCR_LANG", "")                        # 空=引擎預設(Paddle: ch;tesseract: chi_tra+eng)

# 平行度(vision 呼叫走 IO,ThreadPool 即可)
MAX_CONCURRENCY = int(os.environ.get("OKF_MAX_CONCURRENCY", "8"))

# 每個 concept 群最多幾張 slide(超過的群會被強制切開)
MAX_SLIDES_PER_GROUP = int(os.environ.get("OKF_MAX_SLIDES_PER_GROUP", "3"))

# synthesize 時是否把該群 slide 的圖「再餵一次」給模型。
#   True  = 忠實度最高(補回 densify 漏掉的視覺細節),較貴
#   False = 純文字 reduce,便宜但品質受 densify 上限卡死
SYNTH_REFEED_IMAGES = os.environ.get("OKF_SYNTH_REFEED_IMAGES", "true").lower() not in ("false", "0", "no")

# 產物根目錄
BUNDLE_ROOT = os.environ.get("OKF_BUNDLE_ROOT", "./bundle")

# ── RAG(Phase 1)──────────────────────────────────────────────
# embedding 端點(OpenAI 相容,self-host bge-m3 / Qwen3-Embedding)
EMBED_BASE_URL = os.environ.get("OKF_EMBED_BASE_URL", "http://localhost:8001/v1")
EMBED_API_KEY = os.environ.get("OKF_EMBED_API_KEY", "EMPTY")
EMBED_MODEL = os.environ.get("OKF_EMBED_MODEL", "bge-m3")
EMBED_BATCH = int(os.environ.get("OKF_EMBED_BATCH", "64"))

# 向量庫:Phase 1 用內建 sqlite 暴力 cosine(零 infra);規模上來換 Qdrant/pgvector
RAG_DB = os.environ.get("OKF_RAG_DB", "./rag.db")

# 疑似重複門檻:高(保守),寧漏報不誤報(把根因不同的相似缺陷併掉最糟)
DEDUP_THRESHOLD = float(os.environ.get("OKF_DEDUP_THRESHOLD", "0.92"))
