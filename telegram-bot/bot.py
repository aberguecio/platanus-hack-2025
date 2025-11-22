import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuration (read from environment variables set by Docker Compose)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://localhost:8000/webhook")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is required")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all incoming messages and forward to API"""

    # Get the raw update as dict
    update_dict = update.to_dict()

    try:
        # Send to API
        response = requests.post(API_URL, json=update_dict, timeout=30)
        response.raise_for_status()

        # Parse API response
        api_response = response.json()

        # Extract the message text to send back
        if api_response.get("method") == "sendMessage":
            text = api_response.get("text", "No response")
            parse_mode = api_response.get("parse_mode")

            # Send response back to user
            await update.message.reply_text(
                text=text,
                parse_mode=parse_mode if parse_mode else None
            )
        else:
            # Unknown response format
            await update.message.reply_text("Done!")

    except requests.RequestException as e:
        print(f"API Error: {e}")
        await update.message.reply_text(
            "Sorry, there was an error processing your request."
        )
    except Exception as e:
        print(f"Unexpected error: {e}")
        await update.message.reply_text(
            "Sorry, something went wrong."
        )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "👋 Welcome to Memories Bot!\n\n"
        "I can help you store and organize your memories.\n\n"
        "Try saying:\n"
        "- 'Create event Birthday Party on 2025-12-25'\n"
        "- 'List my events'\n"
        "- 'Add memory to event #1: Had a great time!'"
    )


def main():
    """Start the bot"""
    print("Starting Telegram bot...")

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))

    # Start polling
    print("Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
