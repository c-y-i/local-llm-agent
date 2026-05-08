#!/usr/bin/env python3
"""Read-only local LLM stack monitor. Run with: python3 monitor.py"""
import json
import os
import socket
import subprocess
import time
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


def get_system():
    ram = {"available": False}
    try:
        mem = {}
        with open("/proc/meminfo") as f:
            for line in f:
                if ":" in line:
                    k, v = line.split(":", 1)
                    mem[k.strip()] = int(v.split()[0])
        total_mib = mem["MemTotal"] // 1024
        avail_mib = mem["MemAvailable"] // 1024
        ram = {"available": True, "total_mib": total_mib, "used_mib": total_mib - avail_mib}
    except Exception:
        pass

    cpu = {"available": False}
    try:
        def _read_stat():
            with open("/proc/stat") as f:
                parts = f.readline().split()
            vals = [int(x) for x in parts[1:8]]
            return sum(vals), vals[3] + vals[4]  # total, idle+iowait

        t1, i1 = _read_stat()
        time.sleep(0.1)
        t2, i2 = _read_stat()
        dt = t2 - t1
        cpu = {
            "available": True,
            "pct": round(100.0 * (1 - (i2 - i1) / dt), 1) if dt > 0 else 0.0,
            "count": os.cpu_count() or 1,
        }
    except Exception:
        pass

    return {"ram": ram, "cpu": cpu}


# ---------------------------------------------------------------------------
# Dashboard HTML — defined here, populated in the HTML template task
# ---------------------------------------------------------------------------

DASHBOARD_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Local LLM Monitor</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;font-size:14px;background:#0f0f0f;color:#e0e0e0;padding:20px}
h1{font-size:16px;font-weight:600;color:#fff}
header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
#ts{font-size:12px;color:#666}
.grid{display:grid;grid-template-columns:220px 1fr 1fr;gap:12px;margin-bottom:12px}
.card{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:4px;padding:14px}
.card h2{font-size:11px;font-weight:600;letter-spacing:.08em;color:#888;text-transform:uppercase;margin-bottom:10px}
.row{display:flex;align-items:center;gap:8px;padding:3px 0}
.dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.on{background:#22c55e}.off{background:#444}
.label{color:#ccc;font-size:13px}
.gpu-name{font-size:13px;color:#ccc;margin-bottom:8px}
meter{width:100%;height:10px;margin:6px 0}
.gpu-stats{font-size:12px;color:#888}
table{width:100%;border-collapse:collapse}
th{text-align:left;font-size:11px;color:#666;font-weight:600;letter-spacing:.06em;text-transform:uppercase;padding:0 0 8px}
td{padding:4px 0;font-size:13px;vertical-align:middle}
td.right{text-align:right;color:#888}
.mono{font-family:ui-monospace,monospace}
.badge{font-size:11px;background:#1e3a2e;color:#22c55e;border-radius:3px;padding:1px 6px}
.na{color:#555;font-style:italic}
</style>
</head>
<body>
<header><h1>Local LLM Monitor</h1><span id="ts">—</span></header>
<div class="grid">
  <div class="card"><h2>Services</h2><div id="svc"><span class="na">loading…</span></div></div>
  <div class="card"><h2>GPU</h2><div id="gpu"><span class="na">loading…</span></div></div>
  <div class="card"><h2>System</h2><div id="sys"><span class="na">loading…</span></div></div>
</div>
<div class="card"><h2>Models</h2><div id="mdl"><span class="na">loading…</span></div></div>
<script>
const SVCS={"ollama":"ollama","llama-cline":"llama-cline","litellm-proxy":"litellm-proxy"};
const PORTS={"anthropic-proxy":"anthropic-proxy :4000","stable-diffusion":"stable-diffusion :7860"};
function esc(s){const d=document.createElement("div");d.appendChild(document.createTextNode(String(s)));return d.innerHTML;}
function dot(on){return '<span class="dot '+(on?"on":"off")+'"></span>';}
function renderSvc(d){
  let h="";
  for(const[k,l] of Object.entries(SVCS)){const on=d.services?.[k]?.status==="active";h+=`<div class="row">${dot(on)}<span class="label">${l}</span></div>`;}
  for(const[k,l] of Object.entries(PORTS)){const on=d.ports?.[k]?.reachable===true;h+=`<div class="row">${dot(on)}<span class="label">${l}</span></div>`;}
  document.getElementById("svc").innerHTML=h;
}
function renderGPU(d){
  const g=d.gpu;
  if(!g?.available){document.getElementById("gpu").innerHTML='<span class="na">unavailable</span>';return;}
  const u=(g.vram_used_mib/1024).toFixed(1),t=(g.vram_total_mib/1024).toFixed(1);
  document.getElementById("gpu").innerHTML=`<div class="gpu-name">${esc(g.name)}</div><meter value="${g.vram_used_mib}" min="0" max="${g.vram_total_mib}"></meter><div class="gpu-stats">VRAM ${u} / ${t} GB &nbsp;·&nbsp; Util ${esc(g.utilization_pct)}% &nbsp;·&nbsp; ${esc(g.temp_c)}°C</div>`;
}
function renderSys(d){
  const s=d.system;
  let h="";
  if(s?.ram?.available){
    const u=(s.ram.used_mib/1024).toFixed(1),t=(s.ram.total_mib/1024).toFixed(1);
    h+=`<div class="gpu-stats" style="margin-bottom:4px">RAM</div><meter value="${s.ram.used_mib}" min="0" max="${s.ram.total_mib}"></meter><div class="gpu-stats">${u} / ${t} GB used</div>`;
  }else{h+='<div class="gpu-stats">RAM unavailable</div>';}
  if(s?.cpu?.available){
    h+=`<div class="gpu-stats" style="margin-top:10px">CPU &nbsp;${esc(s.cpu.pct)}% &nbsp;·&nbsp; ${esc(s.cpu.count)} cores</div>`;
  }else{h+='<div class="gpu-stats" style="margin-top:10px">CPU unavailable</div>';}
  document.getElementById("sys").innerHTML=h;
}
function renderMdl(d){
  const o=d.ollama;
  if(!o?.reachable){document.getElementById("mdl").innerHTML='<span class="na">Ollama unreachable</span>';return;}
  if(!o.models?.length){document.getElementById("mdl").innerHTML='<span class="na">no models pulled</span>';return;}
  const rm=new Map((o.running||[]).map(r=>[r.name,r]));
  let h='<table><thead><tr><th>Model</th><th>Size</th><th></th></tr></thead><tbody>';
  for(const m of o.models){
    const r=rm.get(m.name);
    const badge=r?`<span class="badge">loaded · ${r.vram_mib} MiB</span>`:"";
    h+=`<tr><td class="mono">${esc(m.name)}</td><td class="right">${esc(m.size_gb)} GB</td><td class="right">${badge}</td></tr>`;
  }
  h+="</tbody></table>";
  document.getElementById("mdl").innerHTML=h;
}
async function poll(){
  try{
    const r=await fetch("/api/status");
    if(!r.ok)throw new Error(r.status);
    const d=await r.json();
    document.getElementById("ts").textContent="updated "+(d.timestamp?.slice(11,19)??"—");
    renderSvc(d);renderGPU(d);renderSys(d);renderMdl(d);
  }catch(e){console.error(e);document.getElementById("ts").textContent="fetch failed";}
}
poll();setInterval(poll,5000);
</script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

def build_status():
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "services": get_services(),
        "ports": probe_ports(),
        "gpu": get_gpu(),
        "system": get_system(),
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
    print(f"Local LLM Monitor → http://localhost:{port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
