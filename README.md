<h1 align="center">pip-skill</h1>
<p align="center"><strong>Hallucination-free AI skills for any installed Python package. One command. Offline.</strong></p>
<p align="center">Generates Claude Code, Cursor, Windsurf, OpenCode, and MCP server skills directly from the installed API. No docs scraping, no API key, no LLM in the loop.</p>

<p align="center">
  <a href="https://github.com/xmpuspus/pip-skill/stargazers"><img src="https://img.shields.io/github/stars/xmpuspus/pip-skill" alt="GitHub stars"></a>
  <img src="https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg" alt="Python 3.11/3.12/3.13">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey.svg" alt="Linux | macOS | Windows">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/offline-yes-success.svg" alt="Offline by default">
</p>

<p align="center"><img src="pip-skill-demo.gif" alt="pip-skill demo: one command turns requests into a Claude skill" width="900"></p>

```bash
uvx pip-skill convert requests --install
```

That's the whole loop. One command, no install, the skill bundle lands in
`~/.claude/plugins/requests/` and Claude can call requests with correct
types on the next session.

> **Note:** `convert` imports the target package (which runs its top-level
> code) and walks every submodule. Only convert packages you trust;
> same trust level as installing them with pip.

Prefer a permanent install? `pip install pip-skill` and use the `pip-skill`
binary directly.

## What you get

A self-contained Claude Code plugin, ready to drop into `~/.claude/plugins/`:

```
requests/
├── .claude-plugin/
│   └── plugin.json          # structured manifest: tools, qualnames, params, version
└── skills/requests/
    ├── SKILL.md             # what Claude reads (under 5,000 tokens)
    ├── CONTEXT.md           # agent guidelines for this package
    └── references/
        └── api-reference.md # full schemas, signatures, JSON Schema per tool
```

The `tools` array in `plugin.json` is the canonical record of what the
skill exposes. `pip-skill diff` and `pip-skill test` read it directly,
which is why version drift on a 200-package monorepo is detectable in
seconds and why a stale skill is impossible to silently ship.

## Trust model

`pip-skill convert` does two things that affect security:

1. **Imports the target package.** `inspect.signature` requires a
   real Python module, so we `importlib.import_module(...)` and then
   `pkgutil.walk_packages(...)` every submodule. Top-level code in the
   package runs. The trust requirement is the same as `pip install`
   of that package: only run pip-skill against packages you'd already
   have in your venv.

