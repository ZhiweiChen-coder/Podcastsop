from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict


class HistoryItem(TypedDict):
    version_id: str
    text: str
    time: str
    settings: Dict[str, Any]


class ModuleState(TypedDict):
    current: str
    history: List[HistoryItem]


class Project(TypedDict):
    meta: Dict[str, Any]
    settings: Dict[str, Any]
    input_raw: str
    A: ModuleState
    B: ModuleState
    C: ModuleState
    D: ModuleState
    E: ModuleState
    version_counter: Dict[str, int]


MODULES = ("A", "B", "C", "D", "E")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_empty_project() -> Project:
    empty_module: ModuleState = {"current": "", "history": []}
    return {
        "meta": {
            "title": "",
            "lang": "zh",
            "speakers": ["主持人", "嘉宾"],
            "purpose": "公众号深度访谈",
        },
        "settings": {
            "model_provider": "deepseek",
            "model_name": "deepseek-chat",
            "temperature": 0.2,
            "max_tokens": 4096,
            "strict_no_add": True,
        },
        "input_raw": "",
        "A": {"current": "", "history": []},
        "B": {"current": "", "history": []},
        "C": {"current": "", "history": []},
        "D": {"current": "", "history": []},
        "E": {"current": "", "history": []},
        "version_counter": {m: 0 for m in MODULES},
    }


# 按发稿用途的模块依赖：公众号 A->B->C，播客 A->B->E，社媒 A->B->C->D
WORKFLOW_PREV: dict[str, dict[str, str | None]] = {
    "公众号深度访谈": {"A": None, "B": "A", "C": "B"},
    "播客口播": {"A": None, "B": "A", "E": "B"},
    "社媒素材": {"A": None, "B": "A", "C": "B", "D": "C"},
}


def get_module_input(project: Project, module_name: str, purpose: str | None = None) -> str:
    purpose = purpose or project["meta"].get("purpose", "公众号深度访谈")
    chain = WORKFLOW_PREV.get(purpose, WORKFLOW_PREV["公众号深度访谈"])
    prev = chain.get(module_name)
    if prev is None:
        return project["input_raw"]
    return project.get(prev, {}).get("current", "")


def has_current(project: Project, module_name: str) -> bool:
    return bool(project[module_name]["current"].strip())


def next_version_id(project: Project, module_name: str) -> str:
    project["version_counter"][module_name] += 1
    return f"{module_name}-{project['version_counter'][module_name]}"


def save_version(
    project: Project,
    module_name: str,
    text: str,
    settings_snapshot: Dict[str, Any],
) -> HistoryItem:
    item: HistoryItem = {
        "version_id": next_version_id(project, module_name),
        "text": text,
        "time": _now_iso(),
        "settings": settings_snapshot,
    }
    project[module_name]["history"].append(item)
    project[module_name]["current"] = text
    return item


def list_versions(project: Project, module_name: str) -> List[HistoryItem]:
    return list(project[module_name]["history"])


def rollback_to_version(project: Project, module_name: str, version_id: str) -> Optional[HistoryItem]:
    for item in reversed(project[module_name]["history"]):
        if item["version_id"] == version_id:
            project[module_name]["current"] = item["text"]
            return item
    return None

