from __future__ import annotations
import argparse, json
from pathlib import Path
from .engine import run_command
from .state import StateStore
from .trace import TraceLogger

def main():
    ap = argparse.ArgumentParser(description="COMMAND OS CORE v2 runtime")
    ap.add_argument("command", nargs="+")
    ap.add_argument("--source", choices=["user","document","web","tool","file"], default="user")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--capabilities")
    ap.add_argument("--state-file")
    ap.add_argument("--trace-file")
    args = ap.parse_args()

    raw = " ".join(args.command)
    caps = json.loads(Path(args.capabilities).read_text(encoding="utf-8")) if args.capabilities else None
    result = run_command(raw, source=args.source, provided_capabilities=caps, dry_run=not args.execute)

    if args.state_file:
        store = StateStore(args.state_file)
        result["state"] = store.update(
            current_task=raw,
            current_stage=(result.get("plan", {}).get("steps") or [{}])[-1].get("phase"),
            next_action="Complete semantic/tool execution or continue pipeline."
        )

    if args.trace_file:
        result["trace_event"] = TraceLogger(args.trace_file).append({
            "type":"command_run",
            "raw":raw,
            "execution_status":result.get("execution",{}).get("execution_status"),
            "commands":result.get("ir",{}).get("commands",[])
        })

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
