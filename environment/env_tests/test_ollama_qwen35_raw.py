"""
Raw Ollama test for Qwen 3.5 9B -- no LiteLLM, no ADK.

Tests the /v1/chat/completions endpoint with and without think=false
to check if thinking can be disabled and tool calling still works.

Run: python test_ollama_qwen35_raw.py
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

BASE  = "http://localhost:11434"
MODEL = "qwen3.5:9b"

TOOL_DEF = {
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

HEADERS = {"Authorization": "Bearer unused"}


def call_v1(payload, label=""):
    """POST to /v1/chat/completions and return parsed JSON."""
    r = httpx.post(
        f"{BASE}/v1/chat/completions",
        json=payload,
        headers=HEADERS,
        timeout=120,
    )
    return r.json()


def analyse_response(data, step_label):
    """Log key fields from a /v1 response."""
    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})

    log.info("[%s] finish_reason: %s", step_label, choice.get("finish_reason"))
    log.info("[%s] content: %s", step_label, repr((msg.get("content") or "")[:200]))
    log.info("[%s] has reasoning: %s", step_label, bool(msg.get("reasoning")))
    log.info("[%s] tool_calls: %s", step_label,
             len(msg.get("tool_calls") or []))

    if msg.get("reasoning"):
        log.info("[%s] reasoning preview: %s", step_label,
                 msg["reasoning"][:150])

    return msg


def run_tool_roundtrip(think_flag, label):
    """Two-step tool call roundtrip with a given think setting."""
    log.info("=" * 60)
    log.info("TEST: %s (think=%s)", label, think_flag)
    log.info("=" * 60)

    # Step 1: initial call expecting tool_call
    payload = {
        "model": MODEL,
        "messages": MESSAGES,
        "tools": [TOOL_DEF],
        "stream": False,
    }
    if think_flag is not None:
        payload["think"] = think_flag

    log.info("--- step 1: expecting tool call ---")
    data1 = call_v1(payload)
    msg1 = analyse_response(data1, f"{label}/step1")

    tool_calls = msg1.get("tool_calls")
    if not tool_calls:
        log.info("[%s] no tool calls returned, skipping step 2", label)
        return

    # Step 2: send tool result back
    log.info("--- step 2: sending tool response, expecting final answer ---")
    messages_round2 = MESSAGES + [
        {
            "role": "assistant",
            "content": msg1.get("content") or None,
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
        "messages": messages_round2,
        "tools": [TOOL_DEF],
        "stream": False,
    }
    if think_flag is not None:
        payload2["think"] = think_flag

    data2 = call_v1(payload2)
    msg2 = analyse_response(data2, f"{label}/step2")

    correct = "391" in (msg2.get("content") or "")
    log.info("[%s] correct answer (391 in content): %s", label, correct)


if __name__ == "__main__":
    # Test 1: thinking enabled (default)
    run_tool_roundtrip(think_flag=None, label="thinking_default")
    print()

    # Test 2: thinking explicitly disabled
    run_tool_roundtrip(think_flag=False, label="nothink")
