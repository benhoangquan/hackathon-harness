# Hackathon Harness Rules

This repo is coordinated through GitHub Issues and `git worktree`. Every coding agent reads this
file: Codex, Cursor, Copilot and Jules directly, Claude Code through `CLAUDE.md`, Gemini CLI
through `.gemini/settings.json`.

## Hard rules
1. Never commit or push to `main`. Work only in a worktree made by `./scripts/claim.sh <issue-id>`.
2. Edit only files matching your issue's `Touches` globs, plus the shared files in `harness/config.json`.
   In Claude Code a hook blocks other edits; in every agent `finish-pr.sh` and CI reject them.
   Do not work around either with shell commands.
3. Never change `contracts/` or any other protected path in a feature branch.
   Use `./scripts/propose-contract.sh` instead.
4. Never edit issue labels, assignees, branches or worktrees by hand. Use the scripts in `scripts/`.
5. Commit and push to your `issue/<id>` branch after each meaningful step.
6. If you need a file owned by another slice, stop and run `./scripts/escalate.sh "<what you need>"`.
7. Never read or print `.env`, keys or service account files. Secrets stay in each person's environment.

## Workflow
Use the `hackathon-harness` skill (`.agents/skills/hackathon-harness/SKILL.md`) for the full
Architect, Builder, contract-change and hotfix flows.

## MCP servers
Add shared MCP servers to `mcp.json` (env values as `"${NAME}"`), then run
`python3 scripts/sync-mcp.py`. It writes `.mcp.json`, `.cursor/mcp.json`, `.gemini/settings.json`
and `.codex/config.toml`; CI fails if they drift.
