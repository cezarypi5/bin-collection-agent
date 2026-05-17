#!/usr/bin/env python3
"""Orchestrator — computes schedule, renders image, fires all 5 destinations."""
import asyncio
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

# --- 1. Compute next collection ---
ANCHOR = date(2026, 4, 27)
PATTERNS = {
    "A": ["Black refuse bin", "Food waste caddy"],
    "B": ["Food waste caddy", "Brown garden bin", "Blue recycling bin"],
}
MON_BANK_HOLIDAYS = {
    date(2026, 4, 6): "Easter Monday", date(2026, 5, 4): "Early May",
    date(2026, 5, 25): "Spring",       date(2026, 8, 31): "Summer",
    date(2026, 12, 28): "Boxing Day (sub)",
    date(2027, 3, 29): "Easter Monday", date(2027, 5, 3): "Early May",
    date(2027, 5, 31): "Spring",       date(2027, 8, 30): "Summer",
    date(2027, 12, 27): "Christmas (sub)", date(2028, 1, 3): "New Year (sub)",
}

def next_collection(today=None):
    today = today or date.today()
    days_ahead = (7 - today.weekday()) % 7 or 7
    m = today + timedelta(days=days_ahead)
    weeks = (m - ANCHOR).days // 7
    week = "A" if weeks % 2 == 0 else "B"
    if m in MON_BANK_HOLIDAYS:
        actual, note = m + timedelta(days=1), f"Deferred to Tuesday — {MON_BANK_HOLIDAYS[m]} bank holiday"
    else:
        actual, note = m, None
    return {
        "collection_date": actual.isoformat(),
        "day_of_week": actual.strftime("%A"),
        "week": week,
        "bins": PATTERNS[week],
        "note": note,
        "human_date": actual.strftime("%a %-d %b %Y"),
    }

# --- 2. Render HTML + PNG ---
HTML_TEMPLATE = """<html><body style="margin:0;font-family:'Segoe UI',Arial,sans-serif">
<div style="max-width:560px;margin:24px auto;border-radius:16px;overflow:hidden;background:#fff;box-shadow:0 4px 24px rgba(0,0,0,.1);border:1px solid #e0e0e0">
  <div style="background:linear-gradient(135deg,#2e7d32,#4caf50);color:#fff;padding:24px 28px">
    <div style="font-size:13px;opacity:.85;letter-spacing:1px;text-transform:uppercase">Bin Collection Reminder</div>
    <div style="font-size:30px;font-weight:700;margin-top:6px">{human_date}</div>
    <div style="font-size:14px;opacity:.9;margin-top:8px">207 Markfield Road, Groby · Week {week}</div>
  </div>
  <div style="padding:24px 28px">
    <div style="font-size:13px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px">Put out tonight (by 07:00)</div>
    <div style="font-size:18px;color:#222;line-height:1.6">{bins_html}</div>
    {note_block}
  </div>
  <div style="background:#fafafa;padding:14px 28px;font-size:12px;color:#888;border-top:1px solid #eee">Hinckley & Bosworth · bin-reminder-bot v2.0</div>
</div></body></html>"""

EMOJI = {
    "Black refuse bin": "⬛",
    "Food waste caddy": "🪣",
    "Brown garden bin": "🟤",
    "Blue recycling bin": "♻️",
}

def render(info, html_path, png_path):
    bins_html = "<br>".join(f"{EMOJI.get(b,'•')} {b}" for b in info["bins"])
    note_block = (
        f'<div style="margin-top:14px;padding:10px 14px;background:#fff8e1;border-left:4px solid #ffa000;color:#7c5e00;font-size:14px">⚠️ {info["note"]}</div>'
        if info["note"] else ""
    )
    html = HTML_TEMPLATE.format(human_date=info["human_date"], week=info["week"], bins_html=bins_html, note_block=note_block)
    Path(html_path).write_text(html)

    async def shot():
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            b = await p.chromium.launch()
            page = await b.new_page(viewport={"width": 620, "height": 480})
            await page.goto(f"file://{html_path}")
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=png_path, full_page=True)
            await b.close()
    asyncio.run(shot())

# --- 3. Delivery ---
import requests
import smtplib, ssl
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def env(name, required=True):
    v = os.environ.get(name, "")
    if required and not v:
        raise SystemExit(f"Missing env var: {name}")
    return v

def send_telegram(info, png_path):
    token = env("TELEGRAM_BOT_TOKEN")
    chat = env("TELEGRAM_CHAT_ID")
    caption = f"🗑️ Bin reminder — {info['human_date']} (Week {info['week']})"
    if info["note"]:
        caption += f"\n⚠️ {info['note']}"
    with open(png_path, "rb") as f:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={"chat_id": chat, "caption": caption},
            files={"photo": f},
            timeout=30,
        )
    r.raise_for_status()
    body = r.json()
    if not body.get("ok"):
        raise RuntimeError(f"Telegram error: {body}")
    return "OK"

