import httpx
import logging
from typing import List, Optional
from .config import settings

logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def embed_text(self, text: str) -> List[float]:
        # Priority: OpenAI > Google > Groq (if supported)
        if settings.OPENAI_API_KEY:
            return await self._embed_openai(text)
        elif settings.GOOGLE_API_KEY:
            return await self._embed_google(text)
        else:
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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={settings.GOOGLE_API_KEY}"
        payload = {"content": {"parts": [{"text": text}]}}

        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        # Google returns 768 dims by default, we might need to pad/truncate if consistency is needed
        # but for internal use it's fine as long as we stay consistent within one run.
        return response.json()["embedding"]["values"]

    async def close(self):
        await self.client.aclose()
