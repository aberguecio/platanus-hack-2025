"""
Prompt builder for the AI agent.

This module provides functionality to build dynamic system prompts by composing
templates with runtime context (user info, photos, conversation state, etc.).
"""
from pathlib import Path
from typing import Optional


class PromptBuilder:
    """Builds dynamic system prompts by composing templates with context."""

    def __init__(self):
        """Initialize the prompt builder and load all templates."""
        self.prompts_dir = Path(__file__).parent
        self._load_templates()

    def _load_templates(self):
        """Load all prompt templates from files."""
        self.base_system = self._load_file("base_system.txt")
        self.photo_handling = self._load_file("photo_handling.txt")
        self.tools_description = self._load_file("tools_description.txt")

    def _load_file(self, filename: str) -> str:
        """
        Load a prompt template file.

        Args:
            filename: Name of the file to load

        Returns:
            Contents of the file as a string

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        file_path = self.prompts_dir / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Prompt template not found: {file_path}. "
                f"Make sure all prompt files exist in {self.prompts_dir}"
            )

    def build_system_prompt(
        self,
        telegram_id: Optional[str] = None,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        has_photo: bool = False
    ) -> str:
        """
        Build the complete system prompt with dynamic context.

        This method composes the base system prompt with user context,
        photo handling instructions (if applicable), and tool descriptions.

        Args:
            telegram_id: Telegram ID of the user
            username: Username of the user
            first_name: First name of the user
            has_photo: Whether the current message includes a photo

        Returns:
            Complete system prompt ready to send to the LLM

        Example:
            >>> builder = PromptBuilder()
            >>> prompt = builder.build_system_prompt(
            ...     telegram_id="12345",
            ...     username="johndoe",
            ...     first_name="John",
            ...     has_photo=True
            ... )
        """
        # Build user context section
        user_context = self._build_user_context(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name
        )

        # Build photo context section (only if there's a photo)
        photo_context = ""
        if has_photo:
            photo_context = "\n\n" + self.photo_handling

        # Compose the base system prompt with context
        system_prompt = self.base_system.format(
            user_context=user_context,
            photo_context=photo_context
        )

        # Append tools description
        system_prompt += "\n\n---\n\n" + self.tools_description

        return system_prompt

    def _build_user_context(
        self,
        telegram_id: Optional[str] = None,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> str:
        """
        Build the user context section of the prompt.

        Args:
            telegram_id: Telegram ID of the user
            username: Username of the user
            first_name: First name of the user

        Returns:
            Formatted user context string
        """
        return f"""- Telegram ID: {telegram_id or 'unknown'}
- Username: {username or 'unknown'}
- Nombre: {first_name or 'unknown'}"""


# Singleton instance for performance
_builder: Optional[PromptBuilder] = None


def get_prompt_builder() -> PromptBuilder:
    """
    Get the singleton instance of PromptBuilder.

    This ensures we only load the prompt templates once, improving performance.

    Returns:
        The singleton PromptBuilder instance
    """
    global _builder
    if _builder is None:
        _builder = PromptBuilder()
    return _builder
