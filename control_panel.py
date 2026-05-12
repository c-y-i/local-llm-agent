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
DEFAULT_PULLABLE_MODELS = (
    {"name": "llama3.2:1b",       "size_gb": 1.3,  "desc": "fast / low RAM"},
    {"name": "qwen2.5-coder:1.5b", "size_gb": 0.9, "desc": "small coding"},
    {"name": "qwen2.5-coder:3b",  "size_gb": 1.9,  "desc": "coding"},
    {"name": "qwen3:4b",          "size_gb": 2.6,  "desc": "general chat"},
    {"name": "qwen2.5-coder:7b",  "size_gb": 4.7,  "desc": "coding / Cline"},
    {"name": "qwen3:8b",          "size_gb": 5.2,  "desc": "general chat"},
    {"name": "qwen2.5-coder:14b", "size_gb": 9.0,  "desc": "strong coding"},
    {"name": "qwen2.5-coder:32b", "size_gb": 19.0, "desc": "high-end coding"},
)
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


def _normalize_pullable_model(model):
    if not isinstance(model, dict):
        return None
    name = str(model.get("name", "")).strip()
    if not name:
        return None
    try:
        size_gb = float(model.get("size_gb", 0))
    except (TypeError, ValueError):
        size_gb = 0.0
    return {
        "name": name,
        "size_gb": round(size_gb, 1),
        "desc": str(model.get("desc", "")).strip(),
    }


def pullable_models():
    raw = os.environ.get("LLM_PULLABLE_MODELS_JSON")
    if raw:
        try:
            models = json.loads(raw)
            normalized = [_normalize_pullable_model(m) for m in models]
            return [m for m in normalized if m]
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

    path = os.environ.get("LLM_PULLABLE_MODELS_FILE")
    if path:
        try:
            with open(path) as f:
                models = json.load(f)
            normalized = [_normalize_pullable_model(m) for m in models]
            return [m for m in normalized if m]
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            pass

    return [dict(model) for model in DEFAULT_PULLABLE_MODELS]


def pullable_model_tags():
    return frozenset(model["name"] for model in pullable_models())


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


def get_model_recommendation(gpu, system, models=None):
    if models is None:
        models = pullable_models()
    sized_models = [m for m in models if isinstance(m.get("size_gb"), (int, float)) and m["size_gb"] > 0]
    if not sized_models:
        return None

    memory_gb = None
    memory_kind = "hardware"
    budget_gb = None
    if isinstance(gpu, dict) and gpu.get("available"):
        try:
            memory_gb = gpu.get("vram_total_mib", 0) / 1024
            budget_gb = memory_gb * 0.72
            memory_kind = "VRAM"
        except TypeError:
            memory_gb = None

    ram = system.get("ram", {}) if isinstance(system, dict) else {}
    if budget_gb is None and ram.get("available"):
        try:
            memory_gb = ram.get("total_mib", 0) / 1024
            budget_gb = memory_gb * 0.35
            memory_kind = "RAM"
        except TypeError:
            memory_gb = None

    if budget_gb is None:
        picked = min(sized_models, key=lambda m: m["size_gb"])
        reason = "Hardware details are unavailable, so the smallest configured model is selected."
        context = "2048-4096"
        tier = "unknown hardware"
    else:
        fitting = [m for m in sized_models if m["size_gb"] <= budget_gb]
        if fitting:
            def _rank(model):
                text = f"{model['name']} {model.get('desc', '')}".lower()
                coding_fit = any(term in text for term in ("code", "coder", "cline"))
                return (1 if coding_fit else 0, model["size_gb"])
            picked = max(fitting, key=_rank)
        else:
            picked = min(sized_models, key=lambda m: m["size_gb"])
        headroom = budget_gb / picked["size_gb"] if picked["size_gb"] else 0
        if headroom >= 3.5:
            context = "16384-32768"
        elif headroom >= 2.0:
            context = "8192-16384"
        elif headroom >= 1.2:
            context = "4096-8192"
        else:
            context = "2048-4096"
        tier = f"{memory_gb:.1f} GB {memory_kind}" if memory_gb is not None else "detected hardware"
        reason = (
            f"Selected from the configured pull catalog using a conservative "
            f"{budget_gb:.1f} GB {memory_kind} budget for model weights and KV cache."
        )

    return {
        "model": dict(picked),
        "context": context,
        "tier": tier,
        "reason": reason,
    }


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
        if model not in pullable_model_tags():
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
  font-size:14px;
  font-weight:700;
  border:1px solid var(--line);
  background:rgba(255,255,255,.04);
  color:var(--muted);
  border-radius:999px;
  padding:7px 14px;
  white-space:nowrap;
}
.mode.on{border-color:rgba(54,215,131,.35);background:rgba(54,215,131,.1);color:var(--green)}
.mode.info{border-color:rgba(101,183,255,.35);background:rgba(101,183,255,.08);color:var(--blue)}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:16px}
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
.rec-badge{color:var(--blue);font-size:11px;font-weight:800;text-transform:uppercase;margin-left:6px}
.rec-note{color:var(--muted);font-size:12px;line-height:1.35;margin-top:8px}
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
  <span class="header-right"><a href="/chat" style="font-size:14px;font-weight:700;color:var(--blue);text-decoration:none;border:1px solid rgba(101,183,255,.3);background:rgba(101,183,255,.07);border-radius:999px;padding:7px 16px;white-space:nowrap" onmouseover="this.style.background='rgba(101,183,255,.14)'" onmouseout="this.style.background='rgba(101,183,255,.07)'">Chat</a><span id="mode" class="mode">—</span><span id="ts">—</span></span>
