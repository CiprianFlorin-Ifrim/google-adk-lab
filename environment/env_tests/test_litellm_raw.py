"""
LiteLLM direct test -- no ADK, just LiteLLM on top of Ollama /v1.

Calls litellm.completion directly to see what LiteLLM does to the
Ollama response before ADK ever touches it.

Run: python test_litellm_raw.py
"""

import os
import json
import logging

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt = "%H:%M:%S",
)
log = logging.getLogger(__name__)

os.environ["OPENAI_API_BASE"] = "http://localhost:11434/v1"
os.environ["OPENAI_API_KEY"] = "unused"

import litellm

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


def test_step1_tool_call():
    """First LLM call -- should return a tool call."""
    log.info("=" * 60)
    log.info("STEP 1: initial call (expecting tool_call)")
    log.info("=" * 60)

    response = litellm.completion(
        model    = "openai/gemma4:e4b",
        messages = MESSAGES,
        tools    = [TOOL_DEF],
    )

    # Raw response object
    log.info("raw response type: %s", type(response).__name__)
    log.info("raw response dump:\n%s", json.dumps(response.model_dump(), indent=2, default=str))

    choice = response.choices[0]
    msg = choice.message

    log.info("--- analysis ---")
    log.info("finish_reason: %s", choice.finish_reason)
    log.info("content: %s", repr(msg.content))
    log.info("tool_calls: %s", msg.tool_calls)

    # Check for reasoning field
    if hasattr(msg, "reasoning"):
        log.info("reasoning field: %s", repr(msg.reasoning))
    if hasattr(msg, "reasoning_content"):
        log.info("reasoning_content field: %s", repr(msg.reasoning_content))

    # Check provider_specific_fields
    psf = getattr(msg, "provider_specific_fields", None)
    if psf:
        log.info("provider_specific_fields: %s", psf)

    return response


def test_step2_tool_response(step1_response):
    """Second LLM call -- feed back the tool result."""
    log.info("=" * 60)
    log.info("STEP 2: tool response (expecting final answer)")
    log.info("=" * 60)

    choice = step1_response.choices[0]
    msg = choice.message

    if not msg.tool_calls:
        log.info("no tool_calls in step 1, skipping step 2")
        return None

    tc = msg.tool_calls[0]

    messages_round2 = MESSAGES + [
        {
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": tc.id,
            "content": json.dumps({"result": 391}),
        },
    ]

    response2 = litellm.completion(
        model    = "openai/gemma4:e4b",
        messages = messages_round2,
        tools    = [TOOL_DEF],
    )

    log.info("raw response dump:\n%s", json.dumps(response2.model_dump(), indent=2, default=str))

    choice2 = response2.choices[0]
    msg2 = choice2.message

    log.info("--- analysis ---")
    log.info("finish_reason: %s", choice2.finish_reason)
    log.info("content: %s", repr(msg2.content))
    log.info("tool_calls: %s", msg2.tool_calls)

    if hasattr(msg2, "reasoning"):
        log.info("reasoning field: %s", repr(msg2.reasoning))
    if hasattr(msg2, "reasoning_content"):
        log.info("reasoning_content field: %s", repr(msg2.reasoning_content))

    psf = getattr(msg2, "provider_specific_fields", None)
    if psf:
        log.info("provider_specific_fields: %s", psf)

    return response2


if __name__ == "__main__":
    r1 = test_step1_tool_call()
    print()
    test_step2_tool_response(r1)
