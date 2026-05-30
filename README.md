# llm-quota-mem

`llm-quota-mem` is a lean, production-ready Python package designed to unify **FREE LLM API quotas** and manage **intelligent agent memory**. It aims for 80-90% efficiency gains by reducing redundant API calls and optimizing context window usage.

## Key Features

- **Unified LLM Router**: Seamlessly switch between free tiers (Groq, SambaNova, Together, Gemini, OpenRouter, OpenAI, Cerebras, Mistral, GitHub, Cloudflare, NVIDIA) and **Local SLM Fallback** (Ollama/Llama.cpp) with intelligent failover.
- **Intelligent Task-Aware Routing**: Automatically detects task type (Coding, Reasoning, Fast) and routes to the best-performing and most cost-effective free-tier model.
- **Cross-Session Hybrid Memory**: Seamlessly maintains context between sessions using semantic search and a Knowledge Graph, reducing redundant explanations and saving tokens.
- **Persona & Skill System**: Easily swap between roles (Coder, Architect) and apply specialized instruction sets (Security, Concise) to optimize output quality and length.
- **80-90% Efficiency Gains**: Achieved via intelligent routing, semantic compaction, and session memory hooks.
- **Distilled Design**: Minimal dependencies (< 50MB footprint), high throughput, and async-native.

## Installation

### 1. Backend Gateway
```bash
# Clone the repository
git clone https://github.com/MaheshUmale/llm-quota-mem.git
cd llm-quota-mem

# Install in editable mode
pip install -e .
```

### 2. VS Code Extension (Developer Mode)
1.  Navigate to `vscode-extension/`.
2.  Run `npm install`.
3.  Open the `vscode-extension` folder in VS Code.
4.  Press `F5` to launch the extension in a [Extension Development Host] window.
5.  Find "LLM Quota Mem" in your Activity Bar (left sidebar).

## Setup

Create a `.env` file in your project root with your API keys:

```env
# LLM Providers
GROQ_API_KEY=your_groq_key
SAMBANOVA_API_KEY=your_sambanova_key
TOGETHER_API_KEY=your_together_key
GOOGLE_API_KEY=your_google_key
OPENAI_API_KEY=your_openai_key
CEREBRAS_API_KEY=your_cerebras_key
MISTRAL_API_KEY=your_mistral_key
GITHUB_API_KEY=your_github_key
CLOUDFLARE_API_KEY=your_cloudflare_key
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
NVIDIA_API_KEY=your_nvidia_key

# Optional Configurations
DEFAULT_MODEL=gpt-4o-mini
TEMPERATURE=0.7
```

## Pre-populating API Keys

You can pre-populate API keys using a `keys.json` file in the root directory:

```json
[
  {
    "platform": "groq",
    "api_key": "your_groq_key"
  },
  {
    "platform": "cloudflare",
    "api_key": "your_cloudflare_key",
    "extra": {
      "account_id": "your_account_id"
    }
  }
]
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

## Core Features

### Management Dashboard
Manage your LLM ecosystem from a simple browser interface at `http://localhost:8000/`. Monitor health, see provider quotas, and test chat completions.

### API Hooks (Memory & Optimization)
`llm-quota-mem` automatically manages memory and optimization via API hooks:

- **Pre-Hook (Recall)**: Automatically searches long-term memory for relevant context based on your query.
- **Post-Hook (Storage)**: Saves the interaction to long-term memory for future recall.
- **Token Optimization**: Use the `concise` skill to minimize output tokens without losing quality.

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
   - **Detailed Guide**: See [VSCODE_SETUP.md](VSCODE_SETUP.md) for full instructions.
   - Install the **Continue** extension in VS Code.
   - Open Continue settings and add a new model pointing to `http://localhost:8000/v1`.
   - Use prefixes like `coder:gpt-4o` to switch personas directly from VS Code!

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
When context is reaching limits, use `semantic_compress` to summarize threads before truncation to stay within model context windows and save tokens.

### Hybrid Memory
Maintains semantic context across sessions using a lightweight vector store and a knowledge graph.

### Benchmarking
Run the built-in benchmarking suite to track performance and token savings:
```bash
python -m llm_quota_mem.benchmarking
```

## License

Apache-2.0
