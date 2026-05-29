# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.1] - 2026-05-29

Data-science / data-engineering hardening, driven by a 16-package benchmark
(numpy, pandas, polars, pyarrow, scikit-learn, xgboost, statsmodels,
matplotlib, seaborn, plotly, sqlalchemy, duckdb, networkx, joblib, tqdm,
scipy) measuring how much of each library's canonical API the generated
skill actually surfaces.

### Fixed
- Introspection no longer walks test suites and benchmarks (`*.tests.*`,
  `test_*`, `conftest`, `benchmarks`). `pandas.tests` alone is ~1,100 modules;
  converting pandas dropped from minutes to ~9s, and test helpers can no
  longer leak into the candidate pool.
- Deduplication is now class-aware: a function is never folded into a
  same-named class. `numpy.array` (the constructor) was being dropped because
  `numpy.ndarray` (the class) scores higher and the names are 0.83-similar.
  Function-vs-method of the same verb (`requests.get` / `requests.Session.get`)
  still folds as before. Net eval-corpus coverage improved (msgspec +1).

### Added
- `convert` prints an advisory note for sprawling libraries (>300 public
  callables) recommending `--select` (LLM curation), which is the intended
  path when heuristic ranking can't surface a handful of canonical calls out
  of hundreds.

### Known limitation
- Heuristic selection remains best-effort on very large libraries: the
  canonical calls (`pandas.read_csv`, `matplotlib.pyplot.plot`,
  `seaborn.scatterplot`) are structurally indistinguishable from dozens of
  obscure siblings without a usage-frequency signal. Measured attempts to fix
  this via scoring (param-count, README-frequency, exact-dedup) regressed the
  eval corpus and were rejected. Use `--select` for these; a selector redesign
  with a widened LLM candidate pool is tracked for a future release.

## [0.2.0] - 2026-05-29

Audit-driven hardening release. Fixes a code-execution path in generated
MCP servers, closes a prompt-injection sink, and restores conversion of
packages with import-poisoned submodules.

### Security
- Generated MCP server no longer interpolates a package-supplied parameter
  default `repr()` raw into Python source. A malicious package could ship a
  default whose `__repr__` returns executable code, which fired the moment
  the server was imported. Defaults now pass through `ast.literal_eval`;
  non-literals render as `None`.
- `tool.example` is now sanitized before it reaches SKILL.md and
  api-reference.md, closing a prompt-injection path into content the agent
  loads as authoritative.
- Identifier validation now rejects Python keywords and validates every
  parameter name (not just the function name and qualname) before emitting
  generated source.

### Fixed
- `convert` no longer aborts on packages whose submodule raises at import
  (e.g. `mcp`, whose `mcp.cli` calls `sys.exit()` when an optional dep is
  missing). Introspection now walks with `iter_modules` and isolates each
  import, so one bad submodule is skipped rather than killing the run.
- `--max-tools` rejects values below 1 (previously `0` reported a misleading
  "no functions" error and negative values selected nearly everything via a
  list-slice bug).
- `test` on a malformed `plugin.json` reports a clean error instead of an
  uncaught traceback.
- `--dry-run` on an existing output directory now previews instead of failing
  with a collision error, and the collision check runs before the multi-second
  introspection pass.

### Added
- Per-tool usage examples now render in the Cursor, Windsurf, and OpenCode
  formats (previously Claude-only).
- Advisory warning when SKILL.md exceeds the ~5,000-token budget.
- reST/Sphinx markup (`:role:` roles, double-backtick literals) is converted
  to plain text in all formats instead of leaking through.
- Eval matcher resolves local-variable bindings
  (`client = pkg.X(); client.m()` → `pkg.X.m`), unblocking SDK-style eval sets.

## [0.1.0] - 2026-05-24

Initial public release. PyPI publish gated on manual approval of the
`pypi` GitHub environment after the test matrix passes (ubuntu /
macos / windows × Python 3.11 / 3.12 / 3.13).

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
- First measured results in [`RESEARCH.md`](RESEARCH.md), five
  reproducible findings across packages and model sizes:
  - Lift inversely scales with model prior: httpx ceiling (10/10
    both conditions), requests +10pp (9/10 → 10/10 at n=10), polars
    +40pp (15/30 → 27/30 at n=30).
  - Model size barely changes the lift at n=30: Sonnet polars +40pp,
    Haiku polars +43pp. Haiku + skill (29/30) beats Sonnet without
    skill (15/30) by 47pp.
  - Residual failures are concentrated: 2 of 3 polars misses target
    `polars.format` (model prefers Python `str.format` idiom); 1
    targets `polars.cum_reduce` (model prefers `functools.reduce`).
    Real failure mode that prompt engineering alone cannot fix.
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

[0.1.0]: https://github.com/xmpuspus/pip-skill/releases/tag/v0.1.0
