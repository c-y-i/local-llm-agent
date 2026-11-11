import importlib.util
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOADER = SourceFileLoader(
    "anthropic_proxy", str(ROOT / "scripts/ollama/anthropic-proxy.py")
)
SPEC = importlib.util.spec_from_loader("anthropic_proxy", LOADER)
proxy = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(proxy)


class TestAnthropicProxy(unittest.TestCase):
    def test_normalizes_all_system_messages_to_leading_block(self):
        messages = [
            {"role": "user", "content": "first"},
            {"role": "system", "content": "system A"},
            {"role": "assistant", "content": "answer"},
            {"role": "system", "content": "system B"},
        ]
        result = proxy.normalize_system_messages(messages)
        self.assertEqual(result[0]["role"], "system")
        self.assertIn("system A", result[0]["content"])
        self.assertIn("system B", result[0]["content"])
        self.assertNotIn("system", [m["role"] for m in result[1:]])

    def test_guardrail_merges_into_existing_system_message(self):
        messages = [{"role": "system", "content": "original"}]
        proxy.add_local_guardrail(messages)
        self.assertEqual(len(messages), 1)
        self.assertIn("original", messages[0]["content"])
        self.assertIn(proxy.LOCAL_GUARDRAIL, messages[0]["content"])


if __name__ == "__main__":
    unittest.main()
