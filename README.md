# llm-quota-mem

`llm-quota-mem` is a lean, production-ready Python package designed to unify **FREE LLM API quotas** and manage **intelligent agent memory**. It aims for 80-90% efficiency gains by reducing redundant API calls and optimizing context window usage.

## Key Features

- **Unified LLM Router**: Seamlessly switch between free tiers (Groq, SambaNova, Together, Gemini, OpenRouter, OpenAI) and **Local SLM Fallback** (Ollama/Llama.cpp) with intelligent failover.
- **Task Complexity Routing**: Automatically scouts task complexity (SIMPLE, DEV, ARCH) to select the most cost-effective model/provider.
- **Hybrid Memory & Knowledge Graph**: Combines semantic search (numpy-based) with a triple-store Knowledge Graph for complex EA relationship mapping.
- **ECC Ecosystem Integration**: Harness-native hooks and skill manifests for **Everything Claude Code (ECC)**.
- **80-90% Efficiency Gains**: Achieved via response caching, semantic compaction, and real-time token optimization.
- **Distilled Design**: Minimal dependencies (< 50MB footprint), high throughput, and async-native.

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

## ECC Integration

`llm-quota-mem` is designed to work as the optimization engine for [ECC](https://github.com/affaan-m/ECC).

### Native Hooks
Integrate memory lifecycle into your agent harness:
```python
from llm_quota_mem.integrations.ecc.hooks import ECCHooks

hooks = ECCHooks(user_id="jules", project_id="arch_ai")

# On Session Start (Automatic Recall)
context = await hooks.on_session_start("How to migrate to microservices?")

# On Session Stop (Save & Extract Instincts)
await hooks.on_session_stop("We decided to use Kafka for decoupling.")
```

### EA Skills
ECC-compatible `SKILL.md` manifests are available in `llm_quota_mem/integrations/ecc/skills/` for TOGAF, AWS, and C4 Model optimization.

## Quick Start Guide

Verify your installation and start using the unified app in 3 steps:

1. **Start the Unified Server**:
   ```bash
   python -m llm_quota_mem.app
   ```
   The server runs on `http://localhost:8000` with an OpenAI-compatible API.

2. **Run a Quick Test**:
   ```bash
   python llm_quota_mem/examples/quick_start.py
   ```

3. **VS Code Integration**:
   - Install the **Continue** extension in VS Code.
   - Open Continue settings and add a new model:
     ```json
     {
       "title": "llm-quota-mem",
       "model": "gpt-4o",
       "apiBase": "http://localhost:8000/v1",
       "provider": "openai"
     }
     ```
   - Now you can use the unified LLM for coding directly in VS Code!

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

## Advanced Features

### Semantic Compaction
When context is reaching limits, use `semantic_compress` to summarize threads before truncation:
```python
from llm_quota_mem.utils import semantic_compress
summary = await semantic_compress(messages, router)
```

### Knowledge Graph & Instinct Learning
Automated extraction of architectural relations:
```python
# Save to memory and automatically extract triples for the graph
await memory.add_memory("System uses Kubernetes and S3", extract_instincts=True)

# Query connections
rels = memory.graph.query("arch_ai")
```

### Benchmarking
Run the built-in benchmarking suite to track performance and token savings:
```bash
python -m llm_quota_mem.benchmarking
```

## License

Apache-2.0
