#!/usr/bin/env python3
"""Orchestrator — computes schedule, renders image, fires all 5 destinations."""
import argparse
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

HTML_TEMPLATE_CYBERPUNK = """<html><head>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#05050a;font-family:'Share Tech Mono',monospace;color:#e8e8f0;padding:0;margin:0}
  .card{position:relative;max-width:560px;margin:24px auto;background:#0a0a14;border:1px solid #ff2079;box-shadow:0 0 32px rgba(255,32,121,.4),inset 0 0 24px rgba(0,255,255,.06);clip-path:polygon(0 0,100% 0,100% calc(100% - 18px),calc(100% - 18px) 100%,0 100%);overflow:hidden}
  .scanlines{position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(255,255,255,.03) 0,rgba(255,255,255,.03) 1px,transparent 1px,transparent 3px)}
  .hero{padding:22px 26px 24px;background:linear-gradient(180deg,#0a0a14 0%,#16001a 100%);border-bottom:1px solid #ff2079}
  .alert{display:inline-block;padding:4px 10px;background:#ff2079;color:#0a0a14;font-family:'Orbitron',sans-serif;font-weight:900;font-size:11px;letter-spacing:3px;text-transform:uppercase;margin-bottom:14px}
  .title{font-family:'Orbitron',sans-serif;font-weight:900;font-size:34px;color:#00ffff;text-shadow:0 0 12px rgba(0,255,255,.6),0 0 24px rgba(0,255,255,.3);letter-spacing:1px;line-height:1.05}
  .glitch{color:#ff2079;text-shadow:0 0 12px rgba(255,32,121,.6)}
  .meta{margin-top:14px;font-family:'Share Tech Mono',monospace;color:#9d9dae;font-size:13px;letter-spacing:1px}
  .meta span{color:#39ff14}
  .body{padding:24px 26px 20px}
  .heading{font-family:'Orbitron',sans-serif;font-size:12px;font-weight:700;color:#ff2079;letter-spacing:4px;text-transform:uppercase;margin-bottom:12px;border-left:3px solid #ff2079;padding-left:10px}
  .bins{display:flex;flex-direction:column;gap:10px;margin-bottom:18px}
  .bin{display:flex;align-items:center;gap:14px;padding:10px 12px;background:rgba(0,255,255,.05);border-left:2px solid #00ffff;font-size:17px;font-family:'Share Tech Mono',monospace;color:#e8e8f0;letter-spacing:1px}
  .bin .icon{font-size:22px}
  .deadline{margin-top:6px;padding:14px;background:rgba(255,32,121,.08);border:1px dashed #ff2079;text-align:center;font-family:'Orbitron',sans-serif;font-weight:700;font-size:15px;color:#ff2079;letter-spacing:2px;text-transform:uppercase}
  .deadline .countdown{display:block;color:#39ff14;font-size:22px;margin-top:4px;text-shadow:0 0 8px rgba(57,255,20,.5)}
  .note{margin-top:12px;padding:10px 14px;background:rgba(255,178,0,.08);border-left:3px solid #ffb200;color:#ffb200;font-size:13px}
  .foot{padding:10px 26px;background:#05050a;border-top:1px solid #1a1a2e;font-family:'Share Tech Mono',monospace;font-size:11px;color:#4a4a5a;letter-spacing:1px;display:flex;justify-content:space-between}
  .foot .ver{color:#ff2079}
</style></head>
<body><div class="card"><div class="scanlines"></div>
  <div class="hero">
    <div class="alert">⚡ FINAL CALL</div>
    <div class="title">PUT BINS<br><span class="glitch">// OUT NOW</span></div>
    <div class="meta">> COLLECTION: <span>__HUMAN_DATE__</span> · WEEK_<span>__WEEK__</span></div>
  </div>
  <div class="body">
    <div class="heading">// Payload manifest</div>
    <div class="bins">__BINS_HTML__</div>
    <div class="deadline">
      Deploy before
      <span class="countdown">07:00 ⟶ MON</span>
    </div>
    __NOTE_BLOCK__
  </div>
  <div class="foot"><span>207 MARKFIELD RD · LE6 0FT</span><span class="ver">v2.5_cyberpunk</span></div>
</div></body></html>"""

EMOJI = {
    "Black refuse bin": "⬛",
    "Food waste caddy": "🪣",
    "Brown garden bin": "🟤",
    "Blue recycling bin": "♻️",
}

def render(info, html_path, png_path, style="standard"):
    if style == "cyberpunk":
        bins_html = "".join(f'<div class="bin"><span class="icon">{EMOJI.get(b,"•")}</span>{b.upper()}</div>' for b in info["bins"])
        note_block = (
            f'<div class="note">⚠ {info["note"]}</div>' if info["note"] else ""
        )
        html = (HTML_TEMPLATE_CYBERPUNK
                .replace("__HUMAN_DATE__", info["human_date"].upper())
                .replace("__WEEK__", info["week"])
                .replace("__BINS_HTML__", bins_html)
                .replace("__NOTE_BLOCK__", note_block))
    else:
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

def send_telegram(info, png_path, style="standard"):
    token = env("TELEGRAM_BOT_TOKEN")
    chat = env("TELEGRAM_CHAT_ID")
    if style == "cyberpunk":
        caption = f"⚡ FINAL CALL // PUT BINS OUT NOW\nCollection: {info['human_date']} (Week {info['week']})\nDeploy before 07:00 MON"
    else:
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

def send_emails(info, html_path, png_path, style="standard"):
    sender = env("GMAIL_SENDER")
    pw = env("GMAIL_APP_PASSWORD")
    recipients = [env("EMAIL_CEZARY"), env("EMAIL_SUNIA")]
    html = Path(html_path).read_text()
    img_data = Path(png_path).read_bytes()
    results = {}
    if style == "cyberpunk":
        subject = f"⚡ FINAL CALL — PUT BINS OUT NOW ({info['human_date']})"
    else:
        subject = f"🗑️ Bin reminder — {info['human_date']} (Week {info['week']})"
    for to in recipients:
        msg = MIMEMultipart("related")
        msg["From"] = f"Bin Reminder Bot <{sender}>"
        msg["To"] = to
        msg["Subject"] = subject
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


# --- 4. Main ---
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=["standard","cyberpunk"], default="standard")
    args = ap.parse_args()
    style = args.style
    print(f"Style: {style}")

    info = next_collection()
    print(f"Next collection: {json.dumps(info, indent=2)}")

    html_path = "/tmp/bin_reminder.html"
    png_path = "/tmp/bin_reminder.png"
    render(info, html_path, png_path, style=style)
    print(f"Rendered PNG ({os.path.getsize(png_path)} bytes)")

    results = {}
    try:
        results["telegram"] = send_telegram(info, png_path, style=style)
    except Exception as e:
        results["telegram"] = f"FAIL: {e}"
    results["email"] = send_emails(info, html_path, png_path, style=style)

    print("\n=== Results ===")
    print(json.dumps(results, indent=2))

    # Telegram canary: if anything failed, ping Cezary on Telegram
    failed = []
    if isinstance(results["telegram"], str) and results["telegram"].startswith("FAIL"):
        failed.append(f"Telegram: {results['telegram']}")
    for k, v in results["email"].items():
        if v != "OK":
            failed.append(f"Email→{k}: {v}")

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
