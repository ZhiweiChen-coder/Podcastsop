from __future__ import annotations

from typing import Any, Dict, Tuple

from core.llm_client import LLMError, get_client
from core.prompts import MODULE_PROMPTS, SYSTEM_PROMPT


def post_check(output_text: str) -> Tuple[bool, str]:
    """
    MVP heuristic checks.
    Returns (ok, message). If ok is False, message explains the risk.
    """
    lowered = output_text.lower()
    suspicious = [
        "根据外部",
        "引用外部",
        "资料显示",
        "research",
        "source:",
        "参考资料",
        "来自网络",
    ]
    for s in suspicious:
        if s.lower() in lowered:
            return False, f"可能出现外部资料引用迹象：命中「{s}」"
    return True, ""


def run_module(
    *,
    module_name: str,
    input_text: str,
    settings: Dict[str, Any],
) -> Dict[str, Any]:
    prompt_tmpl = MODULE_PROMPTS.get(module_name)
    if not prompt_tmpl:
        raise ValueError(f"Unknown module: {module_name}")

    user_prompt = prompt_tmpl.format(input_text=input_text)

    provider = settings.get("model_provider", "deepseek")
    model = settings.get("model_name", "deepseek-chat")
    temperature = float(settings.get("temperature", 0.2))
    max_tokens = int(settings.get("max_tokens", 4096))

    client = get_client(provider)
    output = client.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    ok, msg = post_check(output)
    return {"text": output, "post_check_ok": ok, "post_check_msg": msg}

