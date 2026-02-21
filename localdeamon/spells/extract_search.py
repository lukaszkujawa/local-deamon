"""Extract search results spell: Converts raw JSON search results to clean Markdown."""

import json
from langchain_core.messages import HumanMessage
from localdeamon.spell import spell
from localdeamon.prompt import Prompt
from localdeamon.llm import get_llm
from localdeamon.console import _normalize_content
from localdeamon import console as c
from localdeamon.prompt_logger import invoke_with_logging


@spell
def extract_search_results(daemon, search_results_json: str) -> str:
    """
    Extract and summarize search results using daemon's context.

    Args:
        daemon: Daemon instance with full conversation context
        search_results_json: Raw JSON search results

    Returns:
        Clean Markdown summary of search results
    """
    try:
        search_data = json.loads(search_results_json)
        search_query = search_data.get("query", "unknown")

        prompt = Prompt.load("EXTRACT_WEBSEARCH")
        rendered = prompt.render(
            search_query=search_query,
            websearch_results=search_results_json
        )

        messages = [daemon.ctx.messages[1], HumanMessage(content=rendered)]
        resp = invoke_with_logging(get_llm(), messages)

        return _normalize_content(resp.content)

    except json.JSONDecodeError:
        return search_results_json
    except Exception as e:
        c.warning(f"Failed to extract search results: {e}")
        return search_results_json
