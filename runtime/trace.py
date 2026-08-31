from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json, time, uuid

class TraceLogger:
    def __init__(self, path):
        self.path = Path(path)

    def append(self, event: Dict[str, Any]) -> Dict[str, Any]:
        rec = {"event_id":str(uuid.uuid4()), "ts":int(time.time()), **event}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec
