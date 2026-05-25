import pytest
from llm_quota_mem.router import LLMRouter, LLMRequest, Message, TaskComplexity

def test_complexity_scouting():
    router = LLMRouter()

    # Simple
    msg1 = [Message(role="user", content="hi")]
    assert router.scouter.scout(msg1) == TaskComplexity.SIMPLE

    # Dev
    msg2 = [Message(role="user", content="implement a binary search")]
    assert router.scouter.scout(msg2) == TaskComplexity.DEV

    # Arch
    msg3 = [Message(role="user", content="design a tradeoff matrix for togaf")]
    assert router.scouter.scout(msg3) == TaskComplexity.ARCH

@pytest.mark.asyncio
async def test_semantic_compress_error(tmp_path):
    # Testing error handling when router is not provided or fails
    from llm_quota_mem.utils import semantic_compress
    messages = [{"role": "user", "content": "test"}]

    # Passing None as router should trigger exception handler
    result = await semantic_compress(messages, None)
    assert "Error during summary" in result
