from __future__ import annotations

from typing import Any, Dict

CONTINUITY_COMMANDS = {"continue", "next", "deeper", "fix", "redo", "focus", "final"}


def resolve_continuity(step: Dict[str, Any], state: Dict[str, Any] | None) -> Dict[str, Any]:
    """Resolve context-dependent continuity commands against persisted work state."""
    state = state or {}
    command = step.get("command")
    if command not in CONTINUITY_COMMANDS:
        return dict(step)

    resolved = dict(step)
    target = resolved.get("target")

    if command == "next":
        target = target or state.get("next_action") or state.get("current_task")
    elif command == "continue":
        target = target or state.get("current_task") or state.get("last_artifact")
    elif command in {"deeper", "fix", "redo", "final"}:
        target = target or state.get("last_artifact") or state.get("current_task")
    elif command == "focus":
        target = target or state.get("current_stage") or state.get("current_task")

    resolved["target"] = target
    resolved["continuity_state"] = {
        "active_project": state.get("active_project"),
        "current_task": state.get("current_task"),
        "current_stage": state.get("current_stage"),
        "last_artifact": state.get("last_artifact"),
        "next_action": state.get("next_action"),
    }
    return resolved
