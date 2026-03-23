"""Unified LLM abstraction layer.

All LLM calls in the project go through this module, making it easy to
swap providers, add logging/caching, and track costs in one place.
"""

import json
import logging

from anthropic import AsyncAnthropic
from pydantic import BaseModel

from shared.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-4-6"
DEFAULT_MAX_TOKENS = 4096


async def extract_structured_data[T: BaseModel](
    system_prompt: str,
    user_content: str,
    response_model: type[T],
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> T:
    """Send a prompt to Claude and parse the response into a Pydantic model.

    Instructs the LLM to return JSON conforming to the provided schema,
    then validates the response with the Pydantic model.

    Args:
        system_prompt: System instructions for the LLM.
        user_content: User message (e.g., paper text to extract from).
        response_model: Pydantic model class to parse the response into.
        model: Anthropic model ID to use.
        max_tokens: Maximum tokens in the response.

    Returns:
        Validated instance of ``response_model``.

    Raises:
        ValueError: If the LLM response cannot be parsed into the model.
    """
    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    schema_json = json.dumps(response_model.model_json_schema(), indent=2)
    full_system = (
        f"{system_prompt}\n\n"
        f"Return your response as JSON matching this schema:\n{schema_json}\n"
        f"Return ONLY valid JSON, no markdown fences or extra text."
    )

    logger.info("LLM request: model=%s, response_model=%s", model, response_model.__name__)

    message = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=full_system,
        messages=[{"role": "user", "content": user_content}],
    )

    raw = message.content[0].text  # type: ignore[union-attr]
    raw = _clean_llm_json(raw)

    logger.info("LLM response: %d chars", len(raw))

    try:
        return response_model.model_validate_json(raw)
    except Exception as exc:
        raise ValueError(
            f"Failed to parse LLM response into {response_model.__name__}: {exc}"
        ) from exc


def _clean_llm_json(raw: str) -> str:
    """Strip markdown fences and surrounding text from LLM JSON output.

    Handles: leading whitespace, ```json fences, surrounding prose,
    and extracts the JSON object even from noisy output.

    Args:
        raw: Raw LLM response text.

    Returns:
        Cleaned JSON string.
    """
    text = raw.strip()

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0].strip()

    # If it's already valid-looking JSON, return it
    if text.startswith("{"):
        return text

    # Extract JSON object from surrounding prose
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]

    return text
