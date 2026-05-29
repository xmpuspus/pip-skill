<h1 align="center">pip-skill</h1>
<p align="center"><strong>AI skills built from the installed Python API. One command. Offline. No fabricated function names.</strong></p>
<p align="center">Generates Claude Code, Cursor, Windsurf, OpenCode, and MCP server skills directly from <code>inspect.signature</code>. No docs scraping, no API key, no LLM in the loop.</p>

<p align="center">
  <a href="https://github.com/xmpuspus/pip-skill/stargazers"><img src="https://img.shields.io/github/stars/xmpuspus/pip-skill" alt="GitHub stars"></a>
  <a href="https://pypi.org/project/pip-skill/"><img src="https://img.shields.io/pypi/v/pip-skill.svg?cacheSeconds=300" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg" alt="Python 3.11/3.12/3.13">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey.svg" alt="Linux | macOS | Windows">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/offline-yes-success.svg" alt="Offline by default">
  <img src="https://img.shields.io/badge/eval-%2B20pp%20Sonnet%20%2F%20%2B22pp%20Haiku%20(blind%2C%209%20pkgs)-brightgreen.svg" alt="Eval: +20pp Sonnet / +22pp Haiku across 9 packages (blind)">
</p>

<p align="center"><img src="pip-skill-demo.gif" alt="pip-skill demo: one command turns requests into a Claude skill" width="900"></p>

```bash
uvx pip-skill convert requests --install
```

That is the entire loop. One command, no install, the skill bundle lands in
`~/.claude/plugins/requests/` and Claude can call requests with correct
types on the next session.

