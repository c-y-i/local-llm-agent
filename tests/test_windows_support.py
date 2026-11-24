import importlib.util
import io
import os
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch

import llm_paths


ROOT = Path(__file__).resolve().parents[1]
LOADER = SourceFileLoader("llm_cli_windows", str(ROOT / "llm"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
llm_cli = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(llm_cli)


class TestWindowsSupport(unittest.TestCase):
    def test_windows_launchers_and_scripts_exist(self):
        for relative in (
            "llm.cmd",
            "claude-local.cmd",
            "codex-local.cmd",
            "hermes-local.cmd",
            "scripts/common/env.ps1",
            "scripts/setup/install-llm.ps1",
            "scripts/setup/check-prereqs.ps1",
            "scripts/setup/build-llama-cpp.ps1",
            "scripts/setup/install-ollama.ps1",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_windows_wrappers_use_managed_python(self):
        llm_wrapper = (ROOT / "llm.cmd").read_text()
        self.assertIn(r".venv\Scripts\python.exe", llm_wrapper)
        self.assertIn('"%~dp0llm" %*', llm_wrapper)
        for agent in ("claude", "codex", "hermes"):
            wrapper = (ROOT / f"{agent}-local.cmd").read_text()
            self.assertIn(f"agent {agent}", wrapper)

    def test_windows_scripts_do_not_hardcode_linux_home(self):
        for path in (ROOT / "scripts").rglob("*.ps1"):
            self.assertNotIn("/home/cy", path.read_text())

    def test_llama_server_command_supports_unified_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / "llama"
            binary.write_text("")
            models = root / "models"
            models.mkdir()
            (models / "qwen3.5-4b-test.gguf").write_text("")
            env = {
                "LLAMA_SERVER_BIN": str(binary),
                "N_CTX": "32768",
                "N_GPU_LAYERS": "999",
            }
            command = llm_cli._llama_server_command(
                env,
                {"models": models, "llama_cpp": root},
                "qwen3.5-4b-test",
            )
        self.assertEqual(command[0], str(binary))
        self.assertEqual(command[1], "serve")
        self.assertIn("--chat-template", command)
        self.assertIn("chatml", command)

    def test_sampling_temperature_ignores_windows_temp_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / "llama-server"
            binary.write_text("")
            models = root / "models"
            models.mkdir()
            (models / "qwen3.5-4b-test.gguf").write_text("")
            env = {
                "LLAMA_SERVER_BIN": str(binary),
                "TEMP": r"C:\Users\test\AppData\Local\Temp",
            }
            command = llm_cli._llama_server_command(
                env,
                {"models": models, "llama_cpp": root},
                "qwen3.5-4b-test",
            )
            env["TEMPERATURE"] = "0.35"
            overridden = llm_cli._llama_server_command(
                env,
                {"models": models, "llama_cpp": root},
                "qwen3.5-4b-test",
            )

        temperature_index = command.index("--temp")
        self.assertEqual(command[temperature_index + 1], "0.2")
        overridden_index = overridden.index("--temp")
        self.assertEqual(overridden[overridden_index + 1], "0.35")

    def test_windows_cmd_execution_is_normalized(self):
        with patch.object(llm_cli, "_is_windows", return_value=True), patch.object(
            llm_cli.shutil,
            "which",
            return_value=r"C:\Users\test\claude.cmd",
        ):
            command = llm_cli._normalized_command(
                ["claude", "--version"], {"COMSPEC": r"C:\Windows\cmd.exe"}
            )
        self.assertEqual(command[:5], [
            r"C:\Windows\cmd.exe",
            "/d",
            "/s",
            "/c",
            r'"C:\Users\test\claude.cmd"',
        ])
        self.assertEqual(command[-1], "--version")

    def test_foreground_server_tracks_and_clears_pid(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            process = unittest.mock.Mock(pid=4321)
            process.wait.return_value = 0
            with patch.object(
                llm_cli.subprocess, "Popen", return_value=process
            ), patch("sys.stderr", new_callable=io.StringIO):
                result = llm_cli._run_foreground_llama(
                    ["llama-server"], {}, {"run": run_dir}
                )
            self.assertEqual(result, 0)
            self.assertFalse((run_dir / "llama-server.pid").exists())

    def test_percent_style_env_expansion(self):
        with patch.dict(os.environ, {"LLM_TEST_ROOT": "/tmp/windows-root"}, clear=False):
            self.assertEqual(
                llm_paths._expand("%LLM_TEST_ROOT%/models"),
                "/tmp/windows-root/models",
            )
            self.assertEqual(
                llm_paths._expand("$LLM_TEST_ROOT/models"),
                "/tmp/windows-root/models",
            )


if __name__ == "__main__":
    unittest.main()
