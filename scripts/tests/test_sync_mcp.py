import importlib.util
import json
import tomllib
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "sync_mcp", Path(__file__).resolve().parent.parent / "sync-mcp.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

SERVERS = {
    "docs": {"command": "npx", "args": ["-y", "some-mcp@1.2.3"], "env": {"API_KEY": "${API_KEY}"}},
    "remote": {"type": "http", "url": "https://example.com/mcp"},
}


class Render(unittest.TestCase):
    def setUp(self):
        self.out = sync.render(SERVERS, {})

    def test_claude_file_is_the_source(self):
        self.assertEqual(json.loads(self.out[".mcp.json"]), {"mcpServers": SERVERS})

    def test_cursor_uses_env_prefix(self):
        env = json.loads(self.out[".cursor/mcp.json"])["mcpServers"]["docs"]["env"]
        self.assertEqual(env, {"API_KEY": "${env:API_KEY}"})

    def test_codex_toml_parses_and_forwards_vars(self):
        cfg = tomllib.loads(self.out[".codex/config.toml"])["mcp_servers"]
        self.assertEqual(cfg["docs"]["args"], ["-y", "some-mcp@1.2.3"])
        self.assertEqual(cfg["docs"]["env_vars"], ["API_KEY"])
        self.assertEqual(cfg["remote"], {"url": "https://example.com/mcp"})

    def test_gemini_keeps_existing_settings(self):
        out = sync.render(SERVERS, {"context": {"fileName": ["X.md"]}, "theme": "dark"})
        gem = json.loads(out[".gemini/settings.json"])
        self.assertEqual(gem["context"], {"fileName": ["X.md"]})
        self.assertEqual(gem["theme"], "dark")
        self.assertEqual(gem["mcpServers"], SERVERS)

    def test_gemini_defaults_to_agents_md(self):
        gem = json.loads(self.out[".gemini/settings.json"])
        self.assertEqual(gem["context"], {"fileName": ["AGENTS.md"]})

    def test_rejects_bad_name(self):
        with self.assertRaises(SystemExit):
            sync.render({"a b": {"command": "x"}}, {})

    def test_rejects_url_and_command_together(self):
        with self.assertRaises(SystemExit):
            sync.render({"x": {"command": "x", "url": "https://e"}}, {})

    def test_empty_config(self):
        out = sync.render({}, {})
        self.assertEqual(tomllib.loads(out[".codex/config.toml"]), {})


if __name__ == "__main__":
    unittest.main()
