from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Protocol, runtime_checkable


@dataclass(frozen=True)
class LLMRequest:
    """Host-neutral semantic request sent to an LLM adapter."""

    purpose: str
    system: str
    user: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    response_contract: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Normalized host-neutral response returned by an LLM adapter."""

    content: Dict[str, Any]
    model: str | None = None
    usage: Dict[str, Any] = field(default_factory=dict)
    raw: Any = None


@runtime_checkable
class LLMAdapter(Protocol):
    """Minimal protocol a host must implement for semantic execution."""

    name: str
    thread_safe: bool

    def complete(self, request: LLMRequest) -> LLMResponse:
        ...


@runtime_checkable
class ToolAdapter(Protocol):
    """Minimal protocol for a concrete external capability such as web.search."""

    capability: str

    def invoke(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        ...
