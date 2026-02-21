from typing import Optional
from functools import lru_cache
from langchain_core.language_models import BaseChatModel
from localdeamon.config import get_config


_llm_instance: Optional[BaseChatModel] = None


def _create_ollama_llm(config) -> BaseChatModel:
    """Create an Ollama LLM instance"""
    from langchain_ollama import ChatOllama

    kwargs = {
        "model": config.model_name,
        "temperature": config.get_temperature(),
    }

    # Add base URL if configured
    base_url = config.get_base_url()
    if base_url:
        kwargs["base_url"] = base_url

    # Add Ollama-specific parameters if configured
    num_ctx = config.get_num_ctx()
    if num_ctx:
        kwargs["num_ctx"] = num_ctx

    num_batch = config.get_num_batch()
    if num_batch:
        kwargs["num_batch"] = num_batch

    return ChatOllama(**kwargs)


def _create_openai_llm(config) -> BaseChatModel:
    """Create an OpenAI LLM instance"""
    from langchain_openai import ChatOpenAI

    kwargs = {
        "model": config.model_name,
        "temperature": config.get_temperature(),
        "max_tokens": config.max_tokens,
    }

    # Add API key if configured
    api_key = config.get_api_key()
    if api_key:
        kwargs["api_key"] = api_key

    # Add base URL if configured (for OpenAI-compatible APIs)
    base_url = config.get_base_url()
    if base_url:
        kwargs["base_url"] = base_url

    return ChatOpenAI(**kwargs)


def _create_anthropic_llm(config) -> BaseChatModel:
    """Create an Anthropic LLM instance"""
    from langchain_anthropic import ChatAnthropic

    kwargs = {
        "model": config.model_name,
        "temperature": config.get_temperature(),
        "max_tokens": config.max_tokens,
    }

    # Add API key if configured
    api_key = config.get_api_key()
    if api_key:
        kwargs["api_key"] = api_key

    return ChatAnthropic(**kwargs)


def get_llm(force_reload: bool = False) -> BaseChatModel:
    """
    Get or create the LLM instance based on configuration.

    Supports multiple providers:
    - ollama: Local Ollama models (e.g., "ollama/gpt-oss:20b")
    - openai: OpenAI models (e.g., "openai/gpt-4o-mini")
    - anthropic: Anthropic models (e.g., "anthropic/claude-3-5-sonnet-20241022")

    Args:
        force_reload: If True, recreate the LLM instance

    Returns:
        BaseChatModel: The configured LLM instance

    Raises:
        ValueError: If the provider is not supported
    """
    global _llm_instance

    if _llm_instance is not None and not force_reload:
        return _llm_instance

    config = get_config()
    provider = config.provider.lower()

    # Provider factory mapping
    provider_factories = {
        "ollama": _create_ollama_llm,
        "openai": _create_openai_llm,
        "anthropic": _create_anthropic_llm,
    }

    if provider not in provider_factories:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: {', '.join(provider_factories.keys())}"
        )

    _llm_instance = provider_factories[provider](config)
    return _llm_instance


def reload_llm() -> BaseChatModel:
    """Reload the LLM instance with fresh configuration"""
    from localdeamon.config import reload_config
    reload_config()
    return get_llm(force_reload=True)
