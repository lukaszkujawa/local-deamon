
from typing import Tuple
from langchain_core.messages import AIMessage


def estimate_tokens(text: str) -> int:
    if not text:
        return 0

    return max(1, len(text) // 4)


def format_tokens(count: int) -> str:
    if count >= 1000:
        return f"{count/1000:.1f}K tokens"
    return f"{count} tokens"


def extract_token_usage(response: AIMessage) -> Tuple[int, int]:
    if not hasattr(response, 'response_metadata'):
        return (0, 0)

    metadata = response.response_metadata


    if 'token_usage' in metadata:
        return (
            metadata['token_usage'].get('prompt_tokens', 0),
            metadata['token_usage'].get('completion_tokens', 0)
        )


    if 'usage' in metadata:
        return (
            metadata['usage'].get('input_tokens', 0),
            metadata['usage'].get('output_tokens', 0)
        )


    if 'prompt_eval_count' in metadata:
        return (
            metadata.get('prompt_eval_count', 0),
            metadata.get('eval_count', 0)
        )

    return (0, 0)


def extract_completion_duration(response: AIMessage) -> float:
    if not hasattr(response, 'response_metadata'):
        return 0.0

    metadata = response.response_metadata


    if 'eval_duration' in metadata:
        nanoseconds = metadata.get('eval_duration', 0)
        return nanoseconds / 1_000_000_000.0


    return metadata.get('invoke_duration_seconds', 0.0)


def extract_total_duration(response: AIMessage) -> float:
    if not hasattr(response, 'response_metadata'):
        return 0.0

    metadata = response.response_metadata


    if 'total_duration' in metadata:
        nanoseconds = metadata.get('total_duration', 0)
        return nanoseconds / 1_000_000_000.0


    if 'prompt_eval_duration' in metadata and 'eval_duration' in metadata:
        prompt_ns = metadata.get('prompt_eval_duration', 0)
        eval_ns = metadata.get('eval_duration', 0)
        return (prompt_ns + eval_ns) / 1_000_000_000.0


    return metadata.get('invoke_duration_seconds', 0.0)


def calculate_tokens_per_second(tokens: int, duration: float) -> float:
    if duration <= 0:
        return 0.0

    return tokens / duration
