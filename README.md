# 🗑️ Bin Collection Reminder — v2.4

Automated weekly bin collection reminder for **207 Markfield Road, Groby, Leicester LE6 0FT**.

Runs as a **GitHub Actions workflow** every Sunday at 19:30 Europe/London. Sends to:

| Channel | Recipients | Mechanism |
|---|---|---|
| 📱 Telegram | Cezary | `api.telegram.org/sendPhoto` |
| 📧 Email | Cezary + Sunia | Gmail SMTP via App Password |

WhatsApp delivery was attempted via Green API but Meta has blocked all free third-party multi-device APIs as of 2026 — sends returned fake `idMessage` OK responses while messages were silently dropped. Sunia receives the reminder via email (same content, same image inline). Cezary receives Telegram + email.

If any delivery fails, the workflow Telegram-pings Cezary with the error (canary channel).

## Architecture

```
.github/workflows/sunday-reminder.yml   ← cron 30 18,19 * * 0  UTC (covers BST + GMT)
└── scripts/run_reminder.py             ← orchestrator (Python, single file)
    ├── compute next collection         ← anchor 2026-04-27 + Mon bank-holiday shifts through Jan 2028
    ├── render PNG                      ← playwright headless chromium
    ├── send_telegram()                 ← multipart/form-data sendPhoto
    └── send_emails()                   ← smtplib SMTP_SSL on smtp.gmail.com:465 — loops over Cezary + Sunia
```

## Local dev / manual test

```bash
pip install playwright requests
python -m playwright install --with-deps chromium

export TELEGRAM_BOT_TOKEN="…"
export TELEGRAM_CHAT_ID="…"
export GMAIL_SENDER="c.makulec@gmail.com"
export GMAIL_APP_PASSWORD="…"
export EMAIL_CEZARY="c.makulec@gmail.com"
export EMAIL_SUNIA="mantra.agni@gmail.com"

python scripts/run_reminder.py
```

## Required GitHub Actions secrets (6 total)

| Secret | Value | Where to get |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | `8791…:AA…` | BotFather — `/mybots` → token |
| `TELEGRAM_CHAT_ID` | numeric chat ID | `getUpdates` after messaging the bot |
| `GMAIL_SENDER` | `c.makulec@gmail.com` | own Gmail address |
| `GMAIL_APP_PASSWORD` | 16-char code | https://myaccount.google.com/apppasswords |
| `EMAIL_CEZARY` | `c.makulec@gmail.com` | |
| `EMAIL_SUNIA` | `mantra.agni@gmail.com` | |

Set them at https://github.com/cezarypi5/bin-collection-agent/settings/secrets/actions

## Bin schedule

Inline in `scripts/run_reminder.py`:
- Anchor: **Monday 27 Apr 2026 = Week A**
- **Week A:** ⬛ Black refuse bin + 🪣 Food waste caddy
- **Week B:** 🪣 Food waste caddy + 🟤 Brown garden bin + ♻️ Blue recycling bin
- Bank-holiday Mondays push collection to Tuesday (Easter, May Day, Spring, Summer, Christmas/Boxing/NY substitutes — encoded through Jan 2028)

Verify against HBBC by 2027-04-01 (extend the bank-holiday map if needed).

## Manual trigger

Either:
- GitHub UI → Actions → "Sunday Bin Reminder" → Run workflow → set `force=true` to bypass the 19:30 time check
- CLI: `gh workflow run sunday-reminder.yml -f force=true`

## Changelog

### v2.4 — 2026-05-17 (dedicated bot)
- 🤖 Switched Telegram delivery from `@ScopeFinderSEO_bot` (Cezary's SEO bot — wrong purpose) to dedicated `@GrobyBinbot` (id 8912420562)
- 🔒 `TELEGRAM_BOT_TOKEN` GitHub secret rotated to the new bot's token

### v2.3 — 2026-05-17 (drop WhatsApp; pure Telegram + Email)
- 🧹 Removed all WhatsApp delivery code — Meta has blocked every free third-party multi-device API (Green API, CallMeBot, etc.)
- 🧹 Deleted 5 unused GitHub Actions secrets (`GREEN_API_*`, `WHATSAPP_CHATID_*`) via API
- ✅ Final architecture: pure GitHub Actions, 2 channels, both rock-solid
- 📧 Sunia still receives the same reminder with the same inline PNG via email

### v2.2 — 2026-05-17 (hybrid attempt — deprecated immediately)
- Tried hybrid GH Actions + Cowork scheduled task; rejected as Cowork scheduler is not reliable enough.

### v2.1 — 2026-05-17 (GitHub Actions migration)
- 🚀 Migrated from Cowork scheduled tasks to GitHub Actions workflow
- 🧱 Consolidated all logic into one `scripts/run_reminder.py` (Python only — no markdown prompts driving an LLM)
- 🔒 Secrets moved to GitHub Actions Secrets (encrypted with libsodium; never on disk in cleartext)
- 📅 Cron covers both BST and GMT (two cron entries + first-step time check)
- 📦 Image artifact uploaded on every run (90-day retention)
- 🛟 Canary: any delivery failure pings Cezary on Telegram with the error

### v2.0 — 2026-05-17 (security + correctness)
- 🔒 Removed live Telegram + Green API tokens from repo; scrubbed git history with `git filter-repo`
- 🐛 Email path: from non-functional Gmail MCP (drafts-only) to Gmail SMTP via App Password
- 🐛 Replaced fragile date-formula week calc with explicit lookup + bank-holiday map

### v1.0 — 2026-04-27 — Initial Cowork-scheduler release
