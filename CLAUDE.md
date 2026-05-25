# pip-skill

CLI tool that converts installed pip packages into AI coding assistant
skills (Claude Code, Cursor, Windsurf, OpenCode, MCP).

## Current State

v0.3 work shipped locally 2026-05-25. HEAD is `b29a5d1`. 198 tests
pass (198 + 2 skipped). Five commits ahead of remote: the v0.1.0 tag
target plus four follow-ups (eval harness, v0.2 corpus draft, v0.2
measurements, v0.3 fixes + blind measurements). GitHub repo
`xmpuspus/pip-skill` does NOT exist yet — that creation is the gating
human-only step blocking the publish workflow.

Authoritative measurements (v0.3 blind, 9 packages × 10 items):

| Model | n | no-skill | skill | Lift |
|---|---|---|---|---|
| Sonnet 4.5 | 90 | 67.8% | 87.8% | +20.0pp |
| Haiku 4.5  | 90 | 68.9% | 91.1% | +22.2pp |

Cross-model: Haiku + skill (91.1%) beats Sonnet alone (67.8%) by 23pp.

Full per-package report: `eval-results/blind/REPORT.md`. RESEARCH.md
"Second measurements" rewritten in place 2026-05-25 (revisionist
style — the older +22pp/+24pp manifest-aware headline was an upper
bound; v0.3 blind is the honest number).

**Author:** Xavier Puspus (xpuspus@gmail.com)
**GitHub:** https://github.com/xmpuspus/pip-skill (NOT YET CREATED)
**PyPI name:** pip-skill

## What This Project Does

Takes a pip package name, introspects its Python API (functions,
classes, instance methods, type hints, docstrings, `Annotated[...]`
metadata), selects the most useful callables, and generates a skill for
your AI coding assistant:

- **Claude Code** (default): `SKILL.md` + `.claude-plugin/plugin.json`
  (with structured `tools` manifest) + `CONTEXT.md` + `api-reference.md`
- **Cursor**: `.cursorrules`
- **Windsurf**: `.windsurfrules`
- **OpenCode**: `AGENTS.md`
- Optionally: FastMCP server + `.mcp.json` config

## Project Structure

```
src/pip_skill/
├── __init__.py          # version via importlib.metadata
├── __main__.py          # python -m pip_skill entry point
├── cli.py               # argparse CLI: convert, batch, info, diff, test,
│                        # build, validate, install, search
├── introspect.py        # Phase 1: package metadata + API enumeration
│                        # (incl. Annotated[X, Field(description=...)] extraction)
├── selector.py          # Phase 2: heuristic scoring (functions + classes
│                        # + instance methods)
├── schema.py            # Phase 3: JSON schema (Pydantic TypeAdapter +
│                        # manual fallback; preserves *args/**kwargs)
├── generator.py         # Phase 4: render Jinja2 templates; sanitize_prose
│                        # filter; safe_identifier guard for MCP
├── registry.py          # Skill registry (search, install from GitHub)
├── docstrings.py        # Docstring parsing (Google/NumPy/reST)
├── templates/
│   ├── skill.md.j2          # Claude Code SKILL.md
│   ├── plugin.json.j2       # plugin manifest with structured tools array
│   ├── api-reference.md.j2  # Full API reference
│   ├── context.md.j2        # Agent guidelines
│   ├── cursorrules.j2       # Cursor .cursorrules
│   ├── windsurfrules.j2     # Windsurf .windsurfrules
│   ├── agents-md.j2         # OpenCode AGENTS.md
│   ├── mcp-server.py.j2     # MCP server (identifier-validated)
│   └── mcp-config.json.j2   # MCP config
└── utils.py             # name normalization, type formatting
tests/
├── conftest.py
├── test_introspect.py
├── test_selector.py
├── test_schema.py
├── test_generator.py
├── test_docstrings.py
├── test_cli.py
├── test_utils.py
├── test_registry.py
├── test_integration.py  # real package tests (requests, httpx, pydantic, …)
└── fixtures/
    └── fake_package/    # synthetic package used in unit tests
.github/workflows/
├── ci.yml               # 3 OS × 3 Python = 9 jobs
└── publish.yml          # OIDC publish gated by `pypi` GitHub environment
action.yml               # Composite GitHub Action (local artifact, not yet published)
.pre-commit-hooks.yaml   # pip-skill-sync + pip-skill-test hooks (local artifact)
docs/demo.tape           # VHS recipe for the hero demo
```

## Tech Stack

- Python 3.11+
- jinja2 >= 3.0 (template rendering)
- docstring-parser >= 0.16 (docstring parsing)
- Optional `[mcp]`: mcp >= 1.0 (MCP server generation)
- Optional `[llm]`: anthropic >= 0.40 (LLM-assisted curation via `--select`)
- Testing: pytest, pytest-tmp-files

## CLI Commands

