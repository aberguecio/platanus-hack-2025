import os
import requests
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from arq import create_pool
from arq.connections import RedisSettings
from message_batcher import MessageBatcher

# Configuration (read from environment variables set by Docker Compose)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://localhost:8000/webhook")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is required")

# Globals for ARQ
redis_pool = None
message_batcher = None


async def startup(application):
    """Initialize Redis pool on bot startup"""
    global redis_pool, message_batcher
    print("[BOT] Initializing ARQ Redis pool...")
    redis_pool = await create_pool(RedisSettings(host="redis", port=6379))
    message_batcher = MessageBatcher(redis_pool, delay_seconds=5)
    print("[BOT] ARQ Redis pool initialized")

async def shutdown(application):
    """Cleanup Redis pool"""
    global redis_pool
    if redis_pool:
        print("[BOT] Closing Redis pool...")
        await redis_pool.close()
        print("[BOT] Redis pool closed")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Encola mensajes en lugar de enviar directamente al backend"""

    user_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id
    update_dict = update.to_dict()

    # Print detailed user and message information
    print("\n" + "="*80)
    print("[BOT] 📨 NEW MESSAGE RECEIVED FROM TELEGRAM")
    print("="*80)
    print(f"[BOT] User ID: {update.effective_user.id}")
    print(f"[BOT] Username: @{update.effective_user.username}")
    print(f"[BOT] First Name: {update.effective_user.first_name}")
    print(f"[BOT] Last Name: {update.effective_user.last_name}")
    print(f"[BOT] Chat ID: {chat_id}")
    print(f"[BOT] Is Bot: {update.effective_user.is_bot}")
    print(f"[BOT] Language Code: {update.effective_user.language_code}")
    print("-"*80)
    print("[BOT] 📋 FULL UPDATE DICT:")
    print("-"*80)
    import json
    print(json.dumps(update_dict, indent=2, ensure_ascii=False))
    print("="*80 + "\n")

    # Encolar mensaje (agrupa automáticamente con ventana de 12.5s)
    try:
        await message_batcher.add_message(user_id, chat_id, update_dict)
        print(f"[BOT] Message from user {user_id} queued for batching")
        # NO responder inmediatamente - el worker ARQ lo hará después del delay
    except Exception as e:
        print(f"[BOT] Error queueing message: {e}")
        await update.message.reply_text(
            "Lo siento, hubo un problema. ¿Podrías intentarlo de nuevo?"
        )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.

    Forwards the command to the backend API.
    If it's a deep link (e.g. /start evt_123), the backend agent will handle the invite.
    If it's just /start, the backend agent will say hello and show their Telegram ID.
    """
    # Show user their Telegram ID first
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "there"

    await update.message.reply_text(
        f"👋 Welcome {first_name}!\n\n"
        f"Your Telegram ID is: `{user_id}`\n\n"
        f"You'll need this ID to log in to the web app.\n"
        f"Use /myid anytime to see it again.",
        parse_mode="Markdown"
    )

    # Then forward to backend agent for processing
    await handle_message(update, context)


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /myid command - shows user their Telegram ID
    """
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name or "User"

    message = (
        f"👤 *Your Telegram Info*\n\n"
        f"• **Telegram ID:** `{user_id}`\n"
    )

    if username:
        message += f"• **Username:** @{username}\n"

    message += f"• **Name:** {first_name}\n\n"
    message += "💡 Use your Telegram ID to log in to the web app at http://localhost:3000/login"

    await update.message.reply_text(message, parse_mode="Markdown")


def main():
    """Start the bot"""
    print("Starting Telegram bot with ARQ batching...")

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Lifecycle hooks
    application.post_init = startup
    application.post_shutdown = shutdown

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("myid", myid_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_message))
    application.add_handler(MessageHandler(filters.VIDEO, handle_message))

    # Start polling
    print("Bot is running with message batching! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
