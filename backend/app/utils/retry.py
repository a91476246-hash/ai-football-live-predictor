"""Async retry helpers built on tenacity."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any, ParamSpec, TypeVar

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

P = ParamSpec("P")
R = TypeVar("R")


def async_retry(
    *,
    attempts: int = 3,
    min_wait: float = 0.5,
    max_wait: float = 5.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]],
    Callable[P, Coroutine[Any, Any, R]],
]:
    """Decorate an async function with exponential-backoff retries.

    Args:
        attempts: maximum attempts before giving up.
        min_wait: initial wait between attempts (seconds).
        max_wait: maximum wait between attempts (seconds).
        exceptions: tuple of exception classes that trigger a retry.
    """

    def decorator(
        func: Callable[P, Coroutine[Any, Any, R]],
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(attempts),
                wait=wait_exponential(multiplier=min_wait, max=max_wait),
                retry=retry_if_exception_type(exceptions),
                reraise=True,
            ):
                with attempt:
                    return await func(*args, **kwargs)
            # Unreachable, but satisfies type checker.
            raise RuntimeError("async_retry: exhausted without return")

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator
