import os
import time
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from llm_quota_mem.router import LLMRouter, LLMRequest, Message
from llm_quota_mem.memory import HybridMemory
from llm_quota_mem.personas import persona_manager
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

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down llm-quota-mem Unified API server")
    await router.close()

# OpenAI-compatible models
class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    stream: Optional[bool] = False
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
        # 1. Initialize Memory for this session
        memory = HybridMemory(user_id=request.user_id, project_id=request.project_id)

        # 2. PRE-HOOK: Memory Recall
        context = ""
        if request.use_memory:
            last_message = request.messages[-1]["content"] if request.messages else ""
            recall_data = await memory.recall(query=last_message)
            if recall_data["memories"]:
                context = "\nRELEVANT CONTEXT FROM PREVIOUS SESSIONS:\n" + "\n".join(recall_data["memories"])

        # 3. Apply Persona and Skills
        system_prompt = ""
        p = persona_manager.get_persona(request.persona)
        if p:
            system_prompt = p.system_prompt

        for skill_name in request.skills:
            s = persona_manager.get_skill(skill_name)
            if s:
                system_prompt += f"\n{s.instructions}"

        if context:
            system_prompt += context

        # 4. Prepare Messages
        final_messages = []
        if system_prompt:
            final_messages.append(Message(role="system", content=system_prompt))

        for m in request.messages:
            if m["role"] != "system": # Override existing system prompt
                final_messages.append(Message(role=m["role"], content=m["content"]))

        # 5. Create LLMRequest
        llm_request = LLMRequest(
            messages=final_messages,
            model=request.model,
            temperature=request.temperature or 0.7,
            max_tokens=request.max_tokens or 4096,
            stream=request.stream or False
        )

        # Determine domain
        domain = "general"
        if request.persona == "coder" or any(s in request.skills for s in ["python"]):
            domain = "coding"

        # 6. Call router
        content = await router.call(llm_request, domain=domain)

        # 7. POST-HOOK: Memory Storage
        if request.use_memory and request.messages:
            user_msg = request.messages[-1]["content"]
            await memory.add_memory(f"User: {user_msg}\nAssistant: {content}")

        # 8. Format response as OpenAI-compatible
        return {
            "id": f"chatcmpl-{os.urandom(12).hex()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
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

def start():
    """Entry point for the application."""
    uvicorn.run("llm_quota_mem.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start()
