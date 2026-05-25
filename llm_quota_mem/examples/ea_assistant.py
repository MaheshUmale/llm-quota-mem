import asyncio
import os
from llm_quota_mem.router import LLMRouter, LLMRequest, Message
from llm_quota_mem.memory import HybridMemory
from llm_quota_mem.domain_adapter import DomainAdapter

async def run_ea_assistant():
    # Initialize components
    router = LLMRouter()
    memory = HybridMemory(user_id="arch_expert_01", project_id="cloud_migration_v1")

    # User query
    query = "How should we migrate our legacy monolithic ERP to a cloud-native architecture?"

    # 1. Recall from memory
    memories = await memory.recall(query=query)

    # 2. Build messages with EA domain prompt
    messages = [
        Message(role="system", content=DomainAdapter.get_ea_prompt()),
    ]

    if memories:
        messages.append(Message(role="system", content=f"Relevant context: {'. '.join(memories)}"))

    messages.append(Message(role="user", content=query))

    # 3. Call LLM via Router
    print(f"Querying LLM Router for: {query}")
    try:
        response = await router.call(LLMRequest(messages=messages))
        print("\n--- ArchAI Response ---")
        print(response)

        # 4. Save to memory (placeholder vector)
        # await memory.add_memory(response, vector=[0.1] * 1536)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await router.close()

if __name__ == "__main__":
    # Ensure API Keys are set or this will fail gracefully
    if not any([os.getenv("GROQ_API_KEY"), os.getenv("OPENAI_API_KEY")]):
        print("Please set GROQ_API_KEY or OPENAI_API_KEY to run this example.")
    else:
        asyncio.run(run_ea_assistant())
