from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LLMAgent(ABC):
    """
    Abstract base class for LLM agents.
    Allows easy swapping between different LLM providers (Anthropic, OpenAI, etc.)
    """

    @abstractmethod
    async def process_message(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and return the agent's decision and response.

        Args:
            user_message: The raw message from the user
            context: Additional context (user info, conversation history, etc.)

        Returns:
            Dict containing:
                - action: The action to perform (create_event, add_memory, etc.)
                - parameters: Parameters for the action
                - response_text: Text to send back to the user
        """
        pass

    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """
        Generate a simple text response without structured output.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            The generated text response
        """
        pass
