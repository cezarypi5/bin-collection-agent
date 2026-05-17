#!/usr/bin/env python3
"""Telegram responder for @GrobyBinbot.

Polls getUpdates, replies to commands, acknowledges via offset+1.
Stateless — Telegram's server-side queue tracks unread updates for ~24h.

Commands:
  /next        Next collection date + bins
  /week        Current week (A or B)
  /schedule    Next 4 collections
  /help|/start Command menu

Plain-text triggers: any message containing "bin", "next", "when".

Env: TELEGRAM_BOT_TOKEN
"""
import json
import os
import sys
import urllib.request
from datetime import date, timedelta

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    sys.exit("TELEGRAM_BOT_TOKEN env var required")

ANCHOR = date(2026, 4, 27)
PATTERNS = {
    "A": ["Black refuse bin", "Food waste caddy"],
    "B": ["Food waste caddy", "Brown garden bin", "Blue recycling bin"],
}
EMOJI = {
    "Black refuse bin": "⬛",
    "Food waste caddy": "🪣",
    "Brown garden bin": "🟤",
    "Blue recycling bin": "♻️",
}
MON_BANK_HOLIDAYS = {
    date(2026, 4, 6): "Easter Monday", date(2026, 5, 4): "Early May",
    date(2026, 5, 25): "Spring", date(2026, 8, 31): "Summer",
    date(2026, 12, 28): "Boxing Day (sub)",
    date(2027, 3, 29): "Easter Monday", date(2027, 5, 3): "Early May",
    date(2027, 5, 31): "Spring", date(2027, 8, 30): "Summer",
    date(2027, 12, 27): "Christmas (sub)", date(2028, 1, 3): "New Year (sub)",
}


def next_collection(offset=0):
    today = date.today()
    days_ahead = (7 - today.weekday()) % 7 or 7
    m = today + timedelta(days=days_ahead + 7 * offset)
    weeks = (m - ANCHOR).days // 7
    week = "A" if weeks % 2 == 0 else "B"
    if m in MON_BANK_HOLIDAYS:
        actual = m + timedelta(days=1)
        note = f"Deferred to Tue — {MON_BANK_HOLIDAYS[m]} bank holiday"
    else:
        actual = m
        note = None
    return {
        "date": actual.isoformat(),
        "human": actual.strftime("%a %-d %b %Y"),
        "week": week,
        "bins": PATTERNS[week],
        "note": note,
    }


def tg(method, **params):
    data = json.dumps(params).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/{method}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())


def send(chat_id, text):
    tg("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML")


def handle(text, chat_id):
    text = text.strip().lower()
    if text.startswith("/next") or text.startswith("/n ") or text == "/n":
        c = next_collection()
        bins = "\n".join(f"{EMOJI[b]} {b}" for b in c["bins"])
        msg = f"<b>Next collection: {c['human']} (Week {c['week']})</b>\n\n{bins}"
        if c["note"]:
            msg += f"\n\n⚠️ {c['note']}"
        msg += "\n\n📍 207 Markfield Rd, Groby LE6 0FT"
        send(chat_id, msg)
        return True

    if text.startswith("/week") or text.startswith("/w"):
        c = next_collection()
        send(chat_id, f"This week's bin: <b>Week {c['week']}</b>\nNext put-out: {c['human']}")
        return True

    if text.startswith("/schedule") or text.startswith("/s"):
        lines = ["<b>Next 4 collections:</b>"]
        for i in range(4):
            c = next_collection(offset=i)
            short = ", ".join(b.replace(" bin", "").replace(" caddy", "") for b in c["bins"])
            note = f" ⚠️ {c['note']}" if c["note"] else ""
            lines.append(f"• {c['human']} (W{c['week']}): {short}{note}")
        send(chat_id, "\n".join(lines))
        return True

    if text.startswith("/help") or text.startswith("/start") or text.startswith("/h"):
        send(
            chat_id,
            "<b>🗑️ Groby Bin Reminder Bot</b>\n\n"
            "Commands:\n"
            "/next — next collection date + bins\n"
            "/week — current week (A or B)\n"
            "/schedule — next 4 collections\n"
            "/help — this menu\n\n"
            "Auto-reminders: Sundays 19:30 + 21:00 BST.",
        )
        return True

    # Natural language fallback
    if any(kw in text for kw in ("bin", "next", "when", "tomorrow", "monday")):
        c = next_collection()
        bins = "\n".join(f"{EMOJI[b]} {b}" for b in c["bins"])
        msg = f"<b>Next collection: {c['human']} (Week {c['week']})</b>\n\n{bins}"
        if c["note"]:
            msg += f"\n\n⚠️ {c['note']}"
        send(chat_id, msg)
        return True

    return False


def main():
    # Drain the queue
    resp = json.loads(
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates?timeout=0", timeout=15
        ).read()
    )
    if not resp.get("ok"):
        print(f"getUpdates error: {resp}", file=sys.stderr)
        sys.exit(1)

    updates = resp.get("result", [])
    if not updates:
        print("No new messages.")
        return

    max_uid = 0
    handled = 0
    for u in updates:
        max_uid = max(max_uid, u["update_id"])
        m = u.get("message", {})
        text = m.get("text", "")
        chat_id = m.get("chat", {}).get("id")
        if not chat_id or not text:
            continue
        from_name = m.get("from", {}).get("first_name", "?")
        print(f"  {from_name}@{chat_id}: {text!r}")
        if handle(text, chat_id):
            handled += 1
        else:
            send(chat_id, "Unknown command. Try /help.")

    # Ack — pass offset = max+1 to drop these from the queue
    if max_uid:
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={max_uid+1}&timeout=0",
            timeout=10,
        ).read()
    print(f"Handled {handled}/{len(updates)} messages, acked up to update_id {max_uid}")


if __name__ == "__main__":
    main()
