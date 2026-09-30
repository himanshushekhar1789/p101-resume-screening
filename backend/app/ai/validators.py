import json
import logging
import re
from typing import Type, TypeVar, Tuple
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMValidationError(Exception):
    """Raised when LLM response is malformed JSON or fails Pydantic schema validation."""
    pass


def extract_json_payload(raw_text: str) -> str:
    """
    Extracts clean JSON substring from a potentially noisy LLM response.
    Handles ```json ... ``` codeblocks or leading/trailing commentary.
    """
    text = raw_text.strip()

    # Match ```json <content> ```
    codeblock_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if codeblock_match:
        return codeblock_match.group(1).strip()

    # Look for outermost braces { ... }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace : last_brace + 1].strip()

    return text


def validate_llm_json(raw_text: str, target_model: Type[T]) -> T:
    """
    Parses and validates raw LLM text output against a target Pydantic model.
    Raises LLMValidationError with sanitized context if validation fails.
    """
    cleaned_json_str = extract_json_payload(raw_text)

    try:
        data = json.loads(cleaned_json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from LLM: {str(e)} | Content: {raw_text[:200]}")
        raise LLMValidationError(f"LLM output could not be parsed as valid JSON: {str(e)}")

    if not isinstance(data, dict):
        raise LLMValidationError(f"Expected JSON object at top level, received {type(data).__name__}")

    try:
        validated_instance = target_model.model_validate(data)
        return validated_instance
    except ValidationError as e:
        logger.error(f"Pydantic schema validation error on LLM response: {str(e)}")
        raise LLMValidationError(f"LLM output failed schema validation: {str(e)}")
