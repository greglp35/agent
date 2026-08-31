from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json

class CommandOSHandler(BaseHTTPRequestHandler):
    app=None
    def _headers(self): return {k:v for k,v in self.headers.items()}
    def _body(self):
        n=int(self.headers.get("content-length") or 0)
        if not n: return {}
        raw=self.rfile.read(n).decode("utf-8"); return json.loads(raw) if raw else {}
    def _send(self,response):
        raw=response.body.encode("utf-8") if isinstance(response.body,str) else json.dumps(response.body,ensure_ascii=False).encode("utf-8")
        self.send_response(response.status); self.send_header("content-type",response.content_type); self.send_header("content-length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self): self._send(self.app.handle("GET",self.path,headers=self._headers()))
    def do_POST(self): self._send(self.app.handle("POST",self.path,self._body(),self._headers()))
    def log_message(self,format,*args): return

def serve(app, host="127.0.0.1", port=8787):
    cls=type("BoundCommandOSHandler",(CommandOSHandler,),{"app":app}); ThreadingHTTPServer((host,int(port)),cls).serve_forever()
