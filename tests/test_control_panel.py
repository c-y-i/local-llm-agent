import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import control_panel


class TestControlsFlag(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_controls_enabled_by_default(self):
        self.assertTrue(control_panel.controls_enabled())

    @patch.dict(os.environ, {"LLM_MONITOR_CONTROLS": "0"})
    def test_controls_disabled_by_env(self):
        self.assertFalse(control_panel.controls_enabled())


class TestPullableModels(unittest.TestCase):
    @patch.dict(os.environ, {"LLM_PULLABLE_MODELS_JSON": '[{"name":"tiny:test","size_gb":0.4,"desc":"test"}]'})
    def test_pullable_models_can_come_from_env_json(self):
        result = control_panel.pullable_models()
        self.assertEqual(result, [{"name": "tiny:test", "size_gb": 0.4, "desc": "test"}])

    @patch.dict(os.environ, {}, clear=True)
    def test_recommendation_prefers_fitting_coder_model(self):
        result = control_panel.get_model_recommendation(
            {"available": True, "vram_total_mib": 6 * 1024},
            {"ram": {"available": True, "total_mib": 32 * 1024}},
            [
                {"name": "general:4b", "size_gb": 2.6, "desc": "general chat"},
                {"name": "coder:3b", "size_gb": 1.9, "desc": "coding"},
                {"name": "coder:7b", "size_gb": 4.7, "desc": "coding"},
            ],
        )
        self.assertEqual(result["model"]["name"], "coder:3b")
        self.assertIn("VRAM", result["tier"])


class TestDashboardTemplate(unittest.TestCase):
    def test_dashboard_uses_app_text(self):
        self.assertIn("<title>Local LLM Control Panel</title>", control_panel.dashboard_html())
        self.assertIn("<h1>Local LLM Control Panel</h1>", control_panel.dashboard_html())


class TestGetServices(unittest.TestCase):
    @patch("control_panel.subprocess.run")
    def test_active_service(self, mock_run):
        mock_run.return_value = MagicMock(stdout="active\n", returncode=0)
        result = control_panel.get_services()
        self.assertEqual(result["ollama"]["status"], "active")

    @patch("control_panel.subprocess.run")
    def test_inactive_service(self, mock_run):
        mock_run.return_value = MagicMock(stdout="inactive\n", returncode=3)
        result = control_panel.get_services()
        self.assertEqual(result["ollama"]["status"], "inactive")

    @patch("control_panel.subprocess.run", side_effect=Exception("timeout"))
    def test_subprocess_error(self, mock_run):
        result = control_panel.get_services()
        self.assertEqual(result["ollama"]["status"], "unknown")


class TestProbePorts(unittest.TestCase):
    @patch("control_panel.socket.create_connection")
    def test_reachable_port(self, mock_conn):
        mock_conn.return_value.__enter__ = MagicMock(return_value=None)
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        result = control_panel.probe_ports()
        self.assertTrue(result["anthropic-proxy"]["reachable"])
        self.assertEqual(result["anthropic-proxy"]["port"], 4000)

    @patch("control_panel.socket.create_connection", side_effect=OSError("refused"))
    def test_unreachable_port(self, mock_conn):
        result = control_panel.probe_ports()
        self.assertFalse(result["anthropic-proxy"]["reachable"])


class TestGetGPU(unittest.TestCase):
    @patch("control_panel.subprocess.run")
    def test_gpu_available(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NVIDIA GeForce GTX 1050 Ti, 3200, 4096, 85, 72\n",
        )
        result = control_panel.get_gpu()
        self.assertTrue(result["available"])
        self.assertEqual(result["vram_used_mib"], 3200)
        self.assertEqual(result["vram_total_mib"], 4096)
        self.assertEqual(result["utilization_pct"], 85)
        self.assertEqual(result["temp_c"], 72)
        self.assertEqual(result["name"], "NVIDIA GeForce GTX 1050 Ti")

    @patch("control_panel.subprocess.run", side_effect=FileNotFoundError)
    def test_nvidia_smi_missing(self, mock_run):
        result = control_panel.get_gpu()
        self.assertFalse(result["available"])

    @patch("control_panel.subprocess.run")
    def test_nvidia_smi_nonzero_exit(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = control_panel.get_gpu()
        self.assertFalse(result["available"])


class TestGetOllama(unittest.TestCase):
    def _make_resp(self, body: bytes):
        r = MagicMock()
        r.__enter__ = MagicMock(return_value=r)
        r.__exit__ = MagicMock(return_value=False)
        r.read.return_value = body
        return r

    @patch("control_panel.urllib.request.urlopen")
    def test_models_and_running(self, mock_open):
        mock_open.side_effect = [
            self._make_resp(
                b'{"models": [{"name": "qwen3:4b", "size": 2600000000}]}'
            ),
            self._make_resp(
                b'{"models": [{"name": "qwen3:4b", "size_vram": 3355443200}]}'
            ),
        ]
        result = control_panel.get_ollama()
        self.assertTrue(result["reachable"])
        self.assertEqual(result["models"][0]["name"], "qwen3:4b")
        self.assertAlmostEqual(result["models"][0]["size_gb"], 2.6, places=0)
        self.assertEqual(result["running"][0]["name"], "qwen3:4b")
        self.assertEqual(result["running"][0]["vram_mib"], 3200)

    @patch("control_panel.urllib.request.urlopen", side_effect=Exception("refused"))
    def test_ollama_unreachable(self, mock_open):
        result = control_panel.get_ollama()
        self.assertFalse(result["reachable"])
        self.assertEqual(result["models"], [])
        self.assertEqual(result["running"], [])

    @patch("control_panel.urllib.request.urlopen")
    def test_tags_ok_ps_fails(self, mock_open):
        # /api/tags succeeds, /api/ps fails → reachable True, running empty
        tags_resp = self._make_resp(
            b'{"models": [{"name": "qwen3:4b", "size": 2600000000}]}'
        )
        mock_open.side_effect = [tags_resp, Exception("timeout")]
        result = control_panel.get_ollama()
        self.assertTrue(result["reachable"])
        self.assertEqual(len(result["models"]), 1)
        self.assertEqual(result["running"], [])


class TestGetSystem(unittest.TestCase):
    MEMINFO = (
        "MemTotal:       16384000 kB\n"
        "MemFree:         4096000 kB\n"
        "MemAvailable:    8192000 kB\n"
        "Buffers:          512000 kB\n"
    )
    # two /proc/stat reads: second has more total/idle ticks → ~25% CPU
    STAT_1 = "cpu  100 0 50 250 10 0 0 0 0 0\n"
    STAT_2 = "cpu  125 0 75 350 15 0 0 0 0 0\n"  # Δtotal=165, Δidle=105 → idle%=63.6 → cpu%=36.4

    @patch("control_panel.time.sleep")
    @patch("builtins.open")
    def test_ram_and_cpu(self, mock_open, mock_sleep):
        mock_open.side_effect = [
            unittest.mock.mock_open(read_data=self.MEMINFO)(),
            unittest.mock.mock_open(read_data=self.STAT_1)(),
            unittest.mock.mock_open(read_data=self.STAT_2)(),
        ]
        result = control_panel.get_system()
        self.assertTrue(result["ram"]["available"])
        self.assertEqual(result["ram"]["total_mib"], 16000)   # 16384000 // 1024
        self.assertEqual(result["ram"]["used_mib"], 8000)     # total - avail = 16000 - 8000
        self.assertTrue(result["cpu"]["available"])
        self.assertGreater(result["cpu"]["pct"], 0)
        self.assertGreater(result["cpu"]["count"], 0)

    @patch("control_panel.time.sleep")
    @patch("builtins.open", side_effect=OSError("no /proc"))
    def test_proc_unavailable(self, mock_open, mock_sleep):
        result = control_panel.get_system()
        self.assertFalse(result["ram"]["available"])
        self.assertFalse(result["cpu"]["available"])


class TestGetSystemCPUModel(unittest.TestCase):
    MEMINFO = "MemTotal: 16384000 kB\nMemAvailable: 8192000 kB\n"
    STAT_1 = "cpu  100 0 50 750 0 0 0 0 0 0\n"
    STAT_2 = "cpu  110 0 55 810 0 0 0 0 0 0\n"
    CPUINFO = "processor\t: 0\nmodel name\t: Intel(R) Core(TM) i7-12700H @ 2.30GHz\nflags\t: fpu\n"

    @patch("control_panel.time.sleep")
    def test_cpu_model_name_parsed(self, mock_sleep):
        with patch("builtins.open", side_effect=[
            unittest.mock.mock_open(read_data=self.MEMINFO)(),
            unittest.mock.mock_open(read_data=self.STAT_1)(),
            unittest.mock.mock_open(read_data=self.STAT_2)(),
            unittest.mock.mock_open(read_data=self.CPUINFO)(),
        ]):
            result = control_panel.get_system()
        self.assertEqual(result["cpu"]["model"], "Intel(R) Core(TM) i7-12700H @ 2.30GHz")

    @patch("control_panel.time.sleep")
    def test_cpu_model_missing_gracefully(self, mock_sleep):
        no_model = "processor\t: 0\nflags\t: fpu\n"
        with patch("builtins.open", side_effect=[
            unittest.mock.mock_open(read_data=self.MEMINFO)(),
            unittest.mock.mock_open(read_data=self.STAT_1)(),
            unittest.mock.mock_open(read_data=self.STAT_2)(),
            unittest.mock.mock_open(read_data=no_model)(),
        ]):
            result = control_panel.get_system()
        self.assertNotIn("model", result["cpu"])


class TestGetStorage(unittest.TestCase):
    @patch("control_panel.shutil.disk_usage")
    @patch("control_panel.os.path.isdir", return_value=False)
    def test_root_filesystem_included(self, mock_isdir, mock_du):
        from collections import namedtuple
        DU = namedtuple("usage", ["total", "used", "free"])
        mock_du.return_value = DU(total=500 * 1024**3, used=200 * 1024**3, free=300 * 1024**3)
        result = control_panel.get_storage()
        self.assertIn("/ (root)", result)
        self.assertTrue(result["/ (root)"]["available"])
        self.assertEqual(result["/ (root)"]["total_bytes"], 500 * 1024**3)
        self.assertEqual(result["/ (root)"]["used_bytes"], 200 * 1024**3)

    @patch("control_panel.shutil.disk_usage")
    @patch("control_panel.os.path.isdir", return_value=True)
    def test_models_dir_included_when_exists(self, mock_isdir, mock_du):
        from collections import namedtuple
        DU = namedtuple("usage", ["total", "used", "free"])
        mock_du.return_value = DU(total=500 * 1024**3, used=40 * 1024**3, free=460 * 1024**3)
        result = control_panel.get_storage()
        self.assertIn("models", result)
        self.assertTrue(result["models"]["available"])

    @patch("control_panel.shutil.disk_usage", side_effect=OSError("no disk"))
    @patch("control_panel.os.path.isdir", return_value=False)
    def test_root_unavailable_on_error(self, mock_isdir, mock_du):
        result = control_panel.get_storage()
        self.assertFalse(result["/ (root)"]["available"])

    def test_build_status_includes_storage(self):
        with patch.multiple(
            "control_panel",
            get_services=lambda: {},
            probe_ports=lambda: {},
            get_gpu=lambda: {"available": False},
            get_system=lambda: {"ram": {"available": False}, "cpu": {"available": False}},
            get_ollama=lambda: {"reachable": False, "models": [], "running": []},
            get_storage=lambda: {"/ (root)": {"available": True, "total_bytes": 1, "used_bytes": 1}},
        ):
            result = control_panel.build_status()
        self.assertIn("storage", result)
        self.assertIn("pullable_models", result)
        self.assertIn("recommendation", result)


class TestRunOllamaPull(unittest.TestCase):
    def test_pull_rejects_non_allowlisted_model(self):
        result = control_panel.run_ollama_action("pull", "evil-model:99b")
        self.assertFalse(result["ok"])
        self.assertIn("allowlist", result["message"])

    @patch("control_panel._known_ollama_models", return_value=None)
    def test_pull_fails_when_ollama_unreachable(self, _):
        result = control_panel.run_ollama_action("pull", "qwen3:4b")
        self.assertFalse(result["ok"])
        self.assertIn("unreachable", result["message"])

    @patch("control_panel.threading.Thread")
    @patch("control_panel._known_ollama_models", return_value={"some:model"})
    def test_pull_starts_thread_and_returns_ok_immediately(self, _, mock_thread):
        mock_instance = MagicMock()
        mock_thread.return_value = mock_instance
        result = control_panel.run_ollama_action("pull", "qwen3:4b")
        self.assertTrue(result["ok"])
        self.assertIn("pulling", result["message"])
        mock_instance.start.assert_called_once()

    @patch("control_panel.threading.Thread")
    @patch("control_panel._known_ollama_models", return_value=set())
    def test_pull_thread_is_daemon(self, _, mock_thread):
        mock_instance = MagicMock()
        mock_thread.return_value = mock_instance
        control_panel.run_ollama_action("pull", "llama3.2:1b")
        _, kwargs = mock_thread.call_args
        self.assertTrue(kwargs.get("daemon", False))


class TestControlActions(unittest.TestCase):
    @patch("control_panel.subprocess.run")
    def test_run_service_action_allowlisted(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = control_panel.run_service_action("ollama", "restart")
        self.assertTrue(result["ok"])
        mock_run.assert_called_once_with(
            ["systemctl", "restart", "ollama"],
            capture_output=True, text=True, timeout=20,
        )

    def test_run_service_action_rejects_unknown_service(self):
        result = control_panel.run_service_action("ssh", "restart")
        self.assertFalse(result["ok"])
        self.assertIn("unsupported service", result["message"])

    def test_run_service_action_rejects_unknown_action(self):
        result = control_panel.run_service_action("ollama", "enable")
        self.assertFalse(result["ok"])
        self.assertIn("unsupported service action", result["message"])

    @patch("control_panel.get_ollama")
    @patch("control_panel._ollama_post")
    def test_run_ollama_warmup(self, mock_post, mock_get_ollama):
        mock_get_ollama.return_value = {
            "reachable": True,
            "models": [{"name": "qwen3:4b"}],
        }
        result = control_panel.run_ollama_action("warmup", "qwen3:4b")
        self.assertTrue(result["ok"])
        mock_post.assert_called_once_with(
            "/api/generate",
            {"model": "qwen3:4b", "stream": False, "prompt": ".", "keep_alive": "10m"},
        )

    @patch("control_panel.get_ollama")
    @patch("control_panel._ollama_post")
    def test_run_ollama_unload(self, mock_post, mock_get_ollama):
        mock_get_ollama.return_value = {
            "reachable": True,
            "models": [{"name": "qwen3:4b"}],
        }
        result = control_panel.run_ollama_action("unload", "qwen3:4b")
        self.assertTrue(result["ok"])
        mock_post.assert_called_once_with(
            "/api/generate",
            {"model": "qwen3:4b", "stream": False, "prompt": "", "keep_alive": 0},
        )

    @patch("control_panel.get_ollama")
    def test_run_ollama_rejects_unknown_model(self, mock_get_ollama):
        mock_get_ollama.return_value = {
            "reachable": True,
            "models": [{"name": "qwen3:4b"}],
        }
        result = control_panel.run_ollama_action("warmup", "missing")
        self.assertFalse(result["ok"])
        self.assertIn("unknown Ollama model", result["message"])


if __name__ == "__main__":
    unittest.main()
