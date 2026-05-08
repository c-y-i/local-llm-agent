import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import monitor


class TestGetServices(unittest.TestCase):
    @patch("monitor.subprocess.run")
    def test_active_service(self, mock_run):
        mock_run.return_value = MagicMock(stdout="active\n", returncode=0)
        result = monitor.get_services()
        self.assertEqual(result["ollama"]["status"], "active")

    @patch("monitor.subprocess.run")
    def test_inactive_service(self, mock_run):
        mock_run.return_value = MagicMock(stdout="inactive\n", returncode=3)
        result = monitor.get_services()
        self.assertEqual(result["ollama"]["status"], "inactive")

    @patch("monitor.subprocess.run", side_effect=Exception("timeout"))
    def test_subprocess_error(self, mock_run):
        result = monitor.get_services()
        self.assertEqual(result["ollama"]["status"], "unknown")


class TestProbePorts(unittest.TestCase):
    @patch("monitor.socket.create_connection")
    def test_reachable_port(self, mock_conn):
        mock_conn.return_value.__enter__ = MagicMock(return_value=None)
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        result = monitor.probe_ports()
        self.assertTrue(result["anthropic-proxy"]["reachable"])
        self.assertEqual(result["anthropic-proxy"]["port"], 4000)

    @patch("monitor.socket.create_connection", side_effect=OSError("refused"))
    def test_unreachable_port(self, mock_conn):
        result = monitor.probe_ports()
        self.assertFalse(result["anthropic-proxy"]["reachable"])


class TestGetGPU(unittest.TestCase):
    @patch("monitor.subprocess.run")
    def test_gpu_available(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NVIDIA GeForce GTX 1050 Ti, 3200, 4096, 85, 72\n",
        )
        result = monitor.get_gpu()
        self.assertTrue(result["available"])
        self.assertEqual(result["vram_used_mib"], 3200)
        self.assertEqual(result["vram_total_mib"], 4096)
        self.assertEqual(result["utilization_pct"], 85)
        self.assertEqual(result["temp_c"], 72)
        self.assertEqual(result["name"], "NVIDIA GeForce GTX 1050 Ti")

    @patch("monitor.subprocess.run", side_effect=FileNotFoundError)
    def test_nvidia_smi_missing(self, mock_run):
        result = monitor.get_gpu()
        self.assertFalse(result["available"])

    @patch("monitor.subprocess.run")
    def test_nvidia_smi_nonzero_exit(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = monitor.get_gpu()
        self.assertFalse(result["available"])


class TestGetOllama(unittest.TestCase):
    def _make_resp(self, body: bytes):
        r = MagicMock()
        r.__enter__ = MagicMock(return_value=r)
        r.__exit__ = MagicMock(return_value=False)
        r.read.return_value = body
        return r

    @patch("monitor.urllib.request.urlopen")
    def test_models_and_running(self, mock_open):
        mock_open.side_effect = [
            self._make_resp(
                b'{"models": [{"name": "qwen3:4b", "size": 2600000000}]}'
            ),
            self._make_resp(
                b'{"models": [{"name": "qwen3:4b", "size_vram": 3355443200}]}'
            ),
        ]
        result = monitor.get_ollama()
        self.assertTrue(result["reachable"])
        self.assertEqual(result["models"][0]["name"], "qwen3:4b")
        self.assertAlmostEqual(result["models"][0]["size_gb"], 2.6, places=0)
        self.assertEqual(result["running"][0]["name"], "qwen3:4b")
        self.assertEqual(result["running"][0]["vram_mib"], 3200)

    @patch("monitor.urllib.request.urlopen", side_effect=Exception("refused"))
    def test_ollama_unreachable(self, mock_open):
        result = monitor.get_ollama()
        self.assertFalse(result["reachable"])
        self.assertEqual(result["models"], [])
        self.assertEqual(result["running"], [])

    @patch("monitor.urllib.request.urlopen")
    def test_tags_ok_ps_fails(self, mock_open):
        # /api/tags succeeds, /api/ps fails → reachable True, running empty
        tags_resp = self._make_resp(
            b'{"models": [{"name": "qwen3:4b", "size": 2600000000}]}'
        )
        mock_open.side_effect = [tags_resp, Exception("timeout")]
        result = monitor.get_ollama()
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

    @patch("monitor.time.sleep")
    @patch("builtins.open")
    def test_ram_and_cpu(self, mock_open, mock_sleep):
        mock_open.side_effect = [
            unittest.mock.mock_open(read_data=self.MEMINFO)(),
            unittest.mock.mock_open(read_data=self.STAT_1)(),
            unittest.mock.mock_open(read_data=self.STAT_2)(),
        ]
        result = monitor.get_system()
        self.assertTrue(result["ram"]["available"])
        self.assertEqual(result["ram"]["total_mib"], 16000)   # 16384000 // 1024
        self.assertEqual(result["ram"]["used_mib"], 8000)     # total - avail = 16000 - 8000
        self.assertTrue(result["cpu"]["available"])
        self.assertGreater(result["cpu"]["pct"], 0)
        self.assertGreater(result["cpu"]["count"], 0)

    @patch("monitor.time.sleep")
    @patch("builtins.open", side_effect=OSError("no /proc"))
    def test_proc_unavailable(self, mock_open, mock_sleep):
        result = monitor.get_system()
        self.assertFalse(result["ram"]["available"])
        self.assertFalse(result["cpu"]["available"])


if __name__ == "__main__":
    unittest.main()
