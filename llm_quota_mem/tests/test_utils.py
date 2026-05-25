import pytest
from llm_quota_mem.utils import estimate_tokens, compress_prompt

def test_estimate_tokens():
    text = "Hello world"
    tokens = estimate_tokens(text)
    assert tokens > 0

def test_compress_prompt():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Message 1"},
        {"role": "assistant", "content": "Response 1"},
        {"role": "user", "content": "Message 2"},
    ]

    # Very small limit to force compression
    # system(6) + M2(3) + R1(3) + M1(3) = 15 tokens total.
    # If I set limit to 10, it should only keep system(6) and M2(3)
    compressed = compress_prompt(messages, max_tokens=10)

    assert len(compressed) == 2
    assert compressed[0]["role"] == "system"
    assert compressed[-1]["content"] == "Message 2"