</header>
<div id="setup-banner" class="setup-banner"></div>
<div class="grid">
  <section class="card"><h2>Services</h2><div id="svc"><span class="na">loading...</span></div></section>
  <section class="card"><h2>GPU</h2><div id="gpu"><span class="na">loading...</span></div></section>
  <section class="card"><h2>System</h2><div id="sys"><span class="na">loading...</span></div></section>
  <section class="card"><h2>Storage</h2><div id="sto"><span class="na">loading...</span></div></section>
</div>
<section class="card"><h2>Models</h2><div id="mdl"><span class="na">loading...</span></div></section>
<section class="card" style="margin-top:16px">
  <h2>Pull from Hugging Face</h2>
  <p style="font-size:14px;color:var(--muted);margin-bottom:14px;line-height:1.6">
    Ollama can run any GGUF model directly from Hugging Face. Use the format below — no account needed.
  </p>
  <div style="background:#060708;border:1px solid rgba(255,255,255,.09);border-radius:5px;padding:12px 14px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;color:#d8dee2;margin-bottom:14px">
    ollama run hf.co/&lt;user&gt;/&lt;repo&gt;:&lt;quant&gt;
  </div>
  <p style="font-size:13px;color:var(--muted);margin-bottom:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase">Recommended quantizations</p>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px;margin-bottom:16px">
    <div style="background:#060708;border:1px solid rgba(255,255,255,.07);border-radius:5px;padding:10px 12px">
      <div style="font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;color:var(--blue);margin-bottom:3px">Q4_K_M</div>
      <div style="font-size:12px;color:var(--muted)">Best balance of size and quality. Start here.</div>
    </div>
    <div style="background:#060708;border:1px solid rgba(255,255,255,.07);border-radius:5px;padding:10px 12px">
      <div style="font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;color:var(--blue);margin-bottom:3px">Q5_K_M</div>
      <div style="font-size:12px;color:var(--muted)">Higher quality, more VRAM. Good if you have headroom.</div>
    </div>
    <div style="background:#060708;border:1px solid rgba(255,255,255,.07);border-radius:5px;padding:10px 12px">
      <div style="font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;color:var(--blue);margin-bottom:3px">Q2_K</div>
      <div style="font-size:12px;color:var(--muted)">Smallest, lowest quality. Use only if RAM is tight.</div>
    </div>
    <div style="background:#060708;border:1px solid rgba(255,255,255,.07);border-radius:5px;padding:10px 12px">
      <div style="font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;color:var(--blue);margin-bottom:3px">IQ4_XS</div>
      <div style="font-size:12px;color:var(--muted)">Smaller than Q4_K_M, similar quality. Good compromise.</div>
    </div>
  </div>
  <p style="font-size:13px;color:var(--muted);margin-bottom:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase">Example</p>
  <div style="background:#060708;border:1px solid rgba(255,255,255,.09);border-radius:5px;padding:12px 14px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;color:#d8dee2;margin-bottom:10px">
    ollama run hf.co/bartowski/Qwen2.5-14B-Instruct-GGUF:Q4_K_M
  </div>
  <p style="font-size:12px;color:var(--dim)">
    Browse models at <span style="color:var(--blue);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">huggingface.co/bartowski</span> &mdash; bartowski publishes reliable GGUF quantizations for most popular models.
  </p>
