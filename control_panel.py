#!/usr/bin/env python3
"""Local LLM stack control panel. Run with: python3 control_panel.py"""
import json
import os
import shutil
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

SERVICES = ("ollama", "llama-cline", "litellm-proxy")
SERVICE_ACTIONS = ("start", "stop", "restart")
PULLABLE_MODELS = (
    {"name": "qwen3:4b",          "size_gb": 2.6, "desc": "general chat"},
    {"name": "qwen2.5-coder:3b",  "size_gb": 1.9, "desc": "coding"},
    {"name": "llama3.2:1b",       "size_gb": 1.3, "desc": "fast / low RAM"},
)
PULLABLE_MODEL_TAGS = frozenset(m["name"] for m in PULLABLE_MODELS)
LOCAL_CLIENTS = ("127.0.0.1", "::1")
DEFAULT_CONTROLS = "1"
DEFAULT_PORT = "8766"
DEFAULT_HOST = "127.0.0.1"
APP_TITLE = "Local LLM Control Panel"
APP_EYEBROW = "Local runtime"
APP_SUBTITLE = (
    "Monitor services, runtime health, loaded models, and local control actions "
    "from one operational dashboard."
)


def controls_enabled():
    return os.environ.get("LLM_MONITOR_CONTROLS", DEFAULT_CONTROLS).lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


# ---------------------------------------------------------------------------
# Data collectors
# ---------------------------------------------------------------------------

def get_services():
    result = {}
    for svc in SERVICES:
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

    # append CPU model name if available
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    cpu["model"] = line.split(":", 1)[1].strip()
                    break
    except Exception:
        pass

    return {"ram": ram, "cpu": cpu}


def get_storage():
    result = {}
    try:
        usage = shutil.disk_usage("/")
        result["/ (root)"] = {
            "available": True,
            "total_bytes": usage.total,
            "used_bytes": usage.used,
        }
    except Exception:
        result["/ (root)"] = {"available": False}

    models_dir = os.environ.get(
        "OLLAMA_MODELS",
        os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Ollama", "models", "llm")
        ),
    )
    if os.path.isdir(models_dir):
        try:
            usage = shutil.disk_usage(models_dir)
            result["models"] = {
                "available": True,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
            }
        except Exception:
            result["models"] = {"available": False}

    return result


# ---------------------------------------------------------------------------
# Control actions
# ---------------------------------------------------------------------------

def _action_result(ok, message, **extra):
    return {"ok": ok, "message": message, **extra}


def _clean_output(text):
    return text.strip()[-1000:]


def run_service_action(service, action):
    if service not in SERVICES:
        return _action_result(False, f"unsupported service: {service}")
    if action not in SERVICE_ACTIONS:
        return _action_result(False, f"unsupported service action: {action}")
    try:
        out = subprocess.run(
            ["systemctl", action, service],
            capture_output=True, text=True, timeout=20,
        )
    except subprocess.TimeoutExpired:
        return _action_result(False, f"{action} {service} timed out")
    except Exception as exc:
        return _action_result(False, f"{action} {service} failed: {exc}")

    stdout = _clean_output(out.stdout)
    stderr = _clean_output(out.stderr)
    message = stderr or stdout or f"{action} {service} exited {out.returncode}"
    if out.returncode == 0:
        message = f"{action} {service} requested"
    return _action_result(out.returncode == 0, message, returncode=out.returncode)


