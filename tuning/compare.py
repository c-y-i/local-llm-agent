#!/usr/bin/env python3
"""Run a single prompt against multiple Ollama models, side-by-side.

Useful for A/B testing Modelfile or parameter tweaks: change personalities.py,
run `python build.py`, then `python compare.py "prompt" old new` to see the
output difference and timings.

Usage:
    python compare.py "Explain mmap in one sentence." llama3.2:3b qwen3:1.7b
    python compare.py --tokens 96 "Write a haiku about Linux." phi4-mini qwen3:1.7b
    python compare.py --temp 0.2 "..." dolphin-strict-coder dolphin-mentor
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request

OLLAMA_HOST = "127.0.0.1:11434"


def run_one(model: str, prompt: str, tokens: int, temperature: float) -> dict:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "num_predict": tokens,
            "temperature": temperature,
        },
    }
    req = urllib.request.Request(
        f"http://{OLLAMA_HOST}/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        return {"model": model, "error": str(exc)}
    wall = time.monotonic() - started
    eval_count = data.get("eval_count", 0)
    eval_time = data.get("eval_duration", 0) / 1e9
    speed = eval_count / eval_time if eval_time else 0.0
    return {
        "model": model,
        "wall": wall,
        "load": data.get("load_duration", 0) / 1e9,
        "tokens": eval_count,
        "speed": speed,
        "output": data.get("response", "").strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Prompt to send to each model")
    parser.add_argument("models", nargs="+", help="Two or more model names")
    parser.add_argument("--tokens", type=int, default=96, help="num_predict (default 96)")
    parser.add_argument("--temp", type=float, default=0.4, help="temperature (default 0.4)")
    args = parser.parse_args()

    print(f"Prompt: {args.prompt}")
    print(f"num_predict={args.tokens}  temperature={args.temp}")
    print()

    results = [run_one(m, args.prompt, args.tokens, args.temp) for m in args.models]

    for r in results:
        print(f"=== {r['model']} ===")
        if "error" in r:
            print(f"ERROR: {r['error']}")
        else:
            print(
                f"{r['tokens']} tokens  {r['speed']:.1f} tok/s  "
                f"wall {r['wall']:.2f}s  load {r['load']:.2f}s"
            )
            print(r["output"])
        print()

    return 0 if all("error" not in r for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
