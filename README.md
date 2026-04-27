# 🗑️ Bin Collection Reminder Agent

Automated weekly reminder + interactive bot for bin collection at **207 Markfield Road, Groby, Leicester LE6 0FT**.

## Two agents

### 1. Weekly Reminder (`bin-collection-reminder`)
Runs every **Sunday at 19:00**. Sends a beautiful image card showing which bins to put out tomorrow.

| Channel | Recipient |
|---------|-----------|
| 📱 Telegram | Personal chat via @ScopeFinderSEO_bot |
| 💬 WhatsApp | Cezary (self) via Green API |
| 💬 WhatsApp | Sunia via Green API |
| 📧 Email | Sunia (mantra.agni@gmail.com) |

### 2. Interactive Bot (`bin-bot-responder`)
Runs every **5 minutes**. Polls for incoming messages on Telegram and WhatsApp. Reply to any bin-related question and get the schedule instantly.

**Just message the bot:**
> "Which bins this week?"  
> "When is next collection?"  
> "What goes out Monday?"

## Bin schedule (HBBC — confirmed April 2026)

Collection day: **Monday**

| Week | Bins collected |
|------|---------------|
| **Week A** (fortnightly) | ⬛ Black refuse bin + 🪣 Food waste caddy |
| **Week B** (fortnightly) | 🪣 Food waste caddy + 🟤 Brown garden bin + ♻️ Blue recycling bin |

Food waste caddy goes out **every week**.  
Anchor: **Monday 27 April 2026 = Week A**

## Config (`telegram_config.json`)

| Key | Description |
|-----|-------------|
| `bot_token` | Telegram bot token |
| `chat_id` | Telegram personal chat ID |
| `green_api_instance` | Green API WhatsApp instance ID |
| `green_api_token` | Green API token |
| `green_api_url` | Green API base URL |
| `sunia_email` | Sunia's email for weekly reminder |

## Stack
- **Scheduler:** Cowork scheduled tasks (Claude agent)
- **Browser automation:** Claude in Chrome MCP
- **WhatsApp:** Green API (instance 7107598382)
- **Telegram:** @ScopeFinderSEO_bot
- **Email:** Gmail MCP

## Powered by Claude (Anthropic) — Cowork mode
