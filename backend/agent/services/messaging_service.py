from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from schemas import TelegramUpdate
from agent.tools import ExecutionContext
from enums import MessageDirectionEnum


class MessagingService:
    """
    Servicio para manejar el procesamiento y envío de mensajes en el contexto del agente.

    Este servicio actúa como capa intermedia entre el webhook de Telegram y el agente de IA,
    encapsulando la lógica de negocio relacionada con mensajería.
    """

    def __init__(self, agent, telegram_service, database_service, s3_service=None, image_service=None):
        """
        Inicializa el servicio de mensajería.

        Args:
            agent: Instancia del agente de IA (AnthropicAgent)
            telegram_service: Instancia del servicio de Telegram
            database_service: Servicio de base de datos
            s3_service: Instancia del servicio de S3 (opcional)
            image_service: Instancia del servicio de imágenes (opcional)
        """
        self.agent = agent
        self.telegram_service = telegram_service
        self.database_service = database_service
        self.s3_service = s3_service
        self.image_service = image_service

        # Initialize ImageService for processing photos in messages
        from services.image import ImageService
        self.image_service = ImageService(
            telegram_service=telegram_service,
            s3_service=s3_service
        )

    async def send_message(
        self,
        text: str,
        chat_id: int,
        parse_mode: str = "Markdown"
    ) -> Dict[str, Any]:
        """
        Envía un mensaje a través de Telegram.

        Args:
            text: Texto del mensaje a enviar
            chat_id: ID del chat de Telegram
            parse_mode: Modo de formato del texto (default: Markdown)

        Returns:
            Dict con la respuesta formateada para la API de Telegram
        """

        return self.telegram_service.format_response(
            text=text,
            chat_id=chat_id,
            parse_mode=parse_mode
        )

    async def process_response(
        self,
        update: TelegramUpdate,
        db: Session
    ) -> Dict[str, Any]:
        """
        Procesa un update de Telegram y genera una respuesta usando el agente de IA.

        Este método encapsula toda la lógica de negocio para:
        1. Extraer datos del mensaje de Telegram
        2. Obtener o crear el usuario en la base de datos
        3. Preparar el contexto para el agente
        4. Procesar el mensaje con el agente de IA
        5. Formatear y retornar la respuesta

        Args:
            update: Update de Telegram con el mensaje del usuario
            db: Sesión de base de datos

        Returns:
            Dict con la respuesta formateada para enviar de vuelta a Telegram
        """
        try:
            print(f"[MESSAGING_SERVICE] Processing new message update")

            # 1. Extraer datos del mensaje usando TelegramService
            message_data = self.telegram_service.extract_message_data(update)

            if not message_data:
                print("[MESSAGING_SERVICE] No valid message data found")
                return self.telegram_service.format_error_response(
                    status="ignored",
                    reason="no_message_or_user"
                )

            # 2. Obtener o crear usuario en la base de datos
            print(f"[MESSAGING_SERVICE] Getting/creating user: {message_data['telegram_id']}")
            user = self.database_service.get_or_create_user(
                db=db,
                telegram_id=message_data["telegram_id"],
                username=message_data["username"],
                first_name=message_data["first_name"],
                last_name=message_data["last_name"]
            )

            # 2.5. Obtener o crear conversación para el usuario
            conversation = self.database_service.get_or_create_conversation(
                db=db,
                user_id=user.id,
                channel_identifier=str(message_data["chat_id"])
            )

            # 3. Guardar mensaje del usuario en la base de datos
            print(f"[MESSAGING_SERVICE] Saving user message to database")
            user_message = await self.database_service.save_message(
                db=db,
                conversation_id=conversation.id,
                direction=MessageDirectionEnum.USER,
                content=message_data["text"],
                photo_file_id=message_data.get("photo_file_id"),
                telegram_service=self.telegram_service,
                image_service=self.image_service,
                s3_service=self.s3_service
            )
            print(f"[MESSAGING_SERVICE] User message saved with ID: {user_message.id}")

            # 4. Obtener historial reciente de conversación
            print(f"[MESSAGING_SERVICE] Fetching recent conversation history")
            recent_messages = self.database_service.get_recent_messages(
                db=db,
                conversation_id=conversation.id,
                limit=11  # Fetch 11 to get 10 history messages (excluding current)
            )

            # Convertir a formato esperado (más antiguos primero, excluyendo el mensaje actual)
            # Los mensajes vienen ordenados desc (más reciente primero), necesitamos invertir
            conversation_history = [
                {
                    "role": msg.direction.value,
                    "content": msg.content,
                    "has_photo": bool(msg.photo_s3_url)  # Include photo info
                }
                for msg in reversed(recent_messages[1:])  # Skip el mensaje actual (primero en la lista)
            ] if len(recent_messages) > 1 else []

            print(f"[MESSAGING_SERVICE] Loaded {len(conversation_history)} previous messages")

            # 5. Preparar contexto de ejecución para el agente
            execution_context = self._build_execution_context(
                message_data, user, db, conversation.id, conversation_history, user_message.id
            )

            print(f"[MESSAGING_SERVICE] ExecutionContext prepared:")
            print(f"  - User DB ID: {user.id}")
            print(f"  - Has photo: {execution_context.has_photo}")
            print(f"  - Text length: {len(message_data['text'])}")
            print(f"  - Conversation history size: {len(conversation_history)}")

            # 6. Procesar mensaje con el agente de IA
            print(f"[MESSAGING_SERVICE] Calling AI agent...")
            final_response = await self.agent.process_message(
                message_data["text"],
                execution_context
            )

            print(f"[MESSAGING_SERVICE] Agent response received: {final_response[:100]}...")

            # 7. Guardar respuesta del bot en la base de datos
            print(f"[MESSAGING_SERVICE] Saving assistant response to database")
            await self.database_service.save_message(
                db=db,
                conversation_id=conversation.id,
                direction=MessageDirectionEnum.ASSISTANT,
                content=final_response
            )

            # 8. Formatear y retornar respuesta
            return await self.send_message(
                text=final_response,
                chat_id=message_data["chat_id"]
            )

        except Exception as e:
            print(f"[MESSAGING_SERVICE] Error processing response: {e}")
            import traceback
            traceback.print_exc()

            return self.telegram_service.format_error_response(
                status="error",
                reason=str(e)
            )

    def _build_execution_context(
        self,
        message_data: Dict[str, Any],
        user: Any,
        db: Session,
        conversation_id: int,
        conversation_history: list = None,
        message_id: int = None
    ) -> ExecutionContext:
        """
        Construye el ExecutionContext necesario para el agente de IA.

        Args:
            message_data: Datos extraídos del mensaje de Telegram
            user: Objeto usuario de la base de datos
            db: Sesión de base de datos
            conversation_id: ID de la conversación actual
            conversation_history: Historial de conversación (opcional)
            message_id: ID del mensaje actual del usuario (opcional)

        Returns:
            ExecutionContext con todos los servicios y metadata
        """
        metadata = {
            "telegram_id": message_data["telegram_id"],
            "username": message_data["username"],
            "first_name": message_data["first_name"],
            "last_name": message_data["last_name"],
            "has_photo": message_data["has_photo"],
            "photo_file_id": message_data["photo_file_id"],
            "message_id": message_id
        }

        return ExecutionContext(
            db=db,
            user=user,
            s3_service=self.s3_service,
            telegram_service=self.telegram_service,
            image_service=self.image_service,
            metadata=metadata,
            conversation_id=conversation_id,
            conversation_history=conversation_history or []
        )

    async def send_error_message(
        self,
        chat_id: int,
        error_message: str = "Lo siento, hubo un error procesando tu solicitud."
    ) -> Dict[str, Any]:
        """
        Envía un mensaje de error al usuario.

        Args:
            chat_id: ID del chat de Telegram
            error_message: Mensaje de error a enviar

        Returns:
            Dict con la respuesta formateada
        """
        return await self.send_message(
            text=error_message,
            chat_id=chat_id
        )

    async def send_welcome_message(self, chat_id: int, first_name: str) -> Dict[str, Any]:
        """
        Envía un mensaje de bienvenida al usuario.

        Args:
            chat_id: ID del chat de Telegram
            first_name: Nombre del usuario

        Returns:
            Dict con la respuesta formateada
        """
        welcome_text = f"""👋 ¡Hola {first_name}! Bienvenido a Memories Bot.

Puedo ayudarte a almacenar y organizar tus recuerdos.

Prueba diciendo:
- 'Crea un evento llamado Cumpleaños'
- 'Lista mis eventos'
- 'Agrega un recuerdo al evento #1: ¡La pasé genial!'

También puedes enviarme fotos directamente 📸"""

        return await self.send_message(
            text=welcome_text,
            chat_id=chat_id
        )


