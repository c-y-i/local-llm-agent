import json
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class _ModelsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/v1/models":
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps({"data": [{"id": "mock-coder"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length", 0))
        request = json.loads(self.rfile.read(length) or b"{}")
        if path == "/v1/messages/count_tokens":
            body = json.dumps({"input_tokens": 1}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path != "/v1/messages":
            self.send_response(404)
            self.end_headers()
            return

        if not request.get("stream"):
            body = json.dumps(
                {
                    "id": "msg_mock",
                    "type": "message",
                    "role": "assistant",
                    "model": "mock-coder",
                    "content": [{"type": "text", "text": "ready"}],
                    "stop_reason": "end_turn",
                    "stop_sequence": None,
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        events = [
            (
                "message_start",
                {
                    "type": "message_start",
                    "message": {
                        "id": "msg_mock",
                        "type": "message",
                        "role": "assistant",
                        "model": "mock-coder",
                        "content": [],
                        "stop_reason": None,
                        "stop_sequence": None,
                        "usage": {"input_tokens": 1, "output_tokens": 0},
                    },
                },
            ),
            (
                "content_block_start",
                {
                    "type": "content_block_start",
                    "index": 0,
                    "content_block": {"type": "text", "text": ""},
                },
            ),
            (
                "content_block_delta",
                {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {"type": "text_delta", "text": "ready"},
                },
            ),
            (
                "content_block_stop",
                {"type": "content_block_stop", "index": 0},
            ),
            (
                "message_delta",
                {
                    "type": "message_delta",
                    "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                    "usage": {"output_tokens": 1},
                },
            ),
            ("message_stop", {"type": "message_stop"}),
        ]
        for event, data in events:
            self.wfile.write(
                f"event: {event}\ndata: {json.dumps(data)}\n\n".encode()
            )
            self.wfile.flush()

    def log_message(self, *_args):
        pass


class TestClaudeLauncher(unittest.TestCase):
    def test_shell_scripts_parse(self):
        scripts = sorted((ROOT / "scripts").rglob("*.sh"))
        self.assertTrue(scripts)
        for script in scripts:
            result = subprocess.run(
                ["bash", "-n", str(script)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, f"{script}: {result.stderr}")

    def test_help_does_not_require_a_backend(self):
        result = subprocess.run(
            [str(ROOT / "scripts/claude/claude-local.sh"), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--backend", result.stdout)

    def test_check_discovers_vllm_model(self):
        server = HTTPServer(("127.0.0.1", 0), _ModelsHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            env = os.environ.copy()
            env.pop("LLM_BACKEND", None)
            env.pop("ANTHROPIC_MODEL", None)
            env["VLLM_BASE_URL"] = f"http://127.0.0.1:{server.server_port}"
            result = subprocess.run(
                [
                    str(ROOT / "scripts/claude/claude-local.sh"),
                    "--backend",
                    "vllm",
                    "--check",
                ],
                capture_output=True,
                text=True,
                env=env,
                timeout=10,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Backend : vllm", result.stderr)
        self.assertIn("Model   : mock-coder", result.stderr)

    def test_rejects_unknown_backend(self):
        result = subprocess.run(
            [
                str(ROOT / "scripts/claude/claude-local.sh"),
                "--backend",
                "not-real",
                "--check",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported backend", result.stderr)

    @unittest.skipUnless(shutil.which("claude"), "Claude Code CLI is not installed")
    def test_claude_code_reaches_mock_backend(self):
        server = HTTPServer(("127.0.0.1", 0), _ModelsHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as home:
                env = os.environ.copy()
                env.update(
                    {
                        "HOME": home,
                        "CLAUDE_BIN": shutil.which("claude"),
                        "VLLM_BASE_URL": f"http://127.0.0.1:{server.server_port}",
                        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
                        "DISABLE_TELEMETRY": "1",
                    }
                )
                result = subprocess.run(
                    [
                        str(ROOT / "scripts/claude/claude-local.sh"),
                        "--backend",
                        "vllm",
                        "--model",
                        "mock-coder",
                        "-p",
                        "Reply with exactly: ready",
                        "--output-format",
                        "text",
                    ],
                    capture_output=True,
                    text=True,
                    env=env,
                    cwd=ROOT,
                    timeout=15,
                )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "ready")


if __name__ == "__main__":
    unittest.main()
