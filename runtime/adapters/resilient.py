from __future__ import annotations
import time
from typing import Any
from .base import LLMAdapter, LLMRequest, LLMResponse
from ..production import BudgetTracker, CircuitBreaker, ExecutionJournal, ProductionPolicy


class ResilientLLMAdapter:
    """Production wrapper adding retry, circuit breaker, budgets and journaling."""

    def __init__(self, inner: LLMAdapter, *, policy: ProductionPolicy | None = None,
                 journal: ExecutionJournal | None = None, sleeper=time.sleep, clock=time.monotonic):
        self.inner = inner
        self.name = f"resilient:{getattr(inner, 'name', type(inner).__name__)}"
        self.thread_safe = bool(getattr(inner, "thread_safe", False))
        self.policy = policy or ProductionPolicy()
        self.journal = journal
        self.sleeper = sleeper
        self.clock = clock
        self.budget = BudgetTracker(self.policy.budget)
        self.circuit = CircuitBreaker(
            failure_threshold=self.policy.circuit_failure_threshold,
            recovery_timeout_s=self.policy.circuit_recovery_timeout_s,
            clock=clock,
        )

    def _log(self, event: dict[str, Any]) -> None:
        if self.journal:
            self.journal.append(event)

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.budget.check_before()
        last_exc: BaseException | None = None
        for attempt in range(1, max(1, self.policy.retry.max_attempts) + 1):
            self.circuit.before_call()
            started = self.clock()
            try:
                response = self.inner.complete(request)
                latency_ms = max(0.0, (self.clock() - started) * 1000.0)
                self.budget.record(response.usage, latency_ms=latency_ms)
                self.circuit.record_success()
                self._log({
                    "type":"llm_call", "status":"EXECUTED", "attempt":attempt,
                    "host":getattr(self.inner,"name",type(self.inner).__name__),
                    "purpose":request.purpose, "usage":response.usage,
                    "latency_ms":round(latency_ms,3), "budget":self.budget.snapshot(),
                })
                return response
            except BaseException as exc:
                last_exc = exc
                self.circuit.record_failure()
                retry = attempt < self.policy.retry.max_attempts and self.policy.retry.should_retry(exc)
                self._log({
                    "type":"llm_call", "status":"RETRY" if retry else "BLOCKED",
                    "attempt":attempt, "purpose":request.purpose,
                    "error":type(exc).__name__, "message":str(exc),
                    "circuit":self.circuit.state,
                })
                if not retry:
                    raise
                self.sleeper(self.policy.retry.delay_for(attempt))
        assert last_exc is not None
        raise last_exc
