"""Evaluation harness for generated skills.

`pip-skill eval` answers a single quantitative question:

    Does the generated SKILL.md let an LLM call the right function for
    a task it has never seen?

It accepts an eval set in JSONL (one `{task, expected_qualname}` per
line) and runs three conditions against a generated plugin bundle:

    coverage   : does the manifest include the expected qualname?
                 (Offline. Lower bound on accuracy: if the tool isn't
                  even in the bundle, the model has zero chance.)

    no-skill   : Claude with no tool spec, just the task. Baseline.
    skill      : Claude with the pip-skill-generated SKILL.md prepended
                 to the system prompt.

For each item we score AST-equivalence of the called function: extract
the first `pkg.fn(...)` call from Claude's emitted Python and compare
its qualified name against the expected one.

The model conditions (`no-skill`, `skill`) use one of two backends:

    claude-cli : shell out to `claude -p` (Claude Code). No API key
                 needed. Default when `claude` is on PATH. Auth comes
                 from your existing Claude Code session.
    api        : call the Anthropic SDK directly. Requires
                 ANTHROPIC_API_KEY and the `[llm]` extra. Supports
                 `temperature=0` for bit-for-bit reproducibility (use
                 this for citable / paper-grade runs).

Backend auto-selection: if ANTHROPIC_API_KEY is set the API backend is
preferred (faster, deterministic). Otherwise we fall back to the
`claude` CLI. Force with `--backend api|claude-cli`.

Methodology aligns with the Berkeley Function-Calling Leaderboard
(BFCL): https://gorilla.cs.berkeley.edu/leaderboard.html

Results are emitted as a JSON object on stdout. CI consumers should
read the `pass_rate` per condition; humans get a printed table.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class EvalItem:
    """A single task in the eval set.

    Items may declare either a single ``expected_qualname`` or a list
    ``expected_qualnames`` of equivalent forms. Lists are useful when a
    task can be solved through more than one canonical path — typically
    a free function and an equivalent method on a class
    (``anthropic.messages.create`` vs ``Anthropic.messages.create``).
    """

    task: str
    expected_qualname: str
    expected_qualnames: list[str] = field(default_factory=list)

    def matches(self, qualname: str | None) -> bool:
        """True iff `qualname` equals the primary or any alternate qualname."""
        if qualname is None:
            return False
        if qualname == self.expected_qualname:
            return True
        return qualname in self.expected_qualnames

    @classmethod
    def from_dict(cls, d: dict) -> EvalItem:
        if "task" not in d:
            raise ValueError(f"Eval item is missing required field 'task': {d!r}.")
        # Accept either form; `expected_qualnames` wins if both are present.
        alternates: list[str] = []
        if "expected_qualnames" in d:
            raw = d["expected_qualnames"]
            if not isinstance(raw, list) or not raw:
                raise ValueError(f"Eval item 'expected_qualnames' must be a non-empty list: {d!r}.")
            alternates = [str(x) for x in raw]
            primary = alternates[0]
            rest = alternates[1:]
        elif "expected_qualname" in d:
            primary = str(d["expected_qualname"])
            rest = []
        else:
            raise ValueError(
                f"Eval item is missing required field 'expected_qualname' "
                f"or 'expected_qualnames': {d!r}."
            )
        return cls(task=str(d["task"]), expected_qualname=primary, expected_qualnames=rest)


@dataclass
class EvalResult:
    """Outcome of one condition on one item."""

    item: EvalItem
    condition: str
    passed: bool
    detail: str = ""
    emitted: str = ""


@dataclass
class EvalSummary:
    """Aggregate results across an eval run."""

    plugin_dir: str
    eval_path: str
    conditions: list[str]
    items: int
    backend: str | None = None
    per_condition_pass: dict[str, int] = field(default_factory=dict)
    per_condition_rate: dict[str, float] = field(default_factory=dict)
    per_item: list[dict] = field(default_factory=list)


def load_eval_set(path: Path) -> list[EvalItem]:
    """Read a JSONL eval set from disk.

    Args:
        path: A `.jsonl` file with one `{task, expected_qualname}` per line.

    Returns:
        Parsed `EvalItem` list.
    """
    items: list[EvalItem] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        items.append(EvalItem.from_dict(json.loads(line)))
    return items


def _strip_markdown(text: str) -> str:
    """Strip backticks and fenced code blocks from model output.

    Models often wrap code as ``requests.get(...)`` or in ```python
    fences. We unwrap conservatively (only when the wrapper bounds the
    whole non-whitespace payload) so legitimate inline backticks in
    legal Python — none exist in expressions, but we'd rather under-
    than over-strip — stay intact.
    """
    s = text.strip()
    if s.startswith("```"):
        # Drop the opening fence (with optional language tag) and the closing fence.
        body = s.split("\n", 1)[1] if "\n" in s else ""
        if body.endswith("```"):
            body = body[: -len("```")]
        s = body.strip()
    if s.startswith("`") and s.endswith("`") and s.count("`") == 2:
        s = s[1:-1].strip()
    return s


