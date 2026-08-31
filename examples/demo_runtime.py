from runtime import compile_command
import json

samples = [
    "/council /audit /decision mon application --forensic --security --terrain",
    "/research réglementation >> /compare A B >> /decision",
    "/expert /audit application de gestion de stock --deep",
    "/fullaudit mon projet --forensic",
]

for s in samples:
    print("=" * 80)
    print(s)
    print(json.dumps(compile_command(s), ensure_ascii=False, indent=2))
