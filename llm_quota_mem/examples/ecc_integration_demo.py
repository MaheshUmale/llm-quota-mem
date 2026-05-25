import asyncio
import os
from llm_quota_mem.integrations.ecc.hooks import ECCHooks
from llm_quota_mem.router import LLMRouter, LLMRequest, Message

async def run_ecc_integration_demo():
    print("Starting ECC Integration Demo...")
    user_id = "ecc_user"
    project_id = "aws_migration"

    # 1. Simulate ECC SessionStart Hook
    hooks = ECCHooks(user_id, project_id)
    query = "How can we use S3 for log storage?"
    print(f"\n[ECC Event] SessionStart for: {query}")
    context = await hooks.on_session_start(query)
    print(f"Recalled Context: {context}")

    # 2. Call LLM with Scouted Complexity
    router = LLMRouter()
    messages = [
        Message(role="system", content="You are an AWS expert."),
        Message(role="user", content=query)
    ]

    print("\nRouting request...")
    response = await router.call(LLMRequest(messages=messages), domain="ea")
    print(f"\nAssistant Response: {response[:100]}...")

    # 3. Simulate ECC Stop Hook (Extract Instincts)
    print("\n[ECC Event] Stop - Saving and Extracting Instincts")
    await hooks.on_session_stop(f"System uses S3 for logs and Lambda for processing. {response}")

    # Verify Graph
    rels = hooks.memory.graph.query(project_id)
    print(f"\nKnowledge Graph Relations for {project_id}:")
    for r in rels:
        print(f"  - {r['relation']} -> {r['target']}")

    await router.close()

if __name__ == "__main__":
    if not any([os.getenv("GROQ_API_KEY"), os.getenv("OPENAI_API_KEY")]):
        print("Please set GROQ_API_KEY or OPENAI_API_KEY to run this demo.")
    else:
        asyncio.run(run_ecc_integration_demo())
