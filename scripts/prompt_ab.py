#!/usr/bin/env python3
"""A/B test eval prompt variants against a plugin bundle.

Usage:
    python scripts/prompt_ab.py <plugin-dir> <eval-file.jsonl>

For each variant, runs the `skill` condition (SKILL.md prepended) via
`claude -p` and reports pass-rate. Use to tune `_BASE_INSTRUCTION` in
src/pip_skill/eval.py without editing-and-rerunning the harness.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pip_skill.eval import (
    BACKEND_CLAUDE_CLI,
    EvalResult,
    _ask_claude_cli,
    _import_name_from_manifest,
    _read_skill_md,
    extract_qualname,
    load_eval_set,
)

# Each variant is (name, base_instruction). The skill text is prepended.
VARIANTS = [
    (
        "v0_original",
        "Respond with ONLY a Python expression that calls the most"
        " appropriate function from the available API to solve the task."
        " No prose, no markdown, no imports. Just the call.",
    ),
    (
        "v1_simplest",
        "Respond with ONLY a Python expression that solves the task."
        " If multiple functions could work, pick the SIMPLEST one"
        " (fewest required parameters, most idiomatic). No prose, no"
        " markdown, no imports. Just the call.",
    ),
    (
        "v2_match_exact",
        "Respond with ONLY a Python expression. Scan the SKILL.md tool"
        " list; if any tool name exactly matches the verb in the task"
        " (`get` for a GET request, `read_json` for reading JSON, etc.),"
        " use it without considering alternatives. No prose, no"
        " markdown, no imports. Just the call.",
    ),
    (
        "v3_prefer_module_level",
        "Respond with ONLY a Python expression. Prefer the module-level"
        " function (e.g. `pkg.get(...)`) over the class-method variant"
        " (e.g. `pkg.Session().get(...)`) unless the task explicitly"
        " requires session/state. No prose, no markdown, no imports."
        " Just the call.",
    ),
]


def run_variant(name: str, instruction: str, plugin_dir: Path, items: list) -> list[EvalResult]:
    import_name = _import_name_from_manifest(plugin_dir)
    system = _read_skill_md(plugin_dir) + "\n\n" + instruction
    out: list[EvalResult] = []
    for item in items:
        try:
            emitted = _ask_claude_cli(item.task, system)
        except Exception as e:
            out.append(
                EvalResult(item=item, condition=name, passed=False, detail=f"err: {e}", emitted="")
            )
            continue
        qual = extract_qualname(emitted, import_name)
        passed = qual == item.expected_qualname
        detail = f"got={qual!r} want={item.expected_qualname!r}"
        out.append(
            EvalResult(item=item, condition=name, passed=passed, detail=detail, emitted=emitted)
        )
    return out


def main() -> int:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <plugin-dir> <eval-file.jsonl>", file=sys.stderr)
        return 2
    plugin_dir = Path(sys.argv[1])
    eval_path = Path(sys.argv[2])
    items = load_eval_set(eval_path)
    print(f"Plugin: {plugin_dir}")
    print(f"Eval:   {eval_path} ({len(items)} items)")
    print(f"Backend: {BACKEND_CLAUDE_CLI}")
    print()

    summary_rows = []
    for name, instruction in VARIANTS:
        print(f"=== {name} ===")
        results = run_variant(name, instruction, plugin_dir, items)
        passed = sum(1 for r in results if r.passed)
        rate = passed / len(items) if items else 0.0
        summary_rows.append((name, passed, len(items), rate))
        for r in results:
            mark = "PASS" if r.passed else "FAIL"
            print(f"  [{mark}] {r.detail}")
        print()

    print("=== summary ===")
    print(f"{'variant':<28} {'pass':>10}  {'rate':>6}")
    for name, p, n, rate in summary_rows:
        print(f"{name:<28} {p:>4}/{n:<3}  {rate * 100:>5.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