# Package aliases models commonly emit (idiomatic `import X as Y` forms).
# We accept calls written through either the full name or the alias, and
# normalize the alias back to the canonical import name in the returned
# qualname so callers can compare against expected `<pkg>.<fn>` exactly.
_PACKAGE_ALIASES: dict[str, list[str]] = {
    "polars": ["pl"],
    "pandas": ["pd"],
    "numpy": ["np"],
    "matplotlib.pyplot": ["plt"],
    "seaborn": ["sns"],
    "tensorflow": ["tf"],
    "sqlalchemy": ["sa"],
    "plotly.express": ["px"],
    "plotly.graph_objects": ["go"],
    "datetime": ["dt"],
}


def _accepted_roots(import_name: str) -> set[str]:
    """Return the set of root identifiers we accept for `import_name`.

    Always includes `import_name` itself plus any registered aliases.
    """
    return {import_name, *_PACKAGE_ALIASES.get(import_name, [])}


def extract_qualname(emitted_python: str, import_name: str) -> str | None:
    """Extract the first strict `import_name.path.fn` call in emitted Python.

    Strict here means the chain bottoms out at a Name node, never
    recursing through inner Calls. This preserves the v0.1 contract:
    `requests.Session().get('x')` returns ``requests.Session`` (the
    constructor), not the method.

    Eval items that want to accept the method-aware form (e.g.
    ``requests.Session.get``) should list both forms in
    ``expected_qualnames``; the eval runner consults
    ``extract_qualnames`` for matching.

    Accepts both the canonical package name (`polars.read_json(...)`)
    and any commonly-used alias (`pl.read_json(...)`). Aliases are
    normalized back to the canonical name in the returned qualname.

    Args:
        emitted_python: Source text the model produced (any wrapping
            allowed; we parse what we can).
        import_name: The package's import name (e.g. ``"requests"``).

    Returns:
        Dotted qualified name like ``"requests.get"`` for the first
        matching call, or None if no call is found.
    """
    cleaned = _strip_markdown(emitted_python)
    try:
        tree = ast.parse(cleaned)
    except SyntaxError:
        return None
    accepted = _accepted_roots(import_name)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            qual = _attr_chain(node.func)
            if not qual:
                continue
            root, _, rest = qual.partition(".")
            if root == import_name:
                return qual
            if root in accepted:
                return f"{import_name}.{rest}" if rest else import_name
    return None


def extract_qualnames(emitted_python: str, import_name: str) -> list[str]:
    """Extract every plausible `import_name.path.fn` chain in emitted Python.

    Returns all matching chains in AST walk order. Each call expression
    contributes up to two chains:

    1. The strict chain (``_attr_chain``) — bottoms out at a Name, never
       traverses inner calls. This is what ``extract_qualname`` returns.
    2. The method-aware chain (``_attr_chain_thru_calls``) — resolves
       through inline class instantiation (``anthropic.Anthropic().messages.create``
       becomes ``anthropic.Anthropic.messages.create``).

    Both forms are kept distinct (deduplicated, but never merged) so
    eval items declaring ``expected_qualnames`` can match either
    expectation without changing the strict extractor's contract.
    """
    cleaned = _strip_markdown(emitted_python)
    try:
        tree = ast.parse(cleaned)
    except SyntaxError:
        return []
    accepted = _accepted_roots(import_name)
    results: list[str] = []

    def _accept(qual: str | None) -> None:
        if not qual:
            return
        root, _, rest = qual.partition(".")
        if root == import_name:
            normalized = qual
        elif root in accepted:
            normalized = f"{import_name}.{rest}" if rest else import_name
        else:
            return
        if normalized not in results:
            results.append(normalized)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            _accept(_attr_chain(node.func))
            _accept(_attr_chain_thru_calls(node.func))
    return results


