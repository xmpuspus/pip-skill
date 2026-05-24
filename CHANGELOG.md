# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Research and evaluation
- `pip-skill eval <plugin-dir> <eval-file.jsonl>` subcommand that
  measures tool-call accuracy on a JSONL eval set. Conditions:
  `coverage` (offline manifest check), `no-skill` (Claude baseline),
  `skill` (Claude with the SKILL.md). AST-equivalence judging
  consistent with the Berkeley Function-Calling Leaderboard (BFCL).
- Two backends for model conditions: `claude-cli` (shells out to
  `claude -p`, uses the existing Claude Code session, **no API key
  needed**) and `api` (Anthropic SDK with `temperature=0` for
  reproducibility). Auto-selects based on whether `ANTHROPIC_API_KEY`
  is set.
- Alias-aware AST extractor: accepts `pl.X`, `pd.X`, `np.X`, `plt.X`,
  `sns.X`, `tf.X`, `sa.X`, `px.X`, `go.X`, `dt.X` as canonical
  package calls and normalises back to the package name.
- `--deterministic` mode: fixed `generatedAt` timestamp, sorted
  module traversal, `temperature=0` on `--select`, and a
  `MANIFEST.sha256` file covering every byte. Required for citable
  bundles.
- Public Python API: `from pip_skill import generate_skill,
  SkillBundle`. Documented at [`src/pip_skill/api.py`](src/pip_skill/api.py).
- Sample eval sets ship for `requests` and `polars` under
  [`examples/eval/`](examples/eval/).
- First measured results in [`RESEARCH.md`](RESEARCH.md), three
  reproducible findings on 4 (package, model) combinations:
  - Lift inversely scales with model prior: httpx ceiling, requests
    +10pp, polars +30pp.
  - Smaller models benefit more: Haiku polars +40pp vs Sonnet polars
    +30pp; Haiku reaches 10/10 on polars with skill.
  - More tools is not better: max_tools sweep N=5/10/20/40 found
    pip-skill's default N=20 was the sweet spot. Doubling the menu
    to 40 produced zero improvement.
  - The uniqueness signal silently drops core API (httpx.post,
    httpx.put deduplicated against httpx.request). Worth quantifying
    via ablation; tracked as Experiment 3 in RESEARCH.md.
- Helper scripts:
  [`scripts/bootstrap-demo.sh`](scripts/bootstrap-demo.sh) provisions
  the demo venv; [`scripts/prompt_ab.py`](scripts/prompt_ab.py)
  sweeps eval prompt variants;
  [`scripts/tool_count_sweep.py`](scripts/tool_count_sweep.py) sweeps
  `max_tools` and reports coverage / no-skill / skill / conditional
  rate per N.

### Core
- `pip-skill convert` command: generate AI coding assistant skills from
  installed pip packages via runtime introspection
- 10-signal heuristic function selection (module depth, `__all__`
  membership, docstring quality, annotation coverage, name quality,
  parameter count, return type, deprecation, re-export, uniqueness)
- Class constructors and instance methods scored alongside top-level
  functions, so canonical patterns like `requests.Session().get()` and
  `boto3.client('s3').list_buckets()` are first-class candidates
- JSON Schema generation via `pydantic.create_model()` +
  `model_json_schema()` with a manual fallback for partially annotated
  APIs
- `Annotated[X, Field(description=...)]` parameter descriptions
  surfaced into the schema
- `*args` and `**kwargs` preserved as synthetic `args` / `kwargs`
  schema properties so dynamic APIs (boto3, stripe, `requests.request`)
  aren't silently truncated
- Package tier auto-detection (Tier 1: well-annotated, Tier 2: partial,
  Tier 3: dynamic / stateful)
- Support for Pydantic v2 models, dataclasses, and C extensions
- `BaseException`-level isolation around per-module imports so packages
  raising `pytest.importorskip` (which inherits from `BaseException`)
  don't crash introspection

### Multi-format output
- Claude Code (default): `SKILL.md` + `.claude-plugin/plugin.json` +
  `CONTEXT.md` + `references/api-reference.md`
