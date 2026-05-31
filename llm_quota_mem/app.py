import os
import time
import json
import asyncio
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from llm_quota_mem.router import LLMRouter, LLMRequest, Message
from llm_quota_mem.memory import HybridMemory
from llm_quota_mem.personas import persona_manager
from llm_quota_mem.tools import get_coder_tools
from llm_quota_mem.intelligence import intelligence_manager
from llm_quota_mem.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_quota_mem.app")

app = FastAPI(title="llm-quota-mem Unified API", description="OpenAI-compatible API for llm-quota-mem")

# Global router instance
router = LLMRouter()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting llm-quota-mem Unified API server")
    # Refresh intelligence data in the background
    asyncio.create_task(intelligence_manager.refresh_intelligence())

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down llm-quota-mem Unified API server")
    await router.close()

# OpenAI-compatible models
class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    stream: Optional[bool] = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    # Custom Extensions
    persona: Optional[str] = "general"
    skills: Optional[List[str]] = []
    user_id: Optional[str] = "default_user"
    project_id: Optional[str] = "default_project"
    use_memory: Optional[bool] = True

@app.get("/v1/models")
async def list_models():
    """List available models across all providers."""
    models = []
    for provider in router.providers.values():
        if provider.healthy:
            for model_name in provider.models:
                models.append({
                    "id": model_name,
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": provider.name
                })
    return {"object": "list", "data": models}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint with Persona and Memory hooks."""
    try:
        # Parse model name for persona and skills (e.g., "coder:python:concise:gpt-4o")
        model_parts = request.model.split(":")
        request_persona = request.persona
        request_skills = request.skills or []
        target_model = request.model

        if len(model_parts) > 1:
            # Check if first part is a persona
            if persona_manager.get_persona(model_parts[0]):
                request_persona = model_parts[0]
                model_parts = model_parts[1:]

            # Check for skills in subsequent parts
            while len(model_parts) > 1:
                if persona_manager.get_skill(model_parts[0]):
                    request_skills.append(model_parts[0])
                    model_parts = model_parts[1:]
                else:
                    break

            target_model = model_parts[0]

        # 1. Initialize Memory for this session
        memory = HybridMemory(user_id=request.user_id, project_id=request.project_id)

        # 2. PRE-HOOK: Memory Recall
        context = ""
        if request.use_memory:
            # Use last 3 messages for better semantic recall context
            recall_query = "\n".join([m["content"] for m in request.messages[-3:]])
            recall_data = await memory.recall(query=recall_query)
            if recall_data["memories"]:
                context = "\nRELEVANT CONTEXT FROM LONG-TERM MEMORY:\n" + "\n".join(recall_data["memories"])

        # 3. Apply Persona and Skills
        system_prompt = ""
        p = persona_manager.get_persona(request_persona)
        if p:
            system_prompt = p.system_prompt

        for skill_name in request_skills:
            s = persona_manager.get_skill(skill_name)
            if s:
                system_prompt += f"\n{s.instructions}"

        if context:
            system_prompt += context

        # 4. Prepare Messages
        final_messages = []
        client_system_prompts = [m["content"] for m in request.messages if m["role"] == "system"]

        # Merge Persona System Prompt with Client System Prompt (File context, etc.)
        combined_system = system_prompt
        if client_system_prompts:
            combined_system += "\n\n### ADDITIONAL CONTEXT FROM CLIENT:\n" + "\n".join(client_system_prompts)

        if combined_system:
            final_messages.append(Message(role="system", content=combined_system))

        for m in request.messages:
            if m["role"] != "system":
                final_messages.append(Message(role=m["role"], content=m["content"]))

        # 5. Create LLMRequest
        llm_request = LLMRequest(
            messages=final_messages,
            model=target_model if target_model != "default" else None,
            temperature=request.temperature or 0.7,
            max_tokens=request.max_tokens or 4096,
            stream=request.stream or False,
            tools=request.tools,
            tool_choice=request.tool_choice
        )

        # Auto-inject tools if persona is coder and no tools provided
        if request_persona == "coder" and not llm_request.tools:
            llm_request.tools = get_coder_tools()

        # Determine domain
        domain = "general"
        if request_persona == "coder" or any(s in request_skills for s in ["python"]):
            domain = "coding"

        # 6. Call router
        result = await router.call(llm_request, domain=domain)

        # Handle Streaming Response
        if request.stream:
            async def stream_generator():
                full_content = ""
                async for chunk in result:
                    yield f"{chunk}\n\n"
                    # Try to extract content for memory
                    try:
                        data = json.loads(chunk.replace("data: ", ""))
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            full_content += delta["content"]
                    except:
                        pass

                # Post-hook for memory after stream ends
                if request.use_memory and request.messages and full_content:
                    user_msg = request.messages[-1]["content"]
                    await memory.add_memory(f"User: {user_msg}\nAssistant: {full_content}")

            return StreamingResponse(stream_generator(), media_type="text/event-stream")

        # Handle Standard Response
        # result can be a string (content) or a full choice object if it has tool calls
        content = ""
        tool_calls = None

        if isinstance(result, str):
            content = result
        elif isinstance(result, dict):
            # This shouldn't happen with current router implementation but being safe
            content = result.get("content", "")
            tool_calls = result.get("tool_calls")

        # Check if the router returned content that is actually a full response object
        # (Router needs update to return full message object for tool calls)

        # 7. POST-HOOK: Memory Storage
        if request.use_memory and request.messages:
            user_msg = request.messages[-1].get("content", "")
            await memory.add_memory(f"User: {user_msg}\nAssistant: {content}")

        # 8. Format response as OpenAI-compatible
        response_message = {
            "role": "assistant",
            "content": content
        }
        if tool_calls:
            response_message["tool_calls"] = tool_calls

        return {
            "id": f"chatcmpl-{os.urandom(12).hex()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": response_message,
                    "finish_reason": "tool_calls" if tool_calls else "stop"
                }
            ],
            "usage": {
                "prompt_tokens": -1,
                "completion_tokens": -1,
                "total_tokens": -1
            }
        }
    except Exception as e:
        logger.error(f"Error in chat_completions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "providers": {name: p.healthy for name, p in router.providers.items()}}

# OpenAI-compatible embeddings endpoint
class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str
    user: Optional[str] = None

@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    """OpenAI-compatible embeddings endpoint for project indexing."""
    try:
        from llm_quota_mem.embeddings import Embedder
        embedder = Embedder()

        inputs = [request.input] if isinstance(request.input, str) else request.input
        data = []
        for i, text in enumerate(inputs):
            vector = await embedder.embed_text(text)
            data.append({
                "object": "embedding",
                "index": i,
                "embedding": vector
            })

        await embedder.close()

        return {
            "object": "list",
            "data": data,
            "model": request.model,
            "usage": {
                "prompt_tokens": -1,
                "total_tokens": -1
            }
        }
    except Exception as e:
        logger.error(f"Error in create_embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Unified Dashboard UI."""
    configured_html = ""
    not_configured_html = ""

    # Pre-defined list of supported platforms for the UI
    supported = {
        "groq": "https://api.groq.com/openai/v1",
        "sambanova": "https://api.sambanova.ai/v1",
        "together": "https://api.together.xyz/v1",
        "google": "https://generativelanguage.googleapis.com/v1beta/openai",
        "openrouter": "https://openrouter.ai/api/v1",
        "openai": "https://api.openai.com/v1",
        "cerebras": "https://api.cerebras.ai/v1",
        "mistral": "https://api.mistral.ai/v1",
        "github": "https://models.inference.ai.azure.com",
        "nvidia": "https://integrate.api.nvidia.com/v1",
        "cloudflare": "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1"
    }

    for name, p in router.providers.items():
        if p.api_key:
            status = "🟢 Active" if p.healthy else "🔴 Error"

            # Add quota info from intelligence
            quota_txt = "Unknown quota"
            strengths = []
            for m_intel in intelligence_manager.models.values():
                if m_intel.provider == name:
                    quota_txt = m_intel.quota_info
                    strengths.extend(m_intel.best_for)
            strengths = list(set(strengths))

            configured_html += f"""
            <div class='card'>
                <strong>{name.upper()}</strong><br>
                <span>Status: {status}</span><br>
                <small>Quota: {quota_txt}</small><br>
                <small>Best for: {", ".join(strengths)}</small><br>
                <small>{p.base_url}</small>
            </div>"""

    for name, url in supported.items():
        if name not in router.providers or not router.providers[name].api_key:
            not_configured_html += f"""
            <div class='card disabled'>
                <strong>{name.upper()}</strong><br>
                <span>⚪ Not Configured</span><br>
                <button onclick="openAdd('{name}', '{url}')">Configure</button>
            </div>"""

    html_content = f"""
    <html>
    <head>
        <title>llm-quota-mem Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 1000px; margin: auto; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }}
            .card {{ background: #fff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-top: 4px solid #007bff; }}
            .card.disabled {{ opacity: 0.7; border: 1px dashed #ccc; border-top: none; }}
            .card strong {{ font-size: 1.1em; color: #007bff; }}
            .section {{ margin-bottom: 40px; }}
            h2 {{ border-bottom: 2px solid #ddd; padding-bottom: 10px; color: #444; }}
            .modal {{ display: none; position: fixed; z-index: 1; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); }}
            .modal-content {{ background: #fff; margin: 10% auto; padding: 20px; border-radius: 8px; width: 400px; }}
            input, select, button {{ width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }}
            button {{ background: #007bff; color: white; border: none; cursor: pointer; font-weight: bold; transition: background 0.3s; }}
            button:hover {{ background: #0056b3; }}
            #chat-box {{ background: #fff; padding: 20px; border-radius: 8px; height: 400px; overflow-y: scroll; border: 1px solid #ddd; display: flex; flex-direction: column; gap: 10px; }}
            .msg {{ padding: 10px 15px; border-radius: 15px; max-width: 80%; line-height: 1.5; }}
            .user {{ align-self: flex-end; background: #007bff; color: white; border-bottom-right-radius: 2px; }}
            .bot {{ align-self: flex-start; background: #e9ecef; color: #333; border-bottom-left-radius: 2px; }}
            .bot pre {{ background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; border: 1px solid #dee2e6; }}
            .bot code {{ font-family: 'Courier New', Courier, monospace; color: #d63384; }}
            .bot p {{ margin: 5px 0; }}
            .loading {{ font-style: italic; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Unified LLM Dashboard</h1>

            <div class="section">
                <h2>Active Providers</h2>
                <div class="grid">{configured_html}</div>
            </div>

            <div class="section">
                <h2>Add / Configure Provider</h2>
                <div class="grid">{not_configured_html}</div>
            </div>

            <div class="section">
                <h2>Chat Test</h2>
                <div id="chat-box"></div>
                <input type="text" id="chat-input" placeholder="Type a message...">
                <button onclick="sendChat()">Send</button>
            </div>
        </div>

        <div id="addModal" class="modal">
            <div class="modal-content">
                <h2 id="modal-title">Configure Provider</h2>
                <form action="/v1/providers" method="post">
                    <input type="hidden" name="name" id="form-name">
                    <label>Base URL</label>
                    <input type="text" name="base_url" id="form-url">
                    <label>API Key</label>
                    <input type="password" name="api_key" placeholder="Enter API Key">
                    <label>Models (comma separated)</label>
                    <input type="text" name="models" value="gpt-4o-mini,llama3.3">
                    <button type="submit">Save Provider</button>
                    <button type="button" onclick="closeAdd()" style="background:#6c757d">Cancel</button>
                </form>
            </div>
        </div>

        <script>
            function openAdd(name, url) {{
                document.getElementById('addModal').style.display = 'block';
                document.getElementById('modal-title').innerText = 'Configure ' + name.toUpperCase();
                document.getElementById('form-name').value = name;
                document.getElementById('form-url').value = url;
            }}
            function closeAdd() {{
                document.getElementById('addModal').style.display = 'none';
            }}
            async function sendChat() {{
                const input = document.getElementById('chat-input');
                const box = document.getElementById('chat-box');
                const text = input.value;
                if(!text) return;

                box.innerHTML += '<div class="msg user">' + text + '</div>';
                input.value = '';

                const loadingId = 'loading-' + Date.now();
                box.innerHTML += '<div id="' + loadingId + '" class="loading msg bot">Assistant is thinking...</div>';
                box.scrollTop = box.scrollHeight;

                try {{
                    const response = await fetch('/v1/chat/completions', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            model: 'default',
                            messages: [{{ role: 'user', content: text }}]
                        }})
                    }});

                    const loadingEl = document.getElementById(loadingId);
                    if (loadingEl) loadingEl.remove();

                    if (!response.ok) {{
                        const errorData = await response.json();
                        box.innerHTML += '<div class="msg bot" style="color:red"><strong>Error:</strong> ' + (errorData.detail || 'Unknown error') + '</div>';
                    }} else {{
                        const data = await response.json();
                        const reply = data.choices[0].message.content;
                        // Use marked.js for proper rendering
                        const htmlReply = marked.parse(reply);
                        box.innerHTML += '<div class="msg bot">' + htmlReply + '</div>';
                    }}
                }} catch (err) {{
                    const loadingEl = document.getElementById(loadingId);
                    if (loadingEl) loadingEl.remove();
                    box.innerHTML += '<div class="msg bot" style="color:red"><strong>Connection Error:</strong> ' + err.message + '</div>';
                }}
                box.scrollTop = box.scrollHeight;
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/v1/providers")
async def add_new_provider(name: str = Form(...), base_url: str = Form(...), api_key: str = Form(...), models: str = Form(...)):
    """Add a new provider via the UI."""
    model_list = [m.strip() for m in models.split(",")]
    router.add_provider(name, base_url, api_key, model_list)
    return HTMLResponse(content="<h2>Provider Added!</h2><a href='/'>Back to Dashboard</a>")

def start():
    """Entry point for the application."""
    uvicorn.run("llm_quota_mem.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start()
