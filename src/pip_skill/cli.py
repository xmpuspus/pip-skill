"""CLI entry point for pip-skill."""

import argparse
import sys
from pathlib import Path

from pip_skill import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pip-skill",
        description="Convert pip packages into AI coding assistant skills",
        epilog=(
            "Examples:\n"
            "  pip-skill convert requests\n"
            "  pip-skill convert boto3 --mcp --format claude\n"
            "  pip-skill convert stripe --format cursor\n"
            "  pip-skill batch requests httpx --workers 4\n"
            "  pip-skill info pydantic\n"
            "  pip-skill diff ./my-requests-skill\n"
            "  pip-skill validate ./my-skill\n"
            "  pip-skill search boto3\n"
            "  pip-skill install requests\n"
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
    subparsers.add_parser("build", help="Interactive skill builder (requires pip-skill[tui])")

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

    # search command
    search_parser = subparsers.add_parser("search", help="Search the skill registry")
    search_parser.add_argument("query", nargs="?", default="", help="Search query")

    args = parser.parse_args(argv)

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
    elif args.command == "search":
        return cmd_search(args)

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

    # Phase 1: Introspect
    try:
        package_info = introspect_package(args.package)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Phase 2: Select
    selected = select_functions(
        package_info,
        max_tools=args.max_tools,
        include_patterns=args.include,
        exclude_patterns=args.exclude,
        verbose=args.verbose,
    )

    if not selected:
        print(f"Error: No usable functions found in '{args.package}'.", file=sys.stderr)
        return 2

    # Phase 3: Schema
    tool_schemas = build_tool_schemas([fn for fn, _ in selected])

    # Phase 4: Generate
    output_dir = args.output or Path(normalize_skill_name(args.package))
    if output_dir.exists() and not args.force:
        print(f"Error: '{output_dir}' already exists. Use --force to overwrite.", file=sys.stderr)
        return 3

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
    options = {"mcp": args.mcp, "format": fmt}
    written = render_templates(package_info, tool_schemas, options, output_dir)

    print(f"Generated plugin in: {output_dir}/")
    for path in written:
        print(f"  {path.relative_to(output_dir)}")

    return 0


def cmd_batch(args) -> int:
    """Convert multiple packages in parallel."""
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

    base_dir = args.output_dir or Path(".")
    fmt = getattr(args, "format", "claude")
    options = {"mcp": args.mcp, "format": fmt}
    errors = 0

    def _convert_one(pkg: str) -> tuple[str, int]:
        try:
            info = introspect_package(pkg)
        except ValueError:
            return pkg, 1

        selected = select_functions(info, max_tools=args.max_tools)
        if not selected:
            return pkg, 2

        schemas = build_tool_schemas([fn for fn, _ in selected])
        out = base_dir / normalize_skill_name(pkg)
        if out.exists() and not args.force:
            return pkg, 3

        render_templates(info, schemas, options, out)
        return pkg, 0

    workers = min(args.workers, len(packages))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_convert_one, pkg): pkg for pkg in packages}
        for fut in as_completed(futures):
            pkg, code = fut.result()
            if code == 0:
                print(f"[DONE] {pkg}")
            else:
                print(f"[FAIL] {pkg} (exit {code})", file=sys.stderr)
                errors += 1

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

        return run_tui()
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

    # Read current skill metadata
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

    # Read previously generated API reference to extract function names
    skill_name = meta.get("name", pkg_name)
    ref_path = plugin_dir / "skills" / skill_name / "references" / "api-reference.md"
    old_names: set[str] = set()
    if ref_path.exists():
        import re

        old_names = set(re.findall(r"`([^`]+)`", ref_path.read_text()))

    # Introspect current package
    from pip_skill.introspect import introspect_package
    from pip_skill.selector import select_functions

    try:
        info = introspect_package(pkg_name)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    selected = select_functions(info, max_tools=100)
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
