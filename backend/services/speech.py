import os
import tempfile
from typing import Optional
from openai import OpenAI


class SpeechService:
    """
    Service for speech-to-text transcription using OpenAI Whisper API.

    Handles voice message transcription from Telegram audio files.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Speech Service.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for speech transcription")

        self.client = OpenAI(api_key=self.api_key)
        print("[SPEECH_SERVICE] Initialized with Whisper API")

    def transcribe_audio(self, audio_bytes: bytes, language: str = "es") -> str:
        """
        Transcribe audio using OpenAI Whisper API.

        Args:
            audio_bytes: Audio file bytes (OGG format from Telegram)
            language: Language code for transcription (default: "es" for Spanish)

        Returns:
            Transcribed text

        Raises:
            Exception: If transcription fails
        """
        temp_path = None

        try:
            # Whisper API requires a file, so save to temp
            print(f"[SPEECH_SERVICE] Saving audio to temp file ({len(audio_bytes)} bytes)")
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp:
                temp.write(audio_bytes)
                temp_path = temp.name

            print(f"[SPEECH_SERVICE] Transcribing audio with Whisper (language: {language})")

            # Transcribe with Whisper
            with open(temp_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="text"  # Get plain text directly
                )

            transcribed_text = transcript.strip() if isinstance(transcript, str) else transcript.text.strip()

            print(f"[SPEECH_SERVICE] Transcription successful: {transcribed_text[:100]}...")

            return transcribed_text

        except Exception as e:
            print(f"[SPEECH_SERVICE] ❌ Error transcribing audio: {e}")
            import traceback
            traceback.print_exc()
            raise

        finally:
            # Cleanup temp file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    print(f"[SPEECH_SERVICE] Temp file cleaned up")
                except Exception as cleanup_error:
                    print(f"[SPEECH_SERVICE] Warning: Failed to cleanup temp file: {cleanup_error}")
