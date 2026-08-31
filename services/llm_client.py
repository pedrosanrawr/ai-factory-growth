"""DONES work file: shared Gemini integration.

Steps:
1. Keep provider initialization and API-key loading lazy.
2. Add one structured JSON helper; agents must not call the SDK directly.
3. Return a typed, safe failure for timeout, provider, and malformed-output
   errors so callers can use their deterministic fallback.
4. Keep credentials in environment variables and mock all provider calls in
   tests.
5. Test configured, missing-key, valid, timeout, and malformed-response paths.

Done when no analysis agent needs to call the provider SDK directly and failed
calls can safely use deterministic fallbacks.
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from google import genai


DEFAULT_MODEL = "gemini-3.6-flash"
REQUEST_TIMEOUT_SECONDS = 30

# Gemini no longer makes 2.5 Flash available to newly created API projects.
# Keep this mapping so an older local .env continues to work during the change.
MODEL_ALIASES = {"gemini-2.5-flash": DEFAULT_MODEL}


class LLMConfigurationError(RuntimeError):
    """Raised when the local Gemini credentials have not been configured."""


def _load_configuration() -> tuple[str, str]:
    """Load local Gemini settings without exposing the API key."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    model = MODEL_ALIASES.get(model, model)

    if not api_key:
        raise LLMConfigurationError(
            "GEMINI_API_KEY is missing. Add it to your local .env file; never commit it."
        )
    return api_key, model


def is_llm_configured() -> bool:
    """Return whether a local Gemini key is available, without returning it."""
    load_dotenv()
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


@lru_cache(maxsize=1)
def get_llm_client() -> genai.Client:
    """Create and cache the official Gemini client."""
    api_key, _ = _load_configuration()
    return genai.Client(api_key=api_key)


def ask_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 800,
) -> str:
    """Send one explicit text request to Gemini and return the model's answer.

    Agents should request structured JSON in their prompts, validate the result,
    and retain the existing deterministic scoring rules as the final authority.
    """
    _, configured_model = _load_configuration()
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
    content = interaction.output_text
    if not content:
        raise RuntimeError("The LLM returned an empty response.")
    return content.strip()
