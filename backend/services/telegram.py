import httpx
from typing import Optional, Dict, Any, Tuple
from schemas import TelegramUpdate


class TelegramService:
    """Service for handling Telegram operations and message processing"""

    def __init__(self, bot_token: str, speech_service=None):
        """
        Initialize Telegram Service.

        Args:
            bot_token: Telegram bot token
            speech_service: SpeechService for voice transcription (optional)
        """
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.speech_service = speech_service

    async def download_file(self, file_id: str) -> bytes:
        """Download a file from Telegram"""
        async with httpx.AsyncClient() as client:
            # Get file path
            response = await client.get(
                f"{self.base_url}/getFile",
                params={"file_id": file_id}
            )
            file_path = response.json()["result"]["file_path"]

            # Download file
            file_response = await client.get(
                f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            )
            return file_response.content

    async def extract_message_data(self, update: TelegramUpdate) -> Optional[Dict[str, Any]]:
        """
        Extrae y procesa los datos del mensaje de Telegram.

        Maneja texto, fotos y mensajes de voz.
        Los audios se transcriben automáticamente a texto.

        Returns:
            Dict con los datos extraídos del mensaje, o None si no hay mensaje válido
        """
        message = update.message
        if not message:
            return None

        # Extract user info
        from_user = message.from_
        if not from_user:
            return None

        telegram_id = str(from_user.id)
        username = from_user.username
        first_name = from_user.first_name
        last_name = from_user.last_name
        chat_id = message.chat.id

        # Extract message content
        text = message.text or ""
        caption = message.caption or ""
        photo = message.photo
        voice = message.voice
        video = message.video

        # DEBUG LOGS
        print(f"\n[TELEGRAM_SERVICE] Received update:")
        print(f"[TELEGRAM_SERVICE] - message.text: '{text}'")
        print(f"[TELEGRAM_SERVICE] - message.caption: '{caption}'")
        print(f"[TELEGRAM_SERVICE] - message.photo: {bool(photo)} (count: {len(photo) if photo else 0})")
        print(f"[TELEGRAM_SERVICE] - message.voice: {bool(voice)}")
        print(f"[TELEGRAM_SERVICE] - message.video: {bool(video)}")

        # Handle photo if present
        photo_file_id = None
        if photo:
            largest_photo = max(photo, key=lambda p: p.file_size or 0)
            photo_file_id = largest_photo.file_id
            print(f"[TELEGRAM_SERVICE] - photo_file_id: {photo_file_id}")

        # Handle voice if present
        voice_file_id = None
        if voice:
            voice_file_id = voice.file_id
            print(f"[TELEGRAM_SERVICE] - voice_file_id: {voice_file_id}")
            print(f"[TELEGRAM_SERVICE] - voice duration: {voice.duration}s")

        # Handle video if present
        video_file_id = None
        if video:
            video_file_id = video.file_id
            print(f"[TELEGRAM_SERVICE] - video_file_id: {video_file_id}")
            print(f"[TELEGRAM_SERVICE] - video duration: {video.duration}s")
            print(f"[TELEGRAM_SERVICE] - video size: {video.file_size} bytes")

        # Determine final text to process
        # Handle voice transcription
        transcribed_audio = None
        if voice_file_id:
            transcribed_audio = await self._transcribe_voice(voice_file_id)
        
        # Handle text/caption (even if there's audio)
        message_text = self._determine_message_text(text, caption, photo or video)
        
        # Combine audio transcription with text/caption if both exist
        if transcribed_audio and message_text and message_text.strip():
            # If there's both audio and text/caption, combine them
            final_text = f"{transcribed_audio}\n\n{message_text}"
        elif transcribed_audio:
            # Only audio
            final_text = transcribed_audio
        else:
            # Only text/caption
            final_text = message_text

        print(f"[TELEGRAM_SERVICE] Final text to process: '{final_text}'")
        print(f"[TELEGRAM_SERVICE] Has photo: {bool(photo)}")
        print(f"[TELEGRAM_SERVICE] Has video: {bool(video)}")
        print(f"[TELEGRAM_SERVICE] Has voice: {bool(voice)}\n")

        return {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "chat_id": chat_id,
            "text": final_text,
            "has_photo": bool(photo),
            "photo_file_id": photo_file_id,
            "has_video": bool(video),
            "video_file_id": video_file_id,
            "has_voice": bool(voice),
            "voice_file_id": voice_file_id
        }

    async def _transcribe_voice(self, voice_file_id: str) -> str:
        """
        Download and transcribe voice message.

        Args:
            voice_file_id: Telegram voice file ID

        Returns:
            Transcribed text with [Audio transcrito] prefix
        """
        if not self.speech_service:
            print("[TELEGRAM_SERVICE] ⚠️ SpeechService not available, cannot transcribe")
            return "[Usuario envió un audio - SpeechService no está configurado]"

        try:
            print(f"[TELEGRAM_SERVICE] 🎤 Downloading voice message...")

            # Download voice from Telegram
            voice_bytes = await self.download_file(voice_file_id)

            print(f"[TELEGRAM_SERVICE] Voice downloaded: {len(voice_bytes)} bytes")
            print(f"[TELEGRAM_SERVICE] Transcribing with Whisper...")

            # Transcribe with Whisper
            transcribed_text = self.speech_service.transcribe_audio(voice_bytes, language="es")

            # Add prefix to indicate it was transcribed
            final_text = f"[Audio transcrito]: {transcribed_text}"

            print(f"[TELEGRAM_SERVICE] ✅ Transcription complete: {transcribed_text[:80]}...")

            return final_text

        except Exception as e:
            print(f"[TELEGRAM_SERVICE] ❌ Error transcribing voice: {e}")
            import traceback
            traceback.print_exc()

            # Return fallback message
            return "[Usuario envió un audio que no pude transcribir]"

    def _determine_message_text(self, text: str, caption: str, photo: Any) -> str:
        """
        Determina el texto final a procesar basado en el contenido del mensaje.

        Args:
            text: Texto del mensaje
            caption: Caption de la foto (si existe)
            photo: Objeto photo del mensaje

        Returns:
            El texto final a procesar
        """
        # Use caption if photo has one, otherwise use text
        if photo and caption.strip():
            print(f"[TELEGRAM_SERVICE] Using caption as text: '{caption}'")
            return caption
        elif photo and not text.strip():
            # If user sent only a photo without text/caption, create a default message
            print(f"[TELEGRAM_SERVICE] Photo without caption, using default message")
            return "I sent you a photo. Please help me save it as a memory."

        return text

    def format_response(self, text: str, chat_id: int, parse_mode: str = "Markdown") -> Dict[str, Any]:
        """
        Formatea la respuesta en el formato esperado por la API de Telegram Bot.

        Args:
            text: Texto de la respuesta
            chat_id: ID del chat al que enviar el mensaje
            parse_mode: Modo de formateo del texto (default: "Markdown")

        Returns:
            Dict con el formato de respuesta de Telegram Bot API
        """
        # Disable parse_mode if text contains t.me links to avoid Markdown parsing issues
        if "t.me/" in text:
            parse_mode = None

        response = {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": text,
        }

        if parse_mode:
            response["parse_mode"] = parse_mode

        return response

    def format_error_response(self, status: str = "error", reason: str = "unknown_error") -> Dict[str, str]:
        """
        Formatea una respuesta de error.
        
        Args:
            status: Estado del error
            reason: Razón del error
            
        Returns:
            Dict con información del error
        """
        return {
            "status": status,
            "reason": reason
        }
