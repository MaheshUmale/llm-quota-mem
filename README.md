# llm-quota-mem: Unified AI Gateway & Agentic Coding Assistant

`llm-quota-mem` is a professional-grade, unified AI gateway designed to aggregate **FREE LLM API quotas** into a single, resilient, and intelligent endpoint. It transforms a collection of disparate free-tier providers into a powerful, project-aware **Agentic Coding Assistant** that integrates natively with VS Code.

---

## 🎯 Project Objectives

1.  **Quota Unification**: Aggregate 10+ free LLM providers (Groq, Google, SambaNova, etc.) into one OpenAI-compatible API to bypass individual rate limits.
2.  **Zero-Cost Agentic Coding**: Provide a high-performance alternative to paid AI assistants by leveraging top-tier free models (DeepSeek-R1, Llama 3.3, GPT-4o) with project-wide context.
3.  **Intelligent Memory**: Maintain project context across sessions using Hybrid Memory (Vector Store + Knowledge Graph), reducing redundant explanations and token waste.
4.  **Resilient Failover**: Implement instant, automatic provider switching to ensure 99.9% availability even when free-tier quotas are exhausted.
5.  **Token Efficiency**: Achieve 80-90% efficiency gains via task-aware routing, semantic compaction, and specialized "Concise" skills.

---

## 🚀 Key Features

### 1. Unified LLM Router
- **Aggregated Quotas**: Support for Groq, SambaNova, Together AI, Google Gemini, OpenRouter, Cerebras, Mistral, GitHub Models, Cloudflare, and NVIDIA.
- **Auto-Failover**: If one provider hits a rate limit (429) or fails, the router instantly retries with the next best available provider.
- **Local Fallback**: Native support for Ollama/Llama.cpp as a final fallback layer.

### 2. Agentic VS Code Integration
- **Native Extension**: A dedicated sidebar chat that manages the backend server and interacts with your workspace.
- **Full Workspace Access**: The agent can list, read, search, and **write** files in your project automatically.
- **OpenAI Compatible**: Seamlessly works with industry-standard tools like **Roo Code**, **Continue**, and **CodeGPT**.

### 3. Intelligent Brain
- **Complexity Scouter**: Automatically detects task types (Fast, Coding, Reasoning) and routes to the most capable free model for that specific job.
- **Hybrid Memory**: Uses semantic search to recall relevant project snippets and a Knowledge Graph to understand code relationships.
- **Persona System**: Hot-swap between "Expert Coder", "System Architect", or "Security Auditor" roles via model name prefixes (e.g., `coder:gpt-4o`).

### 4. Management Dashboard
- **Live Health Monitor**: Real-time status of all configured providers and their current quotas.
- **Dynamic Config**: Add API keys and update model lists on the fly via a clean web interface at `http://localhost:8000`.
- **Chat Playground**: Test your multi-provider setup with full Markdown and code highlight support.

---

## 🛠️ Installation

### 1. Backend Gateway
```bash
# Clone the repository
git clone https://github.com/MaheshUmale/llm-quota-mem.git
cd llm-quota-mem

# Automated Setup (Recommended)
# Windows:
setup.bat
# Linux/macOS:
chmod +x setup.sh && ./setup.sh
```

### 2. VS Code Extension
The extension provides the bridge between the LLM and your local code.
1.  Open VS Code and go to the **Extensions** view (`Ctrl+Shift+X`).
2.  Click the **...** menu (top right) -> **Install from VSIX...**.
3.  Select `vscode-extension/llm-quota-mem.vsix`.
4.  Click the **LLM Quota Mem** icon in your Activity Bar to start!

---

## ⚙️ Configuration

Create a `.env` file or a `keys.json` in the root directory.

### Example `.env`:
```env
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=AIza...
SAMBANOVA_API_KEY=...
GITHUB_API_KEY=...
# Optional:
DEFAULT_MODEL=gpt-4o
```

### Example `keys.json`:
```json
[
  { "platform": "groq", "api_key": "gsk_..." },
  { "platform": "google", "api_key": "AIza..." }
]
```

---

## 📖 Quick Start

1.  **Launch the Gateway**:
    ```bash
    python -m llm_quota_mem.app
    ```
2.  **Visit the Dashboard**: Open `http://localhost:8000` to verify your providers are 🟢 Active.
3.  **Start Coding**: Open the VS Code sidebar and ask: *"Review my project structure and explain the main logic."*

---

## 🧩 Advanced Usage: Personas & Skills

You can trigger specialized logic by prefixing your model name in any OpenAI-compatible client:

-   `coder:gpt-4o` -> Activates the **Agentic Coding** mode (enables workspace tools).
-   `architect:mixtral-8x7b` -> Focuses on high-level system design.
-   `concise:llama-3.3` -> Forces short, token-efficient answers.
-   `coder:python:concise:gpt-4o` -> Combines multiple behaviors!

---

## 🛡️ License

Apache-2.0 - See [LICENSE](LICENSE) for details.
