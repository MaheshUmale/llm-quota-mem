import pytest
from llm_quota_mem.cache import ResponseCache

def test_cache(tmp_path):
    import os
    from llm_quota_mem.config import settings
    settings.CACHE_DIR = str(tmp_path / "cache")

    cache = ResponseCache()
    prompt = "Test prompt"
    model = "test-model"
    response = "Test response"

    assert cache.get(prompt, model) is None
    cache.set(prompt, model, response)
    assert cache.get(prompt, model) == response
