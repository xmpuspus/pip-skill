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

### Finding 3: more tools is not better

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
heuristic didn't include the right tools). Above that, the model's
attention budget is the bottleneck, not menu size.

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
