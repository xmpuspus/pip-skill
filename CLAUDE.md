# pip-skill

CLI tool that converts installed pip packages into Claude Code plugins.

## What This Project Does

Takes a pip package name, introspects its Python API (functions, classes, type hints, docstrings), selects the most useful callables, and generates a Claude Code plugin containing:
- SKILL.md with usage instructions
- plugin.json manifest
- API reference documentation
- Optionally: FastMCP server wrapping selected functions as MCP tools

## Project Structure

```
src/pip_skill/
├── __init__.py          # version, public API
├── __main__.py          # python -m pip_skill entry point
├── cli.py               # argparse CLI (convert, info, test commands)
├── introspect.py        # Phase 1: package metadata + API enumeration
├── selector.py          # Phase 2: function selection (heuristic + optional LLM)
├── schema.py            # Phase 3: JSON schema from signatures
├── generator.py         # Phase 4: output files (SKILL.md, plugin.json, MCP server)
├── docstrings.py        # Docstring parsing (Google/NumPy/reST)
├── templates/           # Jinja2 templates for generated files
│   ├── skill.md.j2
│   ├── plugin.json.j2
│   ├── api-reference.md.j2
│   └── mcp-server.py.j2
└── utils.py             # name normalization, type formatting
tests/
├── test_introspect.py
├── test_selector.py
├── test_schema.py
├── test_generator.py
├── test_docstrings.py
├── test_cli.py
├── test_e2e.py          # end-to-end against real packages
└── fixtures/
    └── sample_package/  # mock package for unit tests
```

## Tech Stack

- Python 3.11+
- pydantic >= 2.0 (schema generation via TypeAdapter)
- jinja2 >= 3.0 (template rendering)
- docstring-parser >= 0.16 (docstring parsing)
- Optional: mcp >= 1.0 (MCP server generation)
- Optional: anthropic (LLM-assisted function curation)
- Testing: pytest, pytest-cov

## Implementation References

All detailed specs are in `.planning/`. Read these before implementing:

| Doc | Content |
|-----|---------|
| `SPEC.md` | Full technical specification — dataclasses, CLI flags, exit codes, error handling |
| `ARCHITECTURE.md` | 11 ADRs — output format, introspection strategy, tier classification, template engine |
| `INTROSPECTION.md` | 7-step introspection engine with complete code — import resolution, module walking, API enumeration |
| `SELECTION.md` | 10-signal scoring algorithm (0-100), weight table, LLM curation prompt, debug output |
| `SCHEMA.md` | JSON Schema generation — Pydantic TypeAdapter, manual fallback, docstring-only fallback |
| `TEMPLATES.md` | All 5 Jinja2 templates — skill.md.j2, plugin.json.j2, api-reference.md.j2, mcp-server.py.j2, mcp-config.json.j2 |
| `SCAFFOLD.md` | pyproject.toml, directory structure, CI/CD, GitHub templates, CLI skeleton |
| `TESTING.md` | Test strategy, fake_package fixture, test cases per module, integration tests |
| `REFERENCES.md` | Prior art — skill-seekers, FastMCP, MCP SDK, agentskills.io spec |
| `README-TEMPLATE.md` | README.md content for the open-source repo |

**Implementation order:** utils.py → docstrings.py → introspect.py → selector.py → schema.py → generator.py → cli.py → templates → tests

## Coding Standards

- ruff for linting and formatting
- Type annotations on all public functions
- Docstrings: Google style
- Tests: pytest, mock external dependencies
- No `eval()` or `exec()` in generated code
- Generated MCP servers must be self-contained (no pip-skill dependency at runtime)

## CLI Commands

```bash
pip-skill convert <package> [--mcp] [--select] [--output DIR] [--max-tools N] [--dry-run]
pip-skill info <package>
pip-skill validate <plugin-dir>
```

## Key Design Principles

1. Works offline by default (no API calls unless --select)
2. Generated plugins are self-contained (no pip-skill runtime dependency)
3. Output conforms to agentskills.io spec + Claude Code plugin format
4. Heuristic selection is good enough for 80% of packages
5. Progressive disclosure: SKILL.md stays under 5000 tokens, details in references/
