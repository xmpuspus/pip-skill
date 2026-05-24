"""High-level Python API for pip-skill.

The CLI is a thin wrapper over `generate_skill()`. Import this module
when scripting from a notebook, eval harness, or CI job.

Example:
    >>> from pip_skill import generate_skill
    >>> result = generate_skill("requests", deterministic=True)
    >>> print(result.tool_count, result.bundle_dir)
    20 PosixPath('requests')
    >>> result.tool_names[:3]
    ['requests.get', 'requests.post', 'requests.put']

The returned `SkillBundle` dataclass exposes the introspected
`PackageInfo`, the selected `ToolSchema` list, the on-disk paths, and
(in deterministic mode) the SHA-256 manifest path.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from pip_skill.generator import render_templates
from pip_skill.introspect import PackageInfo, introspect_package
from pip_skill.schema import ToolSchema, build_tool_schemas
from pip_skill.selector import select_functions
from pip_skill.utils import normalize_skill_name


@dataclass
class SkillBundle:
    """The output of `generate_skill()`.

    Attributes:
        package: Introspected package metadata + module tree.
        tools: Schemas of selected callables (sorted by descending score).
        bundle_dir: Root of the generated skill on disk.
        files_written: All paths written under `bundle_dir`.
        manifest_path: Path to `MANIFEST.sha256` when deterministic
            mode was enabled, otherwise None.
    """

    package: PackageInfo
    tools: list[ToolSchema]
    bundle_dir: Path
    files_written: list[Path]
    manifest_path: Path | None = None
    scores: list[int] = field(default_factory=list)

    @property
    def tool_count(self) -> int:
        return len(self.tools)

    @property
    def tool_names(self) -> list[str]:
        return [t.qualname for t in self.tools]


def generate_skill(
    package: str,
    *,
    output_dir: str | Path | None = None,
    fmt: str = "claude",
    max_tools: int = 20,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    mcp: bool = False,
    select: bool = False,
    api_key: str | None = None,
    deterministic: bool = False,
    force: bool = False,
) -> SkillBundle:
    """Generate a skill from an installed pip package.

    This is the same pipeline the CLI runs. Returns a `SkillBundle` so
    callers (eval harnesses, notebooks, CI jobs) can inspect the
    selected tools and on-disk paths without parsing CLI output.

    Args:
        package: The pip name (e.g. ``"requests"``, ``"Pillow"``).
        output_dir: Where to write the bundle. Defaults to the
            normalized skill name in the current directory.
        fmt: One of ``"claude"``, ``"cursor"``, ``"windsurf"``,
            ``"opencode"``.
        max_tools: Cap on the number of tools to include.
        include: Optional glob patterns; only matching names are
            considered.
        exclude: Optional glob patterns; matching names are dropped.
        mcp: When True, also emit a FastMCP server alongside SKILL.md.
        select: When True, use Claude to re-rank the heuristic top-30.
            Requires ``api_key`` or ``ANTHROPIC_API_KEY`` in the
            environment, plus the ``[llm]`` extra installed.
        api_key: Anthropic API key for ``select``. Falls back to
            ``ANTHROPIC_API_KEY`` env var.
        deterministic: When True, fix the bundle timestamp, sort module
            traversal, force ``temperature=0`` on ``select``, and emit
            ``MANIFEST.sha256`` next to the bundle. Use this for any
            citable artifact (papers, eval baselines, release pins).
        force: When True, overwrite an existing `output_dir`.

    Returns:
        A `SkillBundle` with the introspected package, selected tools,
        and on-disk paths.

    Raises:
        ValueError: If the package is not installed or has no usable
            functions, or if ``select=True`` without an API key.
        FileExistsError: If `output_dir` exists and ``force=False``.
    """
    package_info = introspect_package(package, deterministic=deterministic)

    selected = select_functions(
        package_info,
        max_tools=max_tools,
        include_patterns=include,
        exclude_patterns=exclude,
    )

    if select:
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError(
                "select=True requires `api_key=` or ANTHROPIC_API_KEY in the environment."
            )
        from pip_skill.selector import llm_curate

        curated = llm_curate(
            selected,
            package_info,
            max_tools=max_tools,
            api_key=key,
            deterministic=deterministic,
        )
        score_lookup = {fn.qualname: s for fn, s in selected}
        selected = [(fn, score_lookup.get(fn.qualname, 0)) for fn in curated]

    if not selected:
        raise ValueError(f"No usable functions found in '{package}'.")

    tool_schemas = build_tool_schemas([fn for fn, _ in selected])
    scores = [s for _, s in selected]

    out = Path(output_dir) if output_dir else Path(normalize_skill_name(package))
    if out.exists() and not force:
        raise FileExistsError(f"'{out}' already exists. Pass force=True to overwrite.")
    if out.exists() and force:
        import shutil

        shutil.rmtree(out)

    options = {
        "mcp": mcp,
        "format": fmt,
        "deterministic": deterministic,
    }
    written = render_templates(package_info, tool_schemas, options, out)

    manifest_path = None
    for p in written:
        if p.name == "MANIFEST.sha256":
            manifest_path = p
            break

    return SkillBundle(
        package=package_info,
        tools=tool_schemas,
        bundle_dir=out,
        files_written=written,
        manifest_path=manifest_path,
        scores=scores,
    )


__all__ = ["SkillBundle", "generate_skill"]
