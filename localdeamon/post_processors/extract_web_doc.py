"""Extract web document post-processor: Converts raw fetched web content to clean Markdown."""

import json
import os
import random
import string
from pathlib import Path
from typing import Optional

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from localdeamon.post_processor import post_processor
from localdeamon.prompt import Prompt
from localdeamon.llm import get_llm
from localdeamon.console import _normalize_content
from localdeamon import console as c
from localdeamon.prompt_logger import invoke_with_logging


class WebDocumentExtraction(BaseModel):
    filename: str = Field(description="Short descriptive filename without extension, e.g., 'github-copilot-statistics'")
    title: str = Field(description="Informative title for the document")
    summary: str = Field(description="Concise 1-2 sentence summary of the document content")
    quick_extract: str = Field(description="5-10 key bullet points for immediate context. Prioritize facts most relevant to user task. Include critical numbers, dates, metrics.")
    detailed_content: str = Field(description="Comprehensive extraction organized by sections. Preserve important details, statistics, examples, code snippets. Use Markdown headings (###) for sections. Be thorough but organized.")
    problems: Optional[str] = Field(default=None, description="Issues like missing data, paywall, blocked, wrong page, etc. None if no problems.")


def _generate_random_suffix(length: int = 4) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def _save_document_details(filename: str, title: str, url: str, detailed_content: str, problems: Optional[str]) -> str:
    suffix = _generate_random_suffix()
    safe_filename = f"{filename}-{suffix}.md"
    filepath = Path(safe_filename)

    if filepath.exists():
        suffix = _generate_random_suffix()
        safe_filename = f"{filename}-{suffix}.md"
        filepath = Path(safe_filename)

    content_parts = [
        f"# {title}\n",
        f"**Source:** {url}\n",
        f"\n{detailed_content}\n" if detailed_content.strip() else "\n_No content extracted._\n"
    ]

    if problems:
        content_parts.append(f"\n## Problems\n{problems}\n")

    full_content = "\n".join(content_parts)

    filepath.write_text(full_content, encoding="utf-8")
    c.info(f"Saved document details to: {safe_filename}")

    return safe_filename


@post_processor
def extract_web_doc(daemon, fetch_result_json: str) -> str:
    """
    Extract and summarize web document content using daemon's context.
    Keeps only Document Info in context, saves details to workspace file.

    Args:
        daemon: Daemon instance with full conversation context
        fetch_result_json: Raw JSON from fetch tool containing URL and content

    Returns:
        Compact Markdown with Document Info section only
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
        llm_with_structure = get_llm().with_structured_output(WebDocumentExtraction)

        extraction = llm_with_structure.invoke(messages)

        if hasattr(extraction, 'content'):
            c.warning("Structured output returned AIMessage instead of model - this shouldn't happen")
            raise ValueError("Expected WebDocumentExtraction model, got AIMessage")

        saved_filename = _save_document_details(
            extraction.filename,
            extraction.title,
            document_url,
            extraction.detailed_content,
            extraction.problems
        )

        doc_info = [
            "## Document added to your workspace",
            f"- *Filename:* {saved_filename}",
            f"- *Title:* {extraction.title}",
            f"- *Summary:* {extraction.summary}",
            f"- *Source:* {document_url}"
        ]

        return "\n".join(doc_info)

    except json.JSONDecodeError:
        return fetch_result_json
    except Exception as e:
        c.warning(f"Failed to extract web document: {e}")
        return fetch_result_json