def _attr_chain(node: ast.AST) -> str | None:
    """Recover dotted attribute chain from an AST node, or None.

    Backward-compatible: returns None when the chain bottoms out at a
    Call rather than a Name. The method-aware variant ``_attr_chain_thru_calls``
    handles ``ClassName().method`` patterns separately.
    """
    if isinstance(node, ast.Attribute):
        left = _attr_chain(node.value)
        return f"{left}.{node.attr}" if left else None
    if isinstance(node, ast.Name):
        return node.id
    return None


def _attr_chain_thru_calls(node: ast.AST) -> str | None:
    """Like ``_attr_chain`` but recurses through ``Call`` nodes.

    This recovers the chain for inline class instantiation written as
    ``Anthropic().messages.create(...)`` — the dotted form reads as
    ``Anthropic.messages.create``. Returned only as an alternate; the
    primary chain (without recursion) remains the canonical extraction.
    """
    if isinstance(node, ast.Attribute):
        left = _attr_chain_thru_calls(node.value)
        return f"{left}.{node.attr}" if left else None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Call):
        return _attr_chain_thru_calls(node.func)
    return None


def evaluate_coverage(items: list[EvalItem], plugin_dir: Path) -> list[EvalResult]:
    """Offline metric: is any expected qualname present in plugin.json's manifest?

    For items declaring `expected_qualnames`, coverage passes when ANY
    alternate appears in the manifest.
    """
    pj = plugin_dir / ".claude-plugin" / "plugin.json"
    if not pj.exists():
        raise ValueError(f"plugin.json missing in {plugin_dir}")
    manifest = json.loads(pj.read_text())
    in_skill = {t.get("qualname", "") for t in manifest.get("tools", [])}
    results = []
    for item in items:
        candidates = [item.expected_qualname, *item.expected_qualnames]
        passed = any(c in in_skill for c in candidates)
        detail = "in manifest" if passed else "missing from manifest"
        results.append(EvalResult(item=item, condition="coverage", passed=passed, detail=detail))
    return results


def _read_skill_md(plugin_dir: Path) -> str:
    """Read the SKILL.md from the bundle, normalized name lookup."""
    skills_root = plugin_dir / "skills"
    if not skills_root.is_dir():
        return ""
    for child in skills_root.iterdir():
        candidate = child / "SKILL.md"
        if candidate.exists():
            return candidate.read_text()
    return ""


def _import_name_from_manifest(plugin_dir: Path) -> str:
    pj = plugin_dir / ".claude-plugin" / "plugin.json"
    if not pj.exists():
        return ""
    return json.loads(pj.read_text()).get("importName", "")


BACKEND_API = "api"
BACKEND_CLAUDE_CLI = "claude-cli"
BACKEND_AUTO = "auto"


def select_backend(requested: str, api_key: str | None) -> str:
    """Resolve `auto` to a concrete backend, or validate an explicit choice.

    Selection rules:
        - `api`: requires `api_key`. Errors if missing.
        - `claude-cli`: requires the `claude` binary on PATH. Errors if missing.
        - `auto`: prefers `api` when an API key is set (faster,
          temperature=0, reproducible). Falls back to `claude-cli`.
    """
    if requested == BACKEND_API:
        if not api_key:
            raise ValueError(
                "Backend 'api' requires ANTHROPIC_API_KEY (or --api-key). "
                "Use --backend claude-cli to use your Claude Code session instead."
            )
        return BACKEND_API
    if requested == BACKEND_CLAUDE_CLI:
        if not shutil.which("claude"):
            raise ValueError(
                "Backend 'claude-cli' requires the `claude` binary on PATH. "
                "Install Claude Code, or pass --backend api with ANTHROPIC_API_KEY."
            )
        return BACKEND_CLAUDE_CLI
    if requested == BACKEND_AUTO:
        if api_key:
            return BACKEND_API
        if shutil.which("claude"):
            return BACKEND_CLAUDE_CLI
        raise ValueError(
            "Need either ANTHROPIC_API_KEY (for --backend api) or the `claude` "
            "binary on PATH (for --backend claude-cli)."
        )
    raise ValueError(f"Unknown backend: {requested!r}")


