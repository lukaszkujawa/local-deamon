import os
from dataclasses import dataclass
from pathlib import Path
from functools import lru_cache, cached_property
from typing import Optional



API_BASE_VARS = {
    'ollama': 'OLLAMA_API_BASE',
}


def _load_dotenv_once() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env", override=True)


@dataclass(frozen=True)
class Config:
    agent_llm_model: str
    session_name: str
    prompt_logging: bool
    max_tokens: int

    @cached_property
    def provider(self) -> str:
        return self.agent_llm_model.split('/')[0] if '/' in self.agent_llm_model else 'openai'

    @cached_property
    def model_name(self) -> str:
        return self.agent_llm_model.split('/', 1)[1] if '/' in self.agent_llm_model else self.agent_llm_model

    def get_api_key(self, provider: Optional[str] = None) -> Optional[str]:
        provider = provider or self.provider
        return os.getenv(f"{provider.upper()}_API_KEY")

    def get_base_url(self, provider: Optional[str] = None) -> Optional[str]:
        provider = provider or self.provider
        return os.getenv(f"{provider.upper()}_BASE_URL")

    def get_provider_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return os.getenv(f"{self.provider.upper()}_{key.upper()}", default)

    def get_temperature(self) -> float:
        temp = self.get_provider_config("TEMPERATURE", "0.7")
        return float(temp)

    def get_num_ctx(self) -> Optional[int]:
        ctx = self.get_provider_config("NUM_CTX")
        return int(ctx) if ctx else None

    def get_num_batch(self) -> Optional[int]:
        batch = self.get_provider_config("NUM_BATCH")
        return int(batch) if batch else None

    def get_num_gpu(self) -> Optional[int]:
        gpu = self.get_provider_config("NUM_GPU")
        return int(gpu) if gpu else None

    def get_scraper_url(self) -> str:
        return os.getenv("HOST_GET_URL", "http://127.0.0.1:8000")

    def get_search_url(self) -> str:
        return os.getenv("HOST_WEB_SEARCH", "http://127.0.0.1:8001")

    def get_workspace_dir(self) -> str:
        return os.getenv("WORKSPACE_DIR", "./workspace")

    def setup_llm(self) -> str:
        api_key = self.get_api_key()
        if api_key:
            os.environ[f"{self.provider.upper()}_API_KEY"] = api_key

        base_url = self.get_base_url()
        if base_url:
            env_var = API_BASE_VARS.get(self.provider, f"{self.provider.upper()}_BASE_URL")
            os.environ[env_var] = base_url

        return self.agent_llm_model

    @classmethod
    def from_env(cls) -> "Config":
        _load_dotenv_once()
        return cls(
            agent_llm_model=os.getenv("AGENT_LLM_MODEL", "openai/gpt-4o"),
            session_name=os.getenv("SESSION_NAME", "default"),
            prompt_logging=os.getenv("PROMPT_LOGGING", "false").lower() == "true",
            max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
        )


@lru_cache(maxsize=1)
def get_config() -> Config:
    return Config.from_env()


def reload_config() -> Config:
    get_config.cache_clear()
    return get_config()


config = get_config()
