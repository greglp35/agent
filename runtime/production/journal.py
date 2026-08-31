from __future__ import annotations
from pathlib import Path
from typing import Any
import json, re, time, uuid

_SECRET_KEYS = {"authorization", "api_key", "apikey", "token", "secret", "password", "x-api-key"}
_BEARER_RE = re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+")


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if str(k).lower() in _SECRET_KEYS or any(x in str(k).lower() for x in ("secret", "password", "api_key", "token")):
                out[k] = "***REDACTED***"
            else:
                out[k] = redact(v)
        return out
    if isinstance(value, list):
        return [redact(x) for x in value]
    if isinstance(value, tuple):
        return [redact(x) for x in value]
    if isinstance(value, str):
        return _BEARER_RE.sub("Bearer ***REDACTED***", value)
    return value


class ExecutionJournal:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        record = redact({
            "event_id": str(uuid.uuid4()),
            "ts": int(time.time()),
            **event,
        })
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record
