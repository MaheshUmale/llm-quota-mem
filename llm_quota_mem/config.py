import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Dict, Any, List
from pathlib import Path
from ruamel.yaml import YAML

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    # LLM Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    SAMBANOVA_API_KEY: Optional[str] = None
    TOGETHER_API_KEY: Optional[str] = None

    # Base URLs
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    SAMBANOVA_BASE_URL: str = "https://api.sambanova.ai/v1"
    TOGETHER_BASE_URL: str = "https://api.together.xyz/v1"

    # Memory & Cache
    CACHE_DIR: str = ".llm_cache"
    MEMORY_DIR: str = ".llm_memory"

    # Defaults
    DEFAULT_MODEL: str = "gpt-4o-mini"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 4096

settings = Settings()

def load_yaml_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    yaml = YAML(typ="safe")
    path = Path(config_path)
    if path.exists():
        with open(path, "r") as f:
            return yaml.load(f) or {}
    return {}

# Ensure directories exist
Path(settings.CACHE_DIR).mkdir(exist_ok=True)
Path(settings.MEMORY_DIR).mkdir(exist_ok=True)
