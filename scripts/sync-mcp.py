#!/usr/bin/env python3
"""Copy the MCP servers in mcp.json into each agent's project config.

Claude Code reads .mcp.json, Cursor .cursor/mcp.json, Gemini CLI the mcpServers key of
.gemini/settings.json, Codex .codex/config.toml (trusted projects only). Edit mcp.json, then run
this. --check exits 1 if a generated file is stale; CI runs it.

Secrets stay out of mcp.json: write env values as "${NAME}" and each person exports NAME.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = re.compile(r"^[A-Za-z0-9_-]+$")  # also a valid bare TOML key
VAR = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def cursor(servers):
    # Cursor spells env interpolation ${env:NAME}.
    text = VAR.sub(r"${env:\1}", json.dumps({"mcpServers": servers}, indent=2))
    return text + "\n"


def gemini(servers, current):
    settings = dict(current)
    settings.setdefault("context", {"fileName": ["AGENTS.md"]})
    settings["mcpServers"] = servers
    return json.dumps(settings, indent=2) + "\n"


def codex(servers):
    q = json.dumps  # a JSON string is a valid TOML basic string
    lines = ["# Generated from mcp.json by scripts/sync-mcp.py; edit mcp.json instead."]
    for name, s in servers.items():
        lines += ["", f"[mcp_servers.{name}]"]
        if "url" in s:
            lines.append(f"url = {q(s['url'])}")
        else:
            lines.append(f"command = {q(s['command'])}")
            if s.get("args"):
                lines.append(f"args = [{', '.join(q(a) for a in s['args'])}]")
        # Codex has no ${NAME} expansion; it forwards named variables from the shell instead.
        names = sorted({m for v in s.get("env", {}).values() for m in VAR.findall(str(v))})
        if names:
            lines.append(f"env_vars = [{', '.join(q(n) for n in names)}]")
    return "\n".join(lines) + "\n"


def render(servers, gemini_current):
    for name, s in servers.items():
        if not NAME.match(name):
            raise SystemExit(f"mcp.json: server name {name!r} must match {NAME.pattern}")
        if ("url" in s) == ("command" in s):
            raise SystemExit(f"mcp.json: server {name!r} needs exactly one of url or command")
    claude = json.dumps({"mcpServers": servers}, indent=2) + "\n"
    return {
        ".mcp.json": claude,
        ".cursor/mcp.json": cursor(servers),
        ".gemini/settings.json": gemini(servers, gemini_current),
        ".codex/config.toml": codex(servers),
    }


def main(argv):
    check = "--check" in argv
    servers = json.loads((ROOT / "mcp.json").read_text()).get("mcpServers", {})
    gem = ROOT / ".gemini/settings.json"
    current = json.loads(gem.read_text()) if gem.exists() else {}
    stale = []
    for rel, text in render(servers, current).items():
        path = ROOT / rel
        if path.exists() and path.read_text() == text:
            continue
        stale.append(rel)
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    if check and stale:
        print("stale, run scripts/sync-mcp.py:", ", ".join(stale), file=sys.stderr)
        return 1
    if not check:
        print("wrote " + ", ".join(stale) if stale else "up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
