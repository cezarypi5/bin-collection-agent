# 🗑️ Bin Collection Reminder — v2.2

Automated weekly bin collection reminder for **207 Markfield Road, Groby, Leicester LE6 0FT**.

Runs as a **GitHub Actions workflow** every Sunday at 19:30 Europe/London. Sends to:

| Channel | Recipients | Mechanism | Where it runs |
|---|---|---|---|
| 📱 Telegram | Cezary | `api.telegram.org/sendPhoto` | GitHub Actions |
| 📧 Email | Cezary + Sunia | Gmail SMTP via App Password | GitHub Actions |
| 💬 WhatsApp | Cezary + Sunia | Chrome MCP + WhatsApp Web | Cowork scheduled task (laptop) |

WhatsApp moved to a Cowork scheduled task at Sun 19:35 BST (5 min after the GH Actions fire) because every headless WhatsApp API (Green API, CallMeBot, etc.) has been blocked by WhatsApp's multi-device clampdown. Chrome MCP driving real WhatsApp Web in your browser is the only path that still works reliably. When your laptop is on with Cowork running, WhatsApp fires. When the laptop is off, you and Sunia still get Telegram + email.

If any delivery fails, the workflow Telegram-pings Cezary with the error (canary channel).

## Architecture

```
.github/workflows/sunday-reminder.yml   ← cron 30 18,19 * * 0  (UTC; covers BST + GMT)
└── scripts/run_reminder.py             ← orchestrator (Python, ~250 lines)
    ├── compute next collection         ← anchor 2026-04-27 + Mon bank-holiday shifts
    ├── render PNG                      ← playwright headless chromium
    ├── send_telegram()                 ← multipart/form-data sendPhoto
    ├── send_emails()                   ← smtplib SMTP_SSL on smtp.gmail.com:465
    └── send_whatsapp()                 ← Green API sendFileByUpload (pre-flight: getStateInstance must be authorized)
```

## Local dev / manual test

```bash
pip install playwright requests
python -m playwright install --with-deps chromium

# Export secrets and dry-run
export TELEGRAM_BOT_TOKEN="…"
export TELEGRAM_CHAT_ID="…"
export GMAIL_SENDER="c.makulec@gmail.com"
export GMAIL_APP_PASSWORD="…"
export EMAIL_CEZARY="c.makulec@gmail.com"
export EMAIL_SUNIA="mantra.agni@gmail.com"
# WhatsApp optional — only used if Green API is authorized
export GREEN_API_INSTANCE="…"
export GREEN_API_TOKEN="…"
export GREEN_API_URL="https://….api.greenapi.com"
export WHATSAPP_CHATID_CEZARY="447XXXXXXXXX@c.us"
export WHATSAPP_CHATID_SUNIA="447XXXXXXXXX@c.us"

python scripts/run_reminder.py
```

## Required GitHub Actions secrets

| Secret | Value | Where to get |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | `8791…:AA…` | BotFather — `/mybots` → token |
| `TELEGRAM_CHAT_ID` | numeric chat ID | `getUpdates` after messaging the bot |
| `GMAIL_SENDER` | `c.makulec@gmail.com` | own Gmail address |
| `GMAIL_APP_PASSWORD` | 16-char code | https://myaccount.google.com/apppasswords |
| `EMAIL_CEZARY` | `c.makulec@gmail.com` | |
| `EMAIL_SUNIA` | `mantra.agni@gmail.com` | |
| `GREEN_API_INSTANCE` | e.g. `7107598382` | Green API console |
| `GREEN_API_TOKEN` | hex string | Green API console |
| `GREEN_API_URL` | e.g. `https://7107.api.greenapi.com` | Green API console |
| `WHATSAPP_CHATID_CEZARY` | `447511041288@c.us` | own WA number + `@c.us` |
| `WHATSAPP_CHATID_SUNIA` | `447XXXXXXXXX@c.us` | Sunia's WA number + `@c.us` |

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

## Why GitHub Actions instead of Cowork scheduled tasks
- Runs on GitHub infra — independent of any laptop being open
- Free for public repos (unlimited minutes)
- Properly encrypted secrets (libsodium-encrypted, never in logs)
- Auditable run history with downloadable artifacts (rendered PNG kept for 90 days)
- Reproducible — anyone can clone, set secrets, and run their own copy

## Changelog

### v2.2 — 2026-05-17 (hybrid architecture)
- 🐛 **WhatsApp delivery moved off GitHub Actions** — Green API was returning fake `idMessage` OK responses while silently dropping messages (`lastOutgoingMessages` was empty, `getMessage` returned "not found", `wid`/`phone`/`chatId` all empty). WhatsApp has progressively blocked every free third-party multi-device API.
- 🛠 **Hybrid model:** GH Actions does Telegram + Email (rock solid); Cowork scheduled task drives Chrome MCP + WhatsApp Web for WhatsApp delivery (cron `35 19 * * 0` Europe/London).
- 🧹 Removed `send_whatsapp()` from `run_reminder.py` and all Green API / WhatsApp env vars from the workflow YAML. The 4 unused secrets (`GREEN_API_*`, `WHATSAPP_CHATID_*`) can be deleted from the repo's secret store later if desired.

### v2.1 — 2026-05-17 (GitHub Actions migration)
- 🚀 Migrated from Cowork scheduled tasks to GitHub Actions workflow
- 🧱 Consolidated all logic into one `scripts/run_reminder.py` (~250 lines, Python only — no markdown prompts driving an LLM)
- 🔒 Secrets moved to GitHub Actions Secrets (encrypted; never on disk in cleartext)
- 📅 Cron covers both BST and GMT (two cron entries + first-step time check)
- 📦 Image artifact uploaded on every run (90-day retention)
- 🛟 Canary: any delivery failure pings Cezary on Telegram with the error
- 📁 Moved Cowork-era prompts to `legacy/`

### v2.0 — 2026-05-17 (security + correctness pre-migration)
- 🔒 Removed live Telegram + Green API tokens from repo; scrubbed git history with `git filter-repo`
- 🐛 Email path: from non-functional Gmail MCP (drafts-only) to Gmail SMTP via App Password
- 🐛 Replaced fragile date-formula week calc with explicit lookup + bank-holiday map
- 🐛 Bank-holiday Mon→Tue shifts encoded through Jan 2028
- 🐛 Timezone explicitly pinned to Europe/London
- 🐛 WhatsApp chatId format fixed for both recipients

### v1.0 — 2026-04-27 — Initial Cowork-scheduler release
