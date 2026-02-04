# app/bot/formatters.py
from __future__ import annotations
from typing import Iterable

def _fmt_num(x) -> str:
    try:
        v = float(x)
        if v.is_integer():
            return str(int(v))
        return f"{v:.2f}".rstrip("0").rstrip(".")
    except Exception:
        return str(x)

def _fmt_pct(x) -> str:
    try:
        v = float(x)
        return f"{v:.0f}%"
    except Exception:
        return str(x)

def _chunk(lines: list[str], limit: int = 35) -> list[str]:
    # Telegram message limit safety: split by lines
    out, cur = [], []
    for ln in lines:
        cur.append(ln)
        if len(cur) >= limit:
            out.append("\n".join(cur))
            cur = []
    if cur:
        out.append("\n".join(cur))
    return out

def format_processing(task_id: str) -> str:
    return (
        "🧾 Чек принят.\n"
        "⏳ Идёт распознавание…"
    )

def format_ocr_empty() -> str:
    return (
        "⚠️ Распознавание завершено, но позиции не найдены.\n"
        "Попробуй отправить фото чётче (без бликов, ближе, ровно)."
    )

def format_ocr_positions(result: list[dict]) -> str:
    # result: [{code, qty, amount}]
    lines = ["✅ Позиции распознаны:"]
    for r in result:
        lines.append(f"• {r.get('code')} × {_fmt_num(r.get('qty'))}")
    return "\n".join(lines)

def format_commit_success(receipt_id: int, commit: dict) -> str:
    # commit: {receipt_id, lines:[{ingredient_id, used, before, after, norm, is_low}]}
    low = []
    for ln in commit.get("lines", []) if isinstance(commit, dict) else []:
        if ln.get("is_low"):
            low.append(ln)

    msg = [f"✅ Списание выполнено. Чек #{receipt_id}"]

    return "\n".join(msg)

def format_api_error(user_text: str = "Ошибка. Попробуй ещё раз.") -> str:
    # Никаких dev деталей пользователю
    return f"❌ {user_text}"

def format_alerts(alerts: list[dict]) -> list[str]:
    """
    Возвращает СПИСОК сообщений (чтобы не упираться в лимиты телеграма).
    alerts item: {ingredient_name, current, start, spent_pct, status}
    status: "КОНТРОЛЬ"/"СРОЧНО" (как у тебя на бэке)
    """
    if not alerts:
        return ["✅ По складу всё нормально: нет позиций «КОНТРОЛЬ»/«СРОЧНО»."]

    urgent = []
    control = []
    for a in alerts:
        st = (a.get("status") or "").upper()
        if "СРОЧ" in st or "URG" in st:
            urgent.append(a)
        else:
            control.append(a)

    lines: list[str] = ["📦 Склад: предупреждения"]

    if urgent:
        lines.append("")
        lines.append("🔴 СРОЧНО:")
        for a in urgent:
            name = a.get("ingredient_name")
            cur = _fmt_num(a.get("current"))
            start = _fmt_num(a.get("start"))
            pct = _fmt_pct(a.get("spent_pct"))
            lines.append(f"• {name} — остаток {cur}/{start} (израсходовано {pct})")

    if control:
        lines.append("")
        lines.append("🟡 КОНТРОЛЬ:")
        for a in control:
            name = a.get("ingredient_name")
            cur = _fmt_num(a.get("current"))
            start = _fmt_num(a.get("start"))
            pct = _fmt_pct(a.get("spent_pct"))
            lines.append(f"• {name} — остаток {cur}/{start} (израсходовано {pct})")

    return _chunk(lines, limit=30)
