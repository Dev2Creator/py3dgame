"""A local preview server: the smallest useful editor loop.

Open the URL, look at the render, edit the scene JSON, reload. It binds to
loopback only and serves read-only views of the document. There is no upload
path and no arbitrary file access, on purpose.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from string import Template
from typing import Optional

from .document import SceneDocument
from .preview import render_document_png

_PAGE = Template("""<!doctype html>
<html><head><meta charset="utf-8"><title>py3dgame preview</title>
<style>body{background:#11141c;color:#dfe4f0;font:14px/1.5 system-ui,sans-serif;margin:0;padding:24px}
img{max-width:100%;border-radius:8px;background:#000}h1{font-size:16px;font-weight:600}
pre{background:#0b0e14;padding:12px;border-radius:8px;overflow:auto;max-height:32vh}</style></head>
<body><h1>$name</h1><img id="f" src="/frame.png" alt="render">
<pre>$scene</pre>
<script>setInterval(function(){document.getElementById('f').src='/frame.png?t='+Date.now()},2000)</script>
</body></html>""")


class PreviewServer:
    """Serve a scene document as an auto-refreshing PNG preview."""

    def __init__(self, document: SceneDocument, host: str = "127.0.0.1", port: int = 8080,
                 width: int = 640, height: int = 360) -> None:
        if not isinstance(document, SceneDocument):
            raise TypeError("document must be a SceneDocument")
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("preview server binds to loopback only")
        self.document = document
        self.width = width
        self.height = height
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        outer = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args) -> None:  # keep the console quiet
                return

            def _send(self, status: int, content_type: str, body: bytes) -> None:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:  # noqa: N802 (http.server API)
                path = self.path.split("?")[0]
                if path in {"/", "/index.html"}:
                    page = _PAGE.substitute(
                        name=outer.document.name,
                        scene=json.dumps(outer.document.to_dict(), indent=2)[:4000],
                    )
                    self._send(200, "text/html; charset=utf-8", page.encode("utf-8"))
                elif path == "/frame.png":
                    try:
                        body = render_document_png(outer.document, outer.width, outer.height)
                    except Exception as exc:  # render errors become a clear 500, not a hang
                        self._send(500, "text/plain; charset=utf-8", f"render failed: {exc}".encode())
                        return
                    self._send(200, "image/png", body)
                elif path == "/api/scene":
                    body = json.dumps(outer.document.to_dict(), indent=2).encode("utf-8")
                    self._send(200, "application/json", body)
                else:
                    self._send(404, "text/plain; charset=utf-8", b"not found")

        self._httpd = ThreadingHTTPServer((host, port), Handler)
        self._httpd.daemon_threads = True
        self.host = host

    @property
    def port(self) -> int:
        return int(self._httpd.server_address[1])

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/"

    def start(self) -> "PreviewServer":
        if self._thread is not None:
            return self
        self._thread = threading.Thread(target=self._httpd.serve_forever, name="p3d-preview", daemon=True)
        self._thread.start()
        return self

    def serve_forever(self) -> None:
        try:
            self._httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread = None
