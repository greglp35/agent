from __future__ import annotations
import json, os
from typing import Any
from .base import LLMRequest, LLMResponse
from ..production import ProviderResponseError, JSONHTTPTransport, UrllibJSONTransport


def _extract_text(data: dict[str, Any]) -> str:
    direct = data.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    parts = []
    for item in data.get("output", []) if isinstance(data.get("output"), list) else []:
        for content in item.get("content", []) if isinstance(item, dict) else []:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                parts.append(content["text"])
    return "\n".join(parts)


def _parse_json_text(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:].lstrip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderResponseError("OpenAI response was not a valid JSON object") from exc
    if not isinstance(value, dict):
        raise ProviderResponseError("OpenAI response JSON must be an object")
    return value


class OpenAIResponsesAdapter:
    """Concrete adapter for the OpenAI Responses API using only stdlib HTTP."""
    thread_safe = True

    def __init__(self, model: str, *, api_key: str | None = None,
                 endpoint: str = "https://api.openai.com/v1/responses",
                 transport: JSONHTTPTransport | None = None, timeout_s: float = 60.0,
                 store: bool = False):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.endpoint = endpoint
        self.transport = transport or UrllibJSONTransport()
        self.timeout_s = timeout_s
        self.store = bool(store)
        self.name = f"openai-responses:{model}"

    def complete(self, request: LLMRequest) -> LLMResponse:
        contract = json.dumps(request.response_contract, ensure_ascii=False)
        instructions = request.system + "\nReturn ONLY one valid JSON object. Response contract: " + contract
        result = self.transport.post(
            self.endpoint,
            headers={"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"},
            payload={"model":self.model,"instructions":instructions,"input":request.user,"store":self.store},
            timeout=self.timeout_s,
        )
        data = result.data
        text = _extract_text(data)
        if not text:
            raise ProviderResponseError("OpenAI response contained no text output")
        content = _parse_json_text(text)
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        return LLMResponse(content=content, model=data.get("model") or self.model, usage=usage, raw=data)
