import asyncio
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ModelIntelligence(BaseModel):
    name: str
    provider: str
    best_for: List[str] # e.g. ["coding", "reasoning", "fast", "multimodal"]
    is_free: bool
    quota_info: str
    priority: int # Lower is better

# Hardcoded initial intelligence based on research
DEFAULT_INTELLIGENCE = [
    # Groq - Speed Kings
    ModelIntelligence(name="llama-3.3-70b-versatile", provider="groq", best_for=["reasoning", "general", "fast"], is_free=True, quota_info="1000 RPD, 100K TPD", priority=1),
    ModelIntelligence(name="mixtral-8x7b-32768", provider="groq", best_for=["fast", "long-context"], is_free=True, quota_info="14400 RPD, 500K TPD", priority=2),

    # SambaNova - High Throughput
    ModelIntelligence(name="Meta-Llama-3.1-405B-Instruct", provider="sambanova", best_for=["complex-reasoning", "coding"], is_free=True, quota_info="200K TPD (Developer Tier)", priority=1),
    ModelIntelligence(name="DeepSeek-V3.1", provider="sambanova", best_for=["coding", "reasoning"], is_free=True, quota_info="12000 RPD", priority=2),

    # Cerebras - Extreme Speed
    ModelIntelligence(name="llama3.1-70b", provider="cerebras", best_for=["fast", "real-time"], is_free=True, quota_info="1M TPD", priority=1),

    # GitHub Models - Coding Focused
    ModelIntelligence(name="gpt-4o", provider="github", best_for=["coding", "architectural-design"], is_free=True, quota_info="8K TPM (Free)", priority=2),
    ModelIntelligence(name="Phi-3.5-MoE-instruct", provider="github", best_for=["logic", "efficient"], is_free=True, quota_info="Unlimited (Free Beta)", priority=3),

    # Google - Multimodal & Large Context
    ModelIntelligence(name="gemini-2.0-flash", provider="google", best_for=["multimodal", "fast", "general"], is_free=True, quota_info="15 RPM (Free)", priority=3),
    ModelIntelligence(name="gemini-1.5-pro", provider="google", best_for=["reasoning", "large-context"], is_free=True, quota_info="2 RPM (Free)", priority=4),

    # NVIDIA - High End Models
    ModelIntelligence(name="nvidia/llama-3.1-405b-instruct", provider="nvidia", best_for=["complex-reasoning", "benchmarking"], is_free=True, quota_info="Credits based (1000 free)", priority=3),

    # Mistral - Solid Open Models
    ModelIntelligence(name="mistral-large-latest", provider="mistral", best_for=["reasoning", "general"], is_free=True, quota_info="Limited free experiment tier", priority=4),
]

class IntelligenceManager:
    def __init__(self):
        self.models: Dict[str, ModelIntelligence] = {m.name: m for m in DEFAULT_INTELLIGENCE}

    def get_best_model(self, task: str, available_providers: List[str]) -> Optional[ModelIntelligence]:
        """Find the best model for a task among available providers."""
        candidates = []
        for m in self.models.values():
            if m.provider in available_providers:
                if task in m.best_for:
                    candidates.append(m)

        if not candidates:
            # Fallback to general models if no task-specific ones found
            for m in self.models.values():
                if m.provider in available_providers and "general" in m.best_for:
                    candidates.append(m)

        if candidates:
            # Sort by priority
            candidates.sort(key=lambda x: x.priority)
            return candidates[0]
        return None

    async def refresh_intelligence(self):
        """Placeholder for background refresh logic (e.g., fetching from a remote JSON)."""
        logger.info("Refreshing LLM intelligence data in background...")
        # In a real-world scenario, you'd fetch from a URL here.
        await asyncio.sleep(1)
        logger.info("Intelligence data updated.")

intelligence_manager = IntelligenceManager()
