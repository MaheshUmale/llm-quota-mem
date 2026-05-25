# llm-quota-mem

`llm-quota-mem` is a lean, production-ready Python package designed to unify **FREE LLM API quotas** and manage **intelligent agent memory**. It aims for 80-90% efficiency gains by reducing redundant API calls and optimizing context window usage.

## Key Features

- **Unified LLM Router**: Seamlessly switch between free tiers of Groq, SambaNova, Together AI, Google Gemini, and OpenAI with automatic failover and health tracking.
- **Hybrid Memory Layer**: Combines semantic long-term memory (via a lightweight, numpy-based vector store) with structured session/project state.
- **Token Optimization**: Real-time token estimation and prompt compression to prevent context bloat and minimize usage.
- **Domain-Aware Routing**: Specialized for Enterprise Architecture (EA) with distilled knowledge from TOGAF, C4 Model, and AWS Well-Architected.
- **Async-First**: Built with modern Python `asyncio` and `httpx` for high-throughput agent systems.

## Installation

```bash
# Clone the repository
git clone https://github.com/MaheshUmale/llm-quota-mem.git
cd llm-quota-mem

# Install in editable mode
pip install -e .
```

## Setup

Create a `.env` file in your project root with your API keys:

```env
# LLM Providers
GROQ_API_KEY=your_groq_key
SAMBANOVA_API_KEY=your_sambanova_key
TOGETHER_API_KEY=your_together_key
GOOGLE_API_KEY=your_google_key
OPENAI_API_KEY=your_openai_key

# Optional Configurations
DEFAULT_MODEL=gpt-4o-mini
TEMPERATURE=0.7
```

## Adding New Providers

To add a new LLM provider:

1.  **Update `llm_quota_mem/config.py`**: Add the new API key and base URL to the `Settings` class.
    ```python
    class Settings(BaseSettings):
        NEW_PROVIDER_API_KEY: Optional[str] = None
        NEW_PROVIDER_BASE_URL: str = "https://api.newprovider.com/v1"
    ```
2.  **Update `llm_quota_mem/router.py`**: Initialize the new provider in `_init_providers`.
    ```python
    if settings.NEW_PROVIDER_API_KEY:
        providers["new_provider"] = ProviderConfig(
            name="new_provider",
            base_url=settings.NEW_PROVIDER_BASE_URL,
            api_key=settings.NEW_PROVIDER_API_KEY,
            models=["model-1", "model-2"],
            priority=7
        )
    ```

## Usage

### Unified LLM Router

```python
import asyncio
from llm_quota_mem import LLMRouter, LLMRequest, Message

async def main():
    router = LLMRouter()
    request = LLMRequest(
        messages=[Message(role="user", content="Explain the Strangler Fig pattern.")]
    )

    response = await router.call(request)
    print(response)
    await router.close()

asyncio.run(main())
```

### Hybrid Memory

```python
from llm_quota_mem import HybridMemory

memory = HybridMemory(user_id="expert_01", project_id="ea_migration")

# Add a memory (automatically embedded)
await memory.add_memory("The system uses a microservices architecture with Kafka for messaging.")

# Recall relevant context
context = await memory.recall("How does the system handle messaging?")
print(context)
```

## Next Steps

1. **Local SLM Fallback**: Add support for local GGUF/Llama.cpp inference when all free cloud quotas are exhausted.
2. **Advanced Knowledge Graph**: Integrate graph-based memory retrieval for more complex relationship mapping in EA.
3. **Benchmarking Suite**: Implement a tool to track token savings and success rates across providers in real-time.
4. **Quantization Awareness**: Optimize prompt templates for specific SLM sizes (3B, 7B, 14B).

## License

Apache-2.0
