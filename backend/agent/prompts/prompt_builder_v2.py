"""
Prompt builder v2 - Hybrid architecture with smart context management.

Implements Anthropic's "effective context engineering" principles:
- Smallest possible set of high-signal tokens
- Just-in-time retrieval
- Compaction for long conversations
- Progressive disclosure
"""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from .context import ConversationContext, ImageContext


class PromptBuilderV2:
    """
    Next-generation prompt builder with hybrid format support and smart context.

    Architecture:
    - manifest.json: Orchestration and configuration
    - core/*.txt: Prose content (identity, instructions)
    - examples/*.json: Structured few-shot examples
    - context/*.py: Runtime context management
    """

    def __init__(self):
        """Initialize prompt builder and load configuration."""
        self.prompts_dir = Path(__file__).parent
        self._load_manifest()
        self._load_core_components()
        self._initialize_context_managers()

    def _load_manifest(self):
        """Load manifest.json configuration."""
        manifest_path = self.prompts_dir / "manifest.json"

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                self.manifest = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Manifest not found: {manifest_path}. "
                "Ensure manifest.json exists in prompts directory."
            )

        self.config = self.manifest.get("context_strategy", {})
        self.behavior = self.manifest.get("behavior", {})

    def _load_core_components(self):
        """Load core prompt components (identity, instructions)."""
        components = self.manifest.get("components", {})

        # Load identity
        identity_path = self.prompts_dir / components.get("identity", "core/identity.txt")
        self.identity = self._load_file(identity_path)

        # Load instructions
        instructions_path = self.prompts_dir / components.get("instructions", "core/instructions.xml")
        self.instructions = self._load_file(instructions_path)

    def _initialize_context_managers(self):
        """Initialize context management utilities."""
        compaction_config = self.config.get("compaction", {})

        self.conversation_context = ConversationContext(
            max_messages=self.config.get("max_history_messages", 10),
            compaction_threshold=compaction_config.get("trigger_threshold", 50),
            summary_max_tokens=compaction_config.get("summary_max_tokens", 500)
        )

        image_config = self.config.get("images", {})
        self.image_context = ImageContext(
            mode=image_config.get("mode", "descriptions_only")
        )

    def _load_file(self, file_path: Path) -> str:
        """Load a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Prompt component not found: {file_path}"
            )

    def _load_examples(self, example_file: str) -> List[Dict[str, Any]]:
        """Load few-shot examples from JSON file."""
        examples_dir = self.prompts_dir / self.manifest["examples"]["directory"]
        example_path = examples_dir / example_file

        try:
            with open(example_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Examples are optional - return empty list if not found
            return []

    def build_system_prompt(
        self,
        telegram_id: Optional[str] = None,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        has_photo: bool = False,
        has_video: bool = False,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        include_examples: bool = False
    ) -> str:
        """
        Build complete system prompt with dynamic context.

        Args:
            telegram_id: User's Telegram ID
            username: User's username
            first_name: User's first name
            first_name: User's first name
            has_photo: Whether current message has photo
            has_video: Whether current message has video
            conversation_history: Recent conversation history
            include_examples: Whether to include few-shot examples (optional)

        Returns:
            Complete system prompt optimized for context window
        """
        sections = []

        # 1. Identity (who the bot is)
        sections.append(self.identity)

        # 2. Instructions (structured with XML)
        sections.append(self.instructions)

        # 3. User context (runtime information)
        user_context = self._build_user_context(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name
        )
        sections.append(f"\n<user_context>\n{user_context}\n</user_context>")

        # 4. Conversation context (if available)
        if conversation_history:
            conv_context = self._build_conversation_context(conversation_history)
            if conv_context:
                sections.append(f"\n<recent_context>\n{conv_context}\n</recent_context>")

        # 5. Current state indicators
        state_indicators = []
        if has_photo:
            state_indicators.append("⚠️ El usuario envió una FOTO en este mensaje")
        if has_video:
            state_indicators.append("⚠️ El usuario envió un VIDEO en este mensaje")

        if state_indicators:
            sections.append(f"\n<current_state>\n" + "\n".join(state_indicators) + "\n</current_state>")

        # 6. Optional: Few-shot examples (only if requested and appropriate)
        if include_examples:
            examples_section = self._build_examples_section()
            if examples_section:
                sections.append(f"\n<examples>\n{examples_section}\n</examples>")

        # Combine all sections
        return "\n\n".join(sections)

    def _build_user_context(
        self,
        telegram_id: Optional[str] = None,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> str:
        """Build user context section."""
        return f"""Telegram ID: {telegram_id or 'unknown'}
