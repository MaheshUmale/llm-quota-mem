import asyncio
import httpx
import logging
import json
import time
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from .config import settings

logger = logging.getLogger(__name__)

class TaskComplexity(str, Enum):
    SIMPLE = "simple"   # Pair programming, one-liners, tool execution (Haiku class)
    DEV = "dev"         # Implementation, debugging, logic (Sonnet class)
    ARCH = "arch"       # Complex architecture, reasoning, tradeoffs (Opus class)

class Message(BaseModel):
    role: str
    content: str

class LLMRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None
    temperature: float = settings.TEMPERATURE
    max_tokens: int = settings.MAX_TOKENS
    stream: bool = False

class ProviderConfig(BaseModel):
    name: str
    base_url: str
    api_key: Optional[str]
    models: List[str]
    priority: int = 10
    healthy: bool = True
    last_failure: float = 0
    failure_count: int = 0

class ComplexityScouter:
    @staticmethod
    def scout(messages: List[Message]) -> TaskComplexity:
        full_text = " ".join([m.content.lower() for m in messages[-2:]])

        arch_keywords = ["architecture", "tradeoff", "system design", "component diagram", "togaf", "c4"]
        dev_keywords = ["implement", "write a", "fix", "debug", "test", "refactor"]

        if any(kw in full_text for kw in arch_keywords):
            return TaskComplexity.ARCH
        if any(kw in full_text for kw in dev_keywords):
            return TaskComplexity.DEV
        return TaskComplexity.SIMPLE

