"""Extract web document post-processor: Converts raw fetched web content to clean Markdown."""

import json
from langchain_core.messages import HumanMessage
from localdeamon.post_processor import post_processor
from localdeamon.prompt import Prompt
from localdeamon.llm import get_llm
from localdeamon.console import _normalize_content
from localdeamon import console as c
from localdeamon.prompt_logger import invoke_with_logging


@post_processor
def extract_web_doc(daemon, fetch_result_json: str) -> str:
    """
    Extract and summarize web document content using daemon's context.

    Args:
        daemon: Daemon instance with full conversation context
        fetch_result_json: Raw JSON from fetch tool containing URL and content

    Returns:
        Clean Markdown summary of web document
    """
    try:
        fetch_data = json.loads(fetch_result_json)
        document_url = fetch_data.get("url", "unknown")
        document_content = fetch_data.get("content", "")

        prompt = Prompt.load("EXTRACT_WEBDOC")
        rendered = prompt.render(
            url=document_url,
            webdoc=document_content
        )

        messages = [daemon.ctx.messages[1], HumanMessage(content=rendered)]
        resp = invoke_with_logging(get_llm(), messages)

        return _normalize_content(resp.content)

    except json.JSONDecodeError:
        return fetch_result_json
    except Exception as e:
        c.warning(f"Failed to extract web document: {e}")
        return fetch_result_json
