import json
import importlib.util
import io
from importlib.machinery import SourceFileLoader
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import llm_paths


ROOT = Path(__file__).resolve().parents[1]
LLMCTL_LOADER = SourceFileLoader("llm_cli", str(ROOT / "llm"))
LLMCTL_SPEC = importlib.util.spec_from_loader("llm_cli", LLMCTL_LOADER)
llm_cli = importlib.util.module_from_spec(LLMCTL_SPEC)
assert LLMCTL_SPEC.loader
LLMCTL_SPEC.loader.exec_module(llm_cli)


class TestLLMPaths(unittest.TestCase):
    def test_parameter_default_and_home_expand(self):
        with tempfile.TemporaryDirectory() as home:
            env_file = Path(home) / ".env"
            env_file.write_text('LLM_ROOT="${LLM_ROOT:-$HOME/custom-llm}"\n')
            env = {"HOME": home}
            with patch.dict(os.environ, env, clear=True):
                llm_paths.load_env_file(env_file)
                self.assertEqual(os.environ["LLM_ROOT"], f"{home}/custom-llm")

    def test_individual_path_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "LLM_ROOT": tmp,
                "LLM_MODELS_DIR": f"{tmp}/gguf",
                "HF_HOME": f"{tmp}/hf",
            }
            with patch.dict(os.environ, env, clear=True):
                paths = llm_paths.get_paths()
        self.assertEqual(paths["llm_root"], Path(tmp).resolve())
        self.assertEqual(paths["models"], Path(f"{tmp}/gguf").resolve())
        self.assertEqual(paths["hf_home"], Path(f"{tmp}/hf").resolve())
        self.assertEqual(paths["ollama"], Path(f"{tmp}/ollama").resolve())


class TestLLMCTL(unittest.TestCase):
    def test_paths_json_honors_llm_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["LLM_ROOT"] = tmp
            env["LLM_SKIP_VENV_CHECK"] = "1"
            result = subprocess.run(
                [str(ROOT / "llm"), "paths", "--json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=10,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        paths = json.loads(result.stdout)
        self.assertEqual(paths["llm_root"], str(Path(tmp).resolve()))
        self.assertEqual(paths["models"], str((Path(tmp) / "models").resolve()))

    def test_help_mentions_core_commands(self):
        result = subprocess.run(
            [str(ROOT / "llm"), "--help"],
            capture_output=True,
            text=True,
            env={**os.environ, "LLM_SKIP_VENV_CHECK": "1"},
            timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        for command in (
            "paths",
            "doctor",
            "setup",
            "models",
            "serve",
            "claude",
            "codex",
            "hermes",
            "build",
            "install",
        ):
            self.assertIn(command, result.stdout)

    def test_bare_cli_explains_noninteractive_usage(self):
        result = subprocess.run(
            [str(ROOT / "llm")],
            capture_output=True,
            text=True,
            env={**os.environ, "LLM_SKIP_VENV_CHECK": "1"},
            timeout=10,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("llm --help", result.stdout)

    def test_gguf_model_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            models_dir = Path(tmp)
            (models_dir / "qwen3.5-4b.gguf").write_bytes(b"")
            (models_dir / "ignore.txt").write_text("not a model")
            result = llm_cli._discover_models(
                "llama-cpp",
                {"PATH": os.environ.get("PATH", "")},
                {"models": models_dir},
            )
        self.assertEqual(result, ["qwen3.5-4b"])

    def test_prompt_choice_accepts_number(self):
        with patch.object(llm_cli, "_is_interactive", return_value=True), patch(
            "builtins.input", return_value="2"
        ):
            with unittest.mock.patch("sys.stdout", new_callable=io.StringIO):
                result = llm_cli._prompt_choice(
                    "Choose", [("one", "One"), ("two", "Two")]
                )
        self.assertEqual(result, "two")

    def test_codex_uses_responses_provider_for_native_backend(self):
        command = llm_cli._codex_command(
            "vllm",
            "http://127.0.0.1:8000",
            "local-coder",
            32768,
            ["exec", "test"],
        )
        joined = "\n".join(command)
        self.assertIn('model_providers.local-vllm.base_url="http://127.0.0.1:8000/v1"', joined)
        self.assertIn('model_providers.local-vllm.wire_api="responses"', joined)
        self.assertEqual(command[-2:], ["exec", "test"])

    def test_codex_uses_builtin_ollama_provider(self):
        command = llm_cli._codex_command(
            "ollama", "http://127.0.0.1:11434", "qwen3.5:4b", 32768, []
        )
        self.assertEqual(
            command,
            [
                "ollama",
                "launch",
                "codex",
                "--model",
                "qwen3.5:4b",
                "--",
            ],
        )
        env = llm_cli.codex_environment(
            {"HOME": "/home/test"}, "ollama", "http://127.0.0.1:11434", "local", "qwen"
        )
        self.assertTrue(env["CODEX_HOME"].endswith("/codex-local"))

    def test_hermes_uses_custom_openai_provider(self):
        env = llm_cli.hermes_environment(
            {"PATH": "/usr/bin"}, "llama-cpp", "http://127.0.0.1:8080", "local"
        )
        command = llm_cli._hermes_command(
            "llama-cpp", "http://127.0.0.1:8080", "local-coder", []
        )
        self.assertEqual(env["OPENAI_BASE_URL"], "http://127.0.0.1:8080/v1")
        self.assertEqual(env["OPENAI_API_KEY"], "local")
        self.assertTrue(env["HERMES_HOME"].endswith("/hermes-local"))
        self.assertEqual(
            command,
            [
                "hermes",
                "chat",
                "--provider",
                "custom",
                "--base-url",
                "http://127.0.0.1:8080/v1",
                "--api-key",
                "local",
                "--model",
                "local-coder",
            ],
        )


if __name__ == "__main__":
    unittest.main()