class LLMRouter:
    def __init__(self):
        self.providers: Dict[str, ProviderConfig] = self._init_providers()
        self.scouter = ComplexityScouter()
        self.client = httpx.AsyncClient(timeout=60.0)

    def _init_providers(self) -> Dict[str, ProviderConfig]:
        providers = {}

        if settings.GROQ_API_KEY:
            providers["groq"] = ProviderConfig(
                name="groq",
                base_url=settings.GROQ_BASE_URL,
                api_key=settings.GROQ_API_KEY,
                models=["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
                priority=1
            )

        if settings.SAMBANOVA_API_KEY:
            providers["sambanova"] = ProviderConfig(
                name="sambanova",
                base_url=settings.SAMBANOVA_BASE_URL,
                api_key=settings.SAMBANOVA_API_KEY,
                models=["Meta-Llama-3.1-405B-Instruct", "Meta-Llama-3.1-70B-Instruct"],
                priority=2
            )

        if settings.TOGETHER_API_KEY:
            providers["together"] = ProviderConfig(
                name="together",
                base_url=settings.TOGETHER_BASE_URL,
                api_key=settings.TOGETHER_API_KEY,
                models=["meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo"],
                priority=3
            )

        if settings.GOOGLE_API_KEY:
            providers["google"] = ProviderConfig(
                name="google",
                base_url="https://generativelanguage.googleapis.com/v1beta/openai",
                api_key=settings.GOOGLE_API_KEY,
                models=["gemini-2.0-flash", "gemini-1.5-pro"],
                priority=4
            )

        if settings.OPENROUTER_API_KEY:
            providers["openrouter"] = ProviderConfig(
                name="openrouter",
                base_url=settings.OPENROUTER_BASE_URL,
                api_key=settings.OPENROUTER_API_KEY,
                models=["google/gemini-2.0-flash-001", "anthropic/claude-3.5-sonnet"],
                priority=5
            )

        if settings.OPENAI_API_KEY:
            providers["openai"] = ProviderConfig(
                name="openai",
                base_url=settings.OPENAI_BASE_URL,
                api_key=settings.OPENAI_API_KEY,
                models=["gpt-4o", "gpt-4o-mini"],
                priority=6
            )

        if settings.CEREBRAS_API_KEY:
            providers["cerebras"] = ProviderConfig(
                name="cerebras",
                base_url=settings.CEREBRAS_BASE_URL,
                api_key=settings.CEREBRAS_API_KEY,
                models=["llama3.1-70b", "llama3.1-8b"],
                priority=2 # High speed
            )

        if settings.MISTRAL_API_KEY:
            providers["mistral"] = ProviderConfig(
                name="mistral",
                base_url=settings.MISTRAL_BASE_URL,
                api_key=settings.MISTRAL_API_KEY,
                models=["mistral-large-latest", "pixtral-12b-2409"],
                priority=7
            )

        if settings.GITHUB_API_KEY:
            providers["github"] = ProviderConfig(
                name="github",
                base_url=settings.GITHUB_BASE_URL,
                api_key=settings.GITHUB_API_KEY,
                models=["gpt-4o", "Phi-3.5-MoE-instruct"],
                priority=8
            )

        if settings.CLOUDFLARE_API_KEY and settings.CLOUDFLARE_ACCOUNT_ID:
            base_url = settings.CLOUDFLARE_BASE_URL.format(account_id=settings.CLOUDFLARE_ACCOUNT_ID)
            providers["cloudflare"] = ProviderConfig(
                name="cloudflare",
                base_url=base_url,
                api_key=settings.CLOUDFLARE_API_KEY,
                models=["@cf/meta/llama-3.1-70b-instruct"],
                priority=9
            )

        if settings.NVIDIA_API_KEY:
            providers["nvidia"] = ProviderConfig(
                name="nvidia",
                base_url=settings.NVIDIA_BASE_URL,
                api_key=settings.NVIDIA_API_KEY,
                models=["nvidia/llama-3.1-405b-instruct"],
                priority=5
            )

        if settings.LOCAL_SLM_ENABLED:
            providers["local"] = ProviderConfig(
                name="local",
                base_url=settings.LOCAL_SLM_URL,
                api_key="local-key", # usually ignored
                models=["llama3", "phi3", "mistral"],
                priority=100 # Ultimate fallback
            )

        return providers

    async def _call_provider(self, provider: ProviderConfig, request: LLMRequest) -> Dict[str, Any]:
        url = f"{provider.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json"
        }

        # Use default model if not specified
        payload = request.model_dump(exclude_none=True)
        if not payload.get("model"):
            payload["model"] = provider.models[0]

        logger.debug(f"Calling {provider.name} with model {payload['model']}")

        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def _rank_providers(self, preferred_model: Optional[str] = None, domain: str = "ea") -> List[ProviderConfig]:
        # Filter healthy providers and rank by priority
        now = time.time()
        healthy = []

        for p in self.providers.values():
            if not p.healthy:
                # Cooldown period depends on failure count (exponential backoff for health)
                cooldown = min(300 * (2 ** (p.failure_count - 1)), 3600) # Max 1 hour
                if now - p.last_failure > cooldown:
                    p.healthy = True
                    logger.info(f"Provider {p.name} marked healthy again after cooldown.")

            if p.healthy:
                healthy.append(p)

        # Sort by priority (lower is better)
        def sort_key(p: ProviderConfig):
            score = p.priority
            # Domain-specific optimization: Groq/SambaNova/Cerebras are prioritized for EA due to speed/throughput
            if domain == "ea" and p.name in ["groq", "sambanova", "cerebras"]:
                score -= 5
            elif domain == "coding" and p.name in ["openai", "google", "github"]:
                score -= 2

            # Use preferred model if it matches
            if preferred_model and preferred_model in p.models:
                score -= 10

            return score

        healthy.sort(key=sort_key)
        return healthy

    async def call(self, request: LLMRequest, domain: str = "ea") -> str:
        # ECC-inspired Task Tiering
        complexity = self.scouter.scout(request.messages)
        logger.info(f"Task complexity scouted: {complexity}")

        # Override model if not specified based on complexity to save tokens/quota
        if not request.model:
            if complexity == TaskComplexity.SIMPLE:
                request.model = "gpt-4o-mini" # or haiku if available
            elif complexity == TaskComplexity.DEV:
                request.model = "llama-3.3-70b-versatile"

        providers = self._rank_providers(request.model, domain=domain)

        last_error = None
        for provider in providers:
            try:
                response_data = await self._call_provider(provider, request)
                # Successful call: slowly reduce failure count to recover priority
                if provider.failure_count > 0:
                    provider.failure_count -= 1
                return response_data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limit hit for {provider.name}. Backing off.")
                else:
                    logger.warning(f"Provider {provider.name} returned status {e.response.status_code}")

                provider.healthy = False
                provider.last_failure = time.time()
                provider.failure_count += 1
                last_error = e
                continue
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                provider.healthy = False
                provider.last_failure = time.time()
                provider.failure_count += 1
                last_error = e
                continue

        raise Exception(f"All providers failed. Last error: {last_error}")

    async def close(self):
        await self.client.aclose()
