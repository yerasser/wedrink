import io
import re
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np
from PIL import Image
from celery.utils.log import get_task_logger
from rapidocr import RapidOCR

_OCR = RapidOCR()

INT_RE = re.compile(r"^\d+$")
FLT_RE = re.compile(r"^\d+[.,]\d+$")

SKIP_TOKENS = {
    "kod", "koa",
    "kon-bo", "kol-vo", "k0l-vo", "k0n-bo",
    "cymma", "cyumma",
    "bcero:", "всего:",
}

def _norm_token(s: str) -> str:
    s = str(s).strip().replace("\u00a0", " ").strip()
    return s.replace(",", ".")

def _is_date(tok: str) -> bool:
    return bool(re.match(r"^\d{2}\.\d{2}\.\d{4}", tok))

def _skip(tok: str) -> bool:
    t = tok.strip()
    tl = t.lower()
    if not t:
        return True
    if tl in SKIP_TOKENS:
        return True
    if tl.startswith(("kaccob", "kassov", "кассов", "cmeha", "смена", "итого", "bcero")):
        return True
    if _is_date(t):
        return True
    return False

def tokens_to_items(tokens: Iterable[str]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    t = [_norm_token(x) for x in tokens if _norm_token(x)]

    i = 0
    while i < len(t):
        tok = t[i]
        if _skip(tok):
            i += 1
            continue

        if not INT_RE.match(tok):
            i += 1
            continue

        code = tok
        i += 1

        while i < len(t) and not FLT_RE.match(t[i]):
            if INT_RE.match(t[i]):
                code = None
                break
            i += 1

        if code is None or i >= len(t) or not FLT_RE.match(t[i]):
            continue

        qty = t[i]
        i += 1

        # next float = amount
        if i >= len(t) or not FLT_RE.match(t[i]):
            continue

        amount = t[i]
        i += 1

        if code and qty and amount:
            total = float(qty) * float(amount)
            items.append({"product_code_raw": code, "qty": float(qty), "unit_price": float(amount), "line_total": total})

    return items

def _rapidocr_tokens_from_bytes(image_bytes: bytes) -> tuple[str, tuple[str] | None]:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    arr = np.array(img)

    out = _OCR(arr)
    logger = get_task_logger(__name__)
    logger.info(out.txts)

    tokens = out.txts

    raw_text = "\n".join(tokens)

    return raw_text, tokens

def run_ocr_and_parse(image_bytes: bytes) -> tuple[str, list[dict]]:
    raw_text, tokens = _rapidocr_tokens_from_bytes(image_bytes)
    items = tokens_to_items(tokens)

    return raw_text, items
