from localdeamon.prompt import Prompt
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, BaseMessage
from datetime import datetime
import os
from typing import List


class Context:

    def __init__(self):
        now = datetime.now().strftime("%a %d %b %Y, %H:%M:%S")

        system_msg = Prompt.load("SYSTEM").render(time=now, dir=os.getcwd())
        self.messages: List[BaseMessage] = [SystemMessage(content=system_msg)]

    def add_user_message(self, message: str):
        """Add a user/human message to the context"""
        self.messages.append(HumanMessage(content=message))

    def add_ai_message(self, message: AIMessage):
        """Add an AI message to the context"""
        self.messages.append(message)

    def add_tool_message(self, tool_call_id: str, content: str):
        """Add a tool execution result to the context"""
        self.messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))

    @classmethod
    def fromPrompt(cls, prompt: Prompt, **kwargs):
        ctx = cls()
        ctx.add_user_message(prompt.render(**kwargs))
        return ctx
