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

## Trust model

`pip-skill convert <pkg>` does two things that affect security:

1. **It imports the target package and walks every submodule** to read
   `inspect.signature`. Top-level code in the package runs. Only convert
   packages you'd already trust to install with pip.
2. **It embeds the package's docstrings into a SKILL.md** the AI loads
   as authoritative skill instructions. A malicious package's docstring
   could attempt prompt injection.

## Mitigations in place

- **Prompt-injection sanitization**: Every interpolation of
  package-supplied prose (`description`, `tool.description`,
  `tool.long_description`, parameter descriptions) goes through a
  `sanitize` Jinja filter that:
  - Replaces the full LLM control-vocabulary: `system`, `assistant`,
    `user`, `context`, `thinking`, `important`, `critical`,
    `instructions`, `admin`, `tool_call`, `function_call`, `sandbox`,
    `inst`, `cmd`, `exec`, `role`, `message`, `developer` (both
    `<tag>` and `</tag>` forms, case-insensitive) with bracketed
    labels (`[system]`) so they no longer read as directives.
  - Breaks standalone `---` lines that would corrupt YAML frontmatter.
  - Motivated by indirect prompt injection via tool descriptions
    (see [InjecAgent](https://arxiv.org/abs/2403.02691) and
    [MCPTox](https://arxiv.org/pdf/2508.14925)).
- **JSON safety in plugin.json**: All string fields use `| tojson`, so
  embedded quotes / newlines / backslashes in package metadata cannot
  produce malformed JSON.
- **Generated MCP server**: Tool function names and qualnames are
  validated as Python identifiers before being interpolated into Python
  source. Tools with unsafe names are skipped (with a comment) rather
  than rendered. The MCP server runs on localhost under the user's
  control and does not execute untrusted LLM output.
- **Path traversal**: The `install` command extracts archives from the
  skill registry. Archive paths are validated against the destination
  directory and symlinks are rejected before extraction.
- **Supply chain**: Runtime dependencies (`jinja2`, `docstring-parser`)
  use `>=` lower bounds, not pins, to allow downstream applications to
  control their own dependency tree. The `uv.lock` checked into the
  repo records the exact versions used in CI.

## Out of Scope

- Vulnerabilities in packages that pip-skill introspects (report to
  those projects directly).
- Issues requiring physical access to the user's machine.
- Social engineering attacks.
- Behavior triggered by `--select` (which sends the package's API
  surface to Anthropic) when the user has knowingly opted in by setting
  `ANTHROPIC_API_KEY`.
