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
    If it's just /start, the backend agent will say hello.
    """
    # Reuse the generic message handler logic
    await handle_message(update, context)


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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_message))
    application.add_handler(MessageHandler(filters.VIDEO, handle_message))

    # Start polling
    print("Bot is running with message batching! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
