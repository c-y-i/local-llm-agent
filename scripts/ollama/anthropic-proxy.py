#!/usr/bin/env python3
"""Minimal Anthropic Messages API → Ollama proxy for Claude Code + local models.

Claude Code speaks Anthropic's Messages API. Ollama speaks OpenAI's chat
completions API. This proxy translates between them without LiteLLM so we
can reliably pass think:false and strip reasoning blocks.

Listen port: 4000 (replace LiteLLM for the models listed in MODEL_MAP).
Ollama port: 11434.

Usage:
    python3 anthropic-proxy.py
    claude-local --model qwen3-claude
"""
import json
import os
import re
import uuid
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

OLLAMA_BASE = "http://localhost:11434"
ENABLE_INTENT_ROUTER = os.getenv("CLAUDE_PROXY_ENABLE_INTENT_ROUTER", "1") not in {"0", "false", "False", "no"}
LOCAL_GUARDRAIL = """Local Claude Code model rules:
- Use tools only when the user asks you to inspect files, edit files, run commands, or gather workspace state.
- For greetings, small talk, status checks, and simple Q&A, answer in plain text without tools.
- Never call a tool with a placeholder path such as /path/to/file, /path/to/your/file.txt, example.txt, or TODO.
- If a required file path or command is missing, ask one concise follow-up question instead of inventing it."""

# Map Anthropic model names → Ollama model tags
MODEL_MAP = {
    "qwen3-claude": "qwen3-claude",
    "qwen3:4b": "qwen3:4b",
    "qwen3:1.7b": "qwen3:1.7b",
    "hermes3:3b": "hermes3:3b",
    "llama3.2:3b": "llama3.2:3b",
}


