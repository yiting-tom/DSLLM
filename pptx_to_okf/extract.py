"""① PPTX 拆解:抽文字/表格/講者備註 + 每張 slide 轉成圖(給 vision 用)。"""
from __future__ import annotations

import base64
import io
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from pptx import Presentation
from pdf2image import convert_from_path

from . import config


@dataclass
class Slide:
    index: int                    # 1-based
    title: str = ""
    text: str = ""                # shape 內所有文字(含條列)
    tables: list[list[list[str]]] = field(default_factory=list)
    notes: str = ""               # 講者備註
    image_png: bytes = b""        # 整張 slide 的渲染圖

    def image_data_uri(self) -> str:
        b64 = base64.b64encode(self.image_png).decode()
        return f"data:image/png;base64,{b64}"


@dataclass
class Deck:
    path: Path
    slides: list[Slide]


def _shape_text(shape) -> str:
    if not shape.has_text_frame:
        return ""
    return "\n".join(p.text for p in shape.text_frame.paragraphs if p.text).strip()


def _table(shape) -> list[list[str]] | None:
    if not shape.has_table:
        return None
    tbl = shape.table
    return [[cell.text.strip() for cell in row.cells] for row in tbl.rows]


def _render_slides_to_png(pptx_path: Path) -> list[bytes]:
    """soffice: pptx -> pdf -> 每頁 PNG。頁序對應 slide 序。"""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("找不到 soffice/libreoffice,請先安裝 LibreOffice。")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, str(pptx_path)],
            check=True, capture_output=True, timeout=600,
        )
        pdf = next(Path(tmp).glob("*.pdf"))
        images = convert_from_path(str(pdf), dpi=config.RENDER_DPI)
        out = []
        for img in images:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            out.append(buf.getvalue())
        return out


def extract(pptx_path: str | Path) -> Deck:
    pptx_path = Path(pptx_path)
    prs = Presentation(str(pptx_path))
    pngs = _render_slides_to_png(pptx_path)

    slides: list[Slide] = []
    for i, slide in enumerate(prs.slides, start=1):
        texts, tables, title = [], [], ""
        for shape in slide.shapes:
            if shape == slide.shapes.title:
                title = _shape_text(shape)
                continue
            t = _shape_text(shape)
            if t:
                texts.append(t)
            tbl = _table(shape)
            if tbl:
                tables.append(tbl)
        notes = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes = slide.notes_slide.notes_text_frame.text.strip()
        slides.append(Slide(
            index=i, title=title, text="\n".join(texts), tables=tables, notes=notes,
            image_png=pngs[i - 1] if i - 1 < len(pngs) else b"",
        ))
    return Deck(path=pptx_path, slides=slides)