```bash
pip-skill convert <package> [--mcp] [--select] [--install] [--output DIR]
                            [--max-tools N] [--format FORMAT]
                            [--include PATTERN] [--exclude PATTERN]
                            [--dry-run] [--verbose] [--force]
pip-skill batch [packages...|requirements.txt] [--format FORMAT]
                [--workers N] [--output-dir DIR] [--mcp] [--force]
pip-skill info <package>
pip-skill diff <plugin-dir>
pip-skill test <plugin-dir>
pip-skill build <package>        # requires pip-skill[tui]
pip-skill validate <plugin-dir>
pip-skill search [query]
pip-skill install <package> [--output DIR]
```

## Key Design Decisions

- Works offline by default — no API calls unless `--select`
- Generated skills are self-contained (no pip-skill runtime dependency)
- Heuristic selection covers the common case; LLM curation (`--select`)
  is opt-in for sprawling SDKs
- SKILL.md stays under 5,000 tokens; details go in
  `references/api-reference.md`
- Multi-format output: Claude (default), Cursor, Windsurf, OpenCode
- Batch mode uses ThreadPoolExecutor for parallel package conversion;
  worker output is serialized via a print-lock so per-package status
  lines never interleave
- `diff` and `test` read the structured `tools` array from
  `plugin.json` rather than parsing prose — fast, accurate, and a
  natural single source of truth
- Registry backed by GitHub repo for pre-built skill distribution
- Safety callouts: `[CAUTION]` for destructive ops (delete, terminate,
  kill, revoke, cancel, unlink, …), `[NOTE]` for write ops
- MCP servers include error handling, JSON serialization, AND
  identifier validation before any name is interpolated into Python
  source
- Prompt-injection sanitizer on every prose interpolation; `tojson`
  for every JSON-bound interpolation
- Progress callbacks during introspection for user feedback
- `--install` copies the entire plugin bundle (`.claude-plugin/` +
  `skills/{name}/` + optional MCP scripts) to `~/.claude/plugins/`,
  always normalizing the package name (Pillow → pillow, etc.)
- **v0.3 selector signals** (added to `selector.py`):
  - `resolve_import_name` prefers an import name that matches the pip
    name itself before falling back to dist-name match — breaks the
    `toolz` / `tlz` tie where both map to the same pip distribution.
  - `get_public_api` widens the trust boundary when `__all__` is
    absent to "any callable whose module sits under the top-level
    package" — keeps C-extension re-exports like
    `msgspec.json.encode` (lives in `msgspec._core`) as candidates.
  - `score_canonical` subtracts 20 for `_experimental` / `_unstable`
    / `_legacy` / `_deprecated` / `_internal` / `_v1..3` / `_old`
    suffixes and 10 for `_build_` / `_meta_` / `TlzLoader`
    scaffolding substrings — keeps canonical names ahead of
    better-typed experimental variants.
- **v0.3 eval signals** (added to `eval.py`):
  - `EvalItem.expected_qualnames` (list) accepts multiple equivalent
    qualnames per item; the matcher passes if extracted matches ANY.
    Items still use the singular `expected_qualname` for the
    common case.
  - `extract_qualnames` returns all plausible chains including method-
    aware forms (`pkg.Class().method(...)` → `pkg.Class.method`).
    Strict `extract_qualname` preserves the v0.1 contract — only
    Name-rooted chains, no Call recursion.

## Open v0.4 backlog

1. Same-name dedup across submodules. `score_uniqueness` drops
   `msgspec.json.encode` because `msgspec.toml.encode` is already
   selected. Scope the dedup to the same submodule path.
2. Reduce annotation/docstring weight or boost README signal.
   On more_itertools, `Stats` (well-annotated) outscores `chunked`
   (canonical). Either lower the annotation cap or add a documented-
   in-README boost.
3. Drop function-form when class-form with same noun exists. arrow
   manifest has both `arrow.api.factory` and `arrow.ArrowFactory`;
   class is ranked higher but both stay in the manifest, and the
   model under skill sometimes picks the lowercase function.
4. Variable-binding tracking in `_attr_chain`. Inline
   `pkg.Class().method(...)` works under v0.3; `client = pkg.Class();
   client.method(...)` does not. Unblocks the full Phase 2 corpus
   (anthropic, openai, langgraph, pydantic-ai, crewai) where every
   real example uses local-variable form.

## Gitignored (local-only, do not add to remote)

- `CLAUDE.md` (this file)
- `.claude/` (Claude Code session data)
- `.planning/` (design docs, specs, ADRs)
- `make_demo_gif.py` (dev script for the demo GIF)
- `tmp/` (eval runner scripts, aggregator, status notes)

## Publishing to PyPI

The publish workflow (`.github/workflows/publish.yml`) triggers on
`v*` tags, runs the full CI matrix (ubuntu/macos/windows × Python
3.11/3.12/3.13), then waits for manual approval in the `pypi`
GitHub environment before publishing via OIDC trusted publishing:

```bash
git tag v0.1.0
git push origin v0.1.0
# Then approve the deployment in GitHub Actions
```

No manual PyPI token needed — uses OIDC trusted publishing.

## Coding Standards

- ruff for linting and formatting (`uv run ruff check .` and
  `uv run ruff format .`)
- Type annotations on all public functions
- Google-style docstrings
- Tests: pytest, no `eval()`/`exec()` in generated code
- Generated MCP servers are self-contained
