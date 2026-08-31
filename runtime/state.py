from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json, time

DEFAULT_STATE = {
    "version":"2.0",
    "active_project":None,
    "current_task":None,
    "current_stage":None,
    "last_artifact":None,
    "next_action":None,
    "updated_at":None
}

class StateStore:
    def __init__(self, path):
        self.path = Path(path)

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return dict(DEFAULT_STATE)
        out = dict(DEFAULT_STATE)
        out.update(json.loads(self.path.read_text(encoding="utf-8")))
        return out

    def save(self, state: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(DEFAULT_STATE)
        out.update(state)
        out["updated_at"] = int(time.time())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return out

    def update(self, **changes) -> Dict[str, Any]:
        state = self.load()
        state.update(changes)
        return self.save(state)