def send_emails(info, html_path, png_path):
    sender = env("GMAIL_SENDER")
    pw = env("GMAIL_APP_PASSWORD")
    recipients = [env("EMAIL_CEZARY"), env("EMAIL_SUNIA")]
    html = Path(html_path).read_text()
    img_data = Path(png_path).read_bytes()
    results = {}
    for to in recipients:
        msg = MIMEMultipart("related")
        msg["From"] = f"Bin Reminder Bot <{sender}>"
        msg["To"] = to
        msg["Subject"] = f"🗑️ Bin reminder — {info['human_date']} (Week {info['week']})"
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(f"Bin collection: {info['human_date']} (Week {info['week']}).", "plain"))
        alt.attach(MIMEText(html, "html"))
        msg.attach(alt)
        img = MIMEImage(img_data)
        img.add_header("Content-ID", "<bin_reminder>")
        img.add_header("Content-Disposition", "inline", filename="bin_reminder.png")
        msg.attach(img)
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=30) as s:
                s.login(sender, pw)
                s.sendmail(sender, [to], msg.as_string())
            results[to] = "OK"
        except Exception as e:
            results[to] = f"FAIL: {e}"
    return results

def send_whatsapp(info, png_path):
    instance = env("GREEN_API_INSTANCE", required=False)
    token = env("GREEN_API_TOKEN", required=False)
    url = env("GREEN_API_URL", required=False)
    if not (instance and token and url):
        return {"_skipped": "Green API env vars not set"}

    # Note: getStateInstance lies — returns notAuthorized even when sending works.
    # Trust the actual send response instead. We do a fast log of state for debugging.
    try:
        state = requests.get(f"{url}/waInstance{instance}/getStateInstance/{token}", timeout=15).json()
        print(f"Green API state (informational only): {state}")
    except Exception:
        pass

    recipients = [env("WHATSAPP_CHATID_CEZARY", required=False), env("WHATSAPP_CHATID_SUNIA", required=False)]
    recipients = [r for r in recipients if r and "XXXXXXXXX" not in r]
    if not recipients:
        return {"_skipped": "No WhatsApp recipients configured"}

    caption = f"🗑️ Bin reminder — {info['human_date']} (Week {info['week']})\n"
    caption += "\n".join(f"• {b}" for b in info["bins"])
    if info["note"]:
        caption += f"\n\n⚠️ {info['note']}"
    caption += "\n📍 207 Markfield Rd, Groby LE6 0FT"

    results = {}
    with open(png_path, "rb") as fh:
        png_bytes = fh.read()
    for chatId in recipients:
        try:
            with open(png_path, "rb") as fh:
                r = requests.post(
                    f"{url}/waInstance{instance}/sendFileByUpload/{token}",
                    data={"chatId": chatId, "caption": caption},
                    files={"file": ("bin_reminder.png", fh, "image/png")},
                    timeout=30,
                )
            r.raise_for_status()
            results[chatId] = "OK"
        except Exception as e:
            results[chatId] = f"FAIL: {e}"
    return results

# --- 4. Main ---
def main():
    info = next_collection()
    print(f"Next collection: {json.dumps(info, indent=2)}")

    html_path = "/tmp/bin_reminder.html"
    png_path = "/tmp/bin_reminder.png"
    render(info, html_path, png_path)
    print(f"Rendered PNG ({os.path.getsize(png_path)} bytes)")

    results = {}
    try:
        results["telegram"] = send_telegram(info, png_path)
    except Exception as e:
        results["telegram"] = f"FAIL: {e}"
    results["email"] = send_emails(info, html_path, png_path)
    results["whatsapp"] = send_whatsapp(info, png_path)

    print("\n=== Results ===")
    print(json.dumps(results, indent=2))

    # Telegram canary: if anything failed, ping Cezary on Telegram
    failed = []
    if isinstance(results["telegram"], str) and results["telegram"].startswith("FAIL"):
        failed.append(f"Telegram: {results['telegram']}")
    for k, v in results["email"].items():
        if v != "OK":
            failed.append(f"Email→{k}: {v}")
    if isinstance(results["whatsapp"], dict):
        for k, v in results["whatsapp"].items():
            if v != "OK" and not k.startswith("_"):
                failed.append(f"WhatsApp→{k}: {v}")
            elif k.startswith("_"):
                failed.append(f"WhatsApp {k}: {v}")

    if failed:
        try:
            token = env("TELEGRAM_BOT_TOKEN")
            chat = env("TELEGRAM_CHAT_ID")
            msg = "⚠️ Bin reminder run had failures:\n\n" + "\n".join(failed)
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat, "text": msg},
                timeout=15,
            )
        except Exception:
            pass
        # Don't fail the GH Action — most deliveries succeeded
        # but exit 0 so the artifact still uploads
    print("\nDone.")

if __name__ == "__main__":
    main()