</section>
</div>
<div id="toast"></div>
<script>
const SVCS={"ollama":"ollama","llama-cline":"llama-cline","litellm-proxy":"litellm-proxy"};
const PORTS={"anthropic-proxy":"anthropic-proxy :4000","stable-diffusion":"stable-diffusion :7860"};
function esc(s){const d=document.createElement("div");d.appendChild(document.createTextNode(String(s)));return d.innerHTML;}
function dot(on){return '<span class="dot '+(on?"on":"off")+'"></span>';}
function ctl(d){return d.controls?.enabled===true;}
let _toastTimer=null,_toastClearPending=false;
function setAction(msg,ok){
  const t=document.getElementById("toast");
  clearTimeout(_toastTimer);
  _toastClearPending=false;
  t.className="show "+(ok?"ok":"err");
  t.textContent=msg||"";
  _toastTimer=setTimeout(()=>{t.className="";},4000);
}
async function postAction(path,payload){
  setAction("working…",true);
  try{
    const r=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    const d=await r.json();
    setAction(d.message||("HTTP "+r.status),r.ok&&d.ok);
    await poll();
    _toastClearPending=true;
  }catch(e){setAction("action failed: "+e,false);}
}
function pullModel(btn,model){
  btn.disabled=true;btn.textContent="Pulling…";
  postAction("/api/actions/ollama",{action:"pull",model:model});
}
function serviceButtons(name){
  return `<span class="btn-row"><button class="btn-primary" onclick="postAction('/api/actions/service',{service:'${name}',action:'start'})">Start</button><button class="btn-ghost" onclick="postAction('/api/actions/service',{service:'${name}',action:'stop'})">Stop</button><button class="btn-icon" title="Restart" onclick="postAction('/api/actions/service',{service:'${name}',action:'restart'})">&#x21BA;</button></span>`;
}
function modelButtons(name,loaded){
  const m=encodeURIComponent(name);
  const unload=loaded?`<button class="btn-ghost" onclick="postAction('/api/actions/ollama',{action:'unload',model:decodeURIComponent('${m}')})">Unload</button>`:"";
  return `<span class="btn-row"><button class="btn-primary" onclick="postAction('/api/actions/ollama',{action:'warmup',model:decodeURIComponent('${m}')})">Load</button>${unload}</span>`;
}
function suggestedModels(d){
  const models=Array.isArray(d.pullable_models)?d.pullable_models:[];
  const rec=d.recommendation?.model?.name;
  return models.slice().sort((a,b)=>{
    if(a.name===rec)return -1;
    if(b.name===rec)return 1;
    return (a.size_gb||0)-(b.size_gb||0);
  });
}
function renderBanner(d){
  const b=document.getElementById("setup-banner");
  if(ctl(d)&&!d.ollama?.reachable){
    b.innerHTML=`<div><span style="color:var(--red)">&#x25CF; Ollama is not running</span><br><span style="color:var(--dim);font-size:12px">Start the service to use models and controls.</span></div><button class="btn-primary" onclick="postAction('/api/actions/service',{service:'ollama',action:'start'})">Start Ollama</button>`;
    b.classList.add("visible");
  }else{
    b.innerHTML="";b.classList.remove("visible");
  }
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
  document.getElementById("gpu").innerHTML=`<div class="gpu-name">${esc(g.name)}</div><div class="metric-block"><div class="metric-label"><span>VRAM</span><span class="metric-value">${u} / ${t} GB</span></div><meter value="${g.vram_used_mib}" min="0" max="${g.vram_total_mib}"></meter></div><div class="gpu-stats">Utilization ${esc(g.utilization_pct)}% &nbsp;&middot;&nbsp; Temperature ${esc(g.temp_c)}&deg;C</div>`;
}
function renderSys(d){
  const s=d.system;let h="";
  if(s?.cpu?.model){h+=`<div class="mono" style="font-size:12px;color:#d8dee2;margin-bottom:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(s.cpu.model)}</div>`;}
  if(s?.ram?.available){
    const u=(s.ram.used_mib/1024).toFixed(1),t=(s.ram.total_mib/1024).toFixed(1);
    h+=`<div class="metric-block"><div class="metric-label"><span>RAM</span><span class="metric-value">${u} / ${t} GB used</span></div><meter value="${s.ram.used_mib}" min="0" max="${s.ram.total_mib}"></meter></div>`;
  }else{h+='<div class="gpu-stats">RAM unavailable</div>';}
  if(s?.cpu?.available){
    h+=`<div class="metric-block"><div class="metric-label"><span>CPU</span><span class="metric-value">${esc(s.cpu.pct)}%</span></div><meter value="${esc(s.cpu.pct)}" min="0" max="100"></meter><div class="gpu-stats">${esc(s.cpu.count)} cores</div></div>`;
  }else{h+='<div class="gpu-stats" style="margin-top:10px">CPU unavailable</div>';}
  document.getElementById("sys").innerHTML=h;
}
function renderStorage(d){
  const s=d.storage;
  if(!s){document.getElementById("sto").innerHTML='<span class="na">unavailable</span>';return;}
  let h="";
  for(const[label,entry] of Object.entries(s)){
    if(!entry.available)continue;
    const used=(entry.used_bytes/1e9).toFixed(1),total=(entry.total_bytes/1e9).toFixed(1);
    const pct=entry.used_bytes/entry.total_bytes;
    const warn=pct>0.85?" class='warn' ":"";
    h+=`<div class="metric-block"><div class="metric-label"><span>${esc(label)}</span><span class="metric-value">${used} / ${total} GB</span></div><meter ${warn}value="${entry.used_bytes}" min="0" max="${entry.total_bytes}"></meter></div>`;
  }
  document.getElementById("sto").innerHTML=h||'<span class="na">unavailable</span>';
}
function renderMdl(d){
  const o=d.ollama,controls=ctl(d);
  if(!o?.reachable){document.getElementById("mdl").innerHTML='<span class="na">Ollama unreachable</span>';return;}
  if(!o.models?.length){
    if(controls){
      let h='<div class="setup-step"><span class="step-done">&#x2713;</span>Ollama running</div>';
      h+='<div class="setup-step"><span class="step-now">2</span>No models pulled &mdash; pull one to get started</div>';
      const rec=d.recommendation,recName=rec?.model?.name;
      if(recName){
        h+=`<div class="rec-note">Recommended: <span class="mono">${esc(recName)}</span> for ${esc(rec.tier||"detected hardware")} &middot; context ${esc(rec.context||"default")}</div>`;
      }
      h+='<div class="suggested-models">';
      for(const m of suggestedModels(d)){
        const isRec=m.name===recName;
        const size=(Number(m.size_gb)||0).toFixed(1)+" GB";
        h+=`<div class="mdl-row"><span class="mono">${esc(m.name)}${isRec?'<span class="rec-badge">Recommended</span>':""}</span><span class="sz">${esc(size)} &middot; ${esc(m.desc||"model")}</span><button class="btn-primary" onclick="pullModel(this,decodeURIComponent('${encodeURIComponent(m.name)}'))">Pull</button></div>`;
      }
      h+='</div>';
      document.getElementById("mdl").innerHTML=h;
    }else{
      document.getElementById("mdl").innerHTML='<span class="na">no models pulled</span>';
    }
    return;
  }
  const rm=new Map((o.running||[]).map(r=>[r.name,r]));
  let h='<table><thead><tr><th>Model</th><th>Size</th><th>Status</th>'+(controls?'<th>Actions</th>':'')+'</tr></thead><tbody>';
  for(const m of o.models){
    const r=rm.get(m.name);
    const badge=r?`<span class="badge">loaded &middot; ${r.vram_mib} MiB</span>`:"";
    h+=`<tr><td class="mono">${esc(m.name)}</td><td class="right">${esc(m.size_gb)} GB</td><td class="right">${badge}</td>${controls?`<td class="right actions">${modelButtons(m.name,!!r)}</td>`:""}</tr>`;
  }
  h+="</tbody></table>";
  document.getElementById("mdl").innerHTML=h;
}
async function poll(){
  if(_toastClearPending){_toastClearPending=false;clearTimeout(_toastTimer);document.getElementById("toast").className="";}
  try{
    const r=await fetch("/api/status");
    if(!r.ok)throw new Error(r.status);
    const d=await r.json();
    document.getElementById("ts").textContent="updated "+(d.timestamp?.slice(11,19)??"—");
    const mode=document.getElementById("mode");
    mode.textContent=ctl(d)?"controls on":"read-only";
    mode.className="mode "+(ctl(d)?"on":"info");
    renderBanner(d);
    renderSvc(d);renderGPU(d);renderSys(d);renderStorage(d);renderMdl(d);
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


CHAT_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Local LLM Chat</title>
<style>
:root{
  --bg:#08090a;--line:rgba(255,255,255,.09);--line-strong:rgba(255,255,255,.16);
  --text:#f4f7f8;--muted:#a4adb4;--dim:#7a848c;
  --green:#36d783;--red:#ff6b6b;--blue:#65b7ff;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:16px;line-height:1.5}
.app{display:flex;flex-direction:column;height:100vh;max-width:860px;margin:0 auto;padding:0 24px}
.app-header{
  display:flex;align-items:flex-start;justify-content:space-between;gap:16px;
  padding:22px 0 16px;border-bottom:1px solid var(--line);flex-shrink:0;
}
.eyebrow{color:var(--blue);font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;margin-bottom:4px}
h1{font-size:26px;font-weight:720;color:#fff;line-height:1.15}
.header-right{display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:flex-end;padding-top:4px}
a.back{font-size:12px;font-weight:700;color:var(--muted);text-decoration:none;border:1px solid var(--line-strong);border-radius:999px;padding:5px 11px;white-space:nowrap}
a.back:hover{background:rgba(255,255,255,.05);color:var(--text)}
select{
  background:#0f1113;color:var(--text);border:1px solid var(--line-strong);
  border-radius:4px;padding:6px 10px;font:inherit;font-size:13px;cursor:pointer;outline:none;min-width:180px;
}
select:focus{border-color:rgba(101,183,255,.45)}
button{border-radius:4px;padding:6px 12px;font:inherit;font-size:12px;font-weight:700;cursor:pointer;border:1px solid transparent}
button:disabled{opacity:.4;cursor:not-allowed}
.btn-ghost{background:transparent;color:var(--muted);border-color:var(--line-strong)}
.btn-ghost:hover:not(:disabled){background:rgba(255,255,255,.05);color:var(--text);border-color:rgba(255,255,255,.22)}
.messages{flex:1;overflow-y:auto;padding:20px 0;display:flex;flex-direction:column;gap:14px;scroll-behavior:smooth}
.messages::-webkit-scrollbar{width:6px}
.messages::-webkit-scrollbar-thumb{background:rgba(255,255,255,.1);border-radius:3px}
.message{display:flex;gap:10px;max-width:88%}
.message.user{align-self:flex-end;flex-direction:row-reverse}
.message.assistant{align-self:flex-start}
.msg-avatar{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;flex-shrink:0;margin-top:3px}
.message.user .msg-avatar{background:rgba(101,183,255,.18);color:var(--blue)}
.message.assistant .msg-avatar{background:rgba(54,215,131,.13);color:var(--green)}
.msg-bubble{padding:11px 15px;border-radius:8px;font-size:15px;line-height:1.65;word-break:break-word}
.message.user .msg-bubble{background:rgba(101,183,255,.09);border:1px solid rgba(101,183,255,.18)}
.message.assistant .msg-bubble{background:#0f1113;border:1px solid rgba(255,255,255,.07)}
.msg-bubble pre{background:#060708;border:1px solid rgba(255,255,255,.09);border-radius:5px;padding:11px 14px;margin:10px 0;overflow-x:auto;font-size:13px}
.msg-bubble code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.msg-bubble p:not(:last-child){margin-bottom:7px}
.cursor{display:inline-block;width:2px;height:.9em;background:var(--muted);margin-left:2px;vertical-align:text-bottom;animation:blink .85s step-end infinite}
@keyframes blink{50%{opacity:0}}
.empty-state{display:flex;flex-direction:column;align-items:center;justify-content:center;flex:1;gap:10px;color:var(--dim);font-size:14px;text-align:center;padding:40px 0}
.empty-icon{font-size:36px;line-height:1;margin-bottom:4px;color:var(--muted)}
.input-bar{padding:14px 0 20px;border-top:1px solid var(--line);flex-shrink:0}
.input-wrap{display:flex;gap:8px;align-items:flex-end}
textarea{flex:1;background:#0f1113;border:1px solid var(--line-strong);border-radius:6px;color:var(--text);font:inherit;font-size:15px;padding:10px 14px;resize:none;min-height:44px;max-height:180px;outline:none;line-height:1.55}
textarea:focus{border-color:rgba(101,183,255,.38)}
textarea::placeholder{color:var(--dim)}
.send-btn{background:#e8eaeb;color:#0d0f10;border:none;border-radius:6px;padding:0 18px;font:inherit;font-size:13px;font-weight:700;cursor:pointer;white-space:nowrap;flex-shrink:0;height:44px}
.send-btn:hover:not(:disabled){background:#f4f6f7}
.send-btn:disabled{opacity:.4;cursor:not-allowed}
#toast{position:fixed;top:16px;right:16px;max-width:300px;padding:10px 14px;border-radius:6px;font-size:13px;opacity:0;pointer-events:none;transition:opacity .2s;z-index:100}
#toast.show{opacity:1;background:rgba(255,107,107,.1);border:1px solid rgba(255,107,107,.28);color:var(--red)}
@media(max-width:680px){
  .app{padding:0 14px}.message{max-width:96%}h1{font-size:22px}
  .app-header{flex-direction:column;gap:8px}.header-right{margin-top:0}
}
</style>
</head>
<body>
<div class="app">
  <header class="app-header">
    <div>
      <div class="eyebrow">Local runtime</div>
      <h1>Local LLM Chat</h1>
    </div>
    <div class="header-right">
      <select id="model-sel" title="Select model"><option value="">loading models…</option></select>
      <button class="btn-ghost" id="new-btn" onclick="newChat()">New chat</button>
      <a class="back" href="/">← Dashboard</a>
    </div>
  </header>
  <div class="messages" id="messages">
    <div class="empty-state" id="empty">
      <div class="empty-icon">&#x2B50;</div>
      <div>Select a model and start chatting</div>
    </div>
  </div>
  <div class="input-bar">
    <div class="input-wrap">
      <textarea id="input" placeholder="Message…" rows="1"
        onkeydown="handleKey(event)" oninput="autoResize(this)"></textarea>
      <button class="send-btn" id="send-btn" onclick="sendMessage()">Send</button>
    </div>
  </div>
</div>
<div id="toast"></div>
<script>
var chatMsgs=[];
var streaming=false;

function esc(s){var d=document.createElement("div");d.appendChild(document.createTextNode(String(s)));return d.innerHTML;}

function renderMd(text){
  var html="",lines=text.split("\\n"),inCode=false,codeAcc=[];
  for(var i=0;i<lines.length;i++){
    var line=lines[i];
    if(!inCode&&line.startsWith("```")){inCode=true;codeAcc=[];}
    else if(inCode&&line.startsWith("```")){inCode=false;html+="<pre><code>"+esc(codeAcc.join("\\n"))+"</code></pre>";}
    else if(inCode){codeAcc.push(line);}
    else{
      var l=esc(line);
      l=l.replace(/`([^`]+)`/g,"<code>$1</code>");
      l=l.replace(/[*][*]([^*]+)[*][*]/g,"<strong>$1</strong>");
      l=l.replace(/[*]([^*]+)[*]/g,"<em>$1</em>");
      html+=l.trim()?"<p>"+l+"</p>":"<p style='margin:3px 0'></p>";
    }
  }
  if(inCode&&codeAcc.length){html+="<pre><code>"+esc(codeAcc.join("\\n"))+"</code></pre>";}
  return html;
}

function toast(msg){var t=document.getElementById("toast");t.textContent=msg;t.className="show";setTimeout(function(){t.className="";},4500);}
function autoResize(el){el.style.height="auto";el.style.height=Math.min(el.scrollHeight,180)+"px";}
function handleKey(e){if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();sendMessage();}}
function scrollBot(){var m=document.getElementById("messages");m.scrollTop=m.scrollHeight;}

function newChat(){
  if(streaming)return;
  chatMsgs=[];
  document.getElementById("messages").innerHTML="<div class='empty-state' id='empty'><div class='empty-icon'>&#x2B50;</div><div>Select a model and start chatting</div></div>";
}

function appendMsg(role,content){
  var empty=document.getElementById("empty");if(empty)empty.remove();
  var wrap=document.createElement("div");wrap.className="message "+role;
  var av=document.createElement("div");av.className="msg-avatar";av.textContent=role==="user"?"U":"AI";
  var bub=document.createElement("div");bub.className="msg-bubble";
  bub.innerHTML=role==="user"?"<p>"+esc(content)+"</p>":renderMd(content)+"<span class='cursor'></span>";
  wrap.appendChild(av);wrap.appendChild(bub);
  document.getElementById("messages").appendChild(wrap);
  scrollBot();return bub;
}

async function sendMessage(){
  if(streaming)return;
  var input=document.getElementById("input");
  var text=input.value.trim();if(!text)return;
  var model=document.getElementById("model-sel").value;
  if(!model){toast("Select a model first");return;}
  input.value="";input.style.height="auto";
  appendMsg("user",text);
  chatMsgs.push({role:"user",content:text});
  var bubble=appendMsg("assistant","");
  streaming=true;
  document.getElementById("send-btn").disabled=true;
  document.getElementById("new-btn").disabled=true;
  var fullText="";
  try{
    var resp=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:model,messages:chatMsgs})});
    if(!resp.ok)throw new Error("HTTP "+resp.status);
    var reader=resp.body.getReader(),decoder=new TextDecoder(),buf="";
    while(true){
      var ref=await reader.read();if(ref.done)break;
      buf+=decoder.decode(ref.value,{stream:true});
      var parts=buf.split("\\n");buf=parts.pop();
      for(var i=0;i<parts.length;i++){
        var ln=parts[i];if(!ln.startsWith("data: "))continue;
        try{
          var chunk=JSON.parse(ln.slice(6));
          if(chunk.error){toast(chunk.error);break;}
          if(chunk.delta){fullText+=chunk.delta;bubble.innerHTML=renderMd(fullText)+"<span class='cursor'></span>";scrollBot();}
          if(chunk.done)break;
        }catch(e){}
      }
    }
    bubble.innerHTML=renderMd(fullText);
    chatMsgs.push({role:"assistant",content:fullText});
  }catch(e){
    bubble.innerHTML="<span style='color:var(--red)'>"+esc(String(e))+"</span>";
    toast("Request failed");chatMsgs.pop();
  }
  streaming=false;
  document.getElementById("send-btn").disabled=false;
  document.getElementById("new-btn").disabled=false;
  document.getElementById("input").focus();scrollBot();
}

async function loadModels(){
  try{
    var r=await fetch("/api/models"),d=await r.json();
    var sel=document.getElementById("model-sel");sel.innerHTML="";
    if(!d.reachable){sel.innerHTML="<option value=''>Ollama not running</option>";return;}
    if(!d.models||!d.models.length){sel.innerHTML="<option value=''>no models pulled</option>";return;}
    for(var i=0;i<d.models.length;i++){
      var opt=document.createElement("option");
      opt.value=d.models[i].name;
      opt.textContent=d.models[i].name+" ("+d.models[i].size_gb+" GB)";
      sel.appendChild(opt);
    }
  }catch(e){document.getElementById("model-sel").innerHTML="<option value=''>error loading models</option>";}
}
loadModels();
document.getElementById("input").focus();
</script>
</body>
</html>"""


def chat_html():
    return CHAT_HTML

# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

def build_status():
    gpu = get_gpu()
    system = get_system()
    models = pullable_models()
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "controls": {"enabled": controls_enabled()},
        "services": get_services(),
        "ports": probe_ports(),
        "gpu": gpu,
        "system": system,
        "ollama": get_ollama(),
        "storage": get_storage(),
        "pullable_models": models,
        "recommendation": get_model_recommendation(gpu, system, models),
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
        elif self.path == "/chat":
            body = chat_html().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/models":
            state = get_ollama()
            self._send_json({
                "reachable": state.get("reachable", False),
                "models": state.get("models", []),
            })
        else:
            self.send_response(404)
            self.end_headers()

    def _sse(self, data: dict) -> bytes:
        return ("data: " + json.dumps(data) + "\n\n").encode()

    def _handle_chat(self):
        try:
            body = self._read_json()
        except ValueError as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        model = str(body.get("model", "")).strip()
        messages = body.get("messages", [])
        if not model:
            self._send_json({"error": "model is required"}, 400)
            return
        clean = []
        if isinstance(messages, list):
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                role = str(msg.get("role", "")).strip()
                content = str(msg.get("content", ""))
                if role in ("user", "assistant", "system") and content:
                    clean.append({"role": role, "content": content})
        import urllib.error as _ue
        payload = json.dumps({"model": model, "messages": clean, "stream": True}).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                for raw in resp:
                    line = raw.strip()
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("message", {}).get("content", "")
                    done = bool(chunk.get("done", False))
                    self.wfile.write(self._sse({"delta": delta, "done": done}))
                    self.wfile.flush()
                    if done:
                        break
        except _ue.HTTPError as exc:
            try:
                self.wfile.write(self._sse({"error": f"Ollama HTTP {exc.code}", "done": True}))
                self.wfile.flush()
            except Exception:
                pass
        except Exception as exc:
            try:
                self.wfile.write(self._sse({"error": str(exc), "done": True}))
                self.wfile.flush()
            except Exception:
                pass

    def do_POST(self):
        if self.path == "/api/chat":
            self._handle_chat()
            return
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