def text_from_content(value) -> str:
    """Convert Anthropic block content into text for Ollama/OpenAI messages."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            else:
                parts.append(json.dumps(item))
        return "\n".join(part for part in parts if part)
    return json.dumps(value)


def strip_thinking_text(text: str) -> str:
    """Remove model-emitted thinking text that can leak into content."""
    if not text:
        return text
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    if "<think>" in text:
        text = text.split("<think>", 1)[0]
    return text.strip()


def strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```json") and stripped.endswith("```"):
        return stripped.removeprefix("```json").removesuffix("```").strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        return stripped.removeprefix("```").removesuffix("```").strip()
    return stripped


def contains_placeholder_path(value) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        return any(
            marker in lowered
            for marker in (
                "/path/to/",
                "/users/user/",
                "example.txt",
                "your/file",
                "placeholder",
            )
        )
    if isinstance(value, dict):
        return any(contains_placeholder_path(v) for v in value.values())
    if isinstance(value, list):
        return any(contains_placeholder_path(v) for v in value)
    return False


def is_fake_tool_json(text: str) -> bool:
    candidate = strip_json_fence(text)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        return False

    if not isinstance(data, dict):
        return False

    if "name" in data and "arguments" in data:
        return True

    if "name" in data and "properties" in data:
        return True

    if contains_placeholder_path(data):
        return True

    if len(data) == 1:
        key = next(iter(data))
        if isinstance(key, str) and ("__" in key or key.lower().startswith("claude")):
            return True

    return False


def parse_json_object(text: str):
    candidate = strip_json_fence(text)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def anthropic_tool_names(tools: list[dict]) -> set[str]:
    return {tool.get("name", "") for tool in tools if tool.get("name")}


def choose_tool_name(preferred: list[str], available: set[str]) -> str | None:
    if not available:
        return preferred[0] if preferred else None
    for name in preferred:
        if name in available:
            return name
    lower_map = {name.lower(): name for name in available}
    for name in preferred:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    for preferred_name in preferred:
        needle = preferred_name.lower()
        for available_name in available:
            haystack = available_name.lower()
            if haystack.startswith(needle) or needle in haystack:
                return available_name
    return None


def latest_user_text_from_body(body: dict) -> str:
    for msg in reversed(body.get("messages", [])):
        if msg.get("role") != "user":
            continue
        return text_from_content(msg.get("content", "")).strip()
    return ""


def latest_plain_user_text(body: dict) -> str:
    for msg in reversed(body.get("messages", [])):
        if msg.get("role") != "user":
            continue
        content = msg.get("content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            if any(isinstance(block, dict) and block.get("type") == "tool_result" for block in content):
                return ""
            parts = [
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            return "\n".join(part for part in parts if part).strip()
    return ""


def path_from_args(args: dict) -> str:
    for key in ("file_path", "path", "folder_path", "directory", "dir"):
        value = args.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def path_from_text(text: str) -> str:
    match = re.search(r"(/(?:[\w.@:+-]+/)*[\w.@:+-]+/?)(?=$|\s|[?.!,;:])", text)
    return match.group(1) if match else ""


def wants_current_directory(text: str) -> bool:
    lowered = text.lower()
    return any(
        phrase in lowered
        for phrase in (
            "what path are we in",
            "which path are we in",
            "what directory are we in",
            "which directory are we in",
            "where are we",
            "current directory",
            "cwd",
            "pwd",
        )
    )


def wants_directory_listing(text: str) -> bool:
    lowered = text.lower()
    return any(
        phrase in lowered
        for phrase in (
            "what folders",
            "what files",
            "what's in",
            "whats in",
            "what is in",
            "list",
            "read in",
            "see what's in",
            "show me what's in",
        )
    )


def anthropic_tool_response(model: str, tool_name: str, tool_input: dict) -> dict:
    return {
        "id": f"msg_{uuid.uuid4().hex}",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [
            {
                "type": "tool_use",
                "id": f"toolu_{uuid.uuid4().hex[:8]}",
                "name": tool_name,
                "input": tool_input,
            }
        ],
        "stop_reason": "tool_use",
        "stop_sequence": None,
        "usage": {"input_tokens": 0, "output_tokens": 0},
    }


def direct_filesystem_tool(body: dict) -> dict | None:
    if not ENABLE_INTENT_ROUTER:
        return None

    user_text = latest_plain_user_text(body)
    if not user_text:
        return None

    available = anthropic_tool_names(body.get("tools", []))
    model = body.get("model", "")
    path = path_from_text(user_text)

    if wants_current_directory(user_text):
        tool_name = choose_tool_name(["Bash"], available)
        if tool_name:
            return anthropic_tool_response(
                model,
                tool_name,
                {"command": "pwd", "description": "Print current working directory"},
            )

    if wants_directory_listing(user_text):
        if path:
            tool_name = choose_tool_name(["LS", "List"], available)
            if tool_name:
                return anthropic_tool_response(model, tool_name, {"path": path})
            tool_name = choose_tool_name(["Bash"], available)
            if tool_name:
                return anthropic_tool_response(
                    model,
                    tool_name,
                    {"command": f"ls -la {path}", "description": f"List {path}"},
                )
        elif "here" in user_text.lower() or "this folder" in user_text.lower():
            tool_name = choose_tool_name(["Bash"], available)
            if tool_name:
                return anthropic_tool_response(
                    model,
                    tool_name,
                    {"command": "pwd && ls -la", "description": "List current directory"},
                )

    return None


def fake_tool_json_to_anthropic(text: str, tools: list[dict], user_text: str) -> dict | None:
    data = parse_json_object(text)
    if not data:
        return None

    raw_name = ""
    args = {}
    if "name" in data and "arguments" in data:
        raw_name = str(data.get("name") or "")
        raw_args = data.get("arguments") or {}
        args = raw_args if isinstance(raw_args, dict) else {}
    elif "name" in data and "properties" in data:
        raw_name = str(data.get("name") or "")
        args = {}
    elif len(data) == 1:
        raw_name = str(next(iter(data)))
        raw_args = data[raw_name] or {}
        args = raw_args if isinstance(raw_args, dict) else {}

    if not raw_name:
        return None

    if contains_placeholder_path(args):
        return None

    available = anthropic_tool_names(tools)
    lowered_name = raw_name.lower()
    lowered_user = user_text.lower()

    if lowered_name in {"read", "ls", "list", "list_dir", "list directory"}:
        path = path_from_args(args) or path_from_text(user_text)
        if not path:
            return None
        if os.path.isdir(path) or "folder" in lowered_user or "directory" in lowered_user:
            tool_name = choose_tool_name(["LS", "List"], available)
            tool_args = {"path": path}
        else:
            tool_name = choose_tool_name(["Read"], available)
            tool_args = {"file_path": path}
        if tool_name:
            return {
                "type": "tool_use",
                "id": f"toolu_{uuid.uuid4().hex[:8]}",
                "name": tool_name,
                "input": tool_args,
            }

    if lowered_name in {"bash", "run", "shell"}:
        command = args.get("command")
        if isinstance(command, str) and command.strip():
            tool_name = choose_tool_name(["Bash"], available)
            if tool_name:
                return {
                    "type": "tool_use",
                    "id": f"toolu_{uuid.uuid4().hex[:8]}",
                    "name": tool_name,
                    "input": {"command": command.strip(), "description": args.get("description", "Run shell command")},
                }

    if "directory" in lowered_user or "cwd" in lowered_user or "where are we" in lowered_user:
        tool_name = choose_tool_name(["Bash"], available)
        if tool_name:
            return {
                "type": "tool_use",
                "id": f"toolu_{uuid.uuid4().hex[:8]}",
                "name": tool_name,
                "input": {"command": "pwd", "description": "Print current working directory"},
            }

    return None


def ollama_model_for(body: dict) -> str:
    return MODEL_MAP.get(body.get("model", ""), body.get("model", ""))


def model_needs_no_think(model: str) -> bool:
    return model.startswith("qwen3")


def add_no_think(messages: list[dict]) -> None:
    """Tell Qwen3 chat templates not to spend the response on reasoning."""
    for msg in reversed(messages):
        if msg.get("role") == "user" and isinstance(msg.get("content"), str):
            content = msg["content"]
            if "/no_think" not in content[:64]:
                msg["content"] = "/no_think\n" + content
            return


def latest_user_text(messages: list[dict]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return (msg.get("content") or "").strip()
    return ""


def is_smalltalk(text: str) -> bool:
    normalized = " ".join(text.lower().split())
    return normalized in {
        "hi",
        "hello",
        "hey",
        "yo",
        "sup",
        "good morning",
        "good afternoon",
        "good evening",
        "thanks",
        "thank you",
        "ok",
        "okay",
        "test",
        "ping",
    }


def add_local_guardrail(messages: list[dict]) -> None:
    messages.append({"role": "system", "content": LOCAL_GUARDRAIL})


def anthropic_to_openai(body: dict) -> dict:
    """Convert Anthropic Messages API request → Ollama OpenAI request."""
    messages = []

    # System prompt
    system = body.get("system")
    if system:
        if isinstance(system, list):
            system = " ".join(b.get("text", "") for b in system if b.get("type") == "text")
        messages.append({"role": "system", "content": system})

    # Messages
    for msg in body.get("messages", []):
        role = msg["role"]
        content = msg["content"]
        if isinstance(content, str):
            messages.append({"role": role, "content": content})
        elif isinstance(content, list):
            # Handle tool results and text blocks
            parts = []
            tool_results = []
            for block in content:
                btype = block.get("type")
                if btype == "text":
                    parts.append(block["text"])
                elif btype == "tool_use":
                    # assistant tool call already handled below
                    pass
                elif btype == "tool_result":
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id", ""),
                        "content": text_from_content(block.get("content", "")),
                    })
            if tool_results:
                messages.extend(tool_results)
            elif parts:
                messages.append({"role": role, "content": "\n".join(parts)})
            else:
                # assistant message with tool_use blocks
                tool_calls = []
                text_parts = []
                for block in content:
                    if block.get("type") == "tool_use":
                        tool_calls.append({
                            "id": block.get("id", f"call_{uuid.uuid4().hex[:8]}"),
                            "type": "function",
                            "function": {
                                "name": block["name"],
                                "arguments": json.dumps(block.get("input", {})),
                            },
                        })
                    elif block.get("type") == "text":
                        text_parts.append(block["text"])
                msg_out = {"role": role, "content": "\n".join(text_parts)}
                if tool_calls:
                    msg_out["tool_calls"] = tool_calls
                messages.append(msg_out)

    # Tools
    tools = []
    for tool in body.get("tools", []):
        tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {}),
            },
        })

    model = ollama_model_for(body)
    if model_needs_no_think(model):
        add_no_think(messages)
    user_text = latest_user_text(messages)
    smalltalk = is_smalltalk(user_text)
    if smalltalk:
        messages = [
            {
                "role": "system",
                "content": "You are a concise assistant. Reply naturally in plain text. Do not output JSON and do not use tools.",
            },
            {"role": "user", "content": user_text},
        ]
    else:
        add_local_guardrail(messages)

    out = {
        "model": model,
        "messages": messages,
        "think": False,
        "stream": False,
    }
    if body.get("max_tokens"):
        out["max_tokens"] = body["max_tokens"]
    if tools and not smalltalk:
        out["tools"] = tools
    return out


def openai_to_anthropic(body: dict, model: str, request_body: dict) -> dict:
    """Convert Ollama OpenAI response → Anthropic Messages API response."""
    choice = body.get("choices", [{}])[0]
    message = choice.get("message", {})
    finish = choice.get("finish_reason", "stop")

    content = []
    text = strip_thinking_text(message.get("content") or "")
    user_text = latest_user_text_from_body(request_body)
    tool_use = fake_tool_json_to_anthropic(text, request_body.get("tools", []), user_text)
    if tool_use:
        content.append(tool_use)
        text = ""
        finish = "tool_calls"
    elif is_fake_tool_json(text):
        text = "Hi. How can I help?" if is_smalltalk(user_text) else "I need a concrete path or command before I can use a tool."
    if text:
        content.append({"type": "text", "text": text})

    for tc in message.get("tool_calls", []):
        fn = tc.get("function", {})
        args = fn.get("arguments", "{}")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        content.append({
            "type": "tool_use",
            "id": tc.get("id", f"toolu_{uuid.uuid4().hex[:8]}"),
            "name": fn.get("name", ""),
            "input": args,
        })

    stop_reason_map = {
        "stop": "end_turn",
        "tool_calls": "tool_use",
        "length": "max_tokens",
    }
    stop_reason = stop_reason_map.get(finish, "end_turn")

    usage = body.get("usage", {})
    return {
        "id": f"msg_{uuid.uuid4().hex}",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": content or [{"type": "text", "text": ""}],
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        },
    }


class AnthropicProxy(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path.startswith("/v1/messages"):
            self._handle_messages()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_messages(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length)) if length else {}
        except json.JSONDecodeError as exc:
            self._send_json({"error": f"invalid JSON: {exc}"}, 400)
            return
        model = body.get("model", "")

        direct_result = direct_filesystem_tool(body)
        if direct_result:
            self._send_json(direct_result, 200)
            return

        openai_body = anthropic_to_openai(body)
        data = json.dumps(openai_body).encode()

        req = urllib.request.Request(
            f"{OLLAMA_BASE}/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                raw = json.loads(resp.read())
                # Strip reasoning to avoid confusion
                for c in raw.get("choices", []):
                    c.get("message", {}).pop("reasoning", None)
                result = openai_to_anthropic(raw, model, body)
                status = 200
        except urllib.error.HTTPError as e:
            result = {"error": str(e)}
            status = e.code

        self._send_json(result, status)

    def _send_json(self, result: dict, status: int):
        out = json.dumps(result).encode()
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)
        except BrokenPipeError:
            pass

    def do_GET(self):
        if self.path == "/health":
            out = b'{"status":"ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(out)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    server = ThreadedHTTPServer(("127.0.0.1", 4000), AnthropicProxy)
    print("anthropic-proxy :4000 → Ollama :11434  (think:false, no reasoning blocks)")
    server.serve_forever()
