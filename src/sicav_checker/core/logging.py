from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Iterator

try:
    from loguru import logger
except ImportError:
    class _Logger:
        def info(self, message: str, *args: object) -> None:
            print("INFO: " + message.format(*args))
        def warning(self, message: str, *args: object) -> None:
            print("WARNING: " + message.format(*args))
        def error(self, message: str, *args: object) -> None:
            print("ERROR: " + message.format(*args))
    logger = _Logger()


@contextmanager
def log_stage(stage: str, **context: object) -> Iterator[None]:
    start = perf_counter()
    logger.info("Stage '{}' started {}", stage, context)
    try:
        yield
    except Exception as exc:
        duration = perf_counter() - start
        logger.error("Stage '{}' failed after {:.3f}s: {}", stage, duration, exc)
        raise
    else:
        duration = perf_counter() - start
        logger.info("Stage '{}' finished in {:.3f}s", stage, duration)