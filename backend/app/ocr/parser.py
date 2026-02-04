import re
from app.ocr.engine import ocr
from app.ocr.utils import sort_key, find_idx, norm, box_y_stats

re_code = re.compile(r"^\d{2,5}$")
re_qty  = re.compile(r"^\d+(?:[.,]\d+)?$")
re_amt  = re.compile(r"^\d+(?:[.,]\d{2})$")


def parse_receipt(image_path: str, score_min: float = 0.6):
    res = ocr.ocr(image_path)
    r = res[0]

    items = []
    for text, score, box in zip(r["rec_texts"], r["rec_scores"], r["rec_polys"]):
        text = (text or "").strip()
        if not text or float(score) < score_min:
            continue
        items.append({"text": text, "score": float(score), "box": box})

    # cut above header
    header = [x for x in items if "код" in x["text"].lower()]
    if header:
        h = min(header, key=lambda x: box_y_stats(x["box"])[0])
        _, y_max, _ = box_y_stats(h["box"])
        items = [x for x in items if box_y_stats(x["box"])[2] > y_max + 5]

    items.sort(key=sort_key)
    texts = [x["text"] for x in items]

    end = find_idx(texts, "всего")
    if end is not None:
        texts = texts[:end]

    rows = []
    i = 0
    while i < len(texts):
        if re_code.match(texts[i]):
            code = int(texts[i])
            qty = amt = None
            j = i + 1
            while j < min(i + 12, len(texts)):
                t = norm(texts[j])
                if qty is None and re_qty.match(t):
                    qty = float(t)
                elif qty is not None and re_amt.match(t):
                    amt = float(t)
                    break
                j += 1
            if qty and amt:
                rows.append({"code": code, "qty": qty, "amount": amt})
                i = j + 1
                continue
        i += 1

    return rows
