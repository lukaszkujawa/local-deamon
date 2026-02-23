"""Utility functions for token estimation and tracking."""

from typing import Tuple
from langchain_core.messages import AIMessage


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a text string.

    Uses a simple heuristic: ~4 characters per token.
    This is a rough approximation that works reasonably well for:
    - English text: ~4 chars/token
    - Code: ~3-5 chars/token
    - Mixed content: ~4 chars/token

    For exact counts, use the model's tokenizer, but this is
    fast and good enough for monitoring context usage.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    if not text:
        return 0

    return max(1, len(text) // 4)


def format_tokens(count: int) -> str:
    """
    Format token count for display.

    Args:
        count: Token count

    Returns:
        Formatted string (e.g., "1.2K tokens", "45 tokens")
    """
    if count >= 1000:
        return f"{count/1000:.1f}K tokens"
    return f"{count} tokens"


def extract_token_usage(response: AIMessage) -> Tuple[int, int]:
    """
    Extract token usage from LLM response metadata.

    Works across different providers (OpenAI, Anthropic, Ollama).

    Args:
        response: AI response message

    Returns:
        Tuple of (prompt_tokens, completion_tokens)
    """
    if not hasattr(response, 'response_metadata'):
        return (0, 0)

    metadata = response.response_metadata

    # OpenAI format
    if 'token_usage' in metadata:
        return (
            metadata['token_usage'].get('prompt_tokens', 0),
            metadata['token_usage'].get('completion_tokens', 0)
        )

    # Anthropic format
    if 'usage' in metadata:
        return (
            metadata['usage'].get('input_tokens', 0),
            metadata['usage'].get('output_tokens', 0)
        )

    # Ollama format
    if 'prompt_eval_count' in metadata:
        return (
            metadata.get('prompt_eval_count', 0),
            metadata.get('eval_count', 0)
        )

    return (0, 0)


def extract_completion_duration(response: AIMessage) -> float:
    """
    Extract completion generation duration from LLM response metadata.

    For Ollama: Uses eval_duration (nanoseconds) which is completion-only time.
    For OpenAI/Anthropic: Falls back to total invoke duration.

    Args:
        response: AI response message

    Returns:
        Duration in seconds, or 0 if not available
    """
    if not hasattr(response, 'response_metadata'):
        return 0.0

    metadata = response.response_metadata

    # Ollama format - eval_duration is completion-only time in nanoseconds
    if 'eval_duration' in metadata:
        nanoseconds = metadata.get('eval_duration', 0)
        return nanoseconds / 1_000_000_000.0

    # Fallback to total invoke duration for OpenAI/Anthropic
    return metadata.get('invoke_duration_seconds', 0.0)


def extract_total_duration(response: AIMessage) -> float:
    """
    Extract total LLM invocation duration (prompt processing + completion generation).

    For Ollama: Uses total_duration or sum of prompt_eval_duration + eval_duration.
    For OpenAI/Anthropic: Uses invoke_duration_seconds.

    Args:
        response: AI response message

    Returns:
        Duration in seconds, or 0 if not available
    """
    if not hasattr(response, 'response_metadata'):
        return 0.0

    metadata = response.response_metadata

    # Ollama format - use total_duration if available
    if 'total_duration' in metadata:
        nanoseconds = metadata.get('total_duration', 0)
        return nanoseconds / 1_000_000_000.0

    # Ollama fallback - sum prompt_eval_duration + eval_duration
    if 'prompt_eval_duration' in metadata and 'eval_duration' in metadata:
        prompt_ns = metadata.get('prompt_eval_duration', 0)
        eval_ns = metadata.get('eval_duration', 0)
        return (prompt_ns + eval_ns) / 1_000_000_000.0

    # OpenAI/Anthropic - use invoke_duration_seconds
    return metadata.get('invoke_duration_seconds', 0.0)


def calculate_tokens_per_second(tokens: int, duration: float) -> float:
    """
    Calculate tokens per second.

    Args:
        tokens: Number of tokens
        duration: Duration in seconds

    Returns:
        Tokens per second, or 0 if duration is 0
    """
    if duration <= 0:
        return 0.0

    return tokens / duration
