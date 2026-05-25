import tiktoken
from typing import List, Dict, Any

def estimate_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def compress_prompt(messages: List[Dict[str, Any]], max_tokens: int = 2000, model: str = "gpt-4o-mini") -> List[Dict[str, Any]]:
    """
    Compresses prompt by keeping the system message and as many recent messages
    as possible within the token limit.
    """
    if not messages:
        return []

    system_msgs = [m for m in messages if m.get("role") == "system"]
    other_msgs = [m for m in messages if m.get("role") != "system"]

    current_tokens = sum(estimate_tokens(m.get("content", ""), model) for m in system_msgs)

    if current_tokens > max_tokens:
        # If system messages alone exceed limit, we have to keep them but it's a problem
        return system_msgs

    result_msgs = []
    # Add messages from newest to oldest
    for msg in reversed(other_msgs):
        msg_tokens = estimate_tokens(msg.get("content", ""), model)
        if current_tokens + msg_tokens <= max_tokens:
            result_msgs.insert(0, msg)
            current_tokens += msg_tokens
        else:
            break

    return system_msgs + result_msgs

async def semantic_compress(messages: List[Dict[str, Any]], router: Any) -> str:
    """Uses a cheap LLM to summarize context before truncation."""
    if not messages:
        return ""

    text_to_summarize = "\n".join([f"{m['role']}: {m['content']}" for m in messages if m['role'] != 'system'])

    prompt = (
        "Summarize the following conversation thread concisely, "
        "preserving key decisions and architectural patterns mentioned:\n\n"
        f"{text_to_summarize}"
    )

    from .router import LLMRequest, Message
    try:
        # Use simple complexity to trigger cheapest model
        summary = await router.call(
            LLMRequest(messages=[Message(role="user", content=prompt)]),
            domain="general"
        )
        return summary
    except Exception as e:
        return f"Error during summary: {e}. Original message count: {len(messages)}"

class CostTracker:
    """Tracks token usage and estimated costs."""
    def __init__(self):
        self.usage = {} # model -> {"prompt_tokens": int, "completion_tokens": int}
        # Simplified costs per 1k tokens (placeholder values)
        self.pricing = {
            "gpt-4o": {"prompt": 0.005, "completion": 0.015},
            "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
            "claude-3-5-sonnet-20240620": {"prompt": 0.003, "completion": 0.015},
            "default": {"prompt": 0.0, "completion": 0.0} # free tiers
        }

    def add_usage(self, model: str, prompt_tokens: int, completion_tokens: int):
        if model not in self.usage:
            self.usage[model] = {"prompt_tokens": 0, "completion_tokens": 0}
        self.usage[model]["prompt_tokens"] += prompt_tokens
        self.usage[model]["completion_tokens"] += completion_tokens

    def get_total_cost(self) -> float:
        total = 0.0
        for model, counts in self.usage.items():
            prices = self.pricing.get(model, self.pricing["default"])
            total += (counts["prompt_tokens"] / 1000) * prices["prompt"]
            total += (counts["completion_tokens"] / 1000) * prices["completion"]
        return total

    def get_report(self) -> Dict[str, Any]:
        return {
            "usage": self.usage,
            "total_estimated_cost_usd": self.get_total_cost()
        }
