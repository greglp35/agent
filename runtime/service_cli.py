from __future__ import annotations
import argparse,json,os
from .api_service import CommandOSAPI, StaticTokenAuthenticator
from .http_daemon import serve
from .provider_registry import ProviderRegistry

def main():
    ap=argparse.ArgumentParser(description="COMMAND OS Beta.1 API service")
    ap.add_argument("--host",default="127.0.0.1"); ap.add_argument("--port",type=int,default=8787)
    ap.add_argument("--tokens-env",default="COMMAND_OS_API_TOKENS_JSON")
    args=ap.parse_args()
    raw=os.getenv(args.tokens_env,"{}")
    tokens=json.loads(raw)
    if not tokens: raise SystemExit(f"{args.tokens_env} must contain a JSON token map")
    registry=ProviderRegistry.from_default()
    providers={name:(lambda n=name: registry.build(n)) for name in registry.names()}
    app=CommandOSAPI(providers=providers,authenticator=StaticTokenAuthenticator(tokens))
    serve(app,args.host,args.port)

if __name__=="__main__": main()
