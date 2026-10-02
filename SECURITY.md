# Security Policy

## Reporting a Vulnerability

If you find a security issue in this repository, please do **not** open a
public issue. Email the maintainer directly with a description of the issue
and steps to reproduce. We will respond as quickly as possible.

## Scope notes

- The `fixture/legacy-billing/` codebase **intentionally** contains planted
  vulnerabilities (hardcoded `API_TOKEN=<redacted>`, SQL injection, etc.).
  These are synthetic benchmark targets for the T1 task — not real leaks.
  Do not report them as security issues.
- No real credentials, API keys, or personal data are committed to this
  repository. See `results/qualification/SECURITY-CHECK.md` for the latest
  audit.
