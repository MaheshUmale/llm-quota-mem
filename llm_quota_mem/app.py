import os
import time
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from llm_quota_mem.router import LLMRouter, LLMRequest, Message
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
    """OpenAI-compatible chat completions endpoint."""
    try:
        # Convert to internal Message format
        messages = [Message(role=m["role"], content=m["content"]) for m in request.messages]

        # Create LLMRequest
        llm_request = LLMRequest(
            messages=messages,
            model=request.model,
            temperature=request.temperature or 0.7,
            max_tokens=request.max_tokens or 4096,
            stream=request.stream or False
        )

        # Determine domain (basic heuristic: if "code" or "python" in messages, it's coding)
        domain = "ea"
        full_text = " ".join([m.content.lower() for m in messages])
        if any(kw in full_text for kw in ["code", "python", "javascript", "debug", "implement"]):
            domain = "coding"

        # Call router
        content = await router.call(llm_request, domain=domain)

        # Format response as OpenAI-compatible
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
