"""
Conversation context management with compaction strategy.

Implements the "smallest possible set of high-signal tokens" principle from
Anthropic's context engineering guide.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MessagePriority:
    """Priority weights for different message types."""
    USER_WITH_PHOTO = 3
    USER_EVENT_MENTION = 2
    USER_REGULAR = 1
    ASSISTANT_TOOL_RESULT = 2
    ASSISTANT_REGULAR = 1


class ConversationContext:
    """
    Manages conversation history with smart compaction.

    Strategy: Sliding window with priority-based selection
    - Recent messages always included (last N)
    - Older messages selected by priority (photo uploads, event mentions)
    - Summary generated when approaching token limits
    """

    def __init__(
        self,
        max_messages: int = 10,
        compaction_threshold: int = 50,
        summary_max_tokens: int = 500
    ):
        """
        Initialize conversation context manager.

        Args:
            max_messages: Maximum number of messages to keep in context
            compaction_threshold: Trigger compaction after this many total messages
            summary_max_tokens: Maximum tokens for conversation summary
        """
        self.max_messages = max_messages
        self.compaction_threshold = compaction_threshold
        self.summary_max_tokens = summary_max_tokens

    def process_history(
        self,
        messages: List[Dict[str, Any]],
        total_message_count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Process conversation history with smart selection.

        Args:
            messages: List of message dicts with role, content, metadata
            total_message_count: Total messages in conversation (for compaction trigger)

        Returns:
            Processed list of messages optimized for context
        """
        if not messages:
            return []

        # If under max, return as-is
        if len(messages) <= self.max_messages:
            return self._format_messages(messages)

        # If total conversation is very long, consider compaction
        if total_message_count and total_message_count > self.compaction_threshold:
            return self._compact_history(messages)

        # Otherwise, use sliding window with priority
        return self._sliding_window_with_priority(messages)

    def _format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format messages for Claude API.

        Replaces full images with descriptions to save tokens.
        """
        formatted = []
        for msg in messages:
            content = msg["content"]

            # If user message with photo, append image description
            if msg.get("has_photo") and msg["role"] == "user":
                description = msg.get("image_description", "")
                if description:
                    content = f"[Foto: {description}]\n{content}" if content else f"[Foto: {description}]"
                else:
                    content = f"[Foto enviada]\n{content}" if content else "[Foto enviada]"

            formatted.append({
                "role": msg["role"],
                "content": content
            })

        return formatted

    def _sliding_window_with_priority(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Select messages using sliding window with priority scoring.

        Always keeps recent messages, then selects high-priority older ones.
        """
        # Always keep last N messages
        recent_window = max(5, self.max_messages // 2)
        recent_messages = messages[-recent_window:]

        # Score remaining messages by priority
        older_messages = messages[:-recent_window]
        scored = [
            (self._score_message(msg), idx, msg)
            for idx, msg in enumerate(older_messages)
        ]

        # Sort by score (highest first) and take top ones
        scored.sort(reverse=True, key=lambda x: x[0])
        slots_available = self.max_messages - len(recent_messages)
        selected_older = [msg for _, _, msg in scored[:slots_available]]

        # Combine and maintain chronological order
        all_selected = selected_older + recent_messages
        return self._format_messages(all_selected)

    def _score_message(self, msg: Dict[str, Any]) -> int:
        """
        Score message priority for context selection.

        Higher score = more important to keep in context.
        """
        score = 0
        content = msg.get("content", "").lower()

        # User messages with photos are high priority
        if msg.get("has_photo"):
            score += MessagePriority.USER_WITH_PHOTO

        # Messages mentioning events/memories are important
        event_keywords = ["evento", "event", "álbum", "album", "guardé", "guardada", "creé"]
        if any(keyword in content for keyword in event_keywords):
            score += MessagePriority.USER_EVENT_MENTION

        # User messages generally higher priority than assistant
        if msg["role"] == "user":
            score += MessagePriority.USER_REGULAR
        else:
            score += MessagePriority.ASSISTANT_REGULAR

        return score

    def _compact_history(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compact long conversation history with summary.

        Strategy:
        1. Keep recent messages (last 10)
        2. Summarize middle section
        3. Keep key events from beginning
        """
        # Always keep recent messages
        recent = messages[-self.max_messages:]

        # For now, just use recent messages
        # TODO: Implement summarization with Claude for very long conversations
        return self._format_messages(recent)

    def extract_event_context(self, messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Extract active event context from recent messages.

        Looks for:
        - Recently created events
        - Events mentioned in last 10 messages
        - Event disambiguations

        Returns:
            Dict with event_id, event_name if found, None otherwise
        """
        # Look through messages in reverse (most recent first)
        for msg in reversed(messages):
            content = msg.get("content", "").lower()

            # Check for event creation confirmations
            if "creé" in content or "listo" in content:
                # Try to extract event name (simple heuristic)
                # Pattern: "Creé 'Event Name'" or "Listo! Creé el evento 'Event Name'"
                if "'" in content:
                    parts = content.split("'")
                    if len(parts) >= 2:
                        return {"event_name": parts[1].strip()}

            # Check for explicit event mentions
            # Pattern: "guardada en 'Event Name'" or "en 'Event Name'"
            if "en '" in content:
                parts = content.split("en '")
                if len(parts) >= 2:
                    event_name = parts[1].split("'")[0]
                    return {"event_name": event_name.strip()}

        return None