> **Note:** `convert` imports the target package (its top-level code
> runs) and walks every submodule. Only convert packages you would
> trust to `pip install`. See [Trust model](#trust-model).

Prefer a permanent install? `pip install pip-skill` and use the
`pip-skill` binary directly.

## Does it actually help the AI?

We measured it. See [`RESEARCH.md`](RESEARCH.md) for methodology and
the per-package breakdown.

### 9-package blind eval (May 2026)

Items re-authored from each package's docs/README **without
consulting the generated SKILL.md**, so the eval measures what an
end-user actually sees on a freshly generated skill they did not help
shape.

| Model | Packages | Items | no-skill | **skill** | Lift |
|---|---|---|---|---|---|
| Sonnet 4.5 | 9 | 90 | 61/90 (67.8%) | **79/90 (87.8%)** | **+20.0pp** |
| Haiku 4.5  | 9 | 90 | 62/90 (68.9%) | **82/90 (91.1%)** | **+22.2pp** |

Per-package on Sonnet (blind): mcp `+80pp`, returns / fastmcp `+60pp`
each, msgspec / pendulum `+10pp`, h3 / toolz at ceiling, arrow /
more_itertools `-20pp`. The two regressions share a pattern: the
skill surfaces low-level alternatives like
`arrow.parser.DateTimeParser.parse_iso` over `arrow.get` and
`more_itertools.Stats` over `chunked`, and the model picks the
specific one over the canonical. Coverage gap is the bigger story:
blind authoring shows `h3` 1/10 and `more_itertools` 1/10 in the
manifest because the selector's annotation-bias rewards obscure
well-typed helpers over Cython bindings and README-canonical names.
Full per-package and per-model table in [`eval-results/blind/REPORT.md`](eval-results/blind/REPORT.md).

**Cross-model headline:** Haiku + skill (82/90, 91.1%) beats
Sonnet alone (61/90, 67.8%) by 23pp. The smaller model with
the skill outperforms the larger model without.

### v0.1 baseline (3 packages, May 2026)

| Package | Tier | Model | Items | no-skill | **skill** | Lift |
|---|---|---|---|---|---|---|
| [`httpx`](examples/eval/httpx.jsonl) 0.28 | 1 | Sonnet 4.5 | 10 | 10/10 | **10/10** | ceiling |
| [`requests`](examples/eval/requests.jsonl) 2.34 | 2 | Sonnet 4.5 | 10 | 9/10 | **10/10** | +10pp |
| [`polars`](examples/eval/polars.jsonl) 1.41 | 3 | Sonnet 4.5 | **30** | 15/30 | **27/30** | **+40pp** |
| [`polars`](examples/eval/polars.jsonl) 1.41 | 3 | Haiku 4.5 | **30** | 16/30 | **29/30** | **+43pp** |

Each row: `pip-skill eval ./<bundle> examples/eval/<pkg>.jsonl
--conditions coverage,no-skill,skill --backend claude-cli`. The
`skill` condition prepends the generated SKILL.md to Claude's system
prompt; the `no-skill` condition gives only a static-analyzer
instruction. Judging is BFCL-style AST-equivalence on the first
`<package>.<fn>(...)` call. Backend is `claude -p` against your
existing Claude Code session, so the runs above cost zero API tokens.

**Pattern.** pip-skill's value scales inversely with how well the
model already knows the package. On stable canonical APIs (httpx,
requests, arrow) the model is at or near ceiling without help. On
post-cutoff or non-obvious-top-level packages (mcp, fastmcp,
more_itertools, polars's `cum_count` / `concat_arr` / `coalesce`),
the skill closes most of the gap, `+22pp` to `+80pp` depending on
how unfamiliar the surface is.

## Quick start

### One-shot conversion (no install)

```bash
uvx pip-skill convert httpx --install
```

The bundle lands in `~/.claude/plugins/httpx/`. Claude Code
auto-discovers it on the next session. For Cursor, Windsurf, or
OpenCode, add `--format cursor` (or `windsurf` / `opencode`) and
`--install` writes to the matching project-local config.

### Inspect a package first

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

### Verify a skill is still in sync after `pip install --upgrade`

```bash
pip-skill test ./httpx
```

```
Testing httpx skill (v0.28.1)...
  [PASS] httpx.get
  [PASS] httpx.request
  [PASS] httpx.URL
  ...
Result: 18/18 passed
```

`test` reads the structured `tools` manifest from `plugin.json` and
verifies every entry is still importable in the current Python
environment.

### See what changed

```bash
pip-skill diff ./httpx
```

<p align="center"><img src="demos/diff.gif" alt="pip-skill diff output" width="720"></p>

Added/removed function names print one per line. Pipe into a
regeneration hook to keep skills current automatically.

### Batch the whole requirements.txt

```bash
pip-skill batch requirements.txt --workers 4
```

<p align="center"><img src="demos/batch.gif" alt="pip-skill batch conversion in parallel" width="720"></p>

Worker output is serialized via a print-lock so per-package status
lines never interleave. Failed packages return `[FAIL] <pkg>:
<reason>` on stderr and a non-zero exit code.

## What you get

A self-contained Claude Code plugin, ready to drop into `~/.claude/plugins/`:

```
requests/
├── .claude-plugin/
│   └── plugin.json          # structured manifest: tools, qualnames, params, version
├── skills/requests/
│   ├── SKILL.md             # what Claude reads (~5k tokens; larger for big SDKs)
│   ├── CONTEXT.md           # agent guidelines for this package
│   └── references/
│       └── api-reference.md # full schemas, signatures, JSON Schema per tool
└── MANIFEST.sha256          # only with --deterministic; covers every file above
```

The `tools` array in `plugin.json` is the canonical record of what
the skill exposes. `pip-skill diff` and `pip-skill test` read it
directly, which is why version drift on a 200-package monorepo is
detectable in seconds and why a stale skill is impossible to silently
ship.

## Multi-format output

Generate skills for any major AI coding assistant from the same
introspection pass:

| Format | Flag | Output |
|--------|------|--------|
| Claude Code | `--format claude` (default) | `SKILL.md` + `plugin.json` + `CONTEXT.md` + `api-reference.md` |
| Cursor | `--format cursor` | `.cursorrules` |
| Windsurf | `--format windsurf` | `.windsurfrules` |
| OpenCode | `--format opencode` | `AGENTS.md` |
| MCP server | `--mcp` | FastMCP Python server, identifier-validated |

The generated `SKILL.md` follows the open
[Agent Skills](https://agentskills.io) standard, so it works with
many AI coding tools that consume the spec: Claude Code, Cursor,
Windsurf, OpenCode, GitHub Copilot, VS Code Copilot, OpenAI Codex,
Gemini CLI, JetBrains Junie, Goose, Roo Code, Databricks Genie Code,
and others.

## Real-world examples

Recipe is identical for every package: `pip install <pkg> && uvx
pip-skill convert <pkg> --install`, then start a Claude Code session
and use the package by name. The table below lists capabilities you
gain on the next session; one prompt per row is enough to verify.

| Package | What Claude gains | Example prompt |
|---|---|---|
| `Pillow` | Resize, crop, rotate, watermark, convert formats, filter, composite | "Resize all JPEGs in this folder to 1200px wide and add a 'CONFIDENTIAL' watermark" |
| `openpyxl` | Real `.xlsx` with formulas, merged cells, charts, conditional formatting | "Build a sales report with a pivot-style summary sheet and SUM formulas in the totals row" |
| `boto3` | S3, Lambda, EC2, CloudWatch, SQS, DynamoDB with types from the installed SDK | "List all S3 buckets with their sizes and move archive-bucket objects older than 90 days to Glacier" |
| `pytesseract` | OCR on screenshots, receipts, business cards | "Extract line items and totals from these receipt photos into a spreadsheet" |
| `paramiko` | SSH + SFTP, run commands, transfer files | "SSH into each server in this list and alert me to any partition above 80%" |
| `pdfplumber` | Tables, bounding boxes, character-level positions from PDFs | "Pull the invoice table from each PDF and consolidate into one spreadsheet" |
| `stripe` | Customers, subscriptions, refunds, invoices, products | "Find subscriptions paused >30 days, send a 20% reactivation coupon, log results" |
| `cryptography` | Fernet, RSA, X.509, HMAC, password hashing | "Encrypt all .env files with a passphrase, write to .env.enc, delete originals" |
| `pydub` | Slice, normalize, overlay, format-convert audio | "Split this podcast on >2s silence, normalize to -14 LUFS, export as MP3s" |
| `twilio` | SMS, WhatsApp, voice, phone lookup | "Text everyone on this list that their appointment is confirmed tomorrow" |
| `reportlab` | PDFs with tables, charts, embedded images, custom fonts | "Produce a PDF invoice from this JSON with logo, itemized table, tax calc, footer" |
| `pyarrow` | Parquet, Arrow, columnar queries on datasets too large for pandas | "Read this 4GB Parquet, filter `revenue > 10000 AND region == 'APAC'`, export to CSV" |

Three deeper walkthroughs (anthropic SDK, databricks-sdk,
google-cloud-bigquery) live in [`EXAMPLES.md`](EXAMPLES.md).

## How it works

1. **`importlib.import_module(...)` + `pkgutil.walk_packages(...)`**
   walk every submodule. Import errors are caught at the
   `BaseException` boundary so packages that raise
   `pytest.importorskip` (which inherits from `BaseException`) do not
   crash introspection.
2. **`inspect.signature(eval_str=True)`** with a graceful fallback
   resolves type annotations even on packages like httpx whose
   forward refs reference symbols not exported from the defining
   module.
3. **`typing.get_type_hints()`** walks `from __future__ import
   annotations` and `Annotated[...]` wrappers; the metadata layer
   extracts pydantic `Field(description=...)` and similar.
4. **`docstring-parser`** extracts parameter descriptions from
   Google / NumPy / reST docstrings.
5. **`pydantic.create_model()`** + **`model.model_json_schema()`**
   generate JSON Schema from type annotations; a manual schema
   builder kicks in when annotations are partial.
6. **A 10-signal scoring algorithm** picks the most useful candidates
   (module depth, `__all__` membership, docstring quality, annotation
   coverage, name verb-prefix, parameter count, return-type presence,
   not-deprecated, re-export at top level, and uniqueness against
   higher-scored peers). Default cap is 20 tools per skill, which our
   [tool-count sweep](scripts/tool_count_sweep.py) shows is the sweet
   spot for polars: at N=40 accuracy stays at 80%, at N=10 coverage
   drops to 50%.
7. **Top-level functions, instance methods of public classes, and
   class constructors are all candidates,** so canonical patterns
   like `requests.Session().get()` and
   `boto3.client('s3').list_buckets()` get scored the same way as
   module-level functions.
8. **Destructive verbs** (`delete`, `drop`, `terminate`, `kill`,
   `revoke`, `cancel`, `unlink`, `purge`, `wipe`, `uninstall`, ...)
   automatically earn a `[CAUTION]` callout in the generated SKILL.md
   so Claude confirms before calling.

Source: [`introspect.py`](src/pip_skill/introspect.py),
[`selector.py`](src/pip_skill/selector.py),
[`schema.py`](src/pip_skill/schema.py),
[`generator.py`](src/pip_skill/generator.py).

## Reproducibility (`--deterministic`)

```bash
pip-skill convert requests --deterministic
sha256sum -c MANIFEST.sha256
```

Pins the `generatedAt` timestamp in `plugin.json`, sorts the module
traversal so OS filesystem case-sensitivity does not change picks,
forces `temperature=0` on `--select`, and emits a `MANIFEST.sha256`
covering every byte in the bundle. Two runs against the same package
version with the same pip-skill version produce bit-identical bytes.
Use this whenever you cite a bundle in a paper or pin one as an eval
baseline.

## Measuring a skill (`pip-skill eval`)

```bash
# Offline: is the expected tool in the bundle? No model call.
pip-skill eval ./requests examples/eval/requests.jsonl

# Score against a live model via your existing Claude Code session.
# No API key required: `claude -p` runs under your subscription.
pip-skill eval ./requests examples/eval/requests.jsonl \
    --conditions coverage,no-skill,skill
```

Runs a JSONL eval set of `{task, expected_qualname}` items against
the generated bundle. The `coverage` condition is offline. The
`no-skill` and `skill` conditions ask Claude to emit a Python call
with and without the generated SKILL.md, then judge AST-equivalence
on the first `<package>.<fn>(...)` call. Same metric as the
[Berkeley Function-Calling Leaderboard
(BFCL)](https://gorilla.cs.berkeley.edu/leaderboard.html).

The extractor accepts common aliases (`pl` for polars, `pd` for
pandas, `np` for numpy, etc.) and normalises them back to the
canonical name. Eval sets ship for `requests`, `httpx`, and `polars`
under [`examples/eval/`](examples/eval/); write your own as JSONL
with one `{task, expected_qualname}` per line.

**Backends** (no API key required for the default):

| Backend | Auth | Reproducible | When auto picks it |
|---|---|---|---|
| `claude-cli` | Your Claude Code session via `claude -p` | No (CLI does not expose `temperature`) | When `claude` is on PATH and no API key is set |
| `api` | `ANTHROPIC_API_KEY` + the `[llm]` extra (Anthropic SDK) | Yes (`temperature=0`) | When `ANTHROPIC_API_KEY` is set |

Force with `--backend claude-cli` (zero friction, recommended for
local checks) or `--backend api` (paper-grade reproducibility).

## Python API

For notebooks, eval harnesses, and CI jobs:

```python
from pip_skill import generate_skill

bundle = generate_skill("requests", deterministic=True)
print(bundle.tool_count, bundle.tool_names[:3])
# 20 ['requests.get', 'requests.post', 'requests.put']

print(bundle.manifest_path.read_text().splitlines()[0])
# 8e3f...  .claude-plugin/plugin.json

# Same call, but route through Claude for re-ranking on a sprawling SDK.
bundle = generate_skill("boto3", select=True, deterministic=True)
```

`SkillBundle` exposes the introspected `PackageInfo`, the selected
`ToolSchema` list, the on-disk paths, and (in deterministic mode) the
SHA-256 manifest path. Full surface in
[`src/pip_skill/api.py`](src/pip_skill/api.py).

## vs other skill generators

| | pip-skill | [skill-seekers](https://pypi.org/project/skill-seekers/) | [skillnet-ai](https://pypi.org/project/skillnet-ai/) | [skills-cli](https://pypi.org/project/skills-cli/) |
|---|---|---|---|---|
| **What it does** | Converts installed pip packages into skills | Converts docs, repos, PDFs, videos into skills | Create, evaluate, and connect skills from various sources | Scaffold, validate, and manage existing skills |
| **Input source** | Installed Python package (runtime introspection) | 17 source types (websites, repos, PDFs, videos, wikis) | Conversation logs, repos, documents, prompts | Manual authoring |
| **Type accuracy** | Exact (reads `inspect.signature()` at runtime) | Depends on documentation quality | Depends on source quality | N/A (manual) |
| **API key required** | No (offline by default) | Optional (for AI enhancement) | Yes (for creation/evaluation) | No |
| **Output formats** | Claude, Cursor, Windsurf, OpenCode, MCP | Claude, Gemini, OpenAI, LangChain, 12+ formats | SKILL.md | SKILL.md |
| **Drift detection** | `diff` + `test` against structured manifest | none | none | Spec validation |
| **Reproducibility** | `--deterministic` mode + `MANIFEST.sha256` | none | none | none |
| **Evaluation** | `pip-skill eval` (AST-equivalence, BFCL-style) | none | Evaluation framework | none |
| **Best for** | Python packages you use in code | Documentation and knowledge bases | Discovering pre-built skills | Managing and distributing skills |

These tools are complementary: pip-skill generates skills from
installed Python APIs with exact type signatures; the others work
from documentation or pre-built repositories.

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
  --max-tools N        Maximum tools per skill (default: 20)
  --include PATTERN    Include functions matching glob pattern
  --exclude PATTERN    Exclude functions matching glob pattern
  --force              Overwrite per-package output dirs
```

### `pip-skill info <package>`

Show package metadata + API surface summary.

### `pip-skill diff <plugin-dir>`

Compare a generated skill against the currently installed package
version. Reports added/removed function names from the structured
`tools` manifest.

### `pip-skill test <plugin-dir>`

Verify every function in the skill is still importable in the
current Python environment. Use after a dependency upgrade to catch
stale skills before Claude does.

### `pip-skill validate <plugin-dir>`

Lightweight structural check: `plugin.json` exists, `SKILL.md`
exists and is under the 500-line spec limit. For functional checks,
use `test`.

### `pip-skill eval <plugin-dir> <eval-file.jsonl>`

Score tool-call accuracy on a JSONL eval set. Conditions are
`coverage` (offline, in-manifest check), `no-skill` (Claude with no
spec, baseline), `skill` (Claude with the SKILL.md prepended).
Pass-rates emit as a table or JSON for CI consumption. Methodology
in [`RESEARCH.md`](RESEARCH.md).

### `pip-skill build <package>`

Interactive TUI builder. Requires `pip-skill[tui]`.

### `pip-skill search [query]` / `pip-skill install <package>`

Browse and install pre-built skills from the registry. Optional; the
common path is `pip-skill convert` against a locally installed
package.

## CI integration

[`action.yml`](action.yml) is a composite GitHub Action that wraps
`astral-sh/setup-uv` and `pip-skill batch`. Use it in workflows to
keep generated skills current with `requirements.txt`:

```yaml
- uses: xmpuspus/pip-skill@v0.1.0
  with:
    packages: requirements.txt
    output-dir: ./skills
    workers: 4
```

[`.pre-commit-hooks.yaml`](.pre-commit-hooks.yaml) exposes
`pip-skill-sync` and `pip-skill-test` hooks for pre-commit users.

## Trust model

`pip-skill convert` does two things that affect security:

1. **Imports the target package.** `inspect.signature` requires a
   real Python module, so `importlib.import_module(...)` runs the
   package's top-level code. The trust requirement is the same as
   `pip install` of that package: only run pip-skill against
   packages you would already have in your venv.

2. **Embeds the package's docstrings into a SKILL.md the AI loads as
   authoritative skill instructions.** A malicious package's
   docstring could try prompt injection via
   `<system>...</system>`-style tags. pip-skill neutralizes the LLM
   control-tag vocabulary in every prose interpolation, breaks
   standalone `---` lines that would corrupt YAML frontmatter, and
   validates Python identifiers before emitting them into the
   generated MCP server. The threat model engages with InjecAgent
   ([arXiv:2403.02691](https://arxiv.org/abs/2403.02691)) and MCPTox
   ([arXiv:2508.14925](https://arxiv.org/pdf/2508.14925)). Full list
   in [`SECURITY.md`](SECURITY.md).

## Research

pip-skill's design follows directly from two threads in the
function-calling literature:

1. **Reading the live API removes the train/serve documentation
   skew** that Gorilla and CloudAPIBench measure (no hallucinated
   APIs).
2. **Compressing signature + docstring into a concise tool spec**
   produces EASYTOOL-style instructions at lower token cost than
   pasted documentation.

[`RESEARCH.md`](RESEARCH.md) collects 16 citations (Gorilla, BFCL,
ToolLLM, API-Bank, EasyTool, ToolACE, MetaTool, RestBench,
AgentBench, InjecAgent, MCPTox, MCP Safety Audit, CloudAPIBench,
Robustness of Agentic Function Calling, Agent Skills spec, MCP
spec), the four measured findings from this release, the roadmap
experiments (BFCL submission, drift-cliff measurement, 100-package
real-API corpus), and a BibTeX entry.

If you publish results computed from pip-skill output, regenerate
with `--deterministic` and cite the version stamped in `plugin.json`
(`generatedBy`). The `MANIFEST.sha256` file lets reviewers verify
the bundle byte-for-byte.

## FAQ

**Why not just paste the docs into context?**
Token limits. The boto3 docs are 50MB+. pip-skill selects the top
20 functions by usefulness score and fits everything in ~4,000
tokens with correct types and JSON Schema.

**Why not rely on the LLM's built-in knowledge?**
It works for popular packages like `requests` (we measured 9/10
no-skill on Sonnet). It fails on anything updated after the
training cutoff, niche packages, and complex signatures. pip-skill
reads the actual installed API at runtime, so function names and
type signatures come from `inspect.signature`, not the model.
CloudAPIBench
([arXiv:2407.09726](https://arxiv.org/abs/2407.09726)) quantifies
the training-cutoff gap on low-frequency APIs.

**Why not just use MCP servers?**
pip-skill generates those too (`--mcp`). But skill-only mode is
lighter: no server process, no port, no config. The AI reads the
SKILL.md and writes correct Python directly.

**What about packages with C extensions?**
Works with numpy, pandas, etc. Signature info is limited for C-level
functions, but pip-skill falls back to docstring parsing and marks
the skill as Tier 3 so the AI knows to be cautious.

**Does `--select` change the output a lot?**
For tier-1 packages (httpx, pydantic) the heuristic and the LLM
tend to agree on most of the top-20. The win is on dynamic SDKs
(boto3, stripe) where the LLM is better at picking *use-case
relevant* functions over *highest-scored* functions. Quantitative
comparison is on the roadmap (see
[RESEARCH.md](RESEARCH.md), Experiment 1).

**Where does `--install` put things?**
Claude format -> `~/.claude/plugins/{normalized-name}/`. Cursor ->
`.cursor/rules/{name}.mdc`. Windsurf -> `.windsurf/rules/{name}.md`.
OpenCode -> `./AGENTS.md`. Names are normalized so Pillow -> pillow,
PyYAML -> pyyaml, discord.py -> discord-py, regardless of host
filesystem case sensitivity.

**Is the generated output reproducible?**
With `--deterministic`, yes. Fixed `generatedAt`, sorted traversal,
`temperature=0` on `--select`, and a `MANIFEST.sha256` covering
every byte. Two runs against the same package version with the same
pip-skill version produce bit-identical bundles.

**Does the eval harness need an API key?**
No. The default backend (`claude-cli`) shells out to `claude -p`
under your existing Claude Code session. The `api` backend exists
for paper-grade reproducibility (`temperature=0`) and only kicks in
when `ANTHROPIC_API_KEY` is set.

**Can I use this in CI?**
Yes. See [CI integration](#ci-integration).

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
- `*args` / `**kwargs`: preserved as synthetic `args` / `kwargs`
  schema properties

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development setup and
guidelines. Re-record the demo GIFs with
`./scripts/bootstrap-demo.sh && vhs docs/demo.tape` (and
`docs/batch.tape`, `docs/diff.tape`).

## License

MIT, see [`LICENSE`](LICENSE).

---

<p align="center">Built by <a href="https://github.com/xmpuspus">Xavier Puspus</a></p>
