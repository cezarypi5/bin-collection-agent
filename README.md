# 🗑️ Bin Collection Reminder Agent

Automated weekly reminder for bin collection at **207 Markfield Road, Groby, Leicester LE6 0FT**.

Runs every **Sunday at 19:00** and sends a beautiful reminder image showing which bins to put out the next morning.

## What it sends

A professionally designed reminder card showing:
- The collection date (tomorrow's Monday)
- Which bins go out (with colour-coded bin graphics)
- Friendly message + collection time (7am)

## Channels

| Channel | Recipient |
|---------|-----------|
| 📱 Telegram | Personal chat via @ScopeFinderSEO_bot |
| 💬 WhatsApp | Cezary (self) |
| 💬 WhatsApp | Sunia |
| 📧 Email | Sunia (mantra.agni@gmail.com) |

## Bin schedule (HBBC — confirmed April 2026)

Collection day: **Monday**

| Week | Bins collected |
|------|---------------|
| **Week A** (fortnightly) | ⬛ Black refuse bin + 🪣 Food waste caddy |
| **Week B** (fortnightly) | 🪣 Food waste caddy + 🟤 Brown garden bin + ♻️ Blue recycling bin |

Food waste caddy goes out **every week**.  
Base anchor: **Monday 27 April 2026 = Week A**

## Config

Credentials and settings in `telegram_config.json`:
- Telegram bot token + chat ID
- Address
- Sunia's email and WhatsApp name

## How it works

1. Calculates Week A or B from the anchor date
2. Renders a beautiful HTML card with bin graphics
3. Captures it as PNG using `html2canvas`
4. Sends via Telegram `sendPhoto` API (from browser — bash proxy blocks Telegram)
5. Attaches and sends via WhatsApp Web automation (Chrome MCP)
6. Emails Sunia via Gmail MCP

## Stack

- **Scheduler:** Cowork scheduled tasks (Claude agent, `bin-collection-reminder`)
- **Browser automation:** Claude in Chrome MCP
- **Email:** Gmail MCP
- **Telegram:** Bot API via browser fetch

## Powered by

Claude (Anthropic) — Cowork mode
