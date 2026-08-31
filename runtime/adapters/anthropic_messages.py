from __future__ import annotations
import json, os
from typing import Any
from .base import LLMRequest, LLMResponse
from ..production import ProviderResponseError, JSONHTTPTransport, UrllibJSONTransport


def _extract_text(data: dict[str, Any]) -> str:
    parts=[]
    for block in data.get("content", []) if isinstance(data.get("content"), list) else []:
        if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"])
    return "\n".join(parts)


def _parse_json_text(text: str) -> dict[str, Any]:
    text=text.strip()
    if text.startswith("```"):
        text=text.strip("`")
        if text.lstrip().startswith("json"):
            text=text.lstrip()[4:].lstrip()
    try:
        value=json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderResponseError("Anthropic response was not a valid JSON object") from exc
    if not isinstance(value, dict):
        raise ProviderResponseError("Anthropic response JSON must be an object")
    return value


class AnthropicMessagesAdapter:
    """Concrete adapter for Anthropic Messages API using only stdlib HTTP."""
    thread_safe = True

    def __init__(self, model: str, *, api_key: str | None = None, max_tokens: int = 4096,
                 endpoint: str = "https://api.anthropic.com/v1/messages",
                 anthropic_version: str = "2023-06-01", transport: JSONHTTPTransport | None = None,
                 timeout_s: float = 60.0):
        self.model=model
        self.api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        self.max_tokens=int(max_tokens)
        self.endpoint=endpoint
        self.anthropic_version=anthropic_version
        self.transport=transport or UrllibJSONTransport()
        self.timeout_s=timeout_s
        self.name=f"anthropic-messages:{model}"

    def complete(self, request: LLMRequest) -> LLMResponse:
        contract=json.dumps(request.response_contract, ensure_ascii=False)
        user=request.user + "\n\nReturn ONLY one valid JSON object. Response contract: " + contract
        result=self.transport.post(
            self.endpoint,
            headers={"x-api-key":self.api_key,"anthropic-version":self.anthropic_version,"content-type":"application/json"},
            payload={"model":self.model,"max_tokens":self.max_tokens,"system":request.system,
                     "messages":[{"role":"user","content":user}]},
            timeout=self.timeout_s,
        )
        data=result.data
        text=_extract_text(data)
        if not text:
            raise ProviderResponseError("Anthropic response contained no text output")
        content=_parse_json_text(text)
        usage=data.get("usage") if isinstance(data.get("usage"),dict) else {}
        return LLMResponse(content=content, model=data.get("model") or self.model, usage=usage, raw=data)
