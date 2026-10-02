# Security check — Personal-LLM-Benchmark (2026-10-01)

**Scope:** all 190 git-tracked files + full local git history.
**Verdict:** CLEAN — safe for public.

## Checks performed

| Check | Result |
|---|---|
| Credential files (`.env`, `.pem`, `.key`, `credentials*`, `secrets*`) | None found |
| Private key blocks (`BEGIN PRIVATE KEY`, etc.) | None found |
| Token patterns (`ghp_`, `gho_`, `sk-live`, `AKIA…`, `xox…`, `AIza…`) | None — all `API_TOKEN` hits are `<redacted>` placeholders |
| Real email addresses / PII | None — only synthetic `p@x.com` in fixture test data |
| URLs with embedded credentials | None |
| Real IP addresses | None (localhost only) |
| Git history secret scan (`-S "ghp_"`, `-S "BEGIN PRIVATE KEY"`) | Clean |
| Excluded T3 manifests (npm cache file paths) | No secrets — paths only |

## By-design note

The fixture **intentionally** contains a fake hardcoded credential
(`API_TOKEN=<redacted>` in `fixture/legacy-billing/config.py`) as a planted
vulnerability for the T1 benchmark task to discover. The value is the literal
string `<redacted>` — not a real credential — so it is safe to publish.
This is the benchmark working as designed, not a leak.

## Excluded from the public push (tool limit, not security)

- `results/qualification/t3/manifest.after` (448KB)
- `results/qualification/t3/manifest.diff` (448KB)

Both are npm cache file listings from the Gate 3 sandbox rehearsal.
Scanned: paths only, no secrets. They remain in the local commit `392e96f`
and the `.bundle` file.
