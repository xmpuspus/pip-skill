"""Aggregate Phase 1 eval results into per-package and aggregate tables.

Reads eval-results/<pkg>-<model>.json files written by `pip-skill eval --json`
and prints:
  - per-package: items, coverage, no-skill, skill, lift, per model
  - aggregate: total items, sums, weighted lift, per model
  - residuals: skill-condition misses (item, expected, got)

Usage: python3 eval-results/analyze.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESULTS_DIR = Path(__file__).parent
PACKAGES = [
    "arrow",
    "pendulum",
    "mcp",
    "fastmcp",
    "h3",
    "returns",
    "msgspec",
    "more_itertools",
]
MODELS = ["sonnet", "haiku"]


def load(pkg: str, model: str) -> dict | None:
    p = RESULTS_DIR / f"{pkg}-{model}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return None


def per_package_table() -> str:
    lines = ["| Package | Model | n | coverage | no-skill | skill | Lift |", "|---|---|---|---|---|---|---|"]
    for pkg in PACKAGES:
        for model in MODELS:
            data = load(pkg, model)
            if not data:
                lines.append(f"| {pkg} | {model} | - | MISSING | - | - | - |")
                continue
            n = data.get("items", 0)
            c = data["per_condition_pass"]
            r = data["per_condition_rate"]
            cov = c.get("coverage", "-")
            nos = c.get("no-skill", "-")
            ski = c.get("skill", "-")
            lift = (r.get("skill", 0) - r.get("no-skill", 0)) * 100 if r.get("skill") is not None and r.get("no-skill") is not None else None
            lift_s = f"{lift:+.1f}pp" if lift is not None else "-"
            lines.append(
                f"| {pkg} | {model} | {n} | {cov}/{n} | {nos}/{n} ({r.get('no-skill', 0)*100:.0f}%) | {ski}/{n} ({r.get('skill', 0)*100:.0f}%) | {lift_s} |"
            )
    return "\n".join(lines)


def aggregate_table() -> str:
    lines = ["| Model | Packages | Total items | no-skill | skill | Lift |", "|---|---|---|---|---|---|"]
    for model in MODELS:
        total_items = 0
        total_no = 0
        total_skill = 0
        pkg_count = 0
        for pkg in PACKAGES:
            data = load(pkg, model)
            if not data:
                continue
            pkg_count += 1
            n = data["items"]
            total_items += n
            total_no += data["per_condition_pass"].get("no-skill", 0)
            total_skill += data["per_condition_pass"].get("skill", 0)
        if total_items == 0:
            continue
        no_rate = total_no / total_items
        sk_rate = total_skill / total_items
        lift = (sk_rate - no_rate) * 100
        lines.append(
            f"| {model} | {pkg_count} | {total_items} | {total_no}/{total_items} ({no_rate*100:.1f}%) | {total_skill}/{total_items} ({sk_rate*100:.1f}%) | {lift:+.1f}pp |"
        )
    return "\n".join(lines)


def residuals() -> str:
    out = ["", "## Residual skill misses (model + skill still got it wrong)"]
    for pkg in PACKAGES:
        for model in MODELS:
            data = load(pkg, model)
            if not data:
                continue
            misses = [
                r
                for r in data.get("per_item", [])
                if r.get("condition") == "skill" and not r.get("passed")
            ]
            if not misses:
                continue
            out.append(f"\n### {pkg} ({model}) — {len(misses)} misses")
            for m in misses:
                task = m["task"][:80] + ("..." if len(m["task"]) > 80 else "")
                out.append(f"- expected `{m['expected']}` — {m['detail']}")
                out.append(f"  task: {task}")
    return "\n".join(out)


def main() -> int:
    print("# Phase 1 results\n")
    print("## Per-package\n")
    print(per_package_table())
    print("\n## Aggregate\n")
    print(aggregate_table())
    print(residuals())
    return 0


if __name__ == "__main__":
    sys.exit(main())
