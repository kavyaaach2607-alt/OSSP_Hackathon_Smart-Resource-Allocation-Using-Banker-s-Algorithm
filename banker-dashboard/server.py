"""Dashboard server: serves ./static and exposes the Banker's algorithm as a JSON API.
Run:  python3 server.py   then open http://localhost:8000
"""
import json, os, threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from bankers import Bankers, SAMPLE, sample_manager

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
lock = threading.Lock()
manager = sample_manager()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=STATIC, **kw)

    def log_message(self, fmt, *args):  # quieter console
        pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        if self.path == "/api/state":
            with lock:
                return self._send(200, manager.snapshot())
        if self.path == "/api/sample":
            return self._send(200, SAMPLE)
        return super().do_GET()

    def do_POST(self):
        global manager
        try:
            data = self._body()
            with lock:
                if self.path == "/api/request":
                    result = manager.request(int(data["process"]), [int(x) for x in data["request"]])
                    result["state"] = manager.snapshot()
                    return self._send(200, result)
                if self.path == "/api/reset":
                    manager = sample_manager()
                    return self._send(200, manager.snapshot())
                if self.path == "/api/load":
                    manager = Bankers(data["available"], data["max"], data["allocation"])
                    return self._send(200, manager.snapshot())
            self._send(404, {"error": "Not found"})
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
            self._send(400, {"error": f"Invalid input: {e}"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Dashboard running at http://localhost:{port}  (Ctrl+C to stop)")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
