#!/usr/bin/env python3
"""Serve only the public distribution files from a loopback HTTP listener."""

import argparse
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


class DistributionHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        self.serve_public()

    def do_HEAD(self):
        self.serve_public()

    def serve_public(self):
        path = unquote(urlsplit(self.path).path)
        if path == "/health":
            data = b"ok\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)
            return
        if path == "/":
            self.path = "/index.html"
        elif path in ("/source.json", "/latest.json", "/status.json"):
            self.path = path
        elif path.startswith("/icons/") or path.startswith("/releases/"):
            self.path = path
        else:
            self.send_error(404)
            return
        target = Path(self.translate_path(self.path))
        if not target.is_file() or target.is_symlink() or target.name.startswith("."):
            self.send_error(404)
            return
        super().do_GET() if self.command == "GET" else super().do_HEAD()

    def end_headers(self):
        if self.path.startswith("/releases/") or self.path.startswith("/icons/"):
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        else:
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def guess_type(self, path):
        if path.endswith(".ipa"):
            return "application/octet-stream"
        if path.endswith(".json"):
            return "application/json"
        return mimetypes.guess_type(path)[0] or "application/octet-stream"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1] / "public")
    parser.add_argument("--port", type=int, default=18090)
    args = parser.parse_args()
    handler = lambda *a, **kw: DistributionHandler(*a, directory=str(args.root), **kw)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Serving {args.root} on 127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
