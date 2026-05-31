import httpx
import logging
import asyncio
import hashlib
from typing import List, Optional, Dict
from .config import settings

logger = logging.getLogger(__name__)

# Simple in-memory cache for embeddings to avoid 429s on repeat strings
_EMBEDDING_CACHE: Dict[str, List[float]] = {}

class Embedder:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def embed_text(self, text: str) -> List[float]:
        # Check cache first
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in _EMBEDDING_CACHE:
            return _EMBEDDING_CACHE[cache_key]

        # Priority: OpenAI > Google
        vector = None

        # Try providers with retry logic
        providers = []
        if settings.OPENAI_API_KEY:
            providers.append(("openai", self._embed_openai))
        if settings.GOOGLE_API_KEY:
            providers.append(("google", self._embed_google))

        for name, func in providers:
            try:
                vector = await func(text)
                if vector:
                    break
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Embedding provider {name} rate limited (429). Trying next...")
                    continue
                logger.error(f"Embedding provider {name} error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error with embedding provider {name}: {e}")
                continue

        if vector:
            # Ensure consistent 1536 dimensions
            if len(vector) < 1536:
                vector = vector + [0.0] * (1536 - len(vector))
            elif len(vector) > 1536:
                vector = vector[:1536]

            # Cache result
            _EMBEDDING_CACHE[cache_key] = vector
            return vector

        # Fallback to a zero-vector if no provider is available (to not crash)
        logger.warning("No embedding provider configured. Returning zero vector.")
        return [0.0] * 1536

    async def _embed_openai(self, text: str) -> List[float]:
        url = f"{settings.OPENAI_BASE_URL}/embeddings"
        headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
        payload = {"input": text, "model": "text-embedding-3-small"}

        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]

    async def _embed_google(self, text: str) -> List[float]:
        # Google uses a different endpoint structure for embeddings
        # Using gemini-embedding-001 as text-embedding-004 is deprecated and returns 404 in v1beta
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-embedding-001:embedContent?key={settings.GOOGLE_API_KEY}"
        payload = {"content": {"parts": [{"text": text}]}}

        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        # gemini-embedding-001 returns 768 dimensions.
        return response.json()["embedding"]["values"]

    async def close(self):
        await self.client.aclose()
