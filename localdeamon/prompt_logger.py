
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Any, Dict
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_core.language_models import BaseChatModel
from localdeamon.config import get_config
from localdeamon.token_utils import estimate_tokens, format_tokens
from localdeamon import console as c


def _get_project_root() -> Path:

    return Path(__file__).parent.parent


def _message_to_dict(message: BaseMessage) -> Dict:
    msg_dict = message.model_dump(exclude_none=True)


    msg_dict.pop('response_metadata', None)
    msg_dict.pop('id', None)


    essential = {
        'type': msg_dict.get('type'),
        'content': msg_dict.get('content')
    }


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
    payload = {}


    payload['messages'] = [_message_to_dict(msg) for msg in messages]


    if llm and hasattr(llm, 'kwargs') and 'tools' in llm.kwargs:
        tools = llm.kwargs['tools']
        if tools:
            payload['tools'] = tools


    return json.dumps(payload, indent=2, ensure_ascii=False)


def _serialize_response(response: AIMessage) -> str:

    response_dict = _message_to_dict(response)


    if hasattr(response, 'response_metadata') and response.response_metadata:
        response_dict['response_metadata'] = response.response_metadata


    return json.dumps(response_dict, indent=2, ensure_ascii=False, default=str)


def log_prompt_and_response(messages: List[BaseMessage], response: AIMessage, llm: BaseChatModel = None) -> None:
    config = get_config()

    if not config.prompt_logging:
        return


    project_root = _get_project_root()
    log_dir = project_root / "logs" / "prompt"
    log_dir.mkdir(parents=True, exist_ok=True)


    timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")


    prompt_file = log_dir / f"{timestamp}-prompt.log"
    prompt_file.write_text(_serialize_messages_as_prompt(messages, llm), encoding="utf-8")


    response_file = log_dir / f"{timestamp}-response.log"
    response_file.write_text(_serialize_response(response), encoding="utf-8")


def _estimate_prompt_tokens(messages: List[BaseMessage]) -> int:
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
    prompt_tokens = _estimate_prompt_tokens(messages)
    c.info(f"Prompt: {format_tokens(prompt_tokens)} estimated")

    start_time = time.perf_counter()
    response = llm.invoke(messages)
    elapsed_time = time.perf_counter() - start_time

    if not hasattr(response, 'response_metadata'):
        response.response_metadata = {}
    response.response_metadata['invoke_duration_seconds'] = elapsed_time

    log_prompt_and_response(messages, response, llm)
    return response