def _ollama_post(path, payload):
    req = urllib.request.Request(
        f"http://localhost:11434{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
    return json.loads(body) if body else {}


def _known_ollama_models():
    state = get_ollama()
    if not state.get("reachable"):
        return None
    return {m["name"] for m in state.get("models", [])}


def run_ollama_action(action, model):
    if action not in ("warmup", "unload", "pull"):
        return _action_result(False, f"unsupported Ollama action: {action}")
    if not isinstance(model, str) or not model.strip():
        return _action_result(False, "model is required")
    model = model.strip()

    if action == "pull":
        if model not in PULLABLE_MODEL_TAGS:
            return _action_result(False, f"model not in pull allowlist: {model}")
        known = _known_ollama_models()
        if known is None:
            return _action_result(False, "Ollama is unreachable")
        def _do_pull():
            try:
                _ollama_post("/api/pull", {"model": model, "stream": False})
            except Exception:
                pass
        threading.Thread(target=_do_pull, daemon=True).start()
        return _action_result(True, f"pulling {model}…")

    known = _known_ollama_models()
    if known is None:
        return _action_result(False, "Ollama is unreachable")
    if model not in known:
        return _action_result(False, f"unknown Ollama model: {model}")

    payload = {"model": model, "stream": False}
    if action == "warmup":
        payload.update({"prompt": ".", "keep_alive": "10m"})
    else:
        payload.update({"prompt": "", "keep_alive": 0})

    try:
        _ollama_post("/api/generate", payload)
    except urllib.error.HTTPError as exc:
        return _action_result(False, f"Ollama returned HTTP {exc.code}")
    except Exception as exc:
        return _action_result(False, f"Ollama {action} failed: {exc}")

    verb = "loaded" if action == "warmup" else "unloaded"
    return _action_result(True, f"{model} {verb}")


# ---------------------------------------------------------------------------
# Dashboard HTML — defined here, populated in the HTML template task
# ---------------------------------------------------------------------------

DASHBOARD_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__APP_TITLE__</title>
<style>
:root{
  --bg:#08090a;
  --panel:rgba(24,26,28,.84);
  --panel-strong:rgba(30,32,35,.92);
  --line:rgba(255,255,255,.09);
  --line-strong:rgba(255,255,255,.16);
  --text:#f4f7f8;
  --muted:#a4adb4;
  --dim:#7a848c;
  --green:#36d783;
  --amber:#f2b84b;
  --red:#ff6b6b;
  --blue:#65b7ff;
}
*{box-sizing:border-box;margin:0;padding:0}
html{background:var(--bg)}
body{
  min-width:320px;
  min-height:100vh;
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  font-size:16px;
  line-height:1.45;
  background:var(--bg);
  color:var(--text);
  padding:28px;
}
.shell{width:100%;max-width:1480px;margin:0 auto}
header{
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
  gap:24px;
  margin-bottom:18px;
}
.eyebrow{
  color:var(--blue);
  font-size:12px;
  font-weight:700;
  letter-spacing:.12em;
  text-transform:uppercase;
  margin-bottom:6px;
}
h1{font-size:28px;line-height:1.15;font-weight:720;color:#fff;letter-spacing:0}
.subtitle{color:var(--muted);font-size:14px;margin-top:8px;max-width:720px}
.header-right{display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:flex-end;padding-top:2px}
#ts{font-size:13px;color:var(--dim);white-space:nowrap}
.mode{
  font-size:12px;
  font-weight:700;
  border:1px solid var(--line);
  background:rgba(255,255,255,.04);
  color:var(--muted);
  border-radius:999px;
  padding:5px 10px;
  white-space:nowrap;
}
.mode.on{border-color:rgba(54,215,131,.35);background:rgba(54,215,131,.1);color:var(--green)}
.mode.info{border-color:rgba(101,183,255,.35);background:rgba(101,183,255,.08);color:var(--blue)}
.grid{
  display:grid;
  grid-template-columns:minmax(340px,.95fr) minmax(280px,1fr) minmax(280px,1fr);
  gap:16px;
  margin-bottom:16px;
}
.card{
  background:#0f1113;
  border:1px solid rgba(255,255,255,.07);
  border-radius:6px;
  padding:18px;
  box-shadow:0 2px 8px rgba(0,0,0,.22);
}
.card h2{
  font-size:12px;
  font-weight:800;
  letter-spacing:.1em;
  color:var(--muted);
  text-transform:uppercase;
  margin-bottom:16px;
}
.row{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:14px;
  padding:9px 0;
  min-height:44px;
  border-bottom:1px solid rgba(255,255,255,.06);
}
.row:last-child{border-bottom:0}
.row-main{display:flex;align-items:center;gap:10px;min-width:0}
.dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;box-shadow:0 0 0 3px rgba(255,255,255,.04)}
.on{background:var(--green)}.off{background:#4d555b}
.label{color:#e6ebee;font-size:15px;font-weight:620;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.gpu-name{font-size:16px;color:#fff;font-weight:680;margin-bottom:14px;overflow-wrap:anywhere}
meter{width:100%;height:14px;margin:8px 0 10px}
meter::-webkit-meter-bar{background:#101214;border:1px solid var(--line);border-radius:999px}
meter::-webkit-meter-optimum-value{background:var(--green);border-radius:999px}
.gpu-stats{font-size:14px;color:var(--muted)}
.metric-block{margin-bottom:18px}
.metric-label{display:flex;justify-content:space-between;gap:12px;color:#d8dee2;font-size:14px;font-weight:680}
.metric-value{color:var(--muted);font-weight:560}
table{width:100%;border-collapse:separate;border-spacing:0}
th{
  text-align:left;
  font-size:12px;
  color:var(--dim);
  font-weight:800;
  letter-spacing:.09em;
  text-transform:uppercase;
  padding:0 0 12px;
}
td{padding:11px 0;font-size:15px;vertical-align:middle;border-top:1px solid rgba(255,255,255,.06)}
td.right{text-align:right;color:var(--muted)}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.badge{
  display:inline-flex;
  align-items:center;
  min-height:24px;
  font-size:12px;
  font-weight:750;
  background:rgba(54,215,131,.1);
  color:var(--green);
  border:1px solid rgba(54,215,131,.24);
  border-radius:999px;
  padding:3px 9px;
  white-space:nowrap;
}
.na{color:var(--dim);font-style:normal}
button{border-radius:4px;padding:4px 9px;font:inherit;font-size:11px;font-weight:700;line-height:1.15;cursor:pointer;border:1px solid transparent}
button:disabled{opacity:.45;cursor:not-allowed}
button:focus-visible{outline:2px solid var(--blue);outline-offset:2px}
.btn-primary{background:#e8eaeb;color:#0d0f10;border-color:#e8eaeb}
.btn-primary:hover{background:#f4f6f7;border-color:#f4f6f7}
.btn-ghost{background:transparent;color:#a4adb4;border-color:rgba(255,255,255,.14)}
.btn-ghost:hover{background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.22)}
.btn-icon{background:transparent;color:#7a848c;border-color:rgba(255,255,255,.12);width:28px;padding:4px 0;text-align:center}
.btn-icon:hover{background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.2);color:#a4adb4}
.btn-row{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}
#toast{position:fixed;top:16px;right:16px;max-width:320px;padding:10px 14px;border-radius:6px;font-size:13px;pointer-events:none;opacity:0;transition:opacity .2s;z-index:100}
#toast.show{opacity:1}
#toast.ok{background:rgba(54,215,131,.12);border:1px solid rgba(54,215,131,.3);color:var(--green)}
#toast.err{background:rgba(255,107,107,.1);border:1px solid rgba(255,107,107,.28);color:var(--red)}
.setup-banner{display:none;align-items:center;justify-content:space-between;gap:12px;padding:10px 14px;border:1px solid rgba(255,107,107,.22);background:rgba(255,107,107,.06);border-radius:6px;margin-bottom:12px}
.setup-banner.visible{display:flex}
.setup-step{display:flex;align-items:center;gap:8px;padding:5px 0;font-size:13px;color:var(--muted)}
.step-done{display:inline-flex;width:18px;height:18px;border-radius:50%;background:rgba(54,215,131,.2);color:var(--green);font-size:10px;align-items:center;justify-content:center;font-weight:800;flex-shrink:0}
.step-now{display:inline-flex;width:18px;height:18px;border-radius:50%;background:rgba(101,183,255,.2);color:var(--blue);font-size:10px;align-items:center;justify-content:center;font-weight:800;flex-shrink:0}
.suggested-models{margin-top:10px;background:#0d1012;border:1px solid rgba(101,183,255,.18);border-radius:5px;padding:8px}
.suggested-models .mdl-row{display:flex;align-items:center;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.05);font-size:13px;gap:10px}
.suggested-models .mdl-row:last-child{border-bottom:none}
.sz{color:var(--muted);font-size:12px;flex:1;text-align:right;padding-right:8px}
meter.warn::-webkit-meter-optimum-value{background:var(--amber)}
.controls-note{color:var(--muted);font-size:13px;margin-top:10px}
@media(max-width:1050px){
  body{padding:20px}
  .grid{grid-template-columns:1fr}
  .card{min-height:auto}
}
@media(max-width:680px){
  body{padding:14px;font-size:15px}
  header{display:block}
  h1{font-size:24px}
  .header-right{justify-content:flex-start;margin-top:14px}
  .row{align-items:flex-start;flex-direction:column}
  .btn-row{justify-content:flex-start}
  table{display:block;overflow-x:auto;white-space:nowrap}
  td.actions{min-width:170px}
}
</style>
</head>
<body>
<div class="shell">
<header>
  <div>
    <div class="eyebrow">__APP_EYEBROW__</div>
    <h1>__APP_TITLE__</h1>
    <p class="subtitle">__APP_SUBTITLE__</p>
  </div>
  <span class="header-right"><span id="mode" class="mode">—</span><span id="ts">—</span></span>
</header>
<div id="action" class="action-status"></div>
<div class="grid">
  <section class="card"><h2>Services</h2><div id="svc"><span class="na">loading...</span></div></section>
  <section class="card"><h2>GPU</h2><div id="gpu"><span class="na">loading...</span></div></section>
  <section class="card"><h2>System</h2><div id="sys"><span class="na">loading...</span></div></section>
</div>
<section class="card models-card"><h2>Models</h2><div id="mdl"><span class="na">loading...</span></div></section>
</div>
<script>
const SVCS={"ollama":"ollama","llama-cline":"llama-cline","litellm-proxy":"litellm-proxy"};
const PORTS={"anthropic-proxy":"anthropic-proxy :4000","stable-diffusion":"stable-diffusion :7860"};
function esc(s){const d=document.createElement("div");d.appendChild(document.createTextNode(String(s)));return d.innerHTML;}
function dot(on){return '<span class="dot '+(on?"on":"off")+'"></span>';}
function ctl(d){return d.controls?.enabled===true;}
function setAction(msg,ok){
  const el=document.getElementById("action");
  el.className="action-status "+(ok?"ok":"err");
  el.textContent=msg||"";
}
async function postAction(path,payload){
  setAction("working...",true);
  try{
    const r=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    const d=await r.json();
    setAction(d.message||("HTTP "+r.status),r.ok&&d.ok);
    await poll();
  }catch(e){setAction("action failed: "+e,false);}
}
function serviceButtons(name){
  return `<span class="btn-row"><button onclick="postAction('/api/actions/service',{service:'${name}',action:'start'})">Start</button><button onclick="postAction('/api/actions/service',{service:'${name}',action:'stop'})">Stop</button><button onclick="postAction('/api/actions/service',{service:'${name}',action:'restart'})">Restart</button></span>`;
}
function modelButtons(name,loaded){
  const m=encodeURIComponent(name);
  const unload=loaded?`<button onclick="postAction('/api/actions/ollama',{action:'unload',model:decodeURIComponent('${m}')})">Unload</button>`:"";
  return `<span class="btn-row"><button onclick="postAction('/api/actions/ollama',{action:'warmup',model:decodeURIComponent('${m}')})">Load</button>${unload}</span>`;
}
function renderSvc(d){
  let h="",controls=ctl(d);
  for(const[k,l] of Object.entries(SVCS)){
    const on=d.services?.[k]?.status==="active";
    h+=`<div class="row"><span class="row-main">${dot(on)}<span class="label">${l}</span></span>${controls?serviceButtons(k):""}</div>`;
  }
  for(const[k,l] of Object.entries(PORTS)){const on=d.ports?.[k]?.reachable===true;h+=`<div class="row"><span class="row-main">${dot(on)}<span class="label">${l}</span></span></div>`;}
  if(!controls)h+='<div class="controls-note">Read-only mode is active.</div>';
  document.getElementById("svc").innerHTML=h;
}
function renderGPU(d){
  const g=d.gpu;
  if(!g?.available){document.getElementById("gpu").innerHTML='<span class="na">unavailable</span>';return;}
  const u=(g.vram_used_mib/1024).toFixed(1),t=(g.vram_total_mib/1024).toFixed(1);
  document.getElementById("gpu").innerHTML=`<div class="gpu-name">${esc(g.name)}</div><div class="metric-block"><div class="metric-label"><span>VRAM</span><span class="metric-value">${u} / ${t} GB</span></div><meter value="${g.vram_used_mib}" min="0" max="${g.vram_total_mib}"></meter></div><div class="gpu-stats">Utilization ${esc(g.utilization_pct)}% &nbsp;·&nbsp; Temperature ${esc(g.temp_c)}°C</div>`;
}
function renderSys(d){
  const s=d.system;
  let h="";
  if(s?.ram?.available){
    const u=(s.ram.used_mib/1024).toFixed(1),t=(s.ram.total_mib/1024).toFixed(1);
    h+=`<div class="metric-block"><div class="metric-label"><span>RAM</span><span class="metric-value">${u} / ${t} GB used</span></div><meter value="${s.ram.used_mib}" min="0" max="${s.ram.total_mib}"></meter></div>`;
  }else{h+='<div class="gpu-stats">RAM unavailable</div>';}
  if(s?.cpu?.available){
    h+=`<div class="metric-block"><div class="metric-label"><span>CPU</span><span class="metric-value">${esc(s.cpu.pct)}%</span></div><meter value="${esc(s.cpu.pct)}" min="0" max="100"></meter><div class="gpu-stats">${esc(s.cpu.count)} cores</div></div>`;
  }else{h+='<div class="gpu-stats" style="margin-top:10px">CPU unavailable</div>';}
  document.getElementById("sys").innerHTML=h;
}
function renderMdl(d){
  const o=d.ollama;
  if(!o?.reachable){document.getElementById("mdl").innerHTML='<span class="na">Ollama unreachable</span>';return;}
  if(!o.models?.length){document.getElementById("mdl").innerHTML='<span class="na">no models pulled</span>';return;}
  const rm=new Map((o.running||[]).map(r=>[r.name,r]));
  const controls=ctl(d);
  let h='<table><thead><tr><th>Model</th><th>Size</th><th>Status</th>'+(controls?'<th>Actions</th>':'')+'</tr></thead><tbody>';
  for(const m of o.models){
    const r=rm.get(m.name);
    const badge=r?`<span class="badge">loaded · ${r.vram_mib} MiB</span>`:"";
    h+=`<tr><td class="mono">${esc(m.name)}</td><td class="right">${esc(m.size_gb)} GB</td><td class="right">${badge}</td>${controls?`<td class="right actions">${modelButtons(m.name,!!r)}</td>`:""}</tr>`;
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
    const mode=document.getElementById("mode");
    mode.textContent=ctl(d)?"controls on":"read-only";
    mode.className="mode "+(ctl(d)?"on":"info");
    document.getElementById("action").style.display=ctl(d)?"":"none";
    renderSvc(d);renderGPU(d);renderSys(d);renderMdl(d);
  }catch(e){console.error(e);document.getElementById("ts").textContent="fetch failed";}
}
poll();setInterval(poll,5000);
</script>
</body>
</html>"""


def dashboard_html():
    return (
        DASHBOARD_HTML
        .replace("__APP_TITLE__", APP_TITLE)
        .replace("__APP_EYEBROW__", APP_EYEBROW)
        .replace("__APP_SUBTITLE__", APP_SUBTITLE)
    )

# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

def build_status():
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "controls": {"enabled": controls_enabled()},
        "services": get_services(),
        "ports": probe_ports(),
        "gpu": get_gpu(),
        "system": get_system(),
        "ollama": get_ollama(),
        "storage": get_storage(),
    }


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class MonitorHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress per-request logs

    def _send_json(self, result, status=200):
        body = json.dumps(result).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("invalid Content-Length")
        if length > 4096:
            raise ValueError("request body too large")
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {exc}") from exc

    def _client_is_local(self):
        return self.client_address[0] in LOCAL_CLIENTS

    def do_GET(self):
        if self.path == "/":
            body = dashboard_html().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/status":
            try:
                self._send_json(build_status())
            except Exception:
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path not in ("/api/actions/service", "/api/actions/ollama"):
            self.send_response(404)
            self.end_headers()
            return
        if not controls_enabled():
            self._send_json(_action_result(False, "controls are disabled"), 403)
            return
        if not self._client_is_local():
            self._send_json(_action_result(False, "controls require a localhost client"), 403)
            return
        try:
            body = self._read_json()
        except ValueError as exc:
            self._send_json(_action_result(False, str(exc)), 400)
            return

        if self.path == "/api/actions/service":
            result = run_service_action(body.get("service"), body.get("action"))
        else:
            result = run_ollama_action(body.get("action"), body.get("model"))
        self._send_json(result, 200 if result["ok"] else 400)


def main():
    port = int(os.environ.get("LLM_DASHBOARD_PORT", os.environ.get("MONITOR_PORT", DEFAULT_PORT)))
    host = os.environ.get("LLM_DASHBOARD_HOST", os.environ.get("MONITOR_HOST", DEFAULT_HOST))
    server = ThreadedHTTPServer((host, port), MonitorHandler)
    label = "localhost" if host in ("", "0.0.0.0", "127.0.0.1") else host
    suffix = "controls enabled" if controls_enabled() else "read-only"
    print(f"{APP_TITLE} → http://{label}:{port}  ({suffix}, Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