Username: {username or 'unknown'}
Nombre: {first_name or 'unknown'}"""

    def _build_conversation_context(
        self,
        history: List[Dict[str, Any]]
    ) -> str:
        """
        Build conversation context from history.

        Uses smart selection and compaction to minimize tokens.
        """
        if not history:
            return ""

        # Extract event context if available
        event_ctx = self.conversation_context.extract_event_context(history)

        context_parts = []

        if event_ctx:
            context_parts.append(
                f"Evento activo en conversación: {event_ctx.get('event_name', 'desconocido')}"
            )

        # Add summary of recent actions
        photo_count = sum(1 for msg in history if msg.get("has_photo"))
        if photo_count > 0:
            context_parts.append(f"Fotos enviadas recientemente: {photo_count}")

        # Add contextual hints
        context_parts.append(
            "Usa el historial para evitar preguntar información que el usuario ya te dio."
        )

        return "\n".join(context_parts)

    def _build_examples_section(self) -> str:
        """
        Build few-shot examples section.

        Loads all example files and formats them for Claude.
        """
        example_files = self.manifest.get("examples", {}).get("files", [])

        if not example_files:
            return ""

        all_examples = []

        # Load all example files
        for example_file in example_files:
            examples = self._load_examples(example_file)
            all_examples.extend(examples)

        if not all_examples:
            return ""

        # Format examples for Claude
        formatted_examples = []

        for example in all_examples:
            scenario = example.get("scenario", "Example scenario")
            conversation = example.get("conversation", [])

            # Build conversation exchange
            conversation_parts = []
            for turn in conversation:
                role = turn.get("role")
                content = turn.get("content", "")

                if role == "user":
                    # User turn
                    has_photo = turn.get("has_photo", False)
                    photo_marker = " [con foto]" if has_photo else ""
                    conversation_parts.append(f"Usuario: {content}{photo_marker}")

                elif role == "assistant":
                    # Assistant turn - include thinking if present
                    thinking = turn.get("thinking", "")
                    response = turn.get("response", "")

                    if thinking:
                        conversation_parts.append(f"Asistente (pensamiento): {thinking}")
                    conversation_parts.append(f"Asistente: {response}")

            # Format as example block
            example_block = f"""
{scenario}:
{chr(10).join(conversation_parts)}
"""
            formatted_examples.append(example_block.strip())

        # Combine all examples
        return "\n\n---\n\n".join(formatted_examples)

    def format_conversation_history(
        self,
        messages: List[Dict[str, Any]],
        total_message_count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Format conversation history for inclusion in messages array.

        Applies compaction and image formatting strategies.

        Args:
            messages: Raw message history
            total_message_count: Total messages in full conversation

        Returns:
            Formatted messages ready for Claude API
        """
        # Use conversation context manager to process
        return self.conversation_context.process_history(
            messages,
            total_message_count
        )

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value from manifest."""
        return self.manifest.get(key, default)


# Singleton instance
_builder: Optional[PromptBuilderV2] = None


def get_prompt_builder() -> PromptBuilderV2:
    """
    Get singleton instance of PromptBuilderV2.

    Returns:
        The singleton builder instance
    """
    global _builder
    if _builder is None:
        _builder = PromptBuilderV2()
    return _builder