def _ask_api(task: str, system: str, api_key: str) -> str:
    """One Claude call via the Anthropic SDK (temperature=0 for reproducibility)."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    model = os.environ.get("PIP_SKILL_MODEL", "claude-sonnet-4-5")
    response = client.messages.create(
        model=model,
        max_tokens=256,
        temperature=0,
        system=system,
        messages=[{"role": "user", "content": task}],
    )
    return response.content[0].text


_CLAUDE_DISALLOWED_TOOLS = (
    # Lock out everything that would let Claude Code DO the task instead
    # of naming the call that does it. The eval is a static-analysis
    # judgement, not an execution.
    "Bash WebFetch WebSearch Read Write Edit NotebookEdit Glob Grep"
    " TodoWrite Agent Task BashOutput SlashCommand KillShell"
)


def _ask_claude_cli(task: str, system: str) -> str:
    """One Claude call via the `claude` CLI (uses your Claude Code session).

    Runs `claude -p --append-system-prompt <system> <wrapped-task>`. We
    do NOT pass `--bare` (it disables OAuth/keychain, which is the very
    auth we want). We DO pass `--disallowedTools` to prevent Claude
    Code from running Bash/WebFetch/etc. and actually executing the
    task instead of naming the call.

    The task is wrapped in a "name the call, do not execute" frame so
    Claude treats it as static analysis rather than a request to act.
    """
    model = os.environ.get("PIP_SKILL_MODEL", "sonnet")
    wrapped = (
        "Task description: " + task + "\n\n"
        "Do NOT execute, fetch, read, write, or run anything. Identify"
        " the single Python function call that would accomplish this"
        " task and respond with that call only."
    )
    cmd = [
        "claude",
        "-p",
        "--model",
        model,
        "--disallowedTools",
        _CLAUDE_DISALLOWED_TOOLS,
        "--append-system-prompt",
        system,
        wrapped,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude CLI exited {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc.stdout


_BASE_INSTRUCTION = (
    "You are a Python STATIC ANALYZER. You do not execute anything;"
    " you only IDENTIFY which Python call would accomplish a described"
    " task. For each task, respond with EXACTLY one Python expression"
    " of the form `package.fn(args...)` and nothing else: no prose, no"
    " markdown, no imports, no explanation, no leading/trailing text."
    " If multiple functions could work, pick the simplest one (fewest"
    " required parameters; module-level over class-method when both"
    " apply). Use placeholder values for arguments (e.g."
    " `'https://example.com'` for URLs)."
)


def evaluate_with_claude(
    items: list[EvalItem],
    plugin_dir: Path,
    with_skill: bool,
    backend: str,
    api_key: str | None = None,
) -> list[EvalResult]:
    """Online metric: ask Claude (with or without the SKILL.md) to emit a call.

    Args:
        items: Eval items.
        plugin_dir: Bundle root.
        with_skill: When True, prepend the bundle's SKILL.md to the
            system prompt. When False, give only `_BASE_INSTRUCTION`.
        backend: Concrete backend (`api` or `claude-cli`). Use
            `select_backend()` to resolve `auto`.
        api_key: Required when backend is `api`.

    Returns:
        Per-item results. `passed` is True iff the AST-extracted
        qualname equals the expected qualname.
    """
    import_name = _import_name_from_manifest(plugin_dir)
    if not import_name:
        raise ValueError(f"Cannot determine importName from {plugin_dir}")
    condition = "skill" if with_skill else "no-skill"
    if with_skill:
        system = _read_skill_md(plugin_dir) + "\n\n" + _BASE_INSTRUCTION
    else:
        system = (
            f"You are answering tasks about the `{import_name}` Python package. {_BASE_INSTRUCTION}"
        )

    results = []
    for item in items:
        try:
            if backend == BACKEND_API:
                emitted = _ask_api(item.task, system, api_key)
            else:
                emitted = _ask_claude_cli(item.task, system)
        except Exception as e:
            results.append(
                EvalResult(
                    item=item,
                    condition=condition,
                    passed=False,
                    detail=f"{backend} error: {e}",
                    emitted="",
                )
            )
            continue
        # Collect every plausible call chain, then pass if any matches
        # the primary expected qualname or any declared alternate.
        candidates = extract_qualnames(emitted, import_name)
        # `qual` keeps the canonical first-match for legacy detail output.
        qual = candidates[0] if candidates else None
        matched = next((c for c in candidates if item.matches(c)), None)
        passed = matched is not None
        if passed:
            detail = f"matched {matched!r}"
        else:
            expected_repr = (
                repr(item.expected_qualname)
                if not item.expected_qualnames
                else f"one of {[item.expected_qualname, *item.expected_qualnames]!r}"
            )
            detail = f"got {qual!r}, expected {expected_repr}"
        results.append(
            EvalResult(
                item=item, condition=condition, passed=passed, detail=detail, emitted=emitted
            )
        )
    return results


def run_eval(
    plugin_dir: Path,
    eval_path: Path,
    conditions: list[str],
    api_key: str | None = None,
    backend: str = BACKEND_AUTO,
) -> EvalSummary:
    """Run an eval against a plugin bundle and return aggregated results.

    Args:
        plugin_dir: Generated skill bundle.
        eval_path: JSONL file with `{task, expected_qualname}` items.
        conditions: Subset of `coverage`, `no-skill`, `skill`.
        api_key: Anthropic API key. Required only if backend resolves
            to `api`. Read from ANTHROPIC_API_KEY when None.
        backend: `auto` (default), `api`, or `claude-cli`. Auto prefers
            `api` when a key is set and falls back to the `claude` CLI.
    """
    items = load_eval_set(eval_path)
    all_results: list[EvalResult] = []

    # Only resolve a model backend if a model-using condition is requested.
    model_conditions = {"no-skill", "skill"}
    resolved_backend: str | None = None
    if model_conditions.intersection(conditions):
        resolved_backend = select_backend(backend, api_key)

    for condition in conditions:
        if condition == "coverage":
            all_results.extend(evaluate_coverage(items, plugin_dir))
        elif condition in model_conditions:
            all_results.extend(
                evaluate_with_claude(
                    items,
                    plugin_dir,
                    with_skill=(condition == "skill"),
                    backend=resolved_backend,
                    api_key=api_key,
                )
            )
        else:
            raise ValueError(f"Unknown condition: {condition!r}")

    summary = EvalSummary(
        plugin_dir=str(plugin_dir),
        eval_path=str(eval_path),
        conditions=conditions,
        items=len(items),
        backend=resolved_backend,
    )
    for c in conditions:
        passed = sum(1 for r in all_results if r.condition == c and r.passed)
        summary.per_condition_pass[c] = passed
        summary.per_condition_rate[c] = passed / len(items) if items else 0.0
    summary.per_item = [
        {
            "task": r.item.task,
            "expected": r.item.expected_qualname,
            "condition": r.condition,
            "passed": r.passed,
            "detail": r.detail,
        }
        for r in all_results
    ]
    return summary


def render_table(summary: EvalSummary) -> str:
    """Render a human-readable summary table."""
    lines = [
        f"Eval: {summary.eval_path} ({summary.items} items)",
        f"Plugin: {summary.plugin_dir}",
    ]
    if summary.backend:
        lines.append(f"Backend: {summary.backend}")
    lines.extend(
        [
            "",
            "Condition   Pass    Rate",
            "---------   ----    ----",
        ]
    )
    for c in summary.conditions:
        passed = summary.per_condition_pass[c]
        rate = summary.per_condition_rate[c]
        lines.append(f"{c:<11} {passed:>4}/{summary.items:<3} {rate * 100:>5.1f}%")
    return "\n".join(lines)


def to_json(summary: EvalSummary) -> str:
    """Render the summary as a JSON object (for CI consumption)."""
    return json.dumps(asdict(summary), indent=2)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint when imported by `pip_skill.cli`."""
    import argparse

    parser = argparse.ArgumentParser(prog="pip-skill eval")
    parser.add_argument("plugin_dir", type=Path)
    parser.add_argument("eval_file", type=Path)
    parser.add_argument(
        "--conditions",
        default="coverage",
        help=(
            "Comma-separated list of conditions to run: coverage,"
            " no-skill, skill. Coverage runs offline; the others"
            " call Claude via the selected backend."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of table")
    parser.add_argument(
        "--backend",
        choices=[BACKEND_AUTO, BACKEND_API, BACKEND_CLAUDE_CLI],
        default=BACKEND_AUTO,
        help=(
            "Where to send model calls. claude-cli uses `claude -p` and"
            " needs no API key (uses your Claude Code session). api uses"
            " the Anthropic SDK (needs ANTHROPIC_API_KEY) and gives"
            " temperature=0 reproducibility. auto picks api when a key is"
            " set, else claude-cli. Default: auto."
        ),
    )
    parser.add_argument(
        "--api-key",
        help="ANTHROPIC_API_KEY override; otherwise read from environment",
    )
    args = parser.parse_args(argv)

    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    try:
        summary = run_eval(
            args.plugin_dir,
            args.eval_file,
            conditions,
            api_key=api_key,
            backend=args.backend,
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(summary))
    else:
        print(render_table(summary))
    return 0
