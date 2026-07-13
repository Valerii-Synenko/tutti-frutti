#!/usr/bin/env python3
"""
Fetches the OpenAPI schema from each running FastAPI service and saves it
into docs/openapi/, so Zudoku can build documentation from static files
(recommended over Zudoku's runtime URL mode — faster and works offline).

Usage (with the docker-compose stack running):
    python scripts/collect_openapi.py
"""

import json
import pathlib
import urllib.request

SERVICES = {
    "gateway": ("http://localhost:8080/openapi.json", "http://localhost:8080"),
    "users-service": ("http://localhost:8001/openapi.json", "http://localhost:8001"),
    "catalogue-service": ("http://localhost:8002/openapi.json", "http://localhost:8002"),
    "orders-service": ("http://localhost:8003/openapi.json", "http://localhost:8003"),
    "fruit-assistant-service": ("http://localhost:8004/openapi.json", "http://localhost:8004"),
}

OUTPUT_DIR = pathlib.Path(__file__).parent.parent / "docs" / "openapi"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, (url, server_url) in SERVICES.items():
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                spec = json.load(response)
        except Exception as exc:  # noqa: BLE001 - best-effort dev tooling script
            print(f"Skipping {name}: {exc}")
            continue

        spec.setdefault("servers", [{"url": server_url, "description": "Local dev (docker-compose)"}])

        out_path = OUTPUT_DIR / f"{name}.json"
        out_path.write_text(json.dumps(spec, indent=2))
        print(f"Saved {name} -> {out_path}")


if __name__ == "__main__":
    main()
