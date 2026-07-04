"""可插拔 OCR(僅圖片模式當文字錨點):PaddleOCR → tesseract → 空字串。

中英混 + 技術版面建議 PaddleOCR(tesseract CJK 弱)。皆未安裝時靜默略過,
不使流程失敗。引擎只初始化一次。
"""
from __future__ import annotations

import io

from . import config

_engine = None          # "paddle" | "tesseract" | "none"
_paddle = None


def _pick_engine() -> str:
    global _engine, _paddle
    if _engine is not None:
        return _engine
    if config.OCR == "off":
        _engine = "none"
        return _engine

    want = config.OCR                                    # auto | paddle | tesseract
    if want in ("auto", "paddle"):
        try:
            from paddleocr import PaddleOCR                # PaddleOCR 3.x API
            _paddle = PaddleOCR(use_textline_orientation=True, lang=config.OCR_LANG or "ch")
            _engine = "paddle"
            return _engine
        except Exception:
            if want == "paddle":
                _engine = "none"
                return _engine
    if want in ("auto", "tesseract"):
        try:
            import pytesseract  # noqa: F401
            _engine = "tesseract"
            return _engine
        except Exception:
            pass
    _engine = "none"
    return _engine


def ocr_image(raw: bytes) -> str:
    """回傳圖片中的文字;無可用引擎則回空字串。"""
    eng = _pick_engine()
    try:
        if eng == "paddle":
            import numpy as np
            from PIL import Image
            arr = np.array(Image.open(io.BytesIO(raw)).convert("RGB"))
            lines = []
            for page in _paddle.predict(arr) or []:          # 3.x:predict → rec_texts
                for txt in (page.get("rec_texts") or []):
                    if txt:
                        lines.append(txt)
            return "\n".join(lines)
        if eng == "tesseract":
            import pytesseract
            from PIL import Image
            lang = config.OCR_LANG or "chi_tra+eng"
            return pytesseract.image_to_string(Image.open(io.BytesIO(raw)), lang=lang).strip()
    except Exception:
        return ""                                        # OCR 失敗不致命
    return ""
