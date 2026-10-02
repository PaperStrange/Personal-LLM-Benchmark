# Gate 3 rehearsal report — sandboxed extension install

**Extension:** `@modelcontextprotocol/server-filesystem@2026.8.31` (allowlist entry 1, PROPOSED status) \
**Upstream repo:** https://github.com/modelcontextprotocol/servers \
**Registry tarball:** https://registry.npmjs.org/@modelcontextprotocol/server-filesystem/-/server-filesystem-2026.8.31.tgz \
**Sandbox:** temporary HOME `/tmp/gate3-tqsyvgiw` (removed after the run) \
**Date:** 2026-10-01 \
**Outcome:** worked — the extension was installed, configured, and performed
the fixture task. \
**Result:** all six claims evidenced; manifests + cleanup verified.

## The six claims

1. **t3_discovered** — EVIDENCED [REAL]: the operator (acting as the agent
   in this rehearsal) chose the MCP filesystem server over a
   fetch-style server (needs runtime network) and a hand-written plugin (not
   third-party). Task fit: the fixture task is reading fixture files, which
   is exactly what this server does.
2. **t3_installed** — EVIDENCED [REAL]: tarball downloaded from the registry URL,
   sha512 matched the allowlist integrity hash, extracted to
   `$TMPHOME/pkg/package`, dependencies installed with `npm install
   --omit=dev` (all under the temp HOME). `4775` files added, none
   removed.
3. **t3_configured** — EVIDENCED [REAL]: `mcp-config.json` written in the temp HOME
   (server command, allowed root `/home/hatch/workspace/goals/llm-workflow-benchmark-pack/files/llm-workflow-eval-pack/fixture/legacy-billing`, source URL, integrity hash).
   Server launched as `node /tmp/gate3-tqsyvgiw/pkg/package/dist/index.js /home/hatch/workspace/goals/llm-workflow-benchmark-pack/files/llm-workflow-eval-pack/fixture/legacy-billing`.
4. **t3_functional** — EVIDENCED [REAL]: real MCP stdio session —
   initialize → tools/list (14 tools, including `read_text_file`)
   → tools/call `read_text_file` on `fixture/legacy-billing/README.md`
   returned the fixture text (contains "Fictional internal invoicing service"). Observable output
   beyond "it installed fine."
5. **t3_recovered** — EVIDENCED [REAL]: install failures WERE encountered during
   rehearsal and diagnosed/recovered, with error and fix recorded here.
   Split by where the recovery happened:
   - Recovered WITHIN the final run: `npm install` crashed in arborist
     peer-dep resolution ("Cannot read properties of null (reading
     'edgesOut')") → recovered with `--legacy-peer-deps` (peer resolution
     skipped; the server only needs its direct deps).
   - Recovered ACROSS rehearsal iterations by the operator (editing the
     script between runs): the package's `prepare` script ran `tsc`, absent
     under `--omit=dev` → recovered with `--ignore-scripts` (the tarball
     ships prebuilt `dist/`, no build needed). This second fix does NOT
     demonstrate in-run agent recovery; the real Gate 3 must show the
     candidate recovering on its own.
   Additional errors in THIS run:
   - deps: npm arborist crash: Cannot read properties of null (reading 'edgesOut') → fix: retry with --legacy-peer-deps

6. **t3_time** — EVIDENCED [REAL]: time-to-working (install start → first useful
   MCP output): 41 seconds
   (0.7 minutes).

## Manifest accounting

- Before-manifest: 0 files (empty temp HOME).
- After-manifest: 4775 files.
- Added: 4775 files, all under the temp HOME (package files,
  node_modules dependencies, npm cache, tarball, config). Removed: 0.
- Real operator HOME untouched: `~/.npm` mtime unchanged
  (1790763673.5639708 → 1790763673.5639708).

## Cleanup

- `rm -rf` the temp HOME; `test ! -e` verified below (exit 0 only if gone).
- This rehearsal validates the sandbox procedure only. Whether a candidate
  harness absorbs the extension stays [OPEN] for the real Gate 3.
