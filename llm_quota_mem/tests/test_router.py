import pytest
from llm_quota_mem.router import LLMRouter, LLMRequest, Message

@pytest.mark.asyncio
async def test_router_no_providers():
    router = LLMRouter()
    # Mock providers to be empty
    router.providers = {}

    with pytest.raises(Exception) as excinfo:
        await router.call(LLMRequest(messages=[Message(role="user", content="hi")]))
    assert "All providers failed" in str(excinfo.value)
    await router.close()

def test_rank_providers():
    router = LLMRouter()
    # Rank should return list sorted by priority
    ranked = router._rank_providers()
    if ranked:
        priorities = [p.priority for p in ranked]
        assert priorities == sorted(priorities)
