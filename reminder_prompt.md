# Bin Collection Reminder — 207 Markfield Road, Groby, LE6 0FT

## Collection schedule (confirmed from HBBC website April 2026)
Collection day: **Monday** (all bins out by 7am)

- **Week A (Refuse week):** Black refuse bin + food waste caddy
- **Week B (Recycling week):** Food waste caddy + brown garden bin + blue recycling bin
- Food waste caddy goes out **every single week** without exception
- Base anchor: **Monday 27 April 2026 = Week A**

## Schedule (fortnightly alternating from 27 Apr 2026)
| Week | Bins |
|------|------|
| A (27 Apr, 11 May, 25 May...) | ⬛ Black refuse bin + 🪣 Food waste caddy |
| B (4 May, 18 May, 1 Jun...)   | 🪣 Food waste caddy + 🟤 Brown garden bin + ♻️ Blue recycling bin |

## What the agent does every Sunday at 19:00
1. Calculates which bins go out the next Monday (Week A or B)
2. Renders a beautiful HTML reminder card with coloured bin graphics
3. Captures the card as a PNG using html2canvas
4. Sends the image to **Telegram** (@ScopeFinderSEO_bot → personal chat)
5. Sends the image via **WhatsApp** to Cezary (self)
6. Sends the image via **WhatsApp** to Sunia
7. Emails **Sunia** at mantra.agni@gmail.com

## Channels
- Telegram: `@ScopeFinderSEO_bot`, chat ID in `telegram_config.json`
- WhatsApp: via WhatsApp Web (Chrome MCP automation)
- Email: Gmail MCP (c.makulec@gmail.com → mantra.agni@gmail.com)

## Technical notes
- Telegram API is **blocked in bash sandbox** — must use Chrome MCP `javascript_tool`
- Image is rendered via `html2canvas` and POSTed to Telegram `sendPhoto` endpoint
- Week calculation: `weeksSinceAnchor = (nextMonday - 2026-04-27) / 7days`; even = Week A
- Scheduled task ID: `bin-collection-reminder` (cron: `0 19 * * 0`)
