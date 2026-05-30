# llm-quota-mem Agents

This file defines standard agent personas that utilize the unified LLM routing and memory system.

## 💻 Coding Agent
An agent specialized in software development tasks. It uses the `DEV` complexity tier for implementation and `SIMPLE` for quick fixes.
- **Provider Preference**: OpenAI, Google (Gemini).
- **Memory Context**: Focuses on current file, recent changes, and project-wide conventions.

## 🏗️ Architecture Agent
An agent specialized in high-level design and architectural trade-offs. It uses the `ARCH` complexity tier.
- **Provider Preference**: Anthropic (via OpenRouter), SambaNova (for high-throughput reasoning).
- **Memory Context**: Focuses on the Knowledge Graph, EA relationships, and long-term project goals.

## ⚡ Quick Response Agent
Optimized for speed and low-latency interactions.
- **Provider Preference**: Groq (Llama 3.3).
- **Memory Context**: Minimal, focused on the immediate query.

## Custom Agent Template
```python
from llm_quota_mem import LLMRouter, HybridMemory

class MyCustomAgent:
    def __init__(self, name, task_domain="ea"):
        self.name = name
        self.router = LLMRouter()
        self.memory = HybridMemory(user_id="user", project_id="proj")
        self.domain = task_domain

    async def chat(self, user_input):
        # Implementation logic
        pass
```
