import json
import importlib.util
import io
from importlib.machinery import SourceFileLoader
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
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

    def test_docs_links_exist_and_test_agents_are_named(self):
        documents = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
        missing = []
        for document in documents:
            text = document.read_text()
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "#")):
                    continue
                path = (document.parent / target.split("#", 1)[0]).resolve()
                if not path.exists():
                    missing.append(f"{document.relative_to(ROOT)} -> {target}")
        self.assertEqual(missing, [])

        readme = (ROOT / "README.md").read_text()
        self.assertIn("Claude Code", readme)
        self.assertIn("Codex CLI", readme)
        self.assertIn("Hermes Agent", readme)
        self.assertIn("Tested", readme)

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

    def test_local_agent_wrappers_activate_managed_venv(self):
        script = (ROOT / "scripts/agents/launch-local.sh").read_text()
        self.assertIn('VENV_ACTIVATE="${REPO_ROOT}/.venv/bin/activate"', script)
        self.assertIn('source "$VENV_ACTIVATE"', script)

    def test_installer_prints_guided_next_steps(self):
        script = (ROOT / "scripts/setup/install-llm.sh").read_text()
        self.assertIn("Next steps:", script)
        self.assertIn("check-prereqs.sh", script)
        self.assertIn("llm setup", script)

    def test_agent_model_bootstrap_prefers_llama_cpp(self):
        llama_models = ["qwen3.5-4b-official-Q4_K_M"]
        with patch.object(
            llm_cli, "_discover_models", return_value=llama_models
        ), patch.object(
            llm_cli, "_background_llama_model", return_value=True
        ) as start:
            result = llm_cli._ensure_agent_model(
                {}, {"models": Path("/models"), "run": Path("/run")}
            )
        self.assertTrue(result)
        start.assert_called_once()

    def test_background_agent_model_uses_model_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = {
                "run": Path(tmp),
                "models": Path("/models"),
            }
            process = unittest.mock.Mock(pid=1234)
            process.poll.return_value = None
            response = unittest.mock.MagicMock()
            response.status = 200
            response.__enter__.return_value = response
            with patch.object(
                llm_cli.subprocess, "Popen", return_value=process
            ) as popen, patch.object(
                llm_cli.urllib.request, "urlopen", return_value=response
            ), patch.object(
                llm_cli,
                "_backend_status",
                return_value={
                    "llama-cpp": {"reachable": False},
                    "ollama": {"reachable": False},
                },
            ), unittest.mock.patch("sys.stdout", new_callable=io.StringIO):
                result = llm_cli._background_llama_model(
                    {"LLAMA_CPP_BASE_URL": "http://127.0.0.1:8080"},
                    paths,
                    "qwen3.5-4b-official-Q4_K_M",
                )
            self.assertTrue(result)
            env = popen.call_args.kwargs["env"]
            self.assertEqual(env["N_CTX"], "65536")
            self.assertEqual(
                (paths["run"] / "llama-server.pid").read_text(), "1234\n"
            )

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

    @patch.object(llm_cli, "_backend_status")
    @patch.object(llm_cli, "_ollama_loaded_models", return_value=[])
    def test_idle_ollama_is_not_an_active_model(
        self, _mock_loaded, mock_status
    ):
        mock_status.return_value = {
            "llama-cpp": {
                "url": "http://127.0.0.1:8080",
                "reachable": False,
                "models": [],
            },
            "ollama": {
                "url": "http://127.0.0.1:11434",
                "reachable": True,
                "models": ["qwen3.5-2b-official:latest"],
            },
        }
        result = llm_cli._active_models({})
        self.assertEqual(result, {})

    @patch.object(llm_cli, "_backend_status")
    def test_llama_cpp_served_model_is_active(self, mock_status):
        mock_status.return_value = {
            "llama-cpp": {
                "url": "http://127.0.0.1:8080",
                "reachable": True,
                "models": ["qwen3.5-2b-official-Q4_K_M"],
            }
        }
        result = llm_cli._active_models({})
        self.assertEqual(
            result, {"llama-cpp": ["qwen3.5-2b-official-Q4_K_M"]}
        )

    @patch.object(
        llm_cli,
        "_active_models",
        return_value={"ollama": ["huihui_ai/qwen3.5-abliterated:2b"]},
    )
    @patch.object(llm_cli, "_backend_status")
    @patch.object(llm_cli, "_launch_hermes", return_value=0)
    @patch.object(llm_cli, "_prompt_choice")
    def test_agent_uses_loaded_ollama_model_without_prompt(
        self, mock_prompt, mock_launch, mock_status, _mock_active
    ):
        mock_status.return_value = {
            "ollama": {
                "url": "http://127.0.0.1:11434",
                "reachable": True,
                "models": ["installed-a", "installed-b"],
            }
        }
        with patch.object(llm_cli, "_configured_env", return_value={}):
            result = llm_cli.cmd_agent(
                SimpleNamespace(
                    agent="hermes",
                    backend=None,
                    model=None,
                    agent_args=[],
                )
            )
        self.assertEqual(result, 0)
        mock_prompt.assert_not_called()
        mock_launch.assert_called_once()
        self.assertEqual(
            mock_launch.call_args.args[:3],
            (
                {},
                "ollama",
                "huihui_ai/qwen3.5-abliterated:2b",
            ),
        )

    def test_models_can_be_ordered_smallest_first(self):
        models = ["small", "large", "medium"]
        sizes = {"small": 1_000, "medium": 2_000, "large": 3_000}
        self.assertEqual(
            llm_cli._ordered_models(models, sizes, "size"),
            ["small", "medium", "large"],
        )

    def test_models_sort_by_size_by_default(self):
        args = llm_cli.build_parser().parse_args(["models"])
        self.assertEqual(args.sort, "size")

    def test_logs_command_selects_backend_and_follows(self):
        args = llm_cli.build_parser().parse_args(
            ["logs", "--backend", "ollama", "--lines", "25", "--follow"]
        )
        self.assertEqual(args.backend, "ollama")
        self.assertEqual(args.lines, 25)
        self.assertTrue(args.follow)

    def test_managed_ollama_uses_external_model_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = {
                "run": Path(tmp),
                "ollama_models": Path(tmp) / "models",
            }
            paths["ollama_models"].mkdir()
            process = unittest.mock.Mock(pid=4321)
            process.poll.return_value = None
            response = unittest.mock.MagicMock()
            response.__enter__.return_value = response
            with patch.object(
                llm_cli.subprocess, "Popen", return_value=process
            ) as popen, patch.object(
                llm_cli.urllib.request, "urlopen", return_value=response
            ), patch.object(
                llm_cli,
                "_backend_status",
                return_value={
                    "llama-cpp": {"reachable": False},
                    "ollama": {"reachable": False},
                },
            ), unittest.mock.patch("sys.stdout", new_callable=io.StringIO):
                result = llm_cli._start_managed_ollama({}, paths)
            self.assertTrue(result)
            env = popen.call_args.kwargs["env"]
            self.assertEqual(
                env["OLLAMA_MODELS"], str(paths["ollama_models"])
            )
            self.assertTrue(popen.call_args.kwargs["start_new_session"])

    def test_starting_ollama_stops_llama_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = {
                "run": Path(tmp),
                "ollama_models": Path(tmp) / "models",
            }
            process = unittest.mock.Mock(pid=4321)
            process.poll.return_value = None
            response = unittest.mock.MagicMock()
            response.__enter__.return_value = response
            with patch.object(
                llm_cli,
                "_backend_status",
                return_value={
                    "llama-cpp": {"reachable": True},
                    "ollama": {"reachable": False},
                },
            ), patch.object(
                llm_cli,
                "_stop_tracked_llama",
                return_value=(True, "stopped llama.cpp"),
            ) as stop_llama, patch.object(
                llm_cli.subprocess, "Popen", return_value=process
            ), patch.object(
                llm_cli.urllib.request, "urlopen", return_value=response
            ), unittest.mock.patch("sys.stdout", new_callable=io.StringIO):
                result = llm_cli._start_managed_ollama({}, paths)
            self.assertTrue(result)
            stop_llama.assert_called_once_with(paths)

    @patch.object(llm_cli, "_is_interactive", return_value=True)
    @patch.object(llm_cli, "_prompt_choice", return_value="qwen3.5-4b")
    @patch.object(llm_cli, "_discover_models")
    @patch.object(llm_cli, "_model_sizes")
    def test_model_picker_sorts_by_size_and_defaults_to_qwen_4b(
        self, mock_sizes, mock_models, mock_prompt, _mock_interactive
    ):
        mock_models.return_value = ["qwen3.5-4b", "qwen3.5-2b", "large"]
        mock_sizes.return_value = {
            "qwen3.5-4b": 2_000,
            "qwen3.5-2b": 1_000,
            "large": 3_000,
        }
        llm_cli._choose_model("llama-cpp", {}, {"models": Path("/models")}, None)
        choices = mock_prompt.call_args.args[1]
        self.assertEqual(
            [value for value, _label in choices],
            ["qwen3.5-2b", "qwen3.5-4b", "large"],
        )
        self.assertEqual(mock_prompt.call_args.kwargs["default"], 2)

    def test_llama_profiles_balance_context_and_hybrid_memory(self):
        self.assertEqual(
            llm_cli._llama_profile(
                "huihui-qwen3.5-2b-abliterated-f16"
            ),
            {"context": 32768, "gpu_layers": 999},
        )
        self.assertEqual(
            llm_cli._llama_profile("qwen3.5-2b-official-Q4_K_M"),
            {"context": 131072, "gpu_layers": 999},
        )
        self.assertEqual(
            llm_cli._llama_profile("qwen3.5-4b-official-Q4_K_M"),
            {"context": 65536, "gpu_layers": 999},
        )
        self.assertEqual(
            llm_cli._llama_profile("gemma4-e4b-official-QAT-Q4_0"),
            {"context": 32768, "gpu_layers": 30},
        )
        self.assertEqual(
            llm_cli._llama_profile("qwen3.5-9b-defiant-IQ3_M"),
            {"context": 32768, "gpu_layers": 24},
        )

    def test_context_menu_offers_256k_for_qwen_2b(self):
        with patch.object(llm_cli, "_is_interactive", return_value=True), patch(
            "builtins.input", return_value="4"
        ), unittest.mock.patch("sys.stdout", new_callable=io.StringIO) as output:
            result = llm_cli._choose_context_window(
                "qwen3.5-2b-official-Q4_K_M", 131072
            )
        self.assertEqual(result, 262144)
        self.assertIn("128K tokens (default)", output.getvalue())
        self.assertIn("256K tokens", output.getvalue())

    def test_ollama_context_profiles(self):
        self.assertEqual(
            llm_cli._ollama_context_profile(
                "qwen3.5-2b-official:latest"
            )[1],
            65536,
        )
        self.assertEqual(
            llm_cli._ollama_context_profile(
                "huihui_ai/qwen3.5-abliterated:2b-agent"
            )[1],
            32768,
        )

    @patch.object(llm_cli.urllib.request, "urlopen")
    def test_ollama_warmup_passes_selected_context(self, mock_open):
        response = mock_open.return_value.__enter__.return_value
        result = llm_cli._warm_ollama_model(
            {"OLLAMA_BASE_URL": "http://127.0.0.1:11434"},
            "qwen3.5-2b-official:latest",
            131072,
        )
        self.assertEqual(result, 0)
        request = mock_open.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload["options"]["num_ctx"], 131072)

    def test_f16_context_menu_offers_128k_and_256k(self):
        self.assertEqual(
            llm_cli._context_choices(
                "huihui-qwen3.5-2b-abliterated-f16"
            ),
            (16384, 32768, 65536, 131072, 262144),
        )

    def test_explicit_context_and_env_skip_context_menu(self):
        self.assertEqual(
            llm_cli._resolve_llama_context("qwen3.5-2b", 32768, {}),
            32768,
        )
        self.assertEqual(
            llm_cli._resolve_llama_context(
                "qwen3.5-2b", None, {"N_CTX": "65536"}
            ),
            65536,
        )

    def test_known_models_are_ordered_for_daily_coding(self):
        models = [
            "gemma4-e4b-official",
            "qwen3.5-9b-defiant",
            "qwen3.5-2b-official",
            "qwen3.5-4b-official",
        ]
        self.assertEqual(
            sorted(models, key=llm_cli._llama_model_sort_key),
            [
                "qwen3.5-4b-official",
                "qwen3.5-2b-official",
                "qwen3.5-9b-defiant",
                "gemma4-e4b-official",
            ],
        )

    def test_prompt_choice_accepts_number(self):
        with patch.object(llm_cli, "_is_interactive", return_value=True), patch(
            "builtins.input", return_value="2"
        ):
            with unittest.mock.patch("sys.stdout", new_callable=io.StringIO):
                result = llm_cli._prompt_choice(
                    "Choose", [("one", "One"), ("two", "Two")]
                )
        self.assertEqual(result, "two")

    @patch.object(llm_cli.subprocess, "run")
    def test_run_preserves_callers_working_directory(self, mock_run):
        mock_run.return_value.returncode = 0
        previous = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                with patch("sys.stderr", new_callable=io.StringIO):
                    llm_cli._run(["true"])
            finally:
                os.chdir(previous)
        self.assertEqual(mock_run.call_args.kwargs["cwd"], Path(tmp))

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

    @patch.object(llm_cli.urllib.request, "urlopen")
    def test_reads_context_window_from_llama_server(self, mock_open):
        response = mock_open.return_value.__enter__.return_value
        response.read.return_value = b'{"data":[{"meta":{"n_ctx":65536}}]}'
        result = llm_cli._served_context_window(
            {"LLAMA_CPP_BASE_URL": "http://127.0.0.1:8080"}, "llama-cpp"
        )
        self.assertEqual(result, 65536)

    @patch.object(llm_cli.urllib.request, "urlopen")
    def test_reads_context_window_from_ollama(self, mock_open):
        response = mock_open.return_value.__enter__.return_value
        response.read.return_value = b'{"models":[{"context_length":32768}]}'
        result = llm_cli._served_context_window(
            {"OLLAMA_BASE_URL": "http://127.0.0.1:11434"}, "ollama"
        )
        self.assertEqual(result, 32768)

    def test_hermes_context_pins_read_only_model_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.yaml"
            config.write_text(
                "model:\n"
                "  provider: custom\n"
                "  context_length: 65536\n"
                "  ollama_num_ctx: 32768\n"
                "other:\n"
                "  ollama_num_ctx: 16384\n"
            )
            result = llm_cli._hermes_context_pins(config)
        self.assertEqual(
            result, {"context_length": 65536, "ollama_num_ctx": 32768}
        )

    @patch.object(llm_cli, "_served_context_window", return_value=131072)
    def test_hermes_context_conflict_detects_stale_pin(self, _mock_served):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "config.yaml").write_text(
                "model:\n  context_length: 65536\n"
            )
            result = llm_cli._hermes_context_conflict(
                {"HERMES_HOME": tmp}, "llama-cpp"
            )
        self.assertEqual(result, ("context_length", 65536, 131072))

    @patch.object(llm_cli, "_served_context_window", return_value=262144)
    def test_hermes_detects_stale_ollama_num_ctx(self, _mock_served):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "config.yaml").write_text(
                "model:\n  ollama_num_ctx: 65536\n"
            )
            result = llm_cli._hermes_context_conflict(
                {"HERMES_HOME": tmp}, "llama-cpp"
            )
        self.assertEqual(result, ("ollama_num_ctx", 65536, 262144))

    @patch.object(llm_cli, "_served_context_window", return_value=131072)
    def test_hermes_context_pin_uses_live_window_when_absent(self, _mock_served):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "config.yaml").write_text(
                "model:\n  provider: custom\n"
            )
            result = llm_cli._hermes_context_conflict(
                {"HERMES_HOME": tmp}, "llama-cpp"
            )
        self.assertIsNone(result)

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
