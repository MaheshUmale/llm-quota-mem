import pytest
import httpx
from llm_quota_mem.router import LLMRouter, LLMRequest, Message, ProviderConfig

@pytest.mark.asyncio
async def test_router_auto_switch_on_error(respx_mock):
    router = LLMRouter()

    # Configure two providers
    router.providers = {
        "p1": ProviderConfig(name="p1", base_url="http://p1.com", api_key="k1", models=["m1"], priority=1),
        "p2": ProviderConfig(name="p2", base_url="http://p2.com", api_key="k2", models=["m2"], priority=2)
    }

    # Mock p1 to return 429 (Rate Limit)
    respx_mock.post("http://p1.com/chat/completions").return_value = httpx.Response(429, json={"error": "rate limit"})

    # Mock p2 to return success
    respx_mock.post("http://p2.com/chat/completions").return_value = httpx.Response(200, json={
        "choices": [{"message": {"content": "Success from p2"}}]
    })

    response = await router.call(LLMRequest(messages=[Message(role="user", content="hi")], model="m1"))

    assert response == "Success from p2"
    assert router.providers["p1"].healthy is False
    assert router.providers["p2"].healthy is True

    await router.close()
