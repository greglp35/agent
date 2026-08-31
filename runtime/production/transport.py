from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol
import json
import urllib.error
import urllib.request
from .policy import ProviderHTTPError, ProviderResponseError


@dataclass
class HTTPResult:
    status: int
    data: dict[str, Any]
    headers: dict[str, str]


class JSONHTTPTransport(Protocol):
    def post(self, url: str, *, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> HTTPResult:
        ...


class UrllibJSONTransport:
    def post(self, url: str, *, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> HTTPResult:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ProviderResponseError("Provider returned non-JSON response") from exc
                return HTTPResult(int(response.status), data, dict(response.headers.items()))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            raise ProviderHTTPError(exc.code, raw[:1000]) from exc
        except urllib.error.URLError as exc:
            reason = exc.reason
            if isinstance(reason, TimeoutError):
                raise reason
            raise ConnectionError(str(reason)) from exc
