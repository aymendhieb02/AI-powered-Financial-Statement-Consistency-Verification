from __future__ import annotations

from loguru import logger

from sicav_checker.config import settings


def ask_ollama(prompt: str) -> str | None:
    try:
        import ollama

        response = ollama.chat(model=settings.ollama_model, messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"]
    except Exception as exc:
        logger.warning("Ollama unavailable, continuing without AI: {}", exc)
        return None
