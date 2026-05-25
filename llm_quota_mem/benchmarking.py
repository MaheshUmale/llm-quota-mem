import asyncio
import time
import json
from typing import List, Dict, Any
from .router import LLMRouter, LLMRequest, Message
from .utils import estimate_tokens, CostTracker

class BenchmarkingSuite:
    def __init__(self):
        self.router = LLMRouter()
        self.cost_tracker = CostTracker()
        self.results = []

    async def run_test_case(self, name: str, query: str, domain: str = "ea"):
        print(f"Running test case: {name}")
        start_time = time.time()

        try:
            req = LLMRequest(messages=[Message(role="user", content=query)])
            response = await self.router.call(req, domain=domain)
            duration = time.time() - start_time

            prompt_tokens = estimate_tokens(query)
            completion_tokens = estimate_tokens(response)
            self.cost_tracker.add_usage(req.model or "unknown", prompt_tokens, completion_tokens)

            self.results.append({
                "case": name,
                "status": "success",
                "latency": duration,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            })
            return response
        except Exception as e:
            self.results.append({
                "case": name,
                "status": "failed",
                "error": str(e)
            })
            return None

    def get_summary(self) -> Dict[str, Any]:
        successes = [r for r in self.results if r["status"] == "success"]
        avg_latency = sum(r["latency"] for r in successes) / len(successes) if successes else 0
        total_tokens = sum(r["prompt_tokens"] + r["completion_tokens"] for r in successes)

        return {
            "total_runs": len(self.results),
            "success_rate": len(successes) / len(self.results) if self.results else 0,
            "avg_latency": avg_latency,
            "total_tokens_consumed": total_tokens,
            "cost_report": self.cost_tracker.get_report()
        }

async def run_benchmarks():
    suite = BenchmarkingSuite()
    await suite.run_test_case("EA Basic", "What is TOGAF ADM?")
    await suite.run_test_case("Cloud Design", "Compare multi-region vs multi-az on AWS.")

    print("\n--- Benchmark Summary ---")
    print(json.dumps(suite.get_summary(), indent=2))
    await suite.router.close()

if __name__ == "__main__":
    asyncio.run(run_benchmarks())
