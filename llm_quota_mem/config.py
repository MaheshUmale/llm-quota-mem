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
    OPENROUTER_API_KEY: Optional[str] = None
    CEREBRAS_API_KEY: Optional[str] = None
    MISTRAL_API_KEY: Optional[str] = None
    GITHUB_API_KEY: Optional[str] = None
    CLOUDFLARE_API_KEY: Optional[str] = None
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = None
    NVIDIA_API_KEY: Optional[str] = None

    # Base URLs
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    SAMBANOVA_BASE_URL: str = "https://api.sambanova.ai/v1"
    TOGETHER_BASE_URL: str = "https://api.together.xyz/v1"
    CEREBRAS_BASE_URL: str = "https://api.cerebras.ai/v1"
    MISTRAL_BASE_URL: str = "https://api.mistral.ai/v1"
    GITHUB_BASE_URL: str = "https://models.inference.ai.azure.com"
    CLOUDFLARE_BASE_URL: str = "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1"
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    LOCAL_SLM_URL: str = "http://localhost:11434/v1" # Default Ollama/Llama.cpp
    LOCAL_SLM_ENABLED: bool = False

    # Memory & Cache
    CACHE_DIR: str = ".llm_cache"
    MEMORY_DIR: str = ".llm_memory"

    # Defaults
    DEFAULT_MODEL: str = "gpt-4o-mini"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 4096

settings = Settings()

import json

def load_keys_from_json(json_path: str = "keys.json"):
    """Load API keys from a JSON file and update settings."""
    path = Path(json_path)
    if path.exists():
        try:
            with open(path, "r") as f:
                data = json.load(f)
                for entry in data:
                    platform = entry.get("platform", "").upper()
                    api_key = entry.get("api_key")
                    if platform and api_key:
                        env_var = f"{platform}_API_KEY"
                        # Dynamically set on settings if exists
                        if hasattr(settings, env_var):
                            setattr(settings, env_var, api_key)
                        # Also set in os.environ for good measure
                        os.environ[env_var] = api_key

                    # Handle extra fields like account_id for Cloudflare
                    if platform == "CLOUDFLARE" and "extra" in entry:
                        account_id = entry["extra"].get("account_id")
                        if account_id:
                            settings.CLOUDFLARE_ACCOUNT_ID = account_id
                            os.environ["CLOUDFLARE_ACCOUNT_ID"] = account_id
        except Exception as e:
            print(f"Error loading keys from JSON: {e}")

def load_yaml_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    yaml = YAML(typ="safe")
    path = Path(config_path)
    if path.exists():
        with open(path, "r") as f:
            return yaml.load(f) or {}
    return {}

# Attempt to load keys from keys.json if it exists
load_keys_from_json()

# Ensure directories exist
Path(settings.CACHE_DIR).mkdir(exist_ok=True)
Path(settings.MEMORY_DIR).mkdir(exist_ok=True)
