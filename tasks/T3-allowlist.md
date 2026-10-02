# T3 extension allowlist

**Status: PROPOSED — approval pending Sakura's nod.** No Gate 3 candidate
run may install anything not on this list. The rehearsal
(`tools/qualification/gate3_rehearsal.py`) exercises the sandbox procedure
with entry 1; the policy decision (is this the right extension for the real
Gate 3) remains Sakura's.

## Entry 1 (proposed 2026-10-01)

- **Name:** `@modelcontextprotocol/server-filesystem`
- **Version:** `2026.8.31` (pinned; no ranges, no `latest`)
- **Source URL:** https://registry.npmjs.org/@modelcontextprotocol/server-filesystem/-/server-filesystem-2026.8.31.tgz
  (upstream repo: https://github.com/modelcontextprotocol/servers)
- **Integrity (sha512, base64):**
  `kKaFkyAh6oipvc9+EAbJ552JafnMnOq5nzmzWkp1jJdBhTAAGpmIpWihUG1+rfNhmEFM98gUZDdCHCDD4v6a7Q==`
  (advertised by the registry 2026-10-01; verified against the downloaded
  tarball before extraction in the rehearsal)
- **Why this one:** the T3 task's Codex line names "a fetch/context7-style
  server"; a filesystem MCP server is the closest canonical equivalent for
  a fixture-reading task. Rejected alternatives:
  - fetch-style servers — need network access at *runtime*, harder to keep
    the rehearsal hermetic;
  - a hand-written plugin — not third-party, proves nothing about absorbing
    outside code.

## Amendment rule

Entries are append-only with date + rationale. Removing an entry requires a
note saying why. Pinning is by exact version + integrity hash, never by tag.
