from __future__ import annotations

from typing import Any, Callable, Dict
from .base import LLMRequest, LLMResponse


class CallableLLMAdapter:
    """Wrap any Python callable as a COMMAND OS LLM adapter.

    The callable receives an ``LLMRequest`` and may return either an ``LLMResponse``
    or a dictionary. This keeps COMMAND OS independent from any specific vendor SDK.
    """

    def __init__(self, fn: Callable[[LLMRequest], LLMResponse | Dict[str, Any]], *, name: str = "callable-host", thread_safe: bool = False):
        self.fn = fn
        self.name = name
        self.thread_safe = thread_safe

    def complete(self, request: LLMRequest) -> LLMResponse:
        result = self.fn(request)
        if isinstance(result, LLMResponse):
            return result
        if isinstance(result, dict):
            return LLMResponse(content=result, model=self.name)
        raise TypeError("LLM adapter callable must return LLMResponse or dict")
