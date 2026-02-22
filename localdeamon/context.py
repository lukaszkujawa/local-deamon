from localdeamon.prompt import Prompt
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, BaseMessage
from datetime import datetime
import os
from typing import List, Dict, Any
import json
from copy import deepcopy
from localdeamon.tool_response import ToolResponse


def _trim_large_tool_args(tool_calls: List[Dict[str, Any]], max_length: int = 100) -> List[Dict[str, Any]]:
    """
    Trim large arguments in tool calls to reduce context bloat.

    Specifically targets 'content' parameter in write tool calls,
    but can be extended to other large parameters.

    Args:
        tool_calls: List of tool call dictionaries
        max_length: Maximum length for trimmed parameters

    Returns:
        New list of tool calls with large args trimmed
    """
    if not tool_calls:
        return tool_calls

    trimmed_calls = []
    for call in tool_calls:
        call_copy = deepcopy(call)

        if 'args' in call_copy and isinstance(call_copy['args'], dict):
            args = call_copy['args']

            if 'content' in args and isinstance(args['content'], str):
                content = args['content']
                if len(content) > max_length:
                    trimmed = content[:max_length] + f"... ({len(content) - max_length} more chars)"
                    call_copy['args']['content'] = trimmed

        trimmed_calls.append(call_copy)

    return trimmed_calls


class Context:

    def __init__(self):
        now = datetime.now().strftime("%a %d %b %Y, %H:%M:%S")

        system_msg = Prompt.load("SYSTEM").render(time=now, dir=os.getcwd())
        self.messages: List[BaseMessage] = [SystemMessage(content=system_msg)]

    def add_user_message(self, message: str):
        """Add a user/human message to the context"""
        self.messages.append(HumanMessage(content=message))

    def add_ai_message(self, message: AIMessage):
        """
        Add an AI message to the context.

        Trims large tool call arguments (like write content) to prevent
        context bloat while preserving tool call structure.
        """
        if message.tool_calls:
            message_copy = message.copy(deep=True)
            message_copy.tool_calls = _trim_large_tool_args(message.tool_calls)
            self.messages.append(message_copy)
        else:
            self.messages.append(message)

    def add_tool_message(self, tool_call_id: str, content: str):
        """
        Add a tool execution result to the context.

        If content is a ToolResponse, extracts tool_name and preserves it
        in the ToolMessage.name field for later inspection.
        """
        tool_name = None
        if isinstance(content, ToolResponse):
            tool_name = content.tool_name

        self.messages.append(ToolMessage(
            content=str(content),
            tool_call_id=tool_call_id,
            name=tool_name
        ))

    def size_kb(self) -> float:
        """Calculate approximate size of context in kilobytes"""
        try:
            total_chars = 0
            for msg in self.messages:
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

            return (total_chars * 1.5) / 1024
        except Exception:
            return 0.0

    @classmethod
    def fromPrompt(cls, prompt: Prompt, **kwargs):
        ctx = cls()
        ctx.add_user_message(prompt.render(**kwargs))
        return ctx

    def clean_up(self):
        '''
        print("=====")
        for msg in self.messages:
            print(msg)
            print("-----")
        print("=====")
        '''