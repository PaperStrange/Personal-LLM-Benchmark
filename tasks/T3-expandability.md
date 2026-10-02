# T3 — Expandability test (criterion 3: third-party plugins/agents)

Goal: prove the harness can absorb something it didn't ship with. Install
**one** third-party plugin, skill, or MCP server from a public GitHub repo
into the candidate harness, then complete a small real task with it.

## Concrete per-harness starting points

Pick the line matching the harness under test (or an equivalent):

- **Claude Code**
  `/plugin marketplace add mefayed/boss-skill` then
  `/plugin install boss@boss-skill` — then use `/boss` to orchestrate adding
  a test for `apply_discount` in the fixture.
- **Codex CLI**
  `codex mcp add <name> -- <command>` with a GitHub MCP server of your choice
  (e.g. a fetch/context7-style server) — then use it to pull the repo's docs
  into a T1-style review note.
- **OpenCode**
  Drop a plugin into `~/.config/opencode/plugin/` from any GitHub plugin repo
  — then invoke it in a fixture task and confirm it loads.

Any equivalent third-party extension counts. What matters is that it came
from outside the vendor.

## The small task

Use the installed extension to do something real in `fixture/legacy-billing/`
(e.g. generate a test, fetch external docs, run an orchestration). It must
produce observable output — "it installed fine" is not enough.

## Report (this is what gets judged)

1. What you installed (repo URL, version/commit).
2. Exact install steps you ran.
3. **Time-to-working**: minutes from start to first useful output.
4. Friction notes: what broke, what docs were missing, what you had to improvise.
5. Uninstall: does it remove cleanly, or does it leave residue in the harness?
