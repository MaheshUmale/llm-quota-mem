import asyncio
from llm_quota_mem.router import LLMRouter, LLMRequest, Message
from llm_quota_mem.memory import HybridMemory

async def run_coding_agent():
    router = LLMRouter()
    memory = HybridMemory(user_id="dev_jules", project_id="llm_quota_mem")

    query = "Write a python function to calculate the hash of a string."

    messages = [
        Message(role="system", content="You are an expert Python developer. Be concise."),
        Message(role="user", content=query)
    ]

    print(f"Coding Agent Query: {query}")
    try:
        response = await router.call(LLMRequest(messages=messages))
        print("\n--- Coding Agent Response ---")
        print(response)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await router.close()

if __name__ == "__main__":
    asyncio.run(run_coding_agent())
