"""Multi-provider AI fallback: Gemini -> Groq -> OpenRouter, with key/model rotation."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from urllib import error, request

logger = logging.getLogger(__name__)
_INSTALLED = False


def _values(prefix: str, count: int) -> list[str]:
    names = [prefix] + [f"{prefix}_{i}" for i in range(2, count + 1)]
    return [os.environ.get(name, "").strip() for name in names if os.environ.get(name, "").strip()]


def gemini_keys() -> list[str]:
    return _values("GEMINI_API_KEY", 5)


def groq_keys() -> list[str]:
    return _values("GROQ_API_KEY", 3)


def openrouter_keys() -> list[str]:
    return _values("OPENROUTER_API_KEY", 3)


def openrouter_models() -> list[str]:
    configured = _values("OPENROUTER_MODEL", 5)
    return configured or ["openrouter/auto"]


def _openrouter_generate(prompt: str, key: str, model: str) -> str:
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "You are the RATHOD VIP quiz engine. Return only the exact requested valid JSON array."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.25,
        "max_tokens": 8192,
    }).encode("utf-8")
    req = request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "HTTP-Referer": "https://teachnlogy7509-pixel.github.io/RATHOD-HUB/",
            "X-Title": "RATHOD HUB Telegram Quiz",
        },
    )
    try:
        with request.urlopen(req, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return str(payload.get("choices", [{}])[0].get("message", {}).get("content") or "")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc


def install(quiz_module):
    """Patch provider key discovery and add OpenRouter after Gemini/Groq exhaustion."""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True
    quiz_module._api_keys = gemini_keys
    quiz_module._groq_keys = groq_keys
    original = quiz_module.generate_questions

    async def generate_questions(topic: str, count: int, style: str = "quiz"):
        provider_errors = []
        try:
            # Existing engine rotates every configured Gemini key/model, then Groq keys.
            return await original(topic, count, style)
        except Exception as exc:
            provider_errors.append("Gemini/Groq: " + str(exc)[:180])
            logger.warning("Gemini/Groq exhausted; switching to OpenRouter: %s", exc)
        keys = openrouter_keys()
        if not keys:
            raise RuntimeError("All Gemini/Groq attempts failed and no OpenRouter key is configured. " + provider_errors[-1])
        prompt = quiz_module._build_prompt(topic, count, style)
        for key_index, key in enumerate(keys):
            for model in openrouter_models():
                for retry in range(2):
                    try:
                        raw_text = await asyncio.to_thread(_openrouter_generate, prompt, key, model)
                        raw = quiz_module._safe_parse_json(raw_text)
                        valid = quiz_module._validate(raw, count)
                        if len(valid) < count:
                            raise ValueError(f"OpenRouter returned {len(valid)}/{count} valid questions")
                        logger.info("OpenRouter fallback succeeded: key=%s model=%s", key_index + 1, model)
                        return valid[:count]
                    except Exception as exc:
                        provider_errors.append(f"OpenRouter key {key_index + 1}/{model}: {str(exc)[:180]}")
                        logger.warning("OpenRouter fallback retry failed: %s", provider_errors[-1])
                        await asyncio.sleep(1 + retry)
        raise RuntimeError("All AI providers failed. Last: " + provider_errors[-1])

    quiz_module.generate_questions = generate_questions
    logger.info("AI fallback installed: Gemini(%s) -> Groq(%s) -> OpenRouter(%s)", len(gemini_keys()), len(groq_keys()), len(openrouter_keys()))


async def cmd_aistatus(update, context):
    g, q, o = len(gemini_keys()), len(groq_keys()), len(openrouter_keys())
    models = ", ".join(openrouter_models())
    await update.message.reply_text(
        "🤖 RATHOD Multi-AI Status\n\n"
        f"Gemini keys: {g}/3 minimum\n"
        f"Groq keys: {q}/2 minimum\n"
        f"OpenRouter keys: {o}/2 minimum\n"
        f"OpenRouter models: {models}\n\n"
        "Fallback: Gemini keys/models → Groq keys/model → OpenRouter keys/models"
    )
