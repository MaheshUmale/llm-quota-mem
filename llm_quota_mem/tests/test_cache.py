import pytest
from llm_quota_mem.cache import ResponseCache

@pytest.mark.asyncio
async def test_cache(tmp_path):
    from llm_quota_mem.config import settings
    settings.CACHE_DIR = str(tmp_path / "cache")

    cache = ResponseCache()
    prompt = "Test prompt"
    model = "test-model"
    response = "Test response"

    assert await cache.get(prompt, model) is None
    await cache.set(prompt, model, response)
    assert await cache.get(prompt, model) == response
