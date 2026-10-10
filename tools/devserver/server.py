"""Local harness (repository only; not uploaded to Qollab).

Serves the repository and answers the Python calls Qollab would answer in the browser:
dev.html maps the import 'compass.api' to shim.js, which POSTs each call here. The backend is a
local simulator: ?backend=basic_simulator (default) or ?backend=aer.

Usage: python tools/devserver/server.py [--port 8770]; open http://127.0.0.1:8770/tools/devserver/dev.html
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from compass import api  # noqa: E402


def make_backend(name: str):
    if name == "aer":
        from qiskit_aer import AerSimulator

        return AerSimulator()
    from qiskit.providers.basic_provider import BasicSimulator

    return BasicSimulator()


class Handler(SimpleHTTPRequestHandler):
    backends: dict = {}  # noqa: RUF012

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        pass

    def do_POST(self):
        name = self.path.removeprefix("/call/")
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])) or b"{}")
        args = [
            self.backends.setdefault(a["__backend__"], make_backend(a["__backend__"]))
            if isinstance(a, dict) and "__backend__" in a
            else a
            for a in body.get("args", [])
        ]
        try:
            out = {"ok": True, "value": getattr(api, name)(*args)}
        except Exception as exc:  # report like Pyodide would: the traceback text
            out = {"ok": False, "error": "".join(traceback.format_exception(exc))}
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8770)
    a = ap.parse_args()
    print(f"http://127.0.0.1:{a.port}/tools/devserver/dev.html")
    HTTPServer(("127.0.0.1", a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
