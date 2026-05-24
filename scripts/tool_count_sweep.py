#!/usr/bin/env python3
"""Sweep max_tools and measure skill-condition accuracy.

Hypothesis: more tools in the SKILL.md menu is not monotonically
better. After some N, the model gets distracted by similarly-named
alternatives and accuracy drops or plateaus.

Usage:
    python scripts/tool_count_sweep.py <package> <eval-file.jsonl> [N N N ...]

For each N in the sweep, regenerates the skill at max_tools=N (in a
temporary dir, deterministic mode), runs the eval set under three
conditions (coverage, no-skill, skill), and emits a table.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

from pip_skill import generate_skill
from pip_skill.eval import run_eval

DEFAULT_NS = [5, 10, 20, 40]


def main() -> int:
    if len(sys.argv) < 3:
        print(
            f"Usage: {sys.argv[0]} <package> <eval-file.jsonl> [N N N ...]",
            file=sys.stderr,
        )
        return 2

    package = sys.argv[1]
    eval_path = Path(sys.argv[2])
    ns = [int(x) for x in sys.argv[3:]] if len(sys.argv) > 3 else DEFAULT_NS

    print(f"Package:    {package}")
    print(f"Eval:       {eval_path}")
    print(f"Sweep:      max_tools in {ns}")
    print()

    rows = []
    workdir = Path(tempfile.mkdtemp(prefix="pip-skill-sweep-"))
    try:
        for n in ns:
            out = workdir / f"{package}-n{n}"
            bundle = generate_skill(
                package,
                output_dir=out,
                max_tools=n,
                deterministic=True,
            )
            summary = run_eval(
                bundle.bundle_dir,
                eval_path,
                ["coverage", "no-skill", "skill"],
            )
            cov = summary.per_condition_rate["coverage"]
            no_skill = summary.per_condition_rate["no-skill"]
            skill = summary.per_condition_rate["skill"]
            # Conditional skill rate: of items where the tool is in
            # the manifest, what fraction did the model get right?
            cov_pass = summary.per_condition_pass["coverage"]
            skill_pass = summary.per_condition_pass["skill"]
            conditional = skill_pass / cov_pass if cov_pass else 0.0
            rows.append((n, bundle.tool_count, cov, no_skill, skill, conditional))
            print(
                f"N={n:>3} tools={bundle.tool_count:>3}  "
                f"cov={cov * 100:5.1f}%  no-skill={no_skill * 100:5.1f}%  "
                f"skill={skill * 100:5.1f}%  cond={conditional * 100:5.1f}%"
            )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print()
    print("max_tools  bundle  coverage  no-skill  skill   cond_skill")
    print("---------  ------  --------  --------  -----   ----------")
    for n, bundle_n, cov, ns_rate, sk_rate, cond in rows:
        print(
            f"{n:>9}  {bundle_n:>6}  {cov * 100:>7.1f}%  {ns_rate * 100:>7.1f}%  "
            f"{sk_rate * 100:>4.1f}%   {cond * 100:>9.1f}%"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
