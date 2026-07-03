"""送 vision 前的確定性圖片前處理:裁邊 → 自適應切塊/縮圖 → 重編碼。

單一入口 normalize(raw) -> list[bytes]:一般頁回 1 張(必要時縮過),
密集頁回多塊(重疊防切字)。Pillow 延遲載入(圖片模式才需要)。
"""
from __future__ import annotations

import base64
import io
import math

from . import config


def data_uri(img: bytes) -> str:
    """依位元組魔數判 mime(配合 JPEG 退路)。"""
    mime = "image/jpeg" if img[:2] == b"\xff\xd8" else "image/png"
    return f"data:{mime};base64,{base64.b64encode(img).decode()}"


def _encode(im) -> bytes:
    """PNG 優先(文字銳利);超 MAX_IMAGE_BYTES 退 JPEG 逐級降質。"""
    im = im.convert("RGB")
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    data = buf.getvalue()
    if len(data) <= config.MAX_IMAGE_BYTES:
        return data
    for q in (90, 85, 80, 70, 60):
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=q)
        data = buf.getvalue()
        if len(data) <= config.MAX_IMAGE_BYTES:
            return data
    return data  # 已是最小,仍回傳


def _resize_to_max(im):
    w, h = im.size
    scale = config.MAX_IMAGE_PX / max(w, h)
    if scale < 1.0:
        im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))))
    return im


def _trim(im):
    """去四周均勻空白邊;近乎全白則不裁。"""
    from PIL import ImageChops

    rgb = im.convert("RGB")
    bg_color = rgb.getpixel((0, 0))
    from PIL import Image
    bg = Image.new("RGB", rgb.size, bg_color)
    bbox = ImageChops.difference(rgb, bg).getbbox()
    if not bbox:
        return im
    pad = 8
    l, t, r, b = bbox
    l, t = max(0, l - pad), max(0, t - pad)
    r, b = min(im.size[0], r + pad), min(im.size[1], b + pad)
    return im.crop((l, t, r, b))


def _tile(im) -> list:
    """重疊切塊:每塊長邊 ~MAX_IMAGE_PX;超 MAX_TILES 則放棄切塊(回 None,改縮圖)。"""
    w, h = im.size
    cols = math.ceil(w / config.MAX_IMAGE_PX)
    rows = math.ceil(h / config.MAX_IMAGE_PX)
    if cols * rows <= 1:
        return [im]
    if cols * rows > config.MAX_TILES:
        return None
    tw, th = math.ceil(w / cols), math.ceil(h / rows)
    ov_x, ov_y = int(tw * 0.05), int(th * 0.05)      # 5% 重疊防切字
    tiles = []
    for r in range(rows):
        for c in range(cols):
            l = max(0, c * tw - ov_x)
            t = max(0, r * th - ov_y)
            tiles.append(im.crop((l, t, min(w, l + tw + ov_x), min(h, t + th + ov_y))))
    return tiles


def normalize(raw: bytes) -> list[bytes]:
    """裁邊 → 密集頁切塊或一般縮圖 → 編碼。回傳 1..N 張圖的 bytes。"""
    from PIL import Image

    im = Image.open(io.BytesIO(raw))
    im.load()
    if config.TRIM_MARGINS:
        im = _trim(im)

    longest = max(im.size)
    parts = _tile(im) if longest > config.TILE_TRIGGER_PX else [im]
    if parts is None:                                # 塊太多 → 退回單張縮圖
        parts = [im]
    return [_encode(_resize_to_max(p)) for p in parts]
