"""Prompt and response logging utilities for debugging and analysis."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Any, Dict
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_core.language_models import BaseChatModel
from localdeamon.config import get_config
from localdeamon.token_utils import estimate_tokens, format_tokens
from localdeamon import console as c


def _get_project_root() -> Path:
    """
    Get the project root directory.

    This ensures logs are written to the project root, not the workspace directory.

    Returns:
        Path to project root
    """
    # Go up from localdeamon/prompt_logger.py to project root
    return Path(__file__).parent.parent


def _message_to_dict(message: BaseMessage) -> Dict:
    """
    Convert a message to dict format as sent to the LLM API.

    Args:
        message: Message to convert

    Returns:
        Dictionary in API format
    """
    msg_dict = message.model_dump(exclude_none=True)

    # Clean up fields that aren't sent to API
    msg_dict.pop('response_metadata', None)
    msg_dict.pop('id', None)

    # Keep only essential fields based on message type
    essential = {
        'type': msg_dict.get('type'),
        'content': msg_dict.get('content')
    }

    # Add type-specific fields
    if 'tool_calls' in msg_dict and msg_dict['tool_calls']:
        essential['tool_calls'] = msg_dict['tool_calls']
    if 'tool_call_id' in msg_dict:
        essential['tool_call_id'] = msg_dict['tool_call_id']
    if 'name' in msg_dict and msg_dict['name']:
        essential['name'] = msg_dict['name']
    if 'additional_kwargs' in msg_dict and msg_dict['additional_kwargs']:
        essential['additional_kwargs'] = msg_dict['additional_kwargs']

    return essential




def _serialize_messages_as_prompt(messages: List[BaseMessage], llm: BaseChatModel = None) -> str:
    """
    Serialize messages EXACTLY as sent to the LLM API.

    This outputs the raw JSON payload that would be sent to the provider,
    with no decorative formatting. Essential for performance tuning.

    Args:
        messages: List of messages to serialize
        llm: LLM instance (to extract bound tools)

    Returns:
        JSON string of exact API payload
    """
    payload = {}

    # Convert messages to API format
    payload['messages'] = [_message_to_dict(msg) for msg in messages]

    # Add tools if bound to LLM
    if llm and hasattr(llm, 'kwargs') and 'tools' in llm.kwargs:
        tools = llm.kwargs['tools']
        if tools:
            payload['tools'] = tools

    # Return as formatted JSON (exact payload)
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _serialize_response(response: AIMessage) -> str:
    """
    Serialize an AI response EXACTLY as received from the LLM API.

    Args:
        response: AI response message

    Returns:
        JSON string of exact API response
    """
    # Convert to dict format
    response_dict = _message_to_dict(response)

    # Add response metadata (token counts, etc.)
    if hasattr(response, 'response_metadata') and response.response_metadata:
        response_dict['response_metadata'] = response.response_metadata

    # Return as formatted JSON (exact response)
    return json.dumps(response_dict, indent=2, ensure_ascii=False, default=str)


def log_prompt_and_response(messages: List[BaseMessage], response: AIMessage, llm: BaseChatModel = None) -> None:
    """
    Log prompt messages and LLM response to timestamped files.

    Creates files in logs/prompt/ directory:
    - dd-mm-YYYY-HH-MM-ss-prompt.log (formatted prompt with tools)
    - dd-mm-YYYY-HH-MM-ss-response.log (formatted response with metadata)

    Only logs if PROMPT_LOGGING=true in .env configuration.

    Args:
        messages: List of prompt messages sent to LLM
        response: Response received from LLM
        llm: LLM instance (to extract tool schemas)
    """
    config = get_config()

    if not config.prompt_logging:
        return

    # Create logs/prompt directory in project root (not workspace)
    project_root = _get_project_root()
    log_dir = project_root / "logs" / "prompt"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp-based filename: dd-mm-YYYY-HH-MM-SS
    timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")

    # Write prompt with tools
    prompt_file = log_dir / f"{timestamp}-prompt.log"
    prompt_file.write_text(_serialize_messages_as_prompt(messages, llm), encoding="utf-8")

    # Write response
    response_file = log_dir / f"{timestamp}-response.log"
    response_file.write_text(_serialize_response(response), encoding="utf-8")


def _estimate_prompt_tokens(messages: List[BaseMessage]) -> int:
    """
    Estimate token count for a list of messages.

    Args:
        messages: Messages to estimate tokens for

    Returns:
        Estimated token count
    """
    total_chars = 0
    for msg in messages:
        if hasattr(msg, 'content'):
            content = msg.content
            if isinstance(content, str):
                total_chars += len(content)
            elif isinstance(content, (list, dict)):
                total_chars += len(json.dumps(content))
            else:
                total_chars += len(str(content))

        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            total_chars += len(json.dumps([tc for tc in msg.tool_calls]))

    return max(1, total_chars // 4)


def invoke_with_logging(llm, messages: List[BaseMessage]) -> AIMessage:
    """
    Invoke LLM with automatic prompt and response logging.

    Args:
        llm: LangChain LLM instance
        messages: Messages to send to LLM

    Returns:
        AI response message
    """
    prompt_tokens = _estimate_prompt_tokens(messages)
    c.info(f"Prompt: {format_tokens(prompt_tokens)} estimated")

    response = llm.invoke(messages)
    log_prompt_and_response(messages, response, llm)
    return response
