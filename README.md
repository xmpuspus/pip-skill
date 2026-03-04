<p align="center">
  <strong>pip-skill</strong><br>
  Turn any pip package into a Claude Code plugin
</p>

<p align="center">
  <a href="https://pypi.org/project/pip-skill/"><img src="https://img.shields.io/pypi/v/pip-skill.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/pip-skill/"><img src="https://img.shields.io/pypi/dm/pip-skill.svg" alt="Downloads"></a>
  <a href="https://pypi.org/project/pip-skill/"><img src="https://img.shields.io/pypi/pyversions/pip-skill.svg" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
  <a href="https://github.com/xavierperez/pip-skill/actions/workflows/ci.yml"><img src="https://github.com/xavierperez/pip-skill/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
</p>

pip-skill introspects installed Python packages and generates Claude Code plugins — complete with skill instructions, API reference, and optional MCP server. No manual wrapping required.

```bash
pip install pip-skill
pip-skill convert requests
```

That's it. You get a ready-to-install Claude Code plugin:

```
requests/
├── .claude-plugin/plugin.json
└── skills/requests/
    ├── SKILL.md
    └── references/api-reference.md
```

## Why pip-skill?

Claude Code skills let Claude use Python libraries directly — but writing SKILL.md files by hand is tedious. You have to read the docs, pick the right functions, document parameters, and format everything correctly.

pip-skill automates the entire pipeline:

1. **Introspects** the installed package (signatures, types, docstrings)
2. **Selects** the most useful functions via a scoring algorithm
3. **Generates** JSON schemas, skill instructions, and API docs
4. **Outputs** a complete plugin directory you can install immediately

## Quick Start

### Install

```bash
pip install pip-skill
# or
uv add pip-skill
```

### Generate a plugin

```bash
# Basic: skill-only mode
pip-skill convert httpx

# With MCP server
pip-skill convert httpx --mcp

# Preview without writing files
pip-skill convert httpx --dry-run --verbose
```

### Install the plugin

```bash
# In Claude Code
/plugin install ./httpx
```

### Explore a package

```bash
pip-skill info pandas
```

```
Package: pandas v2.2.0
Import name: pandas
Description: Powerful data structures for data analysis
Submodules: 42
Public functions: 156
Public classes: 38
Annotation coverage: 65%
Estimated tier: 2 (partial annotations)
```

## How It Works

pip-skill uses runtime introspection to analyze a package's API:

- **`inspect.signature()`** extracts function parameters and type annotations
- **`typing.get_type_hints()`** resolves forward references and `from __future__ import annotations`
- **`pkgutil.walk_packages()`** discovers all submodules
- **`docstring-parser`** extracts parameter descriptions from Google/NumPy/reST docstrings
- **`pydantic.TypeAdapter`** generates JSON Schema from type annotations

Each discovered function gets scored on 10 signals (module depth, docstring quality, annotation coverage, etc.) and the top candidates are selected for the plugin.

## Features

### Skill-Only Mode (default)

Generates a SKILL.md that teaches Claude how to use the package via inline Python:

```
User invokes /requests → Claude reads SKILL.md →
Claude writes Python code → executes via Bash tool
```

### MCP Mode (`--mcp`)

Also generates a FastMCP server that exposes functions as structured tools:

```
Claude Code starts MCP server → tools available via MCP protocol →
Claude calls tools directly → structured JSON responses
```

### Smart Function Selection

- 10-signal scoring algorithm (0-100 per function)
- Prioritizes top-level, well-documented, well-typed functions
- Deduplicates near-identical variants
- Optional LLM curation via `--select` for complex packages

### Package Tier Detection

Automatically classifies packages and adjusts strategy:

| Tier | Criteria | Example |
|------|----------|---------|
| 1 | >70% annotated, stateless | httpx, pydantic |
| 2 | <70% annotated, stateless | requests, click |
| 3 | Stateful/dynamic | boto3, sqlalchemy |

## CLI Reference

### `pip-skill convert <package>`

Generate a Claude Code plugin from an installed package.

```
Options:
  --mcp                Generate MCP server alongside SKILL.md
  --select             Use LLM to curate function selection (needs ANTHROPIC_API_KEY)
  --output DIR         Output directory (default: ./{package-name})
  --max-tools N        Maximum functions to include (default: 20)
  --include PATTERN    Include functions matching glob pattern
  --exclude PATTERN    Exclude functions matching glob pattern
  --dry-run            Preview without writing files
  --verbose            Show scoring breakdown
  --force              Overwrite existing output
```

### `pip-skill info <package>`

Show package metadata and API surface summary.

### `pip-skill validate <plugin-dir>`

Validate a generated plugin directory for correctness.

## Supported Packages

pip-skill works with any installed Python package. It handles:

- Fully annotated APIs (Tier 1): httpx, pydantic, fastapi
- Partially annotated APIs (Tier 2): requests, click, flask
- Stateful/dynamic APIs (Tier 3): boto3, sqlalchemy, stripe
- C extensions: numpy, pandas (limited signature info)
- Pydantic models: auto-detected, fields extracted from `model_fields`
- Dataclasses: auto-detected, fields extracted from `dataclasses.fields()`
- Lazy imports: detected via `__getattr__`, logged as warning

## Examples

See the [`examples/`](examples/) directory for sample generated plugins.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License — see [LICENSE](LICENSE).
