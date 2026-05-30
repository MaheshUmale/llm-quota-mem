import pytest
import httpx
import respx
from fastapi.testclient import TestClient
from llm_quota_mem.app import app, router

@pytest.mark.asyncio
async def test_e2e_unified_gateway():
    # 1. Setup Mock Provider (e.g., Groq)
    async with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={
                "choices": [{"message": {"role": "assistant", "content": "This is a response from the unified gateway!"}}]
            })
        )

        # 2. Add Provider via Internal logic (simulating UI/config)
        router.add_provider(
            name="groq",
            base_url="https://api.groq.com/openai/v1",
            api_key="mock-key",
            models=["llama-3.3-70b-versatile"]
        )

        # 3. Test using TestClient (Sync for convenience, but calls our async app)
        client = TestClient(app)

        # Verify health
        health_resp = client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["providers"]["groq"] is True

        # 4. Verify Chat Completion
        chat_payload = {
            "model": "coder:gpt-4o",
            "messages": [{"role": "user", "content": "Hello, unified app!"}],
            "user_id": "test_user",
            "project_id": "test_proj"
        }

        response = client.post("/v1/chat/completions", json=chat_payload)

        assert response.status_code == 200
        data = response.json()
        assert "unified gateway" in data["choices"][0]["message"]["content"]

        # 5. Verify Memory Storage (Internal Check)
        from llm_quota_mem.memory import HybridMemory
        memory = HybridMemory(user_id="test_user", project_id="test_proj")
        recall = await memory.recall("Hello")
        assert len(recall["memories"]) > 0
        assert "unified gateway" in recall["memories"][0]

if __name__ == "__main__":
    pytest.main([__file__])
