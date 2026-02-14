from math import ceil

PAGE_SIZE = 20
RECEIPTS_PAGE_SIZE = 10
INV_PAGE_SIZE = 15


# ── helpers ──────────────────────────────────────────────────────────────────

def total_pages(n: int, page_size: int = PAGE_SIZE) -> int:
    return max(1, ceil(n / page_size))


def clamp_page(page: int, pages: int) -> int:
    return max(0, min(page, pages - 1))


def short(text: str | None, max_len: int) -> str:
    text = text or ""
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


# ── receipt ───────────────────────────────────────────────────────────────────

def fmt_receipt_page(
    receipt: dict, items: list[dict], page: int
) -> tuple[str, int, int]:
    rid = receipt["id"]
    status = receipt.get("status", "—")
    pages = total_pages(len(items))
    page = clamp_page(page, pages)
    start, end = page * PAGE_SIZE, (page + 1) * PAGE_SIZE

    lines = [
        f"🧾 Чек #{rid}",
        f"Статус: {status}",
        "",
        "№ | Код | Qty | Цена | Сумма",
        "--+-----+-----+-------+-------",
    ]
    for i, it in enumerate(items[start:end], start=start + 1):
        code = short(it.get("product_code_raw"), 21)
        if not it.get("product_id"):
            code = f"⚠ {code}"
        lines.append(
            f"{i:<2}| {code:<4}| {it.get('qty', ''):<4}| {it.get('unit_price', ''):<6}| {it.get('line_total', '')}"
        )

    lines += ["", f"Стр. {page+1}/{pages} (всего: {len(items)})"]
    return "\n".join(lines), page, pages


def fmt_receipts_list(
    receipts: list[dict], page: int
) -> tuple[str, int, int, list[dict]]:
    pages = total_pages(len(receipts), RECEIPTS_PAGE_SIZE)
    page = clamp_page(page, pages)
    start = page * RECEIPTS_PAGE_SIZE
    chunk = receipts[start : start + RECEIPTS_PAGE_SIZE]

    lines = ["🧾 Чеки", ""]
    if not receipts:
        lines.append("Пока нет чеков.")
        return "\n".join(lines), page, pages, chunk

    for r in chunk:
        created = r.get("created_at", "")
        if isinstance(created, str) and len(created) >= 19:
            created = created[:19].replace("T", " ")
        lines.append(f"#{r.get('id')} | {r.get('status', '—')} | {created}")

    lines += ["", f"Стр. {page+1}/{pages} (всего: {len(receipts)})"]
    return "\n".join(lines), page, pages, chunk


# ── inventory ─────────────────────────────────────────────────────────────────

def fmt_inventory_list(
    rows: list[dict], page: int
) -> tuple[str, int, int, list[dict]]:
    pages = total_pages(len(rows), INV_PAGE_SIZE)
    page = clamp_page(page, pages)
    start = page * INV_PAGE_SIZE
    chunk = rows[start : start + INV_PAGE_SIZE]

    lines = [
        "📦 Остатки", "",
        "Ингредиент              | Остаток | MIN",
        "------------------------+---------+-----",
    ]
    for r in chunk:
        icon = {"КОНТРОЛЬ": "🟡 ", "СРОЧНО": "🔴 "}.get(r["label"], "")
        name = short(r["name"], 22)
        lines.append(f"{icon}{name:<22} | {r['on_hand_qty']:<7} | {r['min_qty']}")

    lines += ["", f"Стр. {page+1}/{pages}"]
    return "\n".join(lines), page, pages, chunk


def fmt_inventory_detail(row: dict) -> str:
    lines = [
        "📦 Ингредиент", "",
        f"ID: {row.get('ingredient_id') or row.get('id')}",
        f"Название: {row.get('ingredient_name') or row.get('name') or '—'}",
        f"Остаток: {row.get('on_hand_qty', '—')}",
        f"MIN: {row.get('min_qty', '—')}",
        f"Цена закупки: {row.get('purchase_price', '—')}",
        f"Кол-во в упаковке: {row.get('purchase_pack_qty', '—')}",
    ]
    return "\n".join(lines)


# ── consumption ───────────────────────────────────────────────────────────────

def fmt_consumption(
    rows: list[dict],
    id_to_name: dict[int, str],
    header: str,
) -> str:
    def _qty(r):
        try:
            return float(r.get("qty", 0))
        except Exception:
            return 0.0

    rows = sorted(rows, key=_qty, reverse=True)

    lines = [header, "", "Ингредиент              | Qty", "------------------------+--------"]
    for r in rows[:30]:
        iid = r.get("ingredient_id")
        name = (id_to_name.get(int(iid), f"#{iid}") if iid is not None else "—")[:22]
        lines.append(f"{name:<22} | {r.get('consumed_qty', '')}")

    return "\n".join(lines)


# ── purchase plan ─────────────────────────────────────────────────────────────

def fmt_purchase_plan(items: list[dict], total_cost: float) -> str:
    if not items:
        return "✅ Всё в норме — закупка не нужна."

    lines = [
        "🛒 План закупки",
        "",
        f"{'Ингредиент'} | {'Упак'} | {'×'} | {'Цена'} | {'Итого'} | {'Станет'}",
        f"{'-'*30}",
    ]

    for it in items:
        name  = short(it["name"], 22)
        packs = it["packs_needed"]
        pprice = f"{it['pack_price']:,.0f}"
        cost  = f"{it['cost']:,.0f}"
        after = it["after"]
        lines.append(
            f"{name:<22} | {packs:>4} | × | {pprice:>7} | {cost:>8} | {after:>7}"
        )

    lines += [
        "",
        f"{'ИТОГО':>12}.   {'':>4}   {'':>1}   {'':>7}   {total_cost:>8,.0f}",
    ]
    return "\n".join(lines)