"""Shared Gemini integration for the AI Factory Growth project."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from google import genai
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError


DEFAULT_MODEL = "gemini-3.6-flash"
REQUEST_TIMEOUT_SECONDS = 30

# Keep this mapping so an older local .env setting is upgraded automatically.
MODEL_ALIASES = {
    "gemini-2.5-flash": DEFAULT_MODEL,
}


class LLMConfigurationError(RuntimeError):
    """Raised when the local Gemini credentials are not configured."""


class LLMProviderError(RuntimeError):
    """Raised when the Gemini provider request fails."""


class LLMTimeoutError(LLMProviderError):
    """Raised when a Gemini request times out."""


class LLMResponseError(RuntimeError):
    """Raised when Gemini returns an invalid or unusable response."""


class LLMErrorType(str, Enum):
    """Stable error categories for callers and tests."""

    CONFIGURATION = "configuration"
    TIMEOUT = "timeout"
    PROVIDER = "provider"
    MALFORMED_RESPONSE = "malformed_response"
    INVALID_INPUT = "invalid_input"


@dataclass(frozen=True)
class LLMResult:
    """Typed result returned by the structured JSON helper."""

    ok: bool
    data: dict[str, Any] | None = None
    error_type: LLMErrorType | None = None
    error: str | None = None

    @classmethod
    def success(cls, data: dict[str, Any]) -> "LLMResult":
        """Create a successful result."""
        return cls(ok=True, data=data)

    @classmethod
    def failure(
        cls,
        error_type: LLMErrorType,
        error: str,
    ) -> "LLMResult":
        """Create a failed result."""
        return cls(
            ok=False,
            error_type=error_type,
            error=error,
        )


def _validate_json_against_schema(data: dict[str, Any], schema: dict[str, Any]) -> None:
    """Validate a parsed model response against the caller's JSON Schema."""
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(data)


def _load_configuration() -> tuple[str, str]:
    """Load local Gemini settings without exposing the API key."""
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    model = MODEL_ALIASES.get(model, model)

    if not api_key:
        raise LLMConfigurationError(
            "GEMINI_API_KEY is missing. "
            "Add it to your local .env file; never commit it."
        )

    return api_key, model


def is_llm_configured() -> bool:
    """Return whether a local Gemini API key is available."""
    load_dotenv()
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


@lru_cache(maxsize=1)
def get_llm_client() -> genai.Client:
    """Create and cache the official Gemini client lazily."""
    api_key, _ = _load_configuration()
    return genai.Client(api_key=api_key)


def _validate_common_input(
    system_prompt: str,
    user_prompt: str,
) -> None:
    """Validate prompt inputs before making a provider call."""
    if not isinstance(system_prompt, str) or not system_prompt.strip():
        raise ValueError("system_prompt must be a non-empty string.")

    if not isinstance(user_prompt, str) or not user_prompt.strip():
        raise ValueError("user_prompt must be a non-empty string.")


def ask_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 800,
) -> str:
    """Send one explicit text request to Gemini and return the model answer."""

    _validate_common_input(system_prompt, user_prompt)

    _, configured_model = _load_configuration()

    try:
        interaction = get_llm_client().interactions.create(
            model=model or configured_model,
            system_instruction=system_prompt,
            input=user_prompt,
            generation_config={
                "temperature": max(0.01, min(2.0, float(temperature))),
                "max_output_tokens": max(1, int(max_tokens)),
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except TimeoutError as exc:
        raise LLMTimeoutError("Gemini request timed out.") from exc
    except Exception as exc:
        raise LLMProviderError("Gemini request failed.") from exc

    content = interaction.output_text

    if not content:
        raise LLMResponseError("The LLM returned an empty response.")

    return content.strip()


def ask_llm_json(
    system_prompt: str,
    user_prompt: str,
    *,
    schema: dict[str, Any],
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 800,
) -> LLMResult:
    """
    Send a structured JSON request to Gemini.

    The provider is instructed to return JSON conforming to the supplied
    JSON schema. Provider, timeout, configuration, invalid-input, and
    malformed-response failures are returned as typed LLMResult failures
    so downstream agents can use deterministic fallbacks.
    """
    try:
        _validate_common_input(system_prompt, user_prompt)

        if not isinstance(schema, dict) or not schema:
            return LLMResult.failure(
                LLMErrorType.INVALID_INPUT,
                "schema must be a non-empty dictionary.",
            )

        _, configured_model = _load_configuration()

        interaction = get_llm_client().interactions.create(
            model=model or configured_model,
            system_instruction=system_prompt,
            input=user_prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": schema,
            },
            generation_config={
                "temperature": max(0.01, min(2.0, float(temperature))),
                "max_output_tokens": max(1, int(max_tokens)),
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        content = interaction.output_text

        if not content or not content.strip():
            return LLMResult.failure(
                LLMErrorType.MALFORMED_RESPONSE,
                "The LLM returned an empty response.",
            )

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            return LLMResult.failure(
                LLMErrorType.MALFORMED_RESPONSE,
                f"The LLM returned malformed JSON: {exc.msg}.",
            )

        if not isinstance(data, dict):
            return LLMResult.failure(
                LLMErrorType.MALFORMED_RESPONSE,
                "The LLM response must be a JSON object.",
            )

        try:
            _validate_json_against_schema(data, schema)
        except (SchemaError, ValidationError) as exc:
            return LLMResult.failure(
                LLMErrorType.MALFORMED_RESPONSE,
                f"The LLM response does not match the JSON schema: {exc.message}.",
            )

        return LLMResult.success(data)

    except LLMConfigurationError as exc:
        return LLMResult.failure(
            LLMErrorType.CONFIGURATION,
            str(exc),
        )

    except TimeoutError:
        return LLMResult.failure(
            LLMErrorType.TIMEOUT,
            "Gemini request timed out.",
        )

    except ValueError as exc:
        return LLMResult.failure(
            LLMErrorType.INVALID_INPUT,
            str(exc),
        )

    except Exception:
        return LLMResult.failure(
            LLMErrorType.PROVIDER,
            "Gemini provider request failed.",
        )
