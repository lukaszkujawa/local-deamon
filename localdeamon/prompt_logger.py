"""Prompt and response logging utilities for debugging and analysis."""

import json
from datetime import datetime
from pathlib import Path
from typing import List
from langchain_core.messages import BaseMessage, AIMessage
from localdeamon.config import get_config


def _serialize_message(message: BaseMessage) -> dict:
    """
    Serialize a LangChain message to a dictionary.

    Args:
        message: Message to serialize

    Returns:
        Dictionary representation of the message
    """
    result = {
        "type": message.__class__.__name__,
        "content": message.content,
    }

    # Add additional_kwargs if present
    if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
        result["additional_kwargs"] = message.additional_kwargs

    # Add tool_calls if present (for AIMessage)
    if hasattr(message, 'tool_calls') and message.tool_calls:
        result["tool_calls"] = message.tool_calls

    # Add tool_call_id if present (for ToolMessage)
    if hasattr(message, 'tool_call_id'):
        result["tool_call_id"] = message.tool_call_id

    return result


def _serialize_messages(messages: List[BaseMessage]) -> str:
    """
    Serialize a list of messages to formatted JSON.

    Args:
        messages: List of messages to serialize

    Returns:
        Pretty-printed JSON string
    """
    serialized = [_serialize_message(msg) for msg in messages]
    return json.dumps(serialized, indent=2, ensure_ascii=False)


def _serialize_response(response: AIMessage) -> str:
    """
    Serialize an AI response to formatted JSON.

    Args:
        response: AI response message

    Returns:
        Pretty-printed JSON string
    """
    return json.dumps(_serialize_message(response), indent=2, ensure_ascii=False)


def log_prompt_and_response(messages: List[BaseMessage], response: AIMessage) -> None:
    """
    Log prompt messages and LLM response to timestamped files.

    Creates files in logs/prompt/ directory:
    - dd-mm-YYYY-HH-MM-ss-prompt.log (contains serialized prompt messages)
    - dd-mm-YYYY-HH-MM-ss-response.log (contains serialized response)

    Only logs if PROMPT_LOGGING=true in .env configuration.

    Args:
        messages: List of prompt messages sent to LLM
        response: Response received from LLM
    """
    config = get_config()

    if not config.prompt_logging:
        return

    # Create logs/prompt directory if it doesn't exist
    log_dir = Path("logs") / "prompt"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp-based filename: dd-mm-YYYY-HH-MM-ss
    timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")

    # Write prompt
    prompt_file = log_dir / f"{timestamp}-prompt.log"
    prompt_file.write_text(_serialize_messages(messages), encoding="utf-8")

    # Write response
    response_file = log_dir / f"{timestamp}-response.log"
    response_file.write_text(_serialize_response(response), encoding="utf-8")


def invoke_with_logging(llm, messages: List[BaseMessage]) -> AIMessage:
    """
    Invoke LLM with automatic prompt and response logging.

    Args:
        llm: LangChain LLM instance
        messages: Messages to send to LLM

    Returns:
        AI response message
    """
    response = llm.invoke(messages)
    log_prompt_and_response(messages, response)
    return response
