# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest  | Yes       |

## Reporting a Vulnerability

To report a security vulnerability, please **do not** open a public GitHub issue.

Email: xpuspus@gmail.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You'll receive a response within 48 hours. If the issue is confirmed, a patch will be released as quickly as possible.

## Scope

pip-skill generates code files from installed Python packages. Key areas:

- **Template injection** — Jinja2 templates render package-provided strings (function names, docstrings, type annotations). Malicious packages could attempt template injection. pip-skill uses autoescape for untrusted content and avoids rendering raw user input.
- **Path traversal** — The `install` command extracts archives from the skill registry. pip-skill validates all archive paths against the destination directory and rejects symlinks before extraction.
- **Generated MCP servers** — Generated servers run on localhost and are under the user's control. They do not execute untrusted LLM output.
- **Supply chain** — Dependencies are pinned to exact versions in `pyproject.toml`.

## Out of Scope

- Vulnerabilities in packages that pip-skill introspects (report to those projects directly)
- Issues requiring physical access to the user's machine
- Social engineering attacks