- Cursor: `.cursorrules` via `--format cursor`
- Windsurf: `.windsurfrules` via `--format windsurf`
- OpenCode: `AGENTS.md` via `--format opencode`
- MCP server generation via `--mcp` flag (FastMCP-based)

### CLI commands
- `pip-skill batch`: convert multiple packages in parallel from names
  or `requirements.txt`. Worker output is serialized so per-package
  status lines never interleave on stderr
- `pip-skill info`: package metadata + API surface summary
- `pip-skill diff`: detect API changes by comparing the structured
  `tools` manifest in `plugin.json` against the currently installed
  package
- `pip-skill test`: verify every function in the skill is still
  importable in the current Python environment
- `pip-skill build`: interactive TUI builder (requires `pip-skill[tui]`)
- `pip-skill validate`: structural check on a generated plugin directory
- `pip-skill search` / `pip-skill install`: skill registry browsing
- `pip-skill convert --install`: one-shot install of the generated
  bundle into the AI tool's directory (`~/.claude/plugins/` for Claude,
  project-local for Cursor / Windsurf / OpenCode). Package names are
  normalized so case-mismatched packages (Pillow → pillow,
  PyYAML → pyyaml, discord.py → discord-py) work on case-sensitive
  filesystems.
- `pip-skill convert --select`: optional Claude-assisted curation
  (requires `ANTHROPIC_API_KEY` and `pip-skill[llm]`); model
  overridable via `PIP_SKILL_MODEL`
- `pip-skill convert --force`: clean overwrite of the output directory
  (no stale files from a prior `--format`)

### Quality and safety
- `plugin.json` manifest: name, version, author, homepage, license,
  generation timestamp, tool count, and a structured `tools` array of
  `{name, functionName, qualname, module, isDestructive, isWrite,
  parameters}` that `diff` and `test` read directly
- YAML frontmatter in SKILL.md with prerequisites and dependency list
- CONTEXT.md agent guidelines with context window tips and error
  handling patterns
- Safety callouts: `[CAUTION]` for destructive verbs (`delete`,
  `remove`, `drop`, `destroy`, `purge`, `truncate`, `clear`, `reset`,
  `terminate`, `kill`, `revoke`, `cancel`, `unlink`, `shutdown`,
  `wipe`, `uninstall`, `deregister`, `expire`); `[NOTE]` for write
  verbs (`write`, `send`, `post`, `put`, `patch`, `upload`, `create`,
  `update`, `execute`)
- External documentation links extracted from package metadata
  (`Project-URL: Documentation`)
- Progress indicators during introspection with timing breakdown

### Security
- Prompt-injection sanitization on every interpolation of
  package-supplied prose: LLM control-vocabulary tags (`<system>`,
  `</thinking>`, `<assistant>`, `<context>`, `<important>`,
  `<tool_call>`, `<function_call>`, `<sandbox>`, `<role>`, `<message>`,
  …) are replaced with bracketed labels; standalone `---` lines that
  would corrupt YAML frontmatter are broken
- All string fields in `plugin.json` use `| tojson` so embedded quotes,
  newlines, or backslashes in package metadata cannot produce malformed
  JSON
- Generated MCP server validates Python identifiers before
  interpolating function names and qualnames into source; tools with
  unsafe names are skipped (with a comment) rather than emitted
- Pre-flight key validation: `--select` checks `ANTHROPIC_API_KEY` and
  the `[llm]` extra before any introspection so users don't wait
  through a multi-second `boto3` walk to discover a missing key

### Tooling
- CI matrix: ubuntu-latest, macos-latest, windows-latest × Python 3.11,
  3.12, 3.13
- PyPI publish via OIDC trusted publishing, gated by a `pypi` GitHub
  environment for manual approval
- Composite GitHub Action (`action.yml`) wrapping
  `astral-sh/setup-uv` + `pip-skill batch` for CI integration
- `.pre-commit-hooks.yaml` exposing `pip-skill-sync` and
  `pip-skill-test` hooks
- VHS `.tape` file at `docs/demo.tape` for reproducible terminal demo
  recording

[Unreleased]: https://github.com/xmpuspus/pip-skill/compare/main...HEAD
