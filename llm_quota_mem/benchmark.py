import asyncio
import time
from llm_quota_mem.router import LLMRouter, LLMRequest, Message
from llm_quota_mem.memory import HybridMemory
from llm_quota_mem.cache import ResponseCache
from llm_quota_mem.utils import estimate_tokens

async def run_benchmark():
    print("Starting Efficiency Benchmark...")
    router = LLMRouter()
    memory = HybridMemory(user_id="benchmarker", project_id="efficiency_test")
    cache = ResponseCache()

    query = "What is the C4 model in software architecture?"
    model = "gpt-4o-mini"

    # 1. First call (Cold)
    start_time = time.time()
    response1 = await router.call(LLMRequest(messages=[Message(role="user", content=query)]))
    cold_duration = time.time() - start_time
    print(f"Cold Call Duration: {cold_duration:.2f}s")

    # Save to cache and memory
    cache.set(query, model, response1)
    await memory.add_memory(response1)

    # 2. Second call (Cached)
    start_time = time.time()
    cached_response = await cache.get(query, model)
    if cached_response:
        print("Cache Hit!")
    cache_duration = time.time() - start_time
    print(f"Cached Call Duration: {cache_duration:.4f}s")

    # 3. Recall from Memory
    start_time = time.time()
    memories = await memory.recall(query)
    recall_duration = time.time() - start_time
    print(f"Memory Recall Duration: {recall_duration:.4f}s")
    print(f"Memories found: {len(memories)}")

    # Calculate efficiency
    # In a real scenario, we'd compare tokens saved by using recall instead of full context
    tokens_original = estimate_tokens(response1) # Approximation of a long conversation
    tokens_recalled = sum(estimate_tokens(m) for m in memories)

    print("\n--- Benchmark Results ---")
    print(f"Latency Reduction (Cache vs Cold): {(1 - cache_duration/cold_duration)*100:.2f}%")
    print(f"Memory Recall Latency: {recall_duration:.4f}s")

    await router.close()

if __name__ == "__main__":
    asyncio.run(run_benchmark())
