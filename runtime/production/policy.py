from __future__ import annotations

from dataclasses import dataclass, field
import random
import time
from typing import Any, Callable, Iterable


class ProductionError(RuntimeError):
    pass


class BudgetExceeded(ProductionError):
    pass


class CircuitOpen(ProductionError):
    pass


class ApprovalRequired(ProductionError):
    pass


class ProviderResponseError(ProductionError):
    pass


class ProviderHTTPError(ProductionError):
    def __init__(self, status: int, message: str = "", *, retryable: bool | None = None):
        self.status = int(status)
        self.retryable = bool(retryable) if retryable is not None else self.status in {408, 409, 425, 429, 500, 502, 503, 504}
        super().__init__(f"HTTP {self.status}: {message}".strip())


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_s: float = 0.25
    max_delay_s: float = 4.0
    jitter_s: float = 0.10

    def delay_for(self, attempt: int, *, rng: Callable[[], float] = random.random) -> float:
        base = min(self.max_delay_s, self.base_delay_s * (2 ** max(0, attempt - 1)))
        return max(0.0, base + (rng() * self.jitter_s if self.jitter_s else 0.0))

    def should_retry(self, exc: BaseException) -> bool:
        if isinstance(exc, ProviderHTTPError):
            return exc.retryable
        return isinstance(exc, (TimeoutError, ConnectionError))


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout_s: float = 30.0
    clock: Callable[[], float] = time.monotonic
    failures: int = 0
    opened_at: float | None = None
    half_open_probe: bool = False

    @property
    def state(self) -> str:
        if self.opened_at is None:
            return "CLOSED"
        if self.clock() - self.opened_at >= self.recovery_timeout_s:
            return "HALF_OPEN"
        return "OPEN"

    def before_call(self) -> None:
        state = self.state
        if state == "OPEN":
            raise CircuitOpen("Circuit breaker is OPEN")
        if state == "HALF_OPEN":
            if self.half_open_probe:
                raise CircuitOpen("Circuit breaker HALF_OPEN probe already in flight")
            self.half_open_probe = True

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None
        self.half_open_probe = False

    def record_failure(self) -> None:
        self.failures += 1
        self.half_open_probe = False
        if self.failures >= max(1, self.failure_threshold):
            self.opened_at = self.clock()


@dataclass(frozen=True)
class BudgetPolicy:
    max_requests: int | None = None
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    max_total_tokens: int | None = None
    max_cost_usd: float | None = None
    max_latency_ms: float | None = None


@dataclass
class BudgetTracker:
    policy: BudgetPolicy = field(default_factory=BudgetPolicy)
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0

    def check_before(self) -> None:
        p = self.policy
        if p.max_requests is not None and self.requests >= p.max_requests:
            raise BudgetExceeded(f"Request budget exceeded: {self.requests}/{p.max_requests}")

    def record(self, usage: dict[str, Any] | None = None, *, latency_ms: float = 0.0) -> None:
        usage = usage or {}
        self.requests += 1
        self.input_tokens += int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
        self.output_tokens += int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
        self.cost_usd += float(usage.get("cost_usd") or 0.0)
        self.latency_ms += float(latency_ms or 0.0)
        self._check_after()

    def _check_after(self) -> None:
        p = self.policy
        total = self.input_tokens + self.output_tokens
        checks = [
            (p.max_input_tokens, self.input_tokens, "input token"),
            (p.max_output_tokens, self.output_tokens, "output token"),
            (p.max_total_tokens, total, "total token"),
        ]
        for limit, value, label in checks:
            if limit is not None and value > limit:
                raise BudgetExceeded(f"{label} budget exceeded: {value}/{limit}")
        if p.max_cost_usd is not None and self.cost_usd > p.max_cost_usd:
            raise BudgetExceeded(f"Cost budget exceeded: ${self.cost_usd:.6f}/${p.max_cost_usd:.6f}")
        if p.max_latency_ms is not None and self.latency_ms > p.max_latency_ms:
            raise BudgetExceeded(f"Latency budget exceeded: {self.latency_ms:.1f}/{p.max_latency_ms:.1f} ms")

    def snapshot(self) -> dict[str, Any]:
        return {
            "requests": self.requests,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "cost_usd": round(self.cost_usd, 8),
            "latency_ms": round(self.latency_ms, 3),
        }


@dataclass
class ProductionPolicy:
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    budget: BudgetPolicy = field(default_factory=BudgetPolicy)
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout_s: float = 30.0
    request_timeout_s: float = 60.0
    approval_required_effects: frozenset[str] = frozenset({
        "write", "external_side_effect", "destructive", "production_deploy"
    })
