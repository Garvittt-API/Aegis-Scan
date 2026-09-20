"""Local-only AegisScan security demonstration target."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8010
ROOT = Path(__file__).parent


class DemoHandler(BaseHTTPRequestHandler):
    def _send(self, status=200, content_type="text/html; charset=utf-8", body=b""):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Set-Cookie", "demo_session=local-only; Path=/")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/config":
            self._send(200, "application/json", json.dumps({"debug": True, "environment": "demo"}).encode())
            return
        if self.path == "/api/health":
            self._send(200, "application/json", b'{"status":"ok","scope":"local-demo"}')
            return
        if self.path == "/static/demo.js":
            self._send(200, "application/javascript", (ROOT / "demo.js").read_bytes())
            return
        self._send(200, body=(ROOT / "index.html").read_bytes())

    def log_message(self, format, *args):
        print(f"[demo-lab] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    print(f"AegisScan local security lab: http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), DemoHandler).serve_forever()