2. **Embeds the package's docstrings into a SKILL.md the AI loads as
   authoritative skill instructions.** A malicious package's
   docstring could try prompt injection (`<system>...</system>`-style
   tags). pip-skill neutralizes the LLM control-tag vocabulary in
   every prose interpolation, breaks standalone `---` lines that
   would corrupt YAML frontmatter, and validates Python identifiers
   before emitting them into the generated MCP server. The threat
   model engages with InjecAgent
   ([arXiv:2403.02691](https://arxiv.org/abs/2403.02691)) and MCPTox
   ([arXiv:2508.14925](https://arxiv.org/pdf/2508.14925)); see
   [SECURITY.md](SECURITY.md) for the full list.

## Why pip-skill?

Claude Code skills let Claude use Python libraries directly, but
writing SKILL.md files by hand is tedious. You have to read the docs,
pick the right functions, document parameters, and format everything
correctly.

pip-skill automates the entire pipeline:

1. **Introspects** the installed package (signatures, types, docstrings)
2. **Selects** the most useful functions via a 10-signal scoring algorithm
3. **Generates** JSON schemas, skill instructions, and API docs
4. **Outputs** a self-contained plugin you can install with `--install`

Functions, classes, instance methods, Pydantic v2 models, dataclasses,
and the `Annotated[X, Field(description=...)]` pattern all get
introspected with their descriptions intact. `*args` and `**kwargs` are
preserved in the generated schemas so dynamic APIs like boto3, stripe,
and `requests.request` aren't silently truncated.

## Quick start

### Try it without installing

```bash
uvx pip-skill convert httpx
```

### Or install once

```bash
pip install pip-skill        # or:  uv tool install pip-skill
```

### Explore a package first

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

### Generate, install, done

```bash
pip-skill convert httpx --install
```

The skill bundle lands in `~/.claude/plugins/httpx/`, complete with
`plugin.json`, `SKILL.md`, `CONTEXT.md`, and `references/`. Claude Code
auto-discovers it on the next session.

For Cursor / Windsurf / OpenCode, `--install` writes to the matching
project-local config (`.cursor/rules/`, `.windsurf/rules/`,
`./AGENTS.md`).

### Verify a skill is still in sync

```bash
pip-skill test ./httpx
```

```
Testing httpx skill (v0.28.1)...
  [PASS] httpx.HTTPError
  [PASS] httpx.URL
  [PASS] httpx.request
  [PASS] httpx.delete
  [PASS] httpx.get
  ...

Result: 8/8 passed
```

`test` reads the structured `tools` manifest from `plugin.json` and
verifies every entry is still importable. Run it after a dependency
upgrade to catch drift before Claude does.

### See what changed after an upgrade

```bash
pip-skill diff ./httpx
```

<img src="demos/diff.gif" alt="pip-skill diff output" width="640">

`diff` compares the current installed API against the manifest the
skill was generated from. Added/removed function names print one per
line, ready to pipe into a regenerate hook.

## How it works

- **`inspect.signature(eval_str=True)`** with a graceful fallback
  resolves type annotations on packages like `httpx` whose forward refs
  reference symbols not exported from the defining module.
- **`typing.get_type_hints()`** walks `from __future__ import annotations`
  and `Annotated[...]` wrappers; the metadata layer extracts pydantic
  `Field(description=...)` and similar.
- **`pkgutil.walk_packages()`** discovers submodules; import errors are
  caught at the `BaseException` boundary so packages that raise
  `pytest.importorskip` (which inherits from `BaseException`) don't
  crash introspection.
- **`docstring-parser`** extracts parameter descriptions from
  Google / NumPy / reST docstrings.
- **`pydantic.create_model()`** + **`model.model_json_schema()`**
  generate JSON Schema from type annotations; we fall back to a manual
  schema builder when annotations are partial.

Each discovered function gets scored on 10 signals: module depth,
`__all__` membership, docstring quality, annotation coverage,
name quality (verb prefix), parameter count, return-type presence,
not-deprecated, re-export at top level, and uniqueness vs
higher-scored peers. The top candidates make the SKILL.md.

## Features

### vs writing skills by hand

Manual authoring is roughly an hour per package and produces no drift
signal when the SDK ships a new version. Pasting docs into context
costs tokens, breaks on packages updated after the model's training
cutoff, and produces no JSON Schema. pip-skill takes <1s for a typical
package (<10s for boto3-scale SDKs), reads types from
`inspect.signature` at runtime, and ships a structured manifest that
`pip-skill diff` / `pip-skill test` use to detect drift.

### vs other skill generators

| | pip-skill | [skill-seekers](https://pypi.org/project/skill-seekers/) | [skillnet-ai](https://pypi.org/project/skillnet-ai/) | [skills-cli](https://pypi.org/project/skills-cli/) |
|---|---|---|---|---|
| **What it does** | Converts installed pip packages into skills | Converts docs, repos, PDFs, videos into skills | Create, evaluate, and connect skills from various sources | Scaffold, validate, and manage existing skills |
| **Input source** | Installed Python package (runtime introspection) | 17 source types (websites, repos, PDFs, videos, wikis) | Conversation logs, repos, documents, prompts | Manual authoring |
| **Type accuracy** | Exact (reads `inspect.signature()` at runtime) | Depends on documentation quality | Depends on source quality | N/A (manual) |
| **API key required** | No (offline by default) | Optional (for AI enhancement) | Yes (for creation/evaluation) | No |
| **Output formats** | Claude, Cursor, Windsurf, OpenCode, MCP | Claude, Gemini, OpenAI, LangChain, 12+ formats | SKILL.md | SKILL.md |
| **Drift detection** | `diff` + `test` against structured manifest | none | none | Spec validation |
| **Reproducibility** | `--deterministic` mode + `MANIFEST.sha256` | none | none | none |
| **Evaluation** | `pip-skill eval` (coverage + AST-equivalence, BFCL-style) | none | Evaluation framework | none |
| **Best for** | Python packages you use in code | Documentation and knowledge bases | Discovering pre-built skills | Managing and distributing skills |

These tools are complementary: pip-skill generates skills from
installed Python APIs with exact type signatures; the others work from
documentation or pre-built repositories.

### Skill-only mode (default)

Generates a SKILL.md that teaches Claude how to use the package via
inline Python:

```
User invokes /requests → Claude reads SKILL.md →
Claude writes Python code → executes via Bash tool
```

### MCP mode (`--mcp`)

Also generates a FastMCP server that exposes functions as structured
tools:

```
Claude Code starts MCP server → tools available via MCP protocol →
Claude calls tools directly → structured JSON responses
```

Function names and qualnames are validated as Python identifiers before
being interpolated into the generated server source. Tools whose names
aren't safe identifiers are skipped (with a comment) rather than
emitted, so a hostile attribute name in a third-party package can't
smuggle Python through the MCP code path.

### Multi-format output

Generate skills for any major AI coding assistant from the same
introspection:

| Format | Flag | Output |
|--------|------|--------|
| Claude Code | `--format claude` (default) | `SKILL.md` + `plugin.json` + `CONTEXT.md` + `api-reference.md` |
| Cursor | `--format cursor` | `.cursorrules` |
| Windsurf | `--format windsurf` | `.windsurfrules` |
| OpenCode | `--format opencode` | `AGENTS.md` |

The generated `SKILL.md` follows the open
[Agent Skills](https://agentskills.io) standard, so it works with the
30+ AI coding tools that consume the spec, well beyond the four
explicit format flags above.

### Compatible tools

pip-skill output works with tools that support the Agent Skills standard
or markdown-based skill files:

- Claude Code, Cursor, Windsurf, OpenCode
- GitHub Copilot, VS Code Copilot, OpenAI Codex
- Gemini CLI, JetBrains Junie, Goose, Roo Code
- Databricks Genie Code, and more

Full list: [agentskills.io](https://agentskills.io)

### Batch mode

Convert every dependency in your `requirements.txt` (or just a list of
packages) in parallel:

```bash
pip-skill batch requirements.txt --workers 4
```

<img src="demos/batch.gif" alt="pip-skill batch conversion" width="640">

Worker output is serialized so per-package status lines never
interleave. Failed packages get a clear `[FAIL] <name>: <reason>` line
on stderr and the batch returns a non-zero exit code.

### 10-signal function scoring

Each candidate function gets a score 0-100 from ten signals: module
depth, `__all__` membership, docstring quality, annotation coverage,
name verb-prefix, parameter count, return-type presence,
not-deprecated, re-export at top level, and uniqueness against
higher-scored peers. The full breakdown lives in
[selector.py](src/pip_skill/selector.py).

- Top-level functions, instance methods of public classes, and class
  constructors are all candidates, so canonical patterns like
  `requests.Session().get()` and `boto3.client('s3').list_buckets()`
  get the same scoring treatment as module-level functions
- Near-identical variants (same name shape, same params) are
  deduplicated so the skill doesn't waste tokens on aliases
- Destructive verbs (`delete`, `drop`, `terminate`, `kill`, `revoke`,
  `cancel`, `unlink`, `purge`, `wipe`, `uninstall`, ...) automatically
  earn a `[CAUTION]` callout in the generated SKILL.md so Claude
  confirms before calling

### Optional: LLM-assisted curation (`--select`)

```bash
ANTHROPIC_API_KEY=... pip-skill convert boto3 --select
```

Sends the top heuristic candidates to Claude for re-ranking. Useful for
large SDKs (boto3, stripe) where tier-2 callables look identical to the
scorer. Override the model via `PIP_SKILL_MODEL=claude-opus-4-7`.
Defaults to a current GA Sonnet. Pair with `--deterministic` to fix
`temperature=0` for reproducible curation.

### Package tier detection

`pip-skill info` reports a tier label so you know what to expect from
the generated skill. For dynamic packages (Tier 3), the AI is told to
be more defensive about types in the generated CONTEXT.md.

| Tier | Criteria | Example |
|------|----------|---------|
| 1 | Annotation coverage ≥ 70% | httpx, pydantic |
| 2 | Annotation coverage < 70% | requests, click |
| 3 | Lazy imports OR stateful classes, AND coverage < 50% | boto3, sqlalchemy |

Decision rule (from [introspect.py](src/pip_skill/introspect.py)): a
package lands in Tier 3 only when both conditions hold: runtime
dynamism (module-level `__getattr__` or a public class with >3
non-init methods) *and* annotation coverage under 50%. Otherwise
coverage alone decides between Tier 1 (≥70%) and Tier 2.

### Live-by-version

`pip-skill --version` is git-tag derived (via `hatch-vcs`) and stamped
into every generated `plugin.json` as `generatedBy` and `generatedAt`.
For citable / reproducible bundles, use `--deterministic` (see below).

### Validate the bundle

```bash
pip-skill validate ./my-skill
```

Lightweight structural check (plugin.json present, SKILL.md present,
heading line count under the 500-line spec limit). For functional
validation use `pip-skill test`.

### Reproducible mode (`--deterministic`)

```bash
pip-skill convert requests --deterministic
sha256sum -c MANIFEST.sha256
```

Pins the `generatedAt` timestamp, sorts module traversal, forces
`temperature=0` on `--select`, and emits a `MANIFEST.sha256` covering
every file in the bundle. Two runs against the same package version
with the same pip-skill version produce identical bytes. Required when
citing a generated skill in a paper or pinning it as an eval baseline.
See [RESEARCH.md](RESEARCH.md) for the methodology.

### Measure tool-call accuracy (`pip-skill eval`)

```bash
# Offline: does the manifest contain the expected tool? No model call.
pip-skill eval ./requests examples/eval/requests.jsonl

# Score against a live model via your existing Claude Code session.
# No API key required: `claude -p` runs under your subscription.
pip-skill eval ./requests examples/eval/requests.jsonl \
    --conditions coverage,no-skill,skill
```

Runs a JSONL eval set of `{task, expected_qualname}` items against the
generated bundle. The `coverage` condition is offline. The `no-skill`
and `skill` conditions ask Claude to emit a Python call with and
without the generated SKILL.md, then judge AST-equivalence (the same
metric BFCL uses:
[gorilla.cs.berkeley.edu/leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)).

**Measured lift (claude-cli backend, n=10 per package, May 2026):**

| Package | Model | no-skill | skill | Lift |
|---|---|---|---|---|
| [`httpx`](examples/eval/httpx.jsonl) 0.28 (well-annotated, model knows it) | Sonnet 4.5 | 10/10 | 10/10 | ceiling |
| [`requests`](examples/eval/requests.jsonl) 2.34 (canonical HTTP client) | Sonnet 4.5 | 9/10 | **10/10** | +10pp |
| [`polars`](examples/eval/polars.jsonl) 1.41 (less-canonical tools) | Sonnet 4.5 | 5/10 | **8/10** | +30pp |
| [`polars`](examples/eval/polars.jsonl) 1.41 | Haiku 4.5 | 6/10 | **10/10** | +40pp |

Three reproducible findings ([full writeup](RESEARCH.md#first-measurements-may-2026)):

1. **Lift inversely scales with model prior.** Skill adds ~0pp on
   packages the model already nails, +30pp on packages where the
   heuristic surfaces non-obvious tools.
2. **Smaller models benefit more.** Haiku + pip-skill on polars
   matched perfect; Sonnet without it landed at 50%.
3. **More tools is not better.** Doubling the menu from 20 to 40 on
   polars produced zero improvement — N=20 (the default) was the
   sweet spot in a [max_tools sweep](scripts/tool_count_sweep.py).

Reproduce any of these with `pip-skill eval ./<bundle>
examples/eval/<pkg>.jsonl --conditions coverage,no-skill,skill
--backend claude-cli`.

**Backends.** Model conditions auto-pick the simplest path that works:

| Backend | Auth | Reproducible | When auto picks it |
|---|---|---|---|
| `claude-cli` | Your Claude Code session | No (CLI doesn't expose `temperature`) | When `claude` is on PATH and no API key is set |
| `api` | `ANTHROPIC_API_KEY` + `pip-skill[llm]` | Yes (`temperature=0`) | When `ANTHROPIC_API_KEY` is set |

Force with `--backend claude-cli` (zero friction, recommended for
local checks) or `--backend api` (paper-grade reproducibility).

### Python API

For notebooks, eval harnesses, and CI jobs:

```python
from pip_skill import generate_skill

bundle = generate_skill("requests", deterministic=True)
print(bundle.tool_count, bundle.tool_names[:3])
# 20 ['requests.get', 'requests.post', 'requests.put']
print(bundle.manifest_path.read_text().splitlines()[0])
# 8e3f...  .claude-plugin/plugin.json
```

`SkillBundle` exposes the introspected `PackageInfo`, the selected
`ToolSchema` list, the on-disk paths, and (in deterministic mode) the
SHA-256 manifest path. See [`api.py`](src/pip_skill/api.py) for the
full surface.

## CLI reference

### `pip-skill convert <package>`

Generate a skill from an installed package.

```
Options:
  --mcp                Generate MCP server alongside SKILL.md
  --output DIR         Output directory (default: ./{package-name})
  --max-tools N        Maximum functions to include (default: 20)
  --format FORMAT      Output format: claude (default), cursor, windsurf, opencode
  --include PATTERN    Include functions matching glob pattern
  --exclude PATTERN    Exclude functions matching glob pattern
  --select             Use Claude to refine the heuristic selection
                       (requires ANTHROPIC_API_KEY and pip-skill[llm])
  --install            After generating, install the skill into the AI tool's
                       directory (~/.claude/plugins/, .cursor/rules/, etc.)
  --deterministic      Fixed timestamp, sorted traversal, MANIFEST.sha256
                       (use for citable / reproducible bundles)
  --dry-run            Preview without writing files
  --verbose            Show scoring breakdown
  --force              Overwrite existing output (cleans the dir first)
```

### `pip-skill batch <packages|requirements.txt>`

Convert multiple packages in parallel.

```
Options:
  --workers N          Parallel worker threads (default: 4)
  --output-dir DIR     Base directory (default: cwd)
  --format FORMAT      Output format
  --mcp                Also generate MCP servers
  --force              Overwrite per-package output dirs
```

### `pip-skill info <package>`

Show package metadata and API surface summary.

### `pip-skill diff <plugin-dir>`

Compare a generated skill against the currently installed package
version. Reports added/removed function names. Reads the structured
`tools` manifest from `.claude-plugin/plugin.json`.

### `pip-skill test <plugin-dir>`

Verify every function in the skill is still importable in the current
Python environment. Use after a dependency upgrade to catch stale
skills.

### `pip-skill validate <plugin-dir>`

Lightweight structural check (`plugin.json` exists, `SKILL.md` exists,
under the 500-line limit). For functional checks, use `test`.

### `pip-skill build <package>`

Interactive TUI builder (requires `pip-skill[tui]`).

### `pip-skill eval <plugin-dir> <eval-file.jsonl>`

Score tool-call accuracy on a JSONL eval set. Conditions are
`coverage` (offline, in-manifest check), `no-skill` (Claude with no
spec, baseline), and `skill` (Claude with the SKILL.md prepended).
Pass-rates are emitted as a table or as JSON for CI consumption. See
[RESEARCH.md](RESEARCH.md) for methodology.

### `pip-skill search [query]` / `pip-skill install <package>`

Browse and install pre-built skills from the registry. Optional; the
common path is `pip-skill convert` against a locally installed package.

## Supported packages

pip-skill works with any installed Python package. It handles:

- Fully annotated APIs (Tier 1): httpx, pydantic, fastapi
- Partially annotated APIs (Tier 2): requests, click, flask
- Stateful / dynamic APIs (Tier 3): boto3, sqlalchemy, stripe
- C extensions: numpy, pandas (limited signature info)
- Pydantic v2 models: auto-detected, fields extracted from `model_fields`
- `Annotated[X, Field(description=...)]`: descriptions surfaced into JSON Schema
- Dataclasses: auto-detected; fields surfaced via the `__init__` signature
- Lazy imports via module-level `__getattr__`: detected (pushes the
  package into Tier 3 so the generated CONTEXT.md tells Claude to be
  defensive about attribute resolution)
- `*args` / `**kwargs`: preserved as synthetic `args` / `kwargs` schema properties

## Real-world examples

The recipe is identical for every package: `pip install <pkg> && uvx
pip-skill convert <pkg> --install`, then start a Claude Code session
and use the package by name. The table below lists capabilities you
get on the next session; the worked examples that follow show one
prompt per category.

| Package | What Claude gains | Example prompt |
|---|---|---|
| `Pillow` | Resize, crop, rotate, watermark, convert formats, filter, composite | "Resize all JPEGs in this folder to 1200px wide and add a 'CONFIDENTIAL' watermark" |
| `openpyxl` | Real `.xlsx` with formulas, merged cells, charts, conditional formatting | "Build a sales report with a pivot-style summary sheet and SUM formulas in the totals row" |
| `boto3` | S3, Lambda, EC2, CloudWatch, SQS, DynamoDB with correct types from the installed SDK | "List all S3 buckets with their sizes and move archive-bucket objects older than 90 days to Glacier" |
| `pytesseract` | OCR on screenshots, receipts, business cards | "Extract line items and totals from these receipt photos into a spreadsheet" |
| `paramiko` | SSH + SFTP, run commands, transfer files | "SSH into each server in this list and alert me to any partition above 80%" |
| `pdfplumber` | Tables, bounding boxes, character-level positions from PDFs | "Pull the invoice table from each PDF and consolidate into one spreadsheet" |
| `stripe` | Customers, subscriptions, refunds, invoices, products | "Find subscriptions paused >30 days, send a 20% reactivation coupon, log results" |
| `cryptography` | Fernet, RSA, X.509, HMAC, password hashing | "Encrypt all .env files with a passphrase, write to .env.enc, delete originals" |
| `pydub` | Slice, normalize, overlay, format-convert audio | "Split this podcast on >2s silence, normalize to -14 LUFS, export as MP3s" |
| `twilio` | SMS, WhatsApp, voice, phone lookup | "Text everyone on this list that their appointment is confirmed tomorrow" |
| `reportlab` | PDFs with tables, charts, embedded images, custom fonts | "Produce a PDF invoice from this JSON with logo, itemized table, tax calc, footer" |
| `pyarrow` | Parquet, Arrow, columnar queries on datasets too large for pandas | "Read this 4GB Parquet, filter `revenue > 10000 AND region == 'APAC'`, export to CSV" |

Each row was produced by one command against the installed package on
the author's laptop. Three worked end-to-end walkthroughs (anthropic
SDK, databricks-sdk, google-cloud-bigquery) live in
[EXAMPLES.md](EXAMPLES.md).

## FAQ

**Why not just paste the docs into context?**
Token limits. The boto3 docs are 50MB+. pip-skill selects the top 20
functions by usefulness score and fits everything in ~4,000 tokens with
correct types and schemas.

**Why not rely on the LLM's built-in knowledge?**
It works for popular packages like `requests`. It fails for anything
updated after the training cutoff, niche packages, or complex
signatures. pip-skill reads the actual installed API at runtime, so
hallucination is impossible. CloudAPIBench
([arXiv:2407.09726](https://arxiv.org/abs/2407.09726)) quantifies the
training-cutoff gap on low-frequency APIs.

**Why not just use MCP servers?**
pip-skill generates those too (`--mcp`). But skill-only mode is
lighter: no server process, no port, no config. The AI reads the
SKILL.md and writes correct Python directly.

**What about packages with C extensions?**
Works with numpy, pandas, etc. Signature info is limited for C-level
functions, but pip-skill falls back to docstring parsing and marks the
skill as Tier 3 so the AI knows to be cautious.

**Does `--select` change the output a lot?**
For tier-1 packages (httpx, pydantic) the heuristic and the LLM tend
to agree on most of the top-20. The win is on dynamic SDKs (boto3,
stripe) where the LLM is better at picking *use-case relevant*
functions over *highest-scored* functions. Quantitative comparison is
on the roadmap (see [RESEARCH.md](RESEARCH.md), Experiment 1).

**Where does `--install` put things?**
Claude format -> `~/.claude/plugins/{normalized-name}/`. Cursor ->
`.cursor/rules/{name}.mdc`. Windsurf -> `.windsurf/rules/{name}.md`.
OpenCode -> `./AGENTS.md`. Names are normalized so Pillow -> pillow,
PyYAML -> pyyaml, discord.py -> discord-py, regardless of host
filesystem case sensitivity.

**Can I use this in CI?**
Yes. The repo ships [`action.yml`](action.yml) (a composite GitHub
Action wrapping `astral-sh/setup-uv` and `pip-skill batch`) and
[`.pre-commit-hooks.yaml`](.pre-commit-hooks.yaml) exposing
`pip-skill-sync` and `pip-skill-test` hooks. Pin them at a tagged
release once you're ready to roll out.

**Is the generated output reproducible?**
With `--deterministic`, yes. The bundle gets a fixed `generatedAt`
timestamp, deterministic module traversal, `temperature=0` on
`--select`, and a `MANIFEST.sha256` file covering every emitted byte.
Two runs against the same package version with the same pip-skill
version produce identical bytes. Use this whenever you cite a bundle
in a paper or pin one as an eval baseline.

## Research

pip-skill's design follows directly from two threads in the
function-calling literature:

1. Reading the live API removes the train/serve documentation skew
   that Gorilla and CloudAPIBench measure (no hallucinated APIs).
2. Compressing signature + docstring into a concise tool spec
   produces EASYTOOL-style instructions at lower token cost than
   pasted documentation.

[RESEARCH.md](RESEARCH.md) collects the full reading list (Gorilla,
BFCL, ToolLLM, API-Bank, EasyTool, ToolACE, MetaTool, RestBench,
AgentBench, InjecAgent, MCPTox, MCP Safety Audit, CloudAPIBench), the
roadmap experiments (BFCL submission, drift-cliff measurement, the
100-package real-API corpus), and the BibTeX entry. The `pip-skill
eval` harness implements the same AST-equivalence metric BFCL uses.

If you publish results computed from pip-skill output, regenerate with
`--deterministic` and cite the version stamped in `plugin.json`
(`generatedBy`). The `MANIFEST.sha256` file lets reviewers verify the
bundle byte-for-byte.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and
guidelines.

## License

MIT, see [LICENSE](LICENSE).

---

<p align="center">Built by <a href="https://github.com/xmpuspus">Xavier Puspus</a></p>
