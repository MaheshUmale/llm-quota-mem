# VS Code Integration Guide for llm-quota-mem

This guide provides detailed instructions on how to set up `llm-quota-mem` as your primary LLM interface in VS Code.

## Prerequisites
1.  **Python 3.11+** installed.
2.  **llm-quota-mem** installed and configured (run `setup.bat` or `setup.sh`).

---

## Step 1: Start the Unified Server

Open a terminal and run:
```bash
python -m llm_quota_mem.app
```
The server will start at `http://localhost:8000`. You can visit this URL in your browser to access the management dashboard.

---

## Step 2: Configure VS Code Extensions

### Option A: Using the "Continue" Extension (Recommended)
1.  Install the **Continue** extension from the VS Code Marketplace.
2.  Click on the Continue icon in the sidebar.
3.  Click the gear icon (Settings) to open `config.json`.
4.  Add `llm-quota-mem` to your `models` list:
    ```json
    {
      "models": [
        {
          "title": "llm-quota-mem (Default)",
          "model": "gpt-4o",
          "apiBase": "http://localhost:8000/v1",
          "provider": "openai"
        },
        {
          "title": "llm-quota-mem (Expert Coder)",
          "model": "coder:python:gpt-4o",
          "apiBase": "http://localhost:8000/v1",
          "provider": "openai"
        }
      ]
    }
    ```
5.  Save the file. You can now select these models from the dropdown in the Continue sidebar.

### Option B: Using the "CodeGPT" Extension
1.  Install **CodeGPT** from the VS Code Marketplace.
2.  Open CodeGPT settings.
3.  Select **Custom OpenAI** or **Local** as the provider.
4.  Set the **Base URL** to `http://localhost:8000/v1`.
5.  Set the **API Key** to any non-empty string (it's ignored but required by the extension).

---

## Step 3: Advanced Usage (Personas & Skills)

`llm-quota-mem` supports dynamic persona and skill selection via model name prefixes. You can use these in your extension settings to trigger different behaviors:

-   **`coder:gpt-4o`**: Activates the Expert Coder persona.
-   **`architect:gpt-4o`**: Activates the System Architect persona.
-   **`concise:gpt-4o`**: Injects the Concise Output skill to save tokens.
-   **`coder:python:concise:gpt-4o`**: Combines multiple triggers!

---

## Step 4: Manage Providers via Dashboard

Visit `http://localhost:8000` to:
1.  **Monitor Health**: See which LLM providers are currently active.
2.  **Dynamic Configuration**: Add new API keys (Groq, Cerebras, etc.) without restarting the server.
3.  **Chat Test**: Quickly verify your settings before using them in VS Code.

---

## Troubleshooting
-   **Connection Refused**: Ensure the server is running (`python -m llm_quota_mem.app`).
-   **No Providers Active**: Check your `.env` or `keys.json` file, or add a provider via the dashboard.
-   **Token Limit Reached**: The `concise` skill is highly recommended to stay within free tier limits.
