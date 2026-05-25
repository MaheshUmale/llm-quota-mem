import asyncio
import os
import pytest
from llm_quota_mem.router import LLMRouter, LLMRequest, Message

@pytest.mark.asyncio
async def test_live_apis():
    print("Testing Live APIs...")
    router = LLMRouter()

    # 1. Test Groq
    if os.getenv("GROQ_API_KEY"):
        print("\n--- Testing Groq ---")
        try:
            req = LLMRequest(messages=[Message(role="user", content="Say hello from Groq.")], model="llama-3.3-70b-versatile")
            resp = await router.call(req, domain="ea")
            print(f"Groq Response: {resp}")
        except Exception as e:
            print(f"Groq failed: {e}")
    else:
        print("Groq API key not found.")

    # 2. Test OpenRouter
    if os.getenv("OPENROUTER_API_KEY"):
        print("\n--- Testing OpenRouter ---")
        try:
            req = LLMRequest(messages=[Message(role="user", content="Say hello from OpenRouter.")], model="google/gemini-2.0-flash-001")
            resp = await router.call(req, domain="general")
            print(f"OpenRouter Response: {resp}")
        except Exception as e:
            print(f"OpenRouter failed: {e}")
    else:
        print("OpenRouter API key not found.")

    await router.close()

if __name__ == "__main__":
    asyncio.run(test_live_apis())
