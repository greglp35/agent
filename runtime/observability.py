from __future__ import annotations
from collections import defaultdict
from threading import Lock
import time,uuid

class MetricsRegistry:
    def __init__(self): self._c=defaultdict(float); self._lock=Lock()
    def inc(self,name: str,value: float=1.0,**labels):
        key=(name,tuple(sorted((str(k),str(v)) for k,v in labels.items())))
        with self._lock: self._c[key]+=float(value)
    def snapshot(self):
        with self._lock: return [{"name":k[0],"labels":dict(k[1]),"value":v} for k,v in sorted(self._c.items(),key=lambda x:str(x[0]))]
    def render_prometheus(self):
        lines=[]
        for row in self.snapshot():
            labels=row["labels"]; suffix="" if not labels else "{"+",".join(f'{k}="{str(v).replace(chr(34),chr(92)+chr(34))}"' for k,v in sorted(labels.items()))+"}"
            lines.append(f'{row["name"]}{suffix} {row["value"]}')
        return "\n".join(lines)+("\n" if lines else "")

class RunObserver:
    def __init__(self,metrics=None,journal=None): self.metrics=metrics or MetricsRegistry(); self.journal=journal
    def start(self,operation: str,**meta):
        trace_id=str(uuid.uuid4()); started=time.monotonic(); self.metrics.inc("command_os_runs_total",operation=operation,status="started")
        if self.journal: self.journal.append({"type":"run_start","trace_id":trace_id,"operation":operation,"meta":meta})
        return trace_id,started
    def finish(self,trace_id: str,started: float,operation: str,status: str,**meta):
        ms=max(0.0,(time.monotonic()-started)*1000.0); self.metrics.inc("command_os_runs_total",operation=operation,status=status); self.metrics.inc("command_os_run_latency_ms_total",ms,operation=operation)
        if self.journal: self.journal.append({"type":"run_end","trace_id":trace_id,"operation":operation,"status":status,"latency_ms":round(ms,3),"meta":meta})
        return ms
