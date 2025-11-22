# Telegram Bot for Memories API

Simple Telegram bot that forwards messages to the Memories API.

## Setup

1. **Get Bot Token**
   - Talk to [@BotFather](https://t.me/botfather) on Telegram
   - Create a new bot with `/newbot`
   - Copy the token

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your TELEGRAM_BOT_TOKEN
   ```

4. **Run the Bot**
   ```bash
   python bot.py
   ```

## Usage

The bot will:
1. Receive messages from users
2. Forward the raw Telegram update to your API at `/webhook`
3. Send the API response back to the user

## Example

```
User: Create event Birthday Party on 2025-12-25
Bot: Event 'Birthday Party' created with ID 1!

User: List my events
Bot: Your events:
#1: Birthday Party
```

## Production Deployment

For production, change `API_URL` in `.env` to:
```
API_URL=https://ph.berguecio.cl/webhook
```

Then deploy the bot to a server (VPS, Heroku, etc.) and keep it running.
