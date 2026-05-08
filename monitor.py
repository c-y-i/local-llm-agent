#!/usr/bin/env python3
"""Read-only LLM stack monitor. Run with: python3 monitor.py"""
import json
import os
import socket
import subprocess
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn


# ---------------------------------------------------------------------------
# Data collectors
# ---------------------------------------------------------------------------

def get_services():
    result = {}
    for svc in ("ollama", "llama-cline", "litellm-proxy"):
        try:
            out = subprocess.run(
                ["systemctl", "is-active", svc],
                capture_output=True, text=True, timeout=2,
            )
            result[svc] = {"status": out.stdout.strip()}
        except Exception:
            result[svc] = {"status": "unknown"}
    return result


def probe_ports():
    targets = {"anthropic-proxy": 4000, "stable-diffusion": 7860}
    result = {}
    for name, port in targets.items():
        reachable = False
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                reachable = True
        except OSError:
            pass
        result[name] = {"port": port, "reachable": reachable}
    return result


def get_gpu():
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True, text=True, timeout=3,
        )
        if out.returncode != 0:
            return {"available": False}
        parts = [p.strip() for p in out.stdout.strip().split(",")]
        return {
            "available": True,
            "name": parts[0],
            "vram_used_mib": int(parts[1]),
            "vram_total_mib": int(parts[2]),
            "utilization_pct": int(parts[3]),
            "temp_c": int(parts[4]),
        }
    except FileNotFoundError:
        return {"available": False}
    except Exception:
        return {"available": False}


def get_ollama():
    def fetch(path):
        req = urllib.request.Request(f"http://localhost:11434{path}")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read())

    try:
        tags = fetch("/api/tags")
        models = [
            {"name": m["name"], "size_gb": round(m["size"] / 1e9, 1)}
            for m in tags.get("models", [])
        ]
    except Exception:
        return {"reachable": False, "models": [], "running": []}

    try:
        ps = fetch("/api/ps")
        running = [
            {"name": m["name"], "vram_mib": m.get("size_vram", 0) // (1024 * 1024)}
            for m in ps.get("models", [])
        ]
    except Exception:
        running = []

    return {"reachable": True, "models": models, "running": running}


# ---------------------------------------------------------------------------
# Dashboard HTML — defined here, populated in the HTML template task
# ---------------------------------------------------------------------------

DASHBOARD_HTML = ""  # replaced by Task 3

# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

def build_status():
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "services": get_services(),
        "ports": probe_ports(),
        "gpu": get_gpu(),
        "ollama": get_ollama(),
    }


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class MonitorHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress per-request logs

    def do_GET(self):
        if self.path == "/":
            body = DASHBOARD_HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/status":
            try:
                body = json.dumps(build_status()).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", len(body))
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


def main():
    port = int(os.environ.get("MONITOR_PORT", "8765"))
    server = ThreadedHTTPServer(("", port), MonitorHandler)
    print(f"LLM Monitor → http://localhost:{port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
