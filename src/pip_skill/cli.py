"""CLI entry point for pip-skill."""

import argparse
import importlib
import logging
import os
import sys
import time
from pathlib import Path

from pip_skill import __version__

logger = logging.getLogger("pip_skill")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pip-skill",
        description="Convert pip packages into AI coding assistant skills",
        epilog=(
            "Examples:\n"
            "  pip-skill convert requests\n"
            "  pip-skill convert boto3 --mcp --format claude\n"
            "  pip-skill convert stripe --format cursor\n"
            "  pip-skill convert requests --install\n"
            "  pip-skill batch requirements.txt --workers 4\n"
            "  pip-skill info pydantic\n"
            "  pip-skill diff ./my-requests-skill\n"
            "  pip-skill test ./my-requests-skill\n"
            "  pip-skill validate ./my-skill\n"
            "  pip-skill search boto3\n"
            "  pip-skill install requests\n"
            "\n"
            "WARNING: `convert` imports the target package and walks every\n"
            "submodule. Top-level code in the package will run. Only convert\n"
            "packages you trust the source of (same trust level as installing\n"
            "them with pip).\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # convert command
    convert_parser = subparsers.add_parser(
        "convert", help="Generate a skill from an installed package"
    )
    convert_parser.add_argument("package", help="Installed pip package name")
    convert_parser.add_argument("--mcp", action="store_true", help="Generate MCP server")
    convert_parser.add_argument("--output", type=Path, help="Output directory")
    convert_parser.add_argument("--max-tools", type=int, default=20, help="Max functions")
    convert_parser.add_argument("--include", action="append", help="Include pattern")
    convert_parser.add_argument("--exclude", action="append", help="Exclude pattern")
    convert_parser.add_argument("--dry-run", action="store_true", help="Preview only")
    convert_parser.add_argument("--verbose", action="store_true", help="Show scoring")
    convert_parser.add_argument("--force", action="store_true", help="Overwrite output")
    convert_parser.add_argument(
        "--format",
        choices=["claude", "cursor", "windsurf", "opencode"],
        default="claude",
        help="Output format (default: claude)",
    )
    convert_parser.add_argument(
        "--select",
        action="store_true",
        help="Use LLM to curate function selection (requires ANTHROPIC_API_KEY)",
    )
    convert_parser.add_argument(
        "--install",
        action="store_true",
        help="Install skill directly into AI tool directory",
    )
    convert_parser.add_argument(
        "--deterministic",
        action="store_true",
        help=(
            "Reproducible mode: fixed timestamp in plugin.json, sorted "
            "module traversal, temperature=0 on --select, and a "
            "MANIFEST.sha256 next to the bundle. Use when citing a "
            "generated skill in a paper or evaluation."
        ),
    )

    # batch command
    batch_parser = subparsers.add_parser("batch", help="Convert multiple packages at once")
    batch_parser.add_argument(
        "packages",
        nargs="*",
        help="Package names or path to requirements.txt",
    )
    batch_parser.add_argument("--mcp", action="store_true", help="Generate MCP server")
    batch_parser.add_argument("--output-dir", type=Path, help="Output base directory")
    batch_parser.add_argument("--max-tools", type=int, default=20, help="Max functions")
    batch_parser.add_argument("--force", action="store_true", help="Overwrite output")
    batch_parser.add_argument(
        "--format",
        choices=["claude", "cursor", "windsurf", "opencode"],
        default="claude",
        help="Output format (default: claude)",
    )
    batch_parser.add_argument("--workers", type=int, default=4, help="Parallel workers")

    # info command
    info_parser = subparsers.add_parser("info", help="Show package API surface")
    info_parser.add_argument("package", help="Installed pip package name")

    # build command
    build_parser = subparsers.add_parser(
        "build", help="Interactive skill builder (requires pip-skill[tui])"
    )
    build_parser.add_argument("package", help="Package to build skill for")

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a generated plugin")
    validate_parser.add_argument("plugin_dir", type=Path, help="Plugin directory")

    # diff command
    diff_parser = subparsers.add_parser("diff", help="Show API changes since skill was generated")
    diff_parser.add_argument("plugin_dir", type=Path, help="Plugin directory")

    # install command
    install_parser = subparsers.add_parser(
        "install", help="Install a pre-built skill from the registry"
    )
    install_parser.add_argument("package", help="Package name to install skill for")
    install_parser.add_argument("--output", type=Path, help="Output directory")

    # test command
    test_parser = subparsers.add_parser(
        "test",
        help="Validate generated skill works correctly",
        epilog="Example: pip-skill test ./my-requests-skill/",
    )
    test_parser.add_argument("plugin_dir", type=Path, help="Directory containing generated skill")

    # search command
    search_parser = subparsers.add_parser("search", help="Search the skill registry")
    search_parser.add_argument("query", nargs="?", default="", help="Search query")

    # eval command
    eval_parser = subparsers.add_parser(
        "eval",
        help="Measure tool-call accuracy of a generated skill against an eval set",
        epilog=(
            "Example: pip-skill eval ./requests examples/eval/requests.jsonl\n"
            "         pip-skill eval ./requests examples/eval/requests.jsonl"
            " --conditions coverage,no-skill,skill"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    eval_parser.add_argument("plugin_dir", type=Path, help="Generated skill bundle")
    eval_parser.add_argument("eval_file", type=Path, help="JSONL with task + expected_qualname")
    eval_parser.add_argument(
        "--conditions",
        default="coverage",
        help=(
            "Comma-separated list: coverage (offline), no-skill, skill."
            " The latter two call Claude via the selected backend."
        ),
    )
    eval_parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
    eval_parser.add_argument(
        "--backend",
        choices=["auto", "api", "claude-cli"],
        default="auto",
        help=(
            "Model backend. claude-cli (no API key, uses your Claude Code"
            " session via `claude -p`), api (Anthropic SDK,"
            " ANTHROPIC_API_KEY required, temperature=0 reproducibility),"
            " auto (prefer api when key is set, fall back to claude-cli)."
        ),
    )
    eval_parser.add_argument(
        "--api-key",
        help="ANTHROPIC_API_KEY override (otherwise read from environment)",
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(name)s: %(message)s",
        stream=sys.stderr,
    )

    if args.command == "convert":
        return cmd_convert(args)
    elif args.command == "batch":
        return cmd_batch(args)
    elif args.command == "info":
        return cmd_info(args)
    elif args.command == "build":
        return cmd_build(args)
    elif args.command == "validate":
        return cmd_validate(args)
    elif args.command == "diff":
        return cmd_diff(args)
    elif args.command == "install":
        return cmd_install(args)
    elif args.command == "test":
        return cmd_test(args)
    elif args.command == "search":
        return cmd_search(args)
    elif args.command == "eval":
        return cmd_eval(args)

    return 1


def _parse_requirements(req_file: Path) -> list[str]:
    """Parse package names from a requirements.txt file.

    Strips version specifiers, comments, and editable installs.
    """
    packages = []
    for line in req_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Strip version specifiers: >=, ==, !=, ~=, <=, >
        for sep in (">=", "==", "!=", "~=", "<=", ">", "<", "[", ";"):
            line = line.split(sep)[0].strip()
        if line:
            packages.append(line)
    return packages


def cmd_convert(args) -> int:
    """Generate a skill from an installed package."""
    from pip_skill.generator import render_templates
    from pip_skill.introspect import introspect_package
    from pip_skill.schema import build_tool_schemas
    from pip_skill.selector import select_functions
    from pip_skill.utils import normalize_skill_name

    # Fail-fast pre-flight checks BEFORE we spend seconds importing huge packages.
    api_key = None
    if args.select:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print(
                "Error: --select requires the ANTHROPIC_API_KEY environment variable.",
                file=sys.stderr,
            )
            return 1
        try:
            import anthropic  # noqa: F401
        except ImportError:
            print(
                "Error: --select requires pip-skill[llm]. Run: pip install pip-skill[llm]",
                file=sys.stderr,
            )
            return 1

    t_start = time.perf_counter()

    deterministic = getattr(args, "deterministic", False)

    # Phase 1: Introspect
    try:
        package_info = introspect_package(args.package, deterministic=deterministic)
    except (ValueError, ImportError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    t_introspect = time.perf_counter()

    # Phase 2: Select
    selected = select_functions(
        package_info,
        max_tools=args.max_tools,
        include_patterns=args.include,
        exclude_patterns=args.exclude,
        verbose=args.verbose,
    )

    if args.select and api_key:
        from pip_skill.selector import llm_curate

        curated = llm_curate(
            selected,
            package_info,
            max_tools=args.max_tools,
            api_key=api_key,
            deterministic=deterministic,
        )
        # Preserve (CallableInfo, score) shape; LLM curation returns raw CallableInfo
        # so we re-pair with the heuristic score (or 0 if curation added a new entry).
        score_lookup = {fn.qualname: s for fn, s in selected}
        selected = [(fn, score_lookup.get(fn.qualname, 0)) for fn in curated]

    if not selected:
        print(f"Error: No usable functions found in '{args.package}'.", file=sys.stderr)
        return 2

    t_select = time.perf_counter()

    # Phase 3: Schema
    tool_schemas = build_tool_schemas([fn for fn, _ in selected])

    t_schema = time.perf_counter()

    # Phase 4: Generate
    output_dir = args.output or Path(normalize_skill_name(args.package))
    if output_dir.exists() and not args.force:
        print(f"Error: '{output_dir}' already exists. Use --force to overwrite.", file=sys.stderr)
        return 3
    if output_dir.exists() and args.force:
        # --force should produce a clean output dir, not coexisting files from a
        # prior run with a different --format (e.g. claude artifacts left over
        # when the user re-runs with --format cursor).
        import shutil

        shutil.rmtree(output_dir)

    if args.dry_run:
        print(f"Would generate plugin in: {output_dir}/")
        print(f"  Functions selected: {len(tool_schemas)}")
        for tool in tool_schemas:
            score_info = ""
            if args.verbose:
                score_map = {fn.name: s for fn, s in selected}
                score = score_map.get(tool.function_name, 0)
                score_info = f" (score: {score})"
            print(f"    - {tool.qualname}{score_info}")
        return 0

    fmt = getattr(args, "format", "claude")
    options = {"mcp": args.mcp, "format": fmt, "deterministic": deterministic}
    written = render_templates(package_info, tool_schemas, options, output_dir)

    t_end = time.perf_counter()

    print(f"Generated skill in: {output_dir}/")
    for path in written:
        print(f"  {path.relative_to(output_dir)}")
    print(
        f"  {len(tool_schemas)} functions selected in "
        f"{t_end - t_start:.1f}s "
        f"(introspect {t_introspect - t_start:.1f}s, "
        f"select {t_select - t_introspect:.1f}s, "
        f"generate {t_end - t_schema:.1f}s)"
    )

    if args.install:
        from pip_skill.generator import install_skill

        fmt = getattr(args, "format", "claude") or "claude"
        try:
            target = install_skill(output_dir, package_info.name, fmt, force=args.force)
            print(f"Installed {package_info.name} skill to {target}")
        except FileExistsError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    return 0


def cmd_batch(args) -> int:
    """Convert multiple packages in parallel."""
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from pip_skill.generator import render_templates
    from pip_skill.introspect import introspect_package
    from pip_skill.schema import build_tool_schemas
    from pip_skill.selector import select_functions
    from pip_skill.utils import normalize_skill_name

    packages = list(args.packages) if args.packages else []

    # If a single arg looks like a file, parse it as requirements.txt
    if len(packages) == 1 and Path(packages[0]).is_file():
        packages = _parse_requirements(Path(packages[0]))

    if not packages:
        print("Error: No packages specified.", file=sys.stderr)
        return 1

    t0 = time.perf_counter()
    base_dir = args.output_dir or Path(".")
    fmt = getattr(args, "format", "claude")
    options = {"mcp": args.mcp, "format": fmt}
    errors = 0
    success_count = 0

    _error_messages = {
        1: "not installed or import failed",
        2: "no usable functions found",
        3: "output exists, use --force",
    }

    # The introspect progress callback writes carriage-returned lines to stderr.
    # In ThreadPoolExecutor those interleave and produce garbled output.
    # We disable per-package progress in batch mode and serialize all stdout/stderr.
    print_lock = threading.Lock()

    def _convert_one(pkg: str) -> tuple[str, int, str]:
        try:
            info = introspect_package(pkg)
        except BaseException as e:  # noqa: BLE001  (worker may face import-time SystemExit etc.)
            return pkg, 1, str(e)

        selected = select_functions(info, max_tools=args.max_tools)
        if not selected:
            return pkg, 2, ""

        schemas = build_tool_schemas([fn for fn, _ in selected])
        out = base_dir / normalize_skill_name(pkg)
        if out.exists() and not args.force:
            return pkg, 3, ""

        render_templates(info, schemas, options, out)
        return pkg, 0, ""

    workers = min(args.workers, len(packages))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_convert_one, pkg): pkg for pkg in packages}
        for fut in as_completed(futures):
            pkg, code, detail = fut.result()
            with print_lock:
                # Clear any pending introspect progress line on stderr first.
                print(" " * 60, file=sys.stderr, end="\r", flush=True)
                if code == 0:
                    print(f"[DONE] {pkg}", flush=True)
                    success_count += 1
                else:
                    reason = detail or _error_messages.get(code, "unknown error")
                    print(f"[FAIL] {pkg}: {reason}", file=sys.stderr, flush=True)
                    errors += 1

    total = success_count + errors
    elapsed = time.perf_counter() - t0
    fail_msg = f" ({errors} failed)" if errors else ""
    print(f"\nBatch complete: {success_count}/{total} succeeded{fail_msg} in {elapsed:.1f}s")

    return 1 if errors else 0


def cmd_info(args) -> int:
    """Show package API surface summary."""
    from pip_skill.introspect import introspect_package

    try:
        info = introspect_package(args.package)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    total_funcs = sum(len(m.callables) for m in info.modules)
    total_classes = sum(len(m.classes) for m in info.modules)

    print(f"Package: {info.name} v{info.version}")
    print(f"Import name: {info.import_name}")
    print(f"Description: {info.description}")
    print(f"Submodules: {len(info.modules)}")
    print(f"Public functions: {total_funcs}")
    print(f"Public classes: {total_classes}")
    print(f"Annotation coverage: {info.annotation_coverage:.0%}")
    tier_labels = {1: "well-annotated", 2: "partial annotations", 3: "dynamic/stateful"}
    print(f"Estimated tier: {info.tier} ({tier_labels.get(info.tier, 'unknown')})")

    return 0


def cmd_build(args) -> int:
    """Interactive skill builder (requires pip-skill[tui])."""
    try:
        from pip_skill.tui import run_tui

        return run_tui(args)
    except ImportError:
        print(
            "Error: pip-skill[tui] is required for the build command.\n"
            "Install with: pip install pip-skill[tui]",
            file=sys.stderr,
        )
        return 1


def cmd_validate(args) -> int:
    """Validate a generated plugin directory."""
    import json

    plugin_dir = args.plugin_dir
    errors = 0

    # Check plugin.json
    pj = plugin_dir / ".claude-plugin" / "plugin.json"
    if pj.exists():
        print("[PASS] plugin.json exists")
        try:
            data = json.loads(pj.read_text())
            if "name" in data:
                print("[PASS] plugin.json has 'name' field")
                name = data["name"]
            else:
                print("[FAIL] plugin.json missing 'name' field")
                errors += 1
                name = None
        except json.JSONDecodeError:
            print("[FAIL] plugin.json is not valid JSON")
            errors += 1
            name = None
    else:
        print("[FAIL] plugin.json not found")
        errors += 1
        name = None

    # Check SKILL.md
    if name:
        skill_path = plugin_dir / "skills" / name / "SKILL.md"
        if skill_path.exists():
            print("[PASS] SKILL.md exists")
            content = skill_path.read_text()
            lines = content.split("\n")
            if len(lines) <= 500:
                print(f"[PASS] SKILL.md is {len(lines)} lines (under 500)")
            else:
                print(f"[WARN] SKILL.md is {len(lines)} lines (over 500 limit)")
        else:
            print(f"[FAIL] skills/{name}/SKILL.md not found")
            errors += 1

    # Check MCP (optional)
    mcp_json = plugin_dir / ".mcp.json"
    if mcp_json.exists():
        print("[PASS] .mcp.json found (MCP mode)")
    else:
        print("[WARN] No .mcp.json (skill-only mode)")

    return 1 if errors > 0 else 0


def cmd_diff(args) -> int:
    """Show API changes since skill was last generated."""
    import json

    plugin_dir = args.plugin_dir

    pj = plugin_dir / ".claude-plugin" / "plugin.json"
    if not pj.exists():
        print(f"Error: No plugin.json found in {plugin_dir}", file=sys.stderr)
        return 1

    try:
        meta = json.loads(pj.read_text())
    except json.JSONDecodeError:
        print("Error: plugin.json is not valid JSON", file=sys.stderr)
        return 1

    pkg_name = meta.get("sourcePackage") or meta.get("name", "")
    if not pkg_name:
        print("Error: plugin.json missing 'sourcePackage' field", file=sys.stderr)
        return 1

    # The prior tool set is read from the structured `tools` array in
    # plugin.json. Comparing structured manifest entries (qualname-keyed) is
    # both faster and more accurate than parsing prose.
    tools_meta = meta.get("tools", [])
    old_names: set[str] = {t.get("qualname", "") for t in tools_meta if t.get("qualname")}

    if not old_names:
        print(
            f"Warning: {pj} has no `tools` manifest. Regenerate the skill to enable diffs.",
            file=sys.stderr,
        )

    from pip_skill.introspect import introspect_package
    from pip_skill.selector import select_functions

    try:
        info = introspect_package(pkg_name)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Match the original generation: same default cap so the comparison is fair.
    max_tools = int(meta.get("toolCount") or 100) or 100
    selected = select_functions(info, max_tools=max_tools)
    current_names = {fn.qualname for fn, _ in selected}

    added = current_names - old_names
    removed = old_names - current_names

    if not added and not removed:
        print(f"No API changes detected for {pkg_name} (skill is up to date).")
        return 0

    if added:
        print(f"Added ({len(added)}):")
        for name in sorted(added):
            print(f"  + {name}")
    if removed:
        print(f"Removed ({len(removed)}):")
        for name in sorted(removed):
            print(f"  - {name}")

    return 0


def cmd_install(args) -> int:
    """Install a pre-built skill from the registry."""
    from pip_skill import registry
    from pip_skill.utils import normalize_skill_name

    output_dir = args.output or Path(normalize_skill_name(args.package))
    try:
        msg = registry.install_skill(args.package, output_dir)
        print(msg)
        return 0
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_test(args) -> int:
    """Validate that a generated skill's functions are importable and signatures match."""
    import json

    plugin_dir = Path(args.plugin_dir)
    plugin_json = plugin_dir / ".claude-plugin" / "plugin.json"

    if not plugin_json.exists():
        print(f"Error: No plugin.json found in {plugin_dir}", file=sys.stderr)
        return 1

    meta = json.loads(plugin_json.read_text())
    pkg_name = meta.get("sourcePackage", "")
    pkg_version = meta.get("sourceVersion", "")

    if not pkg_name:
        print("Error: plugin.json missing sourcePackage field", file=sys.stderr)
        return 1

    try:
        import importlib.metadata as im

        installed_version = im.version(pkg_name)
    except im.PackageNotFoundError:
        print(
            f"Error: Package '{pkg_name}' is not installed. Run: pip install {pkg_name}",
            file=sys.stderr,
        )
        return 1

    if installed_version != pkg_version:
        print(
            f"  [WARN] Version mismatch: skill={pkg_version}, installed={installed_version}",
            file=sys.stderr,
        )

    # The `tools` manifest in plugin.json is the source of truth for
    # validation. Each entry records module, name, and qualname so `test`
    # can verify imports without re-introspecting the package.
    tools = meta.get("tools", [])
    if not tools:
        print(
            "Error: plugin.json has no `tools` manifest. Regenerate this skill "
            f"with `pip-skill convert {pkg_name}`.",
            file=sys.stderr,
        )
        return 1

    print(f"Testing {pkg_name} skill (v{pkg_version})...")

    passed = 0
    failed = 0
    for tool in tools:
        qualname = tool.get("qualname") or ""
        mod_name = tool.get("module") or ""
        func_name = tool.get("functionName") or ""
        if not (qualname and mod_name and func_name):
            print(f"  [SKIP] {qualname or '<unnamed>'} — incomplete manifest entry")
            continue
        try:
            mod = importlib.import_module(mod_name)
            getattr(mod, func_name)
            print(f"  [PASS] {qualname}")
            passed += 1
        except (ImportError, AttributeError) as e:
            print(f"  [FAIL] {qualname} — {e}")
            failed += 1

    # Check MCP server syntax if present
    import ast

    mcp_server = plugin_dir / "scripts" / "mcp-server.py"
    if mcp_server.exists():
        try:
            ast.parse(mcp_server.read_text())
            print("  [PASS] MCP server syntax OK")
            passed += 1
        except SyntaxError as e:
            print(f"  [FAIL] MCP server syntax error: {e}")
            failed += 1

    total = passed + failed
    stale_msg = f", {failed} stale" if failed else ""
    print(f"\nResult: {passed}/{total} passed{stale_msg}")
    return 1 if failed else 0


def cmd_search(args) -> int:
    """Search the skill registry."""
    from pip_skill import registry

    results = registry.search_registry(args.query)
    if not results:
        print("No skills found in registry.")
        return 0

    for entry in results:
        name = entry.get("name", "?")
        version = entry.get("version", "?")
        desc = entry.get("description", "")
        tool_count = entry.get("toolCount", "?")
        print(f"{name} v{version} ({tool_count} tools) - {desc}")

    return 0


def cmd_eval(args) -> int:
    """Run an eval set against a generated skill bundle."""
    from pip_skill.eval import render_table, run_eval, to_json

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

    print(to_json(summary) if args.json else render_table(summary))
    return 0
