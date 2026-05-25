import tiktoken
from typing import List, Dict, Any

def estimate_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def compress_prompt(messages: List[Dict[str, Any]], max_tokens: int = 2000, model: str = "gpt-4o-mini") -> List[Dict[str, Any]]:
    """
    Compresses prompt by keeping the system message and as many recent messages
    as possible within the token limit.
    """
    if not messages:
        return []

    system_msgs = [m for m in messages if m.get("role") == "system"]
    other_msgs = [m for m in messages if m.get("role") != "system"]

    current_tokens = sum(estimate_tokens(m.get("content", ""), model) for m in system_msgs)

    if current_tokens > max_tokens:
        # If system messages alone exceed limit, we have to keep them but it's a problem
        return system_msgs

    result_msgs = []
    # Add messages from newest to oldest
    for msg in reversed(other_msgs):
        msg_tokens = estimate_tokens(msg.get("content", ""), model)
        if current_tokens + msg_tokens <= max_tokens:
            result_msgs.insert(0, msg)
            current_tokens += msg_tokens
        else:
            break

    return system_msgs + result_msgs
