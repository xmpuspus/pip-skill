# Research notes

pip-skill turns a runtime-introspected Python package into a tool spec
that an LLM can call. It sits at the intersection of three active
research threads: function-calling benchmarks, tool-instruction
compression, and indirect prompt injection through tool descriptions.
This document collects the prior work it should be read against and
the experiments it should run.

If you reference pip-skill in a paper, please cite the GitHub release
([releases](https://github.com/xmpuspus/pip-skill/releases)) and link
this document so reviewers can locate the experimental scaffolding.

## How pip-skill maps onto the literature

Two design choices follow directly from existing results:

1. **Reading the installed package at runtime instead of scraping
   documentation.** Gorilla showed that LLMs hallucinate APIs that no
   longer exist; CloudAPIBench quantified the recall gap for
   newly-released SDK versions. pip-skill's runtime introspection
   removes the train/serve documentation skew entirely for any package
   the user has installed.
2. **Compressing the docstring + signature into a concise tool spec
   instead of pasting the docs into context.** EASYTOOL reports that
   concise instructions outperform full documentation at lower token
   cost. pip-skill produces an EASYTOOL-style instruction from
   `inspect.signature` and `docstring-parser` output, rather than from
   pre-existing prose documentation.

Two threads pip-skill should engage but does not yet:

3. **Function-calling evaluation.** BFCL and API-Bank give
   reproducible accuracy numbers for tool-using LLMs. pip-skill ships
   a minimal `pip-skill eval` (see below) but does not yet publish a
   BFCL submission. The harness is wired against the same
   AST-equivalence metric BFCL uses.
4. **Tool-description prompt injection.** InjecAgent and MCPTox
   demonstrate that an LLM treats a tool's `description` field as
   trusted prose. pip-skill's `sanitize_prose` filter neutralises the
   LLM control vocabulary in every prose interpolation and validates
   Python identifiers before emitting MCP server source.

## Reading list

Numbered for citation; arXiv links where they exist.

1. **Gorilla: Large Language Model Connected with Massive APIs**,
   Patil et al., NeurIPS 2024.
   [arXiv:2305.15334](https://arxiv.org/abs/2305.15334).
   The first benchmark for API hallucination; APIBench measures pass@1
   on real-world Python/Hugging Face/TensorFlow APIs.

2. **Berkeley Function-Calling Leaderboard (BFCL)**, Patil, Mao,
   Pacchiano, et al., ICML 2025.
   [Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) ·
   [OpenReview entry](https://openreview.net/forum?id=2GmDdhBdDk).
   Multi-turn / multi-step tool-use benchmark with AST-equivalence
   scoring. pip-skill's `eval` harness adopts the same metric.

3. **ToolLLM / ToolBench: Facilitating LLMs to Master 16000+
   Real-world APIs**, Qin et al., ICLR 2024.
   [arXiv:2307.16789](https://arxiv.org/abs/2307.16789).
   16k+ APIs and a synthesis pipeline; pip-skill's bundle format can
   serve as a `tool_spec` source for ToolBench-style training data.

4. **API-Bank: A Comprehensive Benchmark for Tool-Augmented LLMs**,
   Li et al., EMNLP 2023.
   [arXiv:2304.08244](https://arxiv.org/abs/2304.08244).
   73 tools, 314 dialogues; small enough to run as a CI gate.

5. **EasyTool: Enhancing LLM-based Agents with Concise Tool
   Instruction**, Yuan et al., 2024.
   [arXiv:2401.06201](https://arxiv.org/abs/2401.06201).
   Closest prior art; concise tool instructions outperform raw
   documentation at lower token cost. pip-skill should reproduce
   Table 2 with `inspect`-derived instructions instead of LLM-rewritten
   ones.

6. **ToolACE: Winning the Points of LLM Function Calling**, Liu et
   al., 2024. [arXiv:2409.00920](https://arxiv.org/abs/2409.00920).
   Synthetic 26k-API tool corpus. pip-skill can supply the real-API
   equivalent at scale (Experiment 3 below).

7. **MetaTool: Benchmark for Large Language Models to Decide Whether
   to Use Tools and Which to Use**, Huang et al., ICLR 2024.
   [arXiv:2310.03128](https://arxiv.org/abs/2310.03128).
   Tool-selection accuracy across an evolving toolbox; directly
   relevant to pip-skill's `--max-tools` selection cap.

8. **RestGPT / RestBench**, Song et al., 2023.
   [arXiv:2306.06624](https://arxiv.org/abs/2306.06624).
   Practical evaluation of an agent-on-real-API pattern; relevant for
   pip-skill skills generated against REST SDKs (stripe, twilio,
   anthropic).

9. **AgentBench: Evaluating LLMs as Agents**, Liu et al., 2023.
   [arXiv:2308.03688](https://arxiv.org/abs/2308.03688).
   Broader agent evaluation suite; tool-use is one task class.

10. **InjecAgent: Benchmarking Indirect Prompt Injections in
    Tool-Integrated LLM Agents**, Zhan et al., 2024.
    [arXiv:2403.02691](https://arxiv.org/abs/2403.02691).
    Motivates pip-skill's `sanitize_prose` filter for package-supplied
    docstrings. SECURITY.md references this paper.

11. **MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP
    Servers**, 2025.
    [arXiv:2508.14925](https://arxiv.org/pdf/2508.14925).
    Motivates pip-skill's identifier-validation gate in the MCP
    server template.

12. **MCP Safety Audit: LLMs with the Model Context Protocol Allow
    Major Security Exploits**, 2025.
    [arXiv:2504.03767](https://arxiv.org/pdf/2504.03767).
    Threat model for MCP server generation. pip-skill's emitted MCP
    server runs on localhost under the user's control and never
    executes LLM output.

13. **On Mitigating Code LLM Hallucinations with API Documentation
    (CloudAPIBench)**, Jain et al., 2024.
    [arXiv:2407.09726](https://arxiv.org/abs/2407.09726).
    Measures the low-frequency-API recall gap that pip-skill closes
    when a package was updated after the model's training cutoff.

14. **On the Robustness of Agentic Function Calling**, 2025.
    [arXiv:2504.00914](https://arxiv.org/html/2504.00914).
    Tests resilience to perturbed tool descriptions; directly relevant
    when pip-skill regenerates after a `pip install --upgrade`.

15. **Agent Skills specification**, Anthropic, 2025.
    [agentskills.io](https://agentskills.io) ·
    [Spec](https://agentskills.io/specification).
    The open standard pip-skill emits to. Used by Claude Code, Cursor,
    Windsurf, OpenCode, Gemini CLI, JetBrains Junie, Goose, and other
    Agent-Skills-compatible tools.

16. **Model Context Protocol**, Anthropic, 2024.
    [modelcontextprotocol.io](https://modelcontextprotocol.io).
    The MCP standard pip-skill targets with `--mcp`. Server emission
    follows the FastMCP decorator pattern.

## How to cite

```bibtex
@software{pip_skill,
  author = {Puspus, Xavier},
  title = {pip-skill: Hallucination-free AI skills from runtime
           Python introspection},
  url = {https://github.com/xmpuspus/pip-skill},
  year = {2026},
}
```

If you publish results computed from pip-skill output, please pin the
generator version and use `--deterministic` so reviewers can
regenerate the bundle bit-for-bit:

```bash
pip install pip-skill==0.1.0
pip-skill convert <package> --deterministic
sha256sum -c MANIFEST.sha256
```

The `MANIFEST.sha256` file produced by `--deterministic` covers every
file pip-skill writes; the `generatedBy` field in `plugin.json` records
the pip-skill version, and `sourceVersion` records the introspected
package version. A bundle is reproducible iff `(pip-skill version,
package version, --deterministic on)` are the same across runs.

## First measurements (May 2026)

Run on the author's laptop using `pip-skill eval` with the `claude-cli`
backend (Claude Code's `claude -p`, default model alias). Conditions:

- **coverage**: offline, does the bundle's `plugin.json` manifest
  include the expected qualname?
- **no-skill**: Claude with the static-analyzer system prompt only.
- **skill**: Claude with the generated SKILL.md prepended to the
  system prompt.

Judging: AST-equivalence on the first `<package>.<fn>(...)` call in
the emitted Python (the same metric BFCL uses). The extractor accepts
common aliases (`pl` for polars, `pd` for pandas, etc.) and normalizes
them back to the canonical name. Sample size is n=10 per package, so
treat every point as ±10pp; the directional signals replicate across
re-runs but absolute numbers move within that band.

### Finding 1: lift inversely scales with model prior

| Package | Tier | Eval | Items | coverage | no-skill | skill | Lift |
|---|---|---|---|---|---|---|---|
| `httpx` 0.28.1 | 1 | [httpx.jsonl](examples/eval/httpx.jsonl) | 10 | 8/10 | **10/10** | **10/10** | 0 (ceiling) |
| `requests` 2.34.2 | 2 | [requests.jsonl](examples/eval/requests.jsonl) | 10 | 10/10 | 9/10 | **10/10** | +10pp |
| `polars` 1.41.0 | 3 | [polars.jsonl](examples/eval/polars.jsonl) | **30** | 30/30 | 15/30 | **27/30** | **+40pp** |

The pattern is monotonic in model-prior strength. Sonnet 4.5 already
nails `httpx` and `requests` at near-ceiling without any spec; the
skill adds little because there is little room to add. On `polars`
with n=30 items (variance window ±5pp, tight enough to be credible),
the skill closes 80% of the no-skill gap.

Operational rule of thumb: **pip-skill's value is largest when the
package was updated after the model's training cutoff or has a
non-obvious top-level API.** For the long tail of stable, popular
PyPI packages, the model is fine on its own.

### Finding 2: model size barely changes the lift

Re-ran the 30-item polars eval with `PIP_SKILL_MODEL=haiku`:

| Model | Items | no-skill | skill | Lift |
|---|---|---|---|---|
| Sonnet 4.5 | 30 | 15/30 (50.0%) | 27/30 (90.0%) | +40pp |
| Haiku 4.5  | 30 | 16/30 (53.3%) | **29/30 (96.7%)** | **+43pp** |

At n=30 the gap between Sonnet and Haiku narrows: both close to
ceiling with skill, both around half without. The n=10 result from
an earlier run ("Haiku +40 vs Sonnet +30, Haiku reaches perfect")
overstated the model-size effect, which is what n=10 ±10pp variance
predicts.

What stays true: **the smaller model + skill matches or beats the
larger model alone**. For polars specifically, Haiku + skill (29/30)
beats Sonnet alone (15/30) by 47pp. Cost-quality argument is real
even after tightening the sample.

### Finding 3: residual failures are concentrated, not spread

Of the 3 skill failures on Sonnet polars (n=30):

| Task | Expected | What likely happened |
|---|---|---|
| "Format a numeric column with a printf-style format string" | `polars.format` | Model emitted Python `str.format(...)` or `f"{x:.2f}"` |
| "Build a formatted string column from a template and column values" | `polars.format` | Same idiom collision |
| "Reduce values along a Series, accumulating via a binary function" | `polars.cum_reduce` | Model emitted `functools.reduce` or a method-chain |

All three are cases where Python or stdlib has a more idiomatic
function with the same intent, so the model picks that even with the
SKILL.md present. This is a real failure mode that prompt engineering
alone cannot fix. Two paths to address:

1. **Tighter eval items.** Phrase the tasks to disambiguate (e.g.
   "build a Polars Expression that formats values..."). Conflates
   prompt quality with skill quality.
2. **Counter-examples in SKILL.md.** Generated SKILL.md could list
   "do not use Python `str.format` for column formatting; use
   `polars.format` so the value is a Polars Expression." This is a
   selector-level improvement: when `score_uniqueness` keeps a tool
   whose name collides with a stdlib idiom, the generator should
   emit a "vs the obvious alternative" note.

### Finding 4: more tools is not better

Regenerated the polars bundle at four cap sizes ([sweep script](scripts/tool_count_sweep.py)):

| max_tools | coverage | no-skill | skill | conditional skill* |
|---|---|---|---|---|
| 5  | 40%  | 60% | 60% | 150% |
| 10 | 50%  | 60% | 60% | 120% |
| **20** | **100%** | 60% | **80%** | 80% |
| 40 | 100% | 50% | 80% | 80% |

\* `conditional skill = skill_pass / coverage_pass`. Values >100%
mean the model got items right that were not even in the bundle (its
own prior).

Doubling the menu from 20 to 40 produced **zero improvement**. The
sweet spot for this eval is N=20, which happens to be pip-skill's
default. Below that, coverage limits the absolute score (the
heuristic did not include the right tools). Above that, the model's
attention budget is the bottleneck, not menu size.

(This sweep was run at n=10 before the 30-item eval set existed.
Re-running at n=30 to confirm the shape is on the roadmap, but the
n=10 directional signal, N=20 = N=40, replicated across multiple
re-runs.)

### Finding 5: the uniqueness signal silently drops core API

On httpx, `coverage` is 8/10 because the heuristic deduplicated
`httpx.post` and `httpx.put` as too similar to `httpx.request` /
`httpx.get` (the `score_uniqueness` filter at
[selector.py:432](src/pip_skill/selector.py#L432)). These are the
most canonical functions in the package. The model knew them anyway,
so the eval did not penalise this, but the selector hid genuine
value.

Same shape on polars: the heuristic ranked `polars.format`,
`polars.read_lines`, `polars.read_delta` ahead of
`polars.read_csv`, `polars.DataFrame`, `polars.col`. Alphabetic
ordering inside `__all__` membership scoring is the likely cause.

Both are concrete examples of why Experiment 3 below (selector
ablation against a real-API corpus) would be a publishable
contribution: the heuristic shipped today has known systematic
failure modes that an ablation would quantify.

### Methodology footnotes

- All runs use the `claude-cli` backend (no API key). The `api`
  backend is recommended for paper-grade reproducibility because it
  exposes `temperature=0`; the CLI does not, so points carry
  run-to-run variance: roughly ±10pp at n=10, ±5pp at n=30. The
  polars headline numbers (50%/53% no-skill, 90%/97% skill) are at
  n=30; smaller package evals (httpx, requests) are at n=10 and
  should be read as ±10pp.
- `pip-skill eval` shells out to `claude -p` with `--disallowedTools`
  for Bash/WebFetch/Read/Write/Edit/etc. so the model emits the call
  rather than executing the task.
- The system prompt frames the task as static analysis (identify the
  call) rather than execution (do the task), and instructs the model
  to prefer module-level functions over class-method variants and to
  pick the simplest call when multiple options exist. Prompt variants
  were A/B-tested ([scripts/prompt_ab.py](scripts/prompt_ab.py));
  "prefer module-level" was the strongest hint and is baked into the
  shipped `_BASE_INSTRUCTION`.
- The skill bundles were generated with `--deterministic`, so anyone
  re-running with the same `pip-skill`/package versions gets the same
  bytes. Their SHA-256s are stamped in `MANIFEST.sha256`.
- Selection bias warning: eval items were authored by the author
  *after* inspecting the manifest, so coverage is upward-biased on
  polars and requests (we knew which tools the heuristic picked). The
  httpx eval was authored against the documented public API, which is
  why httpx coverage is 8/10 instead of 10/10. Future evals should be
  authored from the package's docs/README, blind to the manifest, to
  remove this bias.

## Second measurements (9-package blind corpus, May 2026)

Nine packages, 10 items each, **authored from each package's docs/README
without consulting the generated SKILL.md**. The blind protocol measures
what an end-user actually sees on a freshly generated skill they did
not help shape, rather than the upper-bound coverage you get when
items are written *against* the manifest.

Total: 90 items × 2 conditions × 2 models = 360 claude-cli calls per
condition pair.

### Aggregate (blind)

| Model | Packages | Items | no-skill | skill | Lift |
|---|---|---|---|---|---|
| Sonnet 4.5 | 9 | 90 | 61/90 (67.8%) | **79/90 (87.8%)** | **+20.0pp** |
| Haiku 4.5  | 9 | 90 | 62/90 (68.9%) | **82/90 (91.1%)** | **+22.2pp** |

Aggregate lift is within 2pp of the prior manifest-aware sweep on
Sonnet, so the headline number survives the bias correction. The
per-package distribution shifts substantially, though: under blind
authoring the regression on arrow doubles, `more_itertools` flips
from a strong positive to a regression, and `returns` quadruples its
lift. The blind corpus exposes which packages the model already knows
(skill confuses it) versus which it doesn't (skill closes the gap).

### Per package (blind, n=10 each)

| Package | Sonnet no-skill / skill / lift | Haiku no-skill / skill / lift |
|---|---|---|
| `arrow` 1.4 | 8/10 (80%) / 6/10 (60%) / **−20.0pp** | 8/10 (80%) / 9/10 (90%) / +10.0pp |
| `pendulum` 3.2 | 9/10 (90%) / 10/10 (100%) / +10.0pp | 10/10 / 10/10 / 0.0pp (ceiling) |
| `returns` 0.27 | 3/10 (30%) / **9/10 (90%)** / **+60.0pp** | 3/10 (30%) / **9/10 (90%)** / **+60.0pp** |
| `mcp` 1.27 | 2/10 (20%) / **10/10 (100%)** / **+80.0pp** | 7/10 (70%) / **10/10 (100%)** / **+30.0pp** |
| `fastmcp` 3.3 | 3/10 (30%) / **9/10 (90%)** / **+60.0pp** | 2/10 (20%) / **9/10 (90%)** / **+70.0pp** |
| `h3` 4.4 | 10/10 / 10/10 / 0.0pp (ceiling) | 7/10 (70%) / 9/10 (90%) / **+20.0pp** |
| `msgspec` 0.21 | 8/10 / 9/10 / +10.0pp | 7/10 (70%) / 9/10 (90%) / **+20.0pp** |
| `more_itertools` 11.1 | 9/10 / 7/10 / **−20.0pp** | 8/10 / 8/10 / 0.0pp |
| `toolz` 1.0 | 9/10 / 9/10 / 0.0pp | 10/10 / 9/10 / −10.0pp |

### Coverage gap is the bigger story

Coverage (offline; does the manifest include the expected qualname?):

| Package | Blind coverage | Diagnostic |
|---|---|---|
| `arrow` | 10/10 (100%) | clean |
| `pendulum` | 10/10 (100%) | clean |
| `returns` | 10/10 (100%) | clean (after `expected_qualnames` accepts converter/pipeline duplicates) |
| `fastmcp` | 10/10 (100%) | clean |
| `mcp` | 9/10 (90%) | clean (one Phase-2 `ClientSession` task) |
| `msgspec` | 5/10 (50%) | `score_uniqueness` deduplicates `msgspec.json.encode` against `msgspec.toml.encode` |
| `toolz` | 4/10 (40%) | annotation-heavy selector picks `apply` / `juxt` over `pipe` / `groupby` |
| `h3` 4.4 | 1/10 (10%) | Cython bindings have no annotations; lose to wrappers |
| `more_itertools` 11.1 | 1/10 (10%) | `Stats` / `run_length` outscore `chunked` / `pairwise` |

The selector's `_experimental` / `_legacy` penalty, C-extension trust
widening, and `tlz`/`toolz` resolution recover the worst earlier
failures: `polygon_to_cells_experimental` no longer beats
`polygon_to_cells`, `msgspec.json.encode` is now a candidate, and
`toolz` introspects the real `toolz` module instead of `tlz._build_tlz`.
The deeper bias remains: when a package has hundreds of public
names, the annotation/docstring score lifts obscure-but-typed helpers
above README-canonical ones. That is the next selector unblock.

### Finding 6: v0.3 fixes close the worst selector gaps but not the annotation bias

Specific gaps the v0.3 fixes close, verified by comparing pre-fix and
post-fix manifests on the v0.2 packages:

- `polygon_to_cells_experimental` no longer beats `polygon_to_cells`
  on h3 (penalty for `_experimental` suffix).
- `tlz._build_tlz.TlzLoader.*` no longer dominates the `toolz` manifest
  (fixed `resolve_import_name`).
- `msgspec.json.encode` / `decode` / `Struct` are now candidates
  (widened `get_public_api` trust boundary to same top-level package
  for C-extension callables).
- `fastmcp.FastMCPApp` and `fastmcp.Context` are in the top 5
  (no regression from the new penalties).

Specific gaps still open:

- `score_uniqueness` deduplicates same-named callables across
  submodules (`msgspec.json.encode` vs `msgspec.toml.encode`: one
  wins, the other drops out).
- The annotation/docstring score rewards type hints regardless of
  whether the function is canonical. On `more_itertools` and `toolz`,
  the canonical names (`chunked`, `pipe`, `groupby`) live in deep
  submodules with sparse annotations and lose to better-typed but
  obscure peers.
- Skill ranking surfaces multiple equivalent forms (`arrow.get` next
  to `arrow.parser.DateTimeParser.parse_iso`), and the model under
  skill chooses the more specific one. Two arrow regressions and one
  more_itertools regression follow this exact pattern.

### Finding 7: blind aggregate confirms the polars direction, refines the magnitude

5 of 9 packages show positive lift on Sonnet (mcp +80, returns +60,
fastmcp +60, pendulum +10, msgspec +10), 2 sit at ceiling without
skill (h3, toolz), and 2 regress (arrow −20, more_itertools −20).
The regression cluster shares a structural cause: the model already
knows the package well (no-skill ≥ 80%), the manifest includes
multiple equivalent canonical forms, and the model picks the one
the eval did not target.

The polars `+40pp` pattern from v0.1 generalizes in *direction*:
big lift on post-cutoff packages (mcp, fastmcp), small or negative
lift on stable canonical APIs the model already nails. Magnitude is
package-specific and depends on how much room the no-skill baseline
leaves.

### Finding 8: smaller model with skill beats larger model alone (replicated, blind)

Haiku + skill (82/90, 91.1%) outperforms Sonnet alone (61/90, 67.8%)
by **23.3pp**. Replicates the v0.1 polars-only result (Haiku+skill
97% beat Sonnet alone 50% by 47pp) on a broader, multi-archetype,
blindly-authored corpus. The cost-quality argument for shipping skills
with small models continues to hold under bias-corrected measurement.

### Finding 9: arrow regression is structural, not a sampling artifact

Arrow Sonnet under blind authoring is −20pp (8/10 no-skill → 6/10
skill). The misses cluster on the same selector pattern:

| Task | Expected | Model emitted under skill | Diagnosis |
|---|---|---|---|
| "Parse an ISO 8601 timestamp" | `arrow.get` | `arrow.parser.DateTimeParser.parse_iso` | skill surfaces low-level alternative |
| "Parse with format string" | `arrow.get` | `arrow.parser.DateTimeParser.parse` | same |
| "Configure custom Arrow subclass" | `arrow.ArrowFactory` | `arrow.api.factory` | function shadows class |

The current selector raises `arrow.ArrowFactory` above `arrow.api.factory`
in the rank order (rank 4 vs rank 11). The class is in the top 5. But
both are still in the manifest, and the model under skill picks the
function form because the prose paragraph adjacent to it mentions
"factory" matching the task text. A future fix is to drop function-
versions when a class-version of the same noun exists in the manifest.

### Threats to validity (v0.3)

- **Blind authoring is not zero-bias.** Items were authored from each
  package's docs/README, which is a different bias (toward the most
  documented surfaces), not no bias. End-users with niche tasks still
  see different coverage from these numbers.
- **n=10 per package, ±15pp variance.** Aggregate (n=90 per model) is
  ±5pp. Per-package numbers below ±15pp should be read as
  directional, not absolute. The +60pp / +80pp signals are large
  enough to survive any reasonable variance correction; the ±20pp
  arrow/more_itertools regressions are at the edge.
- **No `expected_kwargs` checks.** All items score on qualname only.
  Correct kwarg shape is still unmeasured.
- **Method-aware scoring is opt-in.** `expected_qualnames` (new in
  v0.3) lets items accept either form (class constructor vs chained
  method), but variable-bound chains (`client = X(); client.foo()`)
  remain unscoreable. Phase 2 corpus (anthropic, openai, langgraph,
  pydantic-ai, crewai) needs variable-binding tracking before it can
  fully run.
- **Single backend, single OAuth session.** All runs used the same
  Claude Code subscription. No multi-vendor comparison yet.
- **No `--select` LLM curation tested.** The skill bundles used the
  default heuristic. Re-running with `--select` would test whether
  the LLM-curated manifest closes the annotation-bias gap.

## Roadmap experiments

### Experiment 1: pip-skill on BFCL

Take the BFCL v4 single-turn AST evaluation set. For each question
whose API surface is a public PyPI package, generate a pip-skill
SKILL.md against the installed version. Run Claude (and one open model
for comparison) under three conditions:

- no spec
- BFCL-provided tool spec
- pip-skill-generated tool spec

Score with BFCL's AST-equivalence metric. Expected outcome: pip-skill
matches or exceeds the curated BFCL spec on packages where the model's
training cutoff predates the package's last release.

Reproducibility recipe: `pip-skill convert <pkg> --deterministic`, then
`pip-skill eval <pkg> bfcl/<pkg>.jsonl --conditions
coverage,no-skill,skill`.

### Experiment 2: drift cliff

Pick 5 high-churn SDKs (boto3, stripe, anthropic, openai,
databricks-sdk). Generate skills against the latest version *N* and
the version *N-12* (roughly one year old). Construct 50 tasks per SDK
whose correct calls differ between versions. Compare:

- Claude raw (uses training-cutoff knowledge)
- Claude with the *N-12* skill on an *N*-installed env
- Claude with the *N* skill

Metric: call-correctness, runtime errors, hallucinated parameters.
Hypothesis: regenerating the skill at install time closes the
training-cutoff gap.

### Experiment 3: 100-package real-API corpus + ablation

Auto-generate skills for the top 100 most-downloaded PyPI packages
with annotated APIs. Publish as a Hugging Face dataset. For each of
the 10 selector signals, regenerate the corpus with that signal
disabled and measure Kendall-τ on top-20 rank vs. the full scorer,
plus pass-rate on Experiment 1's eval set. The result is two
contributions: the largest real-API tool-spec corpus, and a principled
justification for each selector signal.

## Extended experiments (corpus expansion)

The v0.1 eval ships three packages (httpx, requests, polars); the
expanded corpus adds nine more, structured in three phases.
Candidate list mined from four independent research streams (tool-use
benchmark archaeology, 2026 industry signal, post-cutoff release
notes, per-archetype design rules). The short version below covers
the nine packages shipped under
[`examples/eval/<pkg>-blind.jsonl`](examples/eval/).

### Why these packages

The v0.1 eval covers HTTP clients (well-known to the model) and one
DataFrame library (idiomatic collision with the stdlib). To
generalize the +40pp polars result, the expanded corpus stresses three
new archetypes the model is *known* to mishandle:

1. **Post-cutoff protocol SDKs** (`mcp`, `fastmcp`). Released after
   January 2026; the model has no training data for the v1.x APIs.
2. **Renamed-everything domain libraries** (`h3`). h3-py 4.x renamed
   every public function (`geo_to_h3` → `latlng_to_cell`,
   `polyfill` → `polygon_to_cells`); the model emits 3.x names that
   no longer exist.
3. **Stdlib-shadowing functional util libraries** (`toolz`, `returns`,
   `arrow`, `pendulum`, `msgspec`). Each has a public name that
   collides with a stdlib or third-party convention with a different
   signature. Polars is the existing exemplar; these are the
   non-DataFrame versions of the same trap.

### Phase 1: eight packages (no new harness work)

Shipped as 10-item blind sets in
[`examples/eval/<pkg>-blind.jsonl`](examples/eval/) and measured in
[`eval-results/blind/REPORT.md`](eval-results/blind/REPORT.md).

| Package | Archetype | Items | Eval set |
|---|---|---|---|
| `mcp` | Protocol SDK | 10 | [mcp-blind.jsonl](examples/eval/mcp-blind.jsonl) |
| `fastmcp` | MCP framework | 10 | [fastmcp-blind.jsonl](examples/eval/fastmcp-blind.jsonl) |
| `h3` | Geospatial indexing | 10 | [h3-blind.jsonl](examples/eval/h3-blind.jsonl) |
| `arrow` | Datetime | 10 | [arrow-blind.jsonl](examples/eval/arrow-blind.jsonl) |
| `pendulum` | Datetime | 10 | [pendulum-blind.jsonl](examples/eval/pendulum-blind.jsonl) |
| `toolz` | Functional util | 10 | [toolz-blind.jsonl](examples/eval/toolz-blind.jsonl) |
| `returns` | Result monad | 10 | [returns-blind.jsonl](examples/eval/returns-blind.jsonl) |
| `msgspec` | Serde | 10 | [msgspec-blind.jsonl](examples/eval/msgspec-blind.jsonl) |
| `more_itertools` | Itertools | 10 | [more_itertools-blind.jsonl](examples/eval/more_itertools-blind.jsonl) |

Predictions are calibrated against the polars +40pp result. They
will move once measured; the point is the *direction* and the
*ranking*, not the absolute number.

**Budget:** 174 items × 2 conditions (base vs skill) × 2 models
(Sonnet 4.5 + Haiku 4.5) = 696 claude-cli calls. Add ~10% for
retries and a partial Opus 4.7 replication on the top failures →
~750 calls. Wall time ~1h with the harness's default 8-worker
concurrency. Zero API tokens spent (the harness uses the cached OAuth
session per `gotcha_claude-cli-bare-blocks-oauth`).

### Phase 2: six packages (needs new authoring rules)

These are LLM and agent SDKs where the universal blind-to-manifest
rule is hardest to apply, because every task naturally sounds like
"build an agent" or "send a message". Authoring requires either
explicit version pinning in the prose or `accept_qualnames` lists
in the eval format.

| Package | Items | Predicted lift |
|---|---|---|
| `anthropic` (>=1.12) | 35 | +30pp (beta tool patterns post-cutoff) |
| `openai` (v2) | 35 | +25pp (Responses default vs Chat Completions) |
| `pydantic-ai` | 30 | +30pp (post-cutoff API; `Agent`/`RunContext`) |
| `langgraph` | 30 | +30pp (moved imports in 1.0) |
| `google-genai` | 25 | +35pp (LLM still emits deprecated `google.generativeai`) |
| `crewai` | 25 | +25pp (decorator API LLM frequently invents) |

**Budget:** 180 items × 4 = ~720 calls baseline. With the n=50-per-package
bump recommended for sprawling agent SDKs, scale to ~1200 calls.
Wall time ~2h.

### Phase 3: BFCL submission + scientific corpus

After the expansion ships, three follow-on tracks:

- Convert pip-skill into a BFCL submission (each pip package = one
  "API class" in BFCL terms). Validates the harness against external
  scoring.
- Add heavy-install scientific packages (`scanpy`, `rdkit`,
  `astropy.units`, `qiskit`) under a controlled conda environment.
  Subagent C predicts +30pp+ on `scanpy` (in-place return semantics)
  and `h3`-class +40pp on `qiskit` (Aer removed, Primitives V1 vs
  V2). These are domain-CI-flaky so they wait for Phase 3.
- Teach the selector to read botocore service models so `boto3`'s
  runtime-generated qualnames (`s3.list_buckets`, ~6000 ops across
  ~300 services) become eval-able. This is the unlock for Tier-3
  cloud SDK evaluation.

Estimated Phase 3 budget: 5,000+ calls across multi-vendor models.
Multi-day wall time.

### Recommendation: ship Phase 1 inline, Phase 2 in a follow-up

Phase 1 alone covers three new archetypes (protocol SDK, geospatial
indexing, idiomatic-collision functional utils) at zero API-token
cost. That is enough new evidence to justify a release and a 1h
harness run from the author's laptop. Phase 2 ships two weeks later,
by which point the post-cutoff agent SDKs (`claude-agent-sdk`,
`openai-agents`, `agent-framework`) will have stabilized enough to
add to the corpus as the strongest possible "the LLM literally
cannot have known this API" story.

### Threats to validity (predicted before measuring)

- **Selector miss on deep submodules.** `mcp.client.session.ClientSession`
  is three levels deep. If the v0.1 selector reexport-scores only
  shallow modules, the SKILL.md manifest will not list it and the
  skill condition will score 0 on those items, not because the LLM
  can't use the skill but because the skill doesn't surface the
  target. Verify by running `pip-skill convert mcp` and grepping
  `plugin.json` for each draft's `expected_qualname` before kicking
  off the run.
- **Method qualnames** (`fastmcp.FastMCP.list_tools`, `returns.result.Result.bind`).
  The harness compares against a flat qualname string. If the
  manifest only lists the class but not the method, the skill miss
  is again a coverage gap, not a knowledge gap. May need a separate
  "method discovery" sub-experiment for archetypes where methods are
  the canonical API surface (DataFrames, OO clients, Result monads).
- **Ambiguity on `arrow.now` vs `pendulum.now`.** Both packages
  expose `now()`. The draft items pin the package in the prose, but
  the harness's alias-extraction may collapse them. Spot-check the
  first batch of runs.

## Open questions

These would make good first contributions to the project.

- **Token-budget vs accuracy curve.** pip-skill defaults to 20 tools;
  what's the accuracy/cost trade-off at 10, 50, 100? Plot pass-rate
  against tool count for a tier-3 SDK like boto3.
- **Behavioural drift, not just name drift.** `pip-skill diff` flags
  added/removed names. It does not detect that `requests.get`'s
  `verify` default changed. A schema-hash per tool would catch this.
- **Selector weight optimisation.** The 10 selector weights are
  hand-set integers. Are they Pareto-optimal? An ablation against
  Experiment 3's corpus would say.
- **Multi-package skills.** Most agent tasks need 2-3 packages. Can
  pip-skill emit a single skill bundle whose tools span boto3 + pandas
  + openpyxl without exceeding context limits?
