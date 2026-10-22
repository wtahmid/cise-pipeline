"""A small stdlib-only HTTP service used to demo every CISE pipeline stage.

The route lookup is a pure function (`handle`) so it can be unit-tested
without spinning up a server. Everything else is just HTTP plumbing.
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "0.1.0"

# path -> (status line, JSON body)
ROUTES = {
    "/healthz": ("200", '{"status":"ok"}'),
    "/version": ("200", '{"version":"' + VERSION + '"}'),
}


def handle(path):
    """Pure routing table lookup. Returns (status, body)."""
    return ROUTES.get(path, ("404", "not found"))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, body = handle(self.path)
        data = body.encode("utf-8")
        self.send_response(int(status))
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        # Keep CI/job logs clean; access logs are not security telemetry here.
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
