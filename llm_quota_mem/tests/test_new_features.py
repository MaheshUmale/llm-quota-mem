import pytest
import json
from llm_quota_mem.router import LLMRouter, LLMRequest, Message
from llm_quota_mem.tools import get_coder_tools

@pytest.mark.asyncio
async def test_tool_injection():
    router = LLMRouter()
    tools = get_coder_tools()
    assert len(tools) > 0
    assert any(t["function"]["name"] == "list_files" for t in tools)

@pytest.mark.asyncio
async def test_persona_loading():
    from llm_quota_mem.personas import PersonaManager
    import os

    # Create a dummy agents.md
    with open("agents.md", "w") as f:
        f.write("## Expert Coder\nPrompt**: \"You are a Super AI Coder\"\n")

    pm = PersonaManager()
    persona = pm.get_persona("coder")
    assert "Super AI Coder" in persona.system_prompt
    assert "WORKSPACE TOOLS" in persona.system_prompt

    # Cleanup
    os.remove("agents.md")
