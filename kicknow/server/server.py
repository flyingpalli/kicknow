#!/usr/bin/env python3
import gzip
import http.server
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import urllib.request

_GEO_CACHE = None
_FILE_CACHE = {}
_TUNNEL_CDN_REDIRECTS = {
    "/vendor/maplibre/maplibre-gl.js": "https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js",
    "/vendor/maplibre/maplibre-gl.css": "https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css",
    "/vendor/leaflet/leaflet.js": "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
    "/vendor/leaflet/leaflet.css": "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
}


def fetch_ip_geo():
    global _GEO_CACHE
    if _GEO_CACHE is not None:
        return _GEO_CACHE
    for url in ("https://get.geojs.io/v1/ip/geo.json", "https://ipwho.is/"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "KickNow/1.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                lat = float(data.get("latitude"))
                lng = float(data.get("longitude"))
                _GEO_CACHE = {"lat": lat, "lng": lng, "city": data.get("city", ""), "source": "ip"}
                return _GEO_CACHE
        except Exception:
            continue
    return None


def get_local_ips():
    ips = {"127.0.0.1"}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            ["ip", "-4", "addr", "show", "scope", "global"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        for match in re.findall(r"inet\s+(\d+\.\d+\.\d+\.\d+)", out):
            ips.add(match)
    except Exception:
        pass
    return sorted(ips)


def build_ssl_context():
    cert_path = os.path.join(tempfile.gettempdir(), "kicknow-dev-cert.pem")
    key_path = os.path.join(tempfile.gettempdir(), "kicknow-dev-key.pem")
    san_path = os.path.join(tempfile.gettempdir(), "kicknow-dev-cert.san")
    san = ",".join([f"IP:{ip}" for ip in get_local_ips()] + ["DNS:localhost"])
    need_regen = not (os.path.exists(cert_path) and os.path.exists(key_path))
    if not need_regen:
        try:
            with open(san_path, "r", encoding="utf-8") as f:
                if f.read().strip() != san:
                    need_regen = True
        except Exception:
            need_regen = True
    if need_regen:
        try:
            subprocess.run(
                [
                    "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                    "-keyout", key_path, "-out", cert_path, "-days", "365",
                    "-subj", "/CN=KickNow Local",
                    "-addext", f"subjectAltName={san}",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            with open(san_path, "w", encoding="utf-8") as f:
                f.write(san)
        except Exception:
            try:
                subprocess.run(
                    [
                        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                        "-keyout", key_path, "-out", cert_path, "-days", "365",
                        "-subj", "/CN=KickNow Local",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
            except Exception:
                return None
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
        return ctx
    except Exception:
        return None


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".webmanifest": "application/manifest+json",
    }

    def _send_bytes(self, status, payload, content_type="application/json; charset=utf-8", extra_headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if payload:
            self.wfile.write(payload)

    def _drain_body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            return self.rfile.read(length) if length > 0 else b""
        except Exception:
            return b""

    def do_GET(self):
        clean_path = self.path.split("?", 1)[0]
        if clean_path.startswith("/api/geo"):
            geo = fetch_ip_geo() or {}
            self._send_bytes(200, json.dumps(geo).encode("utf-8"))
            return
        if clean_path.startswith("/api/v1/"):
            self._send_bytes(200, b"{}")
            return
        if clean_path.startswith("/ws/"):
            self._send_bytes(404, b"", content_type="text/plain")
            return

        host = self.headers.get("Host", "").lower()
        is_tunnel = any(d in host for d in ("lhr.life", "localhost.run", "pinggy", "trycloudflare", "ngrok"))
        if is_tunnel and clean_path in _TUNNEL_CDN_REDIRECTS:
            self.send_response(302)
            self.send_header("Location", _TUNNEL_CDN_REDIRECTS[clean_path])
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        fs_path = self.translate_path(self.path)
        if os.path.isdir(fs_path):
            index_candidate = os.path.join(fs_path, "index.html")
            if os.path.isfile(index_candidate):
                fs_path = index_candidate
        if not os.path.isfile(fs_path):
            self._send_bytes(404, b"Not Found", content_type="text/plain; charset=utf-8")
            return

        try:
            mtime = os.path.getmtime(fs_path)
            ctype = self.guess_type(fs_path)
            accept_gzip = "gzip" in self.headers.get("Accept-Encoding", "")
            compressible = any(t in ctype for t in ("text/", "javascript", "json", "svg", "xml"))
            use_gzip = accept_gzip and compressible
            cache_key = (fs_path, mtime, use_gzip)
            if cache_key not in _FILE_CACHE:
                with open(fs_path, "rb") as f:
                    raw = f.read()
                _FILE_CACHE[cache_key] = gzip.compress(raw, compresslevel=9) if use_gzip else raw
            body = _FILE_CACHE[cache_key]
            extra = {"Content-Encoding": "gzip", "Vary": "Accept-Encoding"} if use_gzip else None
            self._send_bytes(200, body, content_type=ctype, extra_headers=extra)
        except Exception:
            self._send_bytes(500, b"Internal Server Error", content_type="text/plain; charset=utf-8")

    def do_HEAD(self):
        clean_path = self.path.split("?", 1)[0]
        fs_path = self.translate_path(self.path)
        if os.path.isdir(fs_path):
            fs_path = os.path.join(fs_path, "index.html")
        if not os.path.isfile(fs_path):
            self._send_bytes(404, b"", content_type="text/plain")
            return
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(fs_path))
        self.send_header("Content-Length", str(os.path.getsize(fs_path)))
        self.end_headers()

    def do_POST(self):
        global _GEO_CACHE
        raw_body = self._drain_body()
        if self.path.startswith("/api/geo"):
            try:
                body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
                lat = float(body.get("lat"))
                lng = float(body.get("lng"))
                _GEO_CACHE = {"lat": lat, "lng": lng, "source": "gps"}
                self._send_bytes(200, json.dumps(_GEO_CACHE).encode("utf-8"))
                return
            except Exception:
                self._send_bytes(400, b"{}")
                return
        if self.path.startswith("/api/v1/"):
            self._send_bytes(200, b"{}")
            return
        self._send_bytes(404, b"{}")

    def do_DELETE(self):
        self._drain_body()
        self._send_bytes(200, b"{}")

    def do_OPTIONS(self):
        self._drain_body()
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, BrokenPipeError, ssl.SSLError, socket.timeout):
            self.close_connection = True


class DualProtocolHTTPServer(http.server.ThreadingHTTPServer):
    """Serves both HTTP and HTTPS on the same port by inspecting the first byte."""
    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 128

    def __init__(self, server_address, RequestHandlerClass, ssl_context=None):
        super().__init__(server_address, RequestHandlerClass)
        self.ssl_context = ssl_context

    def process_request_thread(self, request, client_address):
        if self.ssl_context is not None:
            try:
                request.settimeout(5.0)
                first_byte = request.recv(1, socket.MSG_PEEK)
                if not first_byte:
                    self.shutdown_request(request)
                    return
                if first_byte == b"\x16":
                    request = self.ssl_context.wrap_socket(request, server_side=True)
                request.settimeout(None)
            except Exception:
                try:
                    self.shutdown_request(request)
                except Exception:
                    pass
                return
        super().process_request_thread(request, client_address)


def start_public_tunnel(port):
    if os.environ.get("KICKNOW_NO_TUNNEL") == "1" or not shutil.which("ssh"):
        return None
    state = {"proc": None, "stop": False}

    def _supervisor():
        while not state["stop"]:
            try:
                proc = subprocess.Popen(
                    [
                        "ssh",
                        "-T",
                        "-o", "StrictHostKeyChecking=no",
                        "-o", "UserKnownHostsFile=/dev/null",
                        "-o", "LogLevel=ERROR",
                        "-o", "ServerAliveInterval=20",
                        "-o", "ServerAliveCountMax=3",
                        "-o", "ExitOnForwardFailure=yes",
                        "-o", "ConnectTimeout=8",
                        "-R", f"80:127.0.0.1:{port}",
                        "nokey@localhost.run",
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                state["proc"] = proc
                printed = False
                buf = ""
                while True:
                    chunk = proc.stdout.read(256)
                    if not chunk:
                        break
                    if not printed:
                        buf += chunk.decode("utf-8", errors="ignore")
                        match = re.search(r"https://[a-zA-Z0-9.-]+\.lhr\.life", buf)
                        if match:
                            url = match.group(0)
                            print(f"\nPublic / Hotspot Share URL (works on any phone):\n  {url}\n", flush=True)
                            printed = True
                            buf = ""
                proc.wait()
            except Exception:
                pass
            if not state["stop"]:
                threading.Event().wait(2.0)

    threading.Thread(target=_supervisor, daemon=True).start()
    return state


def run():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    directory = sys.argv[2] if len(sys.argv) > 2 else "."
    ssl_ctx = build_ssl_context()
    handler = lambda *args, **kwargs: NoCacheHandler(*args, directory=directory, **kwargs)

    # Dual HTTP + HTTPS server on primary port (8080)
    http_server = DualProtocolHTTPServer(("0.0.0.0", port), handler, ssl_context=ssl_ctx)

    # Secondary dual HTTP + HTTPS port (8081)
    alt_http_port = port + 1
    try:
        alt_server = DualProtocolHTTPServer(("0.0.0.0", alt_http_port), handler, ssl_context=ssl_ctx)
        threading.Thread(target=alt_server.serve_forever, daemon=True).start()
    except Exception:
        alt_http_port = None

    # Additional HTTPS port (8443)
    https_port = 8443
    if ssl_ctx:
        try:
            https_server = DualProtocolHTTPServer(("0.0.0.0", https_port), handler, ssl_context=ssl_ctx)
            threading.Thread(target=https_server.serve_forever, daemon=True).start()
        except Exception:
            https_port = None

    proto = "HTTP + HTTPS" if ssl_ctx else "HTTP"
    ports = [str(port)] + ([str(alt_http_port)] if alt_http_port else []) + ([str(https_port)] if https_port else [])
    print(f"KickNow {proto} Server serving on port {', '.join(ports)}", flush=True)
    tunnel_state = start_public_tunnel(port)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if tunnel_state is not None:
            tunnel_state["stop"] = True
            if tunnel_state.get("proc") is not None:
                try:
                    tunnel_state["proc"].terminate()
                except Exception:
                    pass


if __name__ == "__main__":
    run()
