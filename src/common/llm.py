from __future__ import annotations

import json
from typing import Any

from openai import OpenAI


class LlmError(RuntimeError):
    """Raised when an LLM response cannot be used."""


def get_text_response(model: str, prompt: str, timeout_seconds: int = 90) -> str:
    client = OpenAI(timeout=timeout_seconds)
    response = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=12000,
    )
    text = getattr(response, "output_text", None)
    if text:
        return text
    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            value = getattr(content, "text", None)
            if value:
                chunks.append(value)
    if chunks:
        return "\n".join(chunks)
    raise LlmError("The model returned no text output.")


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LlmError("The model did not return a JSON object.")
    return json.loads(cleaned[start : end + 1])
