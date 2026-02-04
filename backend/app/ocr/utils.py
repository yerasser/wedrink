def sort_key(it):
    xs = [p[0] for p in it["box"]]
    ys = [p[1] for p in it["box"]]
    return sum(ys) / 4.0, sum(xs) / 4.0


def find_idx(texts, needle):
    needle = needle.lower()
    for i, t in enumerate(texts):
        if needle in (t or "").lower():
            return i
    return None


def norm(s: str) -> str:
    return (s or "").replace(",", ".").strip()


def box_y_stats(box):
    ys = [p[1] for p in box]
    return min(ys), max(ys), sum(ys) / 4.0
