"""CLI entry point for pip-skill."""
import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pip-skill",
        description="Convert pip packages to Claude Code plugins",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # convert command
    convert_parser = subparsers.add_parser(
        "convert", help="Generate a Claude Code plugin from an installed package"
    )
    convert_parser.add_argument("package", help="Installed pip package name")
    convert_parser.add_argument("--mcp", action="store_true", help="Generate MCP server")
    convert_parser.add_argument(
        "--select", action="store_true", help="Use LLM to curate function selection"
    )
    convert_parser.add_argument("--output", type=Path, help="Output directory")
    convert_parser.add_argument("--max-tools", type=int, default=20, help="Max functions")
    convert_parser.add_argument("--include", action="append", help="Include pattern")
    convert_parser.add_argument("--exclude", action="append", help="Exclude pattern")
    convert_parser.add_argument("--dry-run", action="store_true", help="Preview only")
    convert_parser.add_argument("--verbose", action="store_true", help="Show scoring")
    convert_parser.add_argument("--force", action="store_true", help="Overwrite output")

    # info command
    info_parser = subparsers.add_parser("info", help="Show package API surface")
    info_parser.add_argument("package", help="Installed pip package name")

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a generated plugin")
    validate_parser.add_argument("plugin_dir", type=Path, help="Plugin directory")

    args = parser.parse_args(argv)

    if args.command == "convert":
        return cmd_convert(args)
    elif args.command == "info":
        return cmd_info(args)
    elif args.command == "validate":
        return cmd_validate(args)

    return 1


def cmd_convert(args) -> int:
    """Generate a Claude Code plugin from an installed package."""
    from pip_skill.introspect import introspect_package
    from pip_skill.selector import select_functions
    from pip_skill.schema import build_tool_schemas
    from pip_skill.generator import render_templates
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
                # Find score for this tool
                score_map = {fn.name: s for fn, s in selected}
                score = score_map.get(tool.function_name, 0)
                score_info = f" (score: {score})"
            print(f"    - {tool.qualname}{score_info}")
        return 0

    options = {"mcp": args.mcp}
    written = render_templates(package_info, tool_schemas, options, output_dir)

    print(f"Generated plugin in: {output_dir}/")
    for path in written:
        print(f"  {path.relative_to(output_dir)}")

    return 0


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
