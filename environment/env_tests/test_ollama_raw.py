"""
Raw Ollama API test -- no LiteLLM, no ADK.

Calls both /api/chat (native) and /v1/chat/completions (OpenAI-compat)
with the same tool definition and prompt, then prints the raw JSON
responses so we can compare exactly what Ollama returns.

Run: python test_ollama_raw.py
"""

import json
import logging
import httpx

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt = "%H:%M:%S",
)
log = logging.getLogger(__name__)

BASE = "http://localhost:11434"
MODEL = "gemma4:e4b"

TOOL_DEF_NATIVE = {
    "type": "function",
    "function": {
        "name": "multiply",
        "description": "Multiply two numbers together.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["a", "b"],
        },
    },
}

MESSAGES = [
    {"role": "user", "content": "What is 17 times 23?"},
]


def test_native_chat():
    """Call /api/chat (Ollama native endpoint)."""
    log.info("=" * 60)
    log.info("TEST: /api/chat (native)")
    log.info("=" * 60)

    payload = {
        "model": MODEL,
        "messages": MESSAGES,
        "tools": [TOOL_DEF_NATIVE],
        "stream": False,
    }

    r = httpx.post(f"{BASE}/api/chat", json=payload, timeout=60)
    data = r.json()

    log.info("status: %d", r.status_code)
    log.info("response:\n%s", json.dumps(data, indent=2))

    msg = data.get("message", {})
    tool_calls = msg.get("tool_calls", [])
    content = msg.get("content", "")

    log.info("--- analysis ---")
    log.info("has tool_calls: %s (count=%d)", bool(tool_calls), len(tool_calls))
    log.info("content: %s", repr(content[:300]) if content else "<empty>")

    if tool_calls:
        log.info("tool_call[0]: %s", json.dumps(tool_calls[0], indent=2))

        # Feed the tool response back and get the final answer
        log.info("--- sending tool response back ---")
        messages_with_response = MESSAGES + [
            msg,
            {
                "role": "tool",
                "content": json.dumps({"result": 391}),
            },
        ]
        payload2 = {
            "model": MODEL,
            "messages": messages_with_response,
            "tools": [TOOL_DEF_NATIVE],
            "stream": False,
        }
        r2 = httpx.post(f"{BASE}/api/chat", json=payload2, timeout=60)
        data2 = r2.json()
        msg2 = data2.get("message", {})
        log.info("final response:\n%s", json.dumps(msg2, indent=2))

    return data


def test_openai_compat():
    """Call /v1/chat/completions (OpenAI-compatible endpoint)."""
    log.info("=" * 60)
    log.info("TEST: /v1/chat/completions (OpenAI-compat)")
    log.info("=" * 60)

    payload = {
        "model": MODEL,
        "messages": MESSAGES,
        "tools": [TOOL_DEF_NATIVE],
        "stream": False,
    }

    r = httpx.post(
        f"{BASE}/v1/chat/completions",
        json=payload,
        headers={"Authorization": "Bearer unused"},
        timeout=60,
    )
    data = r.json()

    log.info("status: %d", r.status_code)
    log.info("response:\n%s", json.dumps(data, indent=2))

    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})
    tool_calls = msg.get("tool_calls", [])
    content = msg.get("content", "")
    finish = choice.get("finish_reason", "")

    log.info("--- analysis ---")
    log.info("finish_reason: %s", finish)
    log.info("has tool_calls: %s (count=%d)", bool(tool_calls), len(tool_calls))
    log.info("content: %s", repr(content[:300]) if content else "<empty>")

    if tool_calls:
        log.info("tool_call[0]: %s", json.dumps(tool_calls[0], indent=2))

        # Feed the tool response back and get the final answer
        log.info("--- sending tool response back ---")
        messages_with_response = MESSAGES + [
            {
                "role": "assistant",
                "content": content or None,
                "tool_calls": tool_calls,
            },
            {
                "role": "tool",
                "tool_call_id": tool_calls[0].get("id", "call_0"),
                "content": json.dumps({"result": 391}),
            },
        ]
        payload2 = {
            "model": MODEL,
            "messages": messages_with_response,
            "tools": [TOOL_DEF_NATIVE],
            "stream": False,
        }
        r2 = httpx.post(
            f"{BASE}/v1/chat/completions",
            json=payload2,
            headers={"Authorization": "Bearer unused"},
            timeout=60,
        )
        data2 = r2.json()
        choice2 = data2.get("choices", [{}])[0]
        msg2 = choice2.get("message", {})
        log.info("final response:\n%s", json.dumps(msg2, indent=2))
        log.info("finish_reason: %s", choice2.get("finish_reason", ""))

    return data


if __name__ == "__main__":
    test_native_chat()
    print()
    test_openai_compat()
