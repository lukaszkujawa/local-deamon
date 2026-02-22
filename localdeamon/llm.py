from typing import Optional
from functools import lru_cache
from langchain_core.language_models import BaseChatModel
from localdeamon.config import get_config, Config
from localdeamon import console as c


_llm_instance: Optional[BaseChatModel] = None
_bound_llm_instance: Optional[BaseChatModel] = None


def _create_ollama_llm(config: Config) -> BaseChatModel:
    """Create an Ollama LLM instance"""
    from langchain_ollama import ChatOllama

    kwargs = {
        "model": config.model_name,
        "temperature": config.get_temperature(),
    }

    base_url = config.get_base_url()
    if base_url:
        kwargs["base_url"] = base_url

    num_ctx = config.get_num_ctx()
    if num_ctx:
        kwargs["num_ctx"] = num_ctx

    num_batch = config.get_num_batch()
    if num_batch:
        kwargs["num_batch"] = num_batch

    num_gpu = config.get_num_gpu()
    if num_gpu:
        kwargs["num_gpu"] = num_gpu

    c.info(f"🤖 [LLM] Provider: Ollama | Model: {config.model_name} | Temperature: {kwargs['temperature']} | Num CTX: {num_ctx or 'default'} | Num GPU: {num_gpu or 'default'} | Base URL: {base_url or 'default'}")

    return ChatOllama(**kwargs)


def _create_openai_llm(config: Config) -> BaseChatModel:
    """Create an OpenAI LLM instance"""
    from langchain_openai import ChatOpenAI

    kwargs = {
        "model": config.model_name,
        "temperature": config.get_temperature(),
        "max_tokens": config.max_tokens,
    }

    api_key = config.get_api_key()
    if api_key:
        kwargs["api_key"] = api_key

    base_url = config.get_base_url()
    if base_url:
        kwargs["base_url"] = base_url

    c.info(f"🤖 [LLM] Provider: OpenAI | Model: {config.model_name} | Temperature: {kwargs['temperature']} | Max Tokens: {kwargs['max_tokens']}")

    return ChatOpenAI(**kwargs)


def _create_anthropic_llm(config: Config) -> BaseChatModel:
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

    c.info(f"🤖 [LLM] Provider: Anthropic | Model: {config.model_name} | Temperature: {kwargs['temperature']} | Max Tokens: {kwargs['max_tokens']}")

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
    global _bound_llm_instance
    from localdeamon.config import reload_config
    reload_config()
    _bound_llm_instance = None
    return get_llm(force_reload=True)


def get_bound_llm(force_reload: bool = False) -> BaseChatModel:
    """
    Get or create a tool-bound LLM instance.

    This function caches the bound LLM to avoid recreating it on every Daemon instance.
    The bound LLM includes all registered tools and is ready for agentic execution.

    Args:
        force_reload: If True, recreate the bound LLM instance

    Returns:
        BaseChatModel: LLM instance with tools bound
    """
    global _bound_llm_instance

    if _bound_llm_instance is not None and not force_reload:
        return _bound_llm_instance

    from localdeamon.tool_registry import Tool

    base_llm = get_llm(force_reload=force_reload)
    _bound_llm_instance = base_llm.bind_tools(Tool.all())
    return _bound_llm_instance
