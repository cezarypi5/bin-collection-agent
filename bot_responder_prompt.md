# Bin Bot Responder — Telegram + WhatsApp (Green API)

Runs every 5 minutes. Polls both Telegram and WhatsApp for incoming messages.
Replies with the bin collection schedule whenever someone asks.

## Trigger keywords
bin, collection, recycling, refuse, rubbish, caddy, garden, waste, when, next, monday, week

## How it works
1. Calls Telegram `getUpdates` (offset stored in localStorage)
2. Calls Green API `receiveNotification` (drains queue up to 5 messages)
3. For any message matching bin keywords → calculates next collection → replies
4. Always calls `deleteNotification` after each Green API message

## Channels
- Telegram: @ScopeFinderSEO_bot
- WhatsApp: Green API instance 7107598382 (linked to 447511041288)

## Both Cezary and Sunia can ask the bot
