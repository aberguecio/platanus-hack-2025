from arq import create_pool, cron
from arq.connections import RedisSettings
import httpx
from typing import List, Dict, Any
import os

API_URL = os.getenv("API_URL", "http://backend:8000/webhook/batch")

async def process_message_batch(ctx, user_id: str, chat_id: int, updates: List[Dict]):
    """
    ARQ job: Procesa batch de mensajes después de ventana de agrupación.
    """
    print(f"[WORKER] Processing batch for user {user_id}: {len(updates)} messages")

    async with httpx.AsyncClient() as client:
        try:
            # Llamar al backend con el batch
            response = await client.post(
                API_URL,
                json={"updates": updates, "user_id": user_id},
                timeout=90.0
            )
            response.raise_for_status()
            api_response = response.json()

            # Enviar respuesta al usuario via Telegram
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            telegram_api = f"https://api.telegram.org/bot{bot_token}/sendMessage"

            if api_response.get("method") == "sendMessage":
                await client.post(telegram_api, json={
                    "chat_id": chat_id,
                    "text": api_response.get("text"),
                    "parse_mode": api_response.get("parse_mode")
                })

            return {"success": True, "batch_size": len(updates)}

        except Exception as e:
            print(f"[WORKER] Error: {e}")
            # Enviar mensaje de error al usuario
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            telegram_api = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            try:
                await client.post(telegram_api, json={
                    "chat_id": chat_id,
                    "text": "Lo siento, hubo un problema procesando tus mensajes. ¿Podrías intentarlo de nuevo?"
                })
            except:
                pass
            return {"success": False, "error": str(e)}


class WorkerSettings:
    redis_settings = RedisSettings(host="redis", port=6379)
    functions = [process_message_batch]
    max_jobs = 20
    job_timeout = 120
    keep_result = 600  # 10 minutos

