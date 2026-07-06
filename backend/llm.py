"""OpenRouter LLM client (OpenAI-compatible API).

Configure with:
  OPENROUTER_API_KEY  - required for AI features
  OPENROUTER_MODELS   - comma-separated model list (OPENROUTER_MODEL also
                        accepted). Requests rotate through the list round-robin
                        so load spreads across models; on failure the next
                        model is tried immediately, and full cycles retry with
                        exponential backoff (free-tier models rate-limit often).
"""

import itertools
import logging
import os
import random
import time
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

# Modules call llm.get_client()/models() at import or request time; load the
# env here so config doesn't depend on which module imported dotenv first
load_dotenv()

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
MAX_CYCLES = 3  # full passes over the model list before giving up

_rotation = itertools.count()


def get_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)


def models() -> list[str]:
    configured = os.getenv("OPENROUTER_MODELS") or os.getenv("OPENROUTER_MODEL") or DEFAULT_MODEL
    # Some .env parsers keep surrounding quotes; strip them before splitting
    configured = configured.strip().strip("\"'")
    return [m.strip() for m in configured.split(",") if m.strip()]


def complete(client: OpenAI, prompt: str) -> str:
    """Run the prompt, rotating round-robin through the configured models.

    Each call starts at the next model in the rotation. On failure the next
    model is tried immediately; if the whole list fails, the cycle repeats
    (up to MAX_CYCLES) with exponential backoff between cycles.
    """
    model_list = models()
    start = next(_rotation) % len(model_list)
    delay = 1.0
    last_error: Optional[Exception] = None

    for cycle in range(MAX_CYCLES):
        if cycle:
            time.sleep(delay + random.random())
            delay = min(delay * 2, 8.0)
        for offset in range(len(model_list)):
            model = model_list[(start + offset) % len(model_list)]
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                # OpenRouter can return HTTP 200 with choices=None and the
                # real error in the body (e.g. upstream rate limiting)
                if not response.choices:
                    error = getattr(response, "error", None)
                    last_error = RuntimeError(f"{model} returned no choices: {error or 'unknown error'}")
                    logger.warning(f"OpenRouter model {model} failed (cycle {cycle + 1}): {last_error}")
                    continue
                content = response.choices[0].message.content
                if content:
                    return content
                last_error = RuntimeError(f"{model} returned empty content")
            except Exception as e:
                logger.warning(f"OpenRouter model {model} failed (cycle {cycle + 1}): {e}")
                last_error = e

    raise RuntimeError(f"All configured OpenRouter models failed after {MAX_CYCLES} cycles: {last_error}")
