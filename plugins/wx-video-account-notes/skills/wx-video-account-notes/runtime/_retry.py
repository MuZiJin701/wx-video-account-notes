from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")

_MAX_RETRIES = 3
_INITIAL_BACKOFF_SECONDS = 2.0


def _log_retry(message: str) -> None:
    print(f"[wx-video-account-notes][retry] {message}")


def retry_call(action: Callable[[], T], *, description: str = "", max_retries: int = _MAX_RETRIES) -> T:
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return action()
        except Exception as exc:
            last_error = exc
            if attempt == max_retries:
                break
            delay = _INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))
            label = f" ({description})" if description else ""
            _log_retry(f"attempt={attempt}/{max_retries} failed, retrying in {delay:.1f}s{label}")
            time.sleep(delay)
    raise RuntimeError(f"All {max_retries} retries exhausted") from last_error
