from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests


class LLMError(RuntimeError):
    pass


class DeepSeekClient:
    """
    Minimal DeepSeek Chat Completions client.
    Expects env var: DEEPSEEK_API_KEY
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        timeout_s: int = 120,
    ) -> None:
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            raise LLMError("Missing DEEPSEEK_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def chat(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout_s)
        if resp.status_code >= 400:
            raise LLMError(f"DeepSeek API error {resp.status_code}: {resp.text}")
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise LLMError(f"Unexpected DeepSeek response shape: {data}") from e


def get_client(provider: str) -> DeepSeekClient:
    provider_norm = (provider or "").strip().lower()
    if provider_norm in ("deepseek", "ds"):
        return DeepSeekClient()
    raise LLMError(f"Unsupported provider: {provider}")

