"""Template rendering pipeline for pip-skill."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import jinja2

from pip_skill import __version__
from pip_skill.introspect import PackageInfo
from pip_skill.schema import ToolSchema
from pip_skill.utils import normalize_skill_name


def tools_signature(tool: ToolSchema) -> str:
    """Render a Python-style signature string from a ToolSchema.

    Args:
        tool: The tool schema to render a signature for.

    Returns:
        A signature string like '(url: str, timeout: int = 30) -> dict'.
    """
    parts = []
    for param in tool.parameters:
        p = param.name
        if param.type_str and param.type_str != "any":
            p += f": {param.type_str}"
        if not param.required:
            p += f" = {param.default or 'None'}"
        parts.append(p)
    sig = ", ".join(parts)
    ret = f" -> {tool.output_hint}" if tool.output_hint and tool.output_hint != "unknown" else ""
    return f"({sig}){ret}"


def tool_params_with_types(tool: ToolSchema) -> str:
    """Render typed parameters for MCP tool function signature.

    Args:
        tool: The tool schema.

    Returns:
        Parameter string suitable for a Python function definition.
    """
    type_map = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
    }
    parts = []
    for param in tool.parameters:
        py_type = type_map.get(param.json_type, "str")
        if not param.required:
            py_type = f"{py_type} | None"
        p = f"{param.name}: {py_type}"
        if not param.required:
            p += f" = {param.default or 'None'}"
        parts.append(p)
    return ", ".join(parts)


def tool_call_args(tool: ToolSchema) -> str:
    """Render the argument-forwarding call for an MCP tool.

    Args:
        tool: The tool schema.

    Returns:
        Argument string like 'url=url, timeout=timeout'.
    """
    parts = [f"{param.name}={param.name}" for param in tool.parameters]
    return ", ".join(parts)


def _make_env() -> jinja2.Environment:
    """Create and configure the Jinja2 environment."""
    env = jinja2.Environment(
        loader=jinja2.PackageLoader("pip_skill", "templates"),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["tools_signature"] = tools_signature
    env.globals["tool_params_with_types"] = tool_params_with_types
    env.globals["tool_call_args"] = tool_call_args
    return env


def render_skill_md_string(
    package_info: PackageInfo,
    tool_schemas: list[ToolSchema],
    options: dict | None = None,
) -> str:
    """Render SKILL.md content as a string without writing to disk.

    Used by the TUI builder for live preview.

    Args:
        package_info: The introspected package info.
        tool_schemas: Selected tools with schemas.
        options: Optional CLI options dict.

    Returns:
        Rendered SKILL.md content as a string.
    """
    env = _make_env()
    skill_name = normalize_skill_name(package_info.name)
    context = {
        "package": package_info,
        "tools": tool_schemas,
        "options": options or {},
        "skill_name": skill_name,
        "timestamp": datetime.now(UTC).isoformat(),
        "pip_skill_version": __version__,
    }
    return env.get_template("skill.md.j2").render(context)


def _render_claude(
    env: jinja2.Environment,
    context: dict,
    output_dir: Path,
    options: dict,
) -> list[Path]:
    """Render Claude Code skill format (default)."""
    skill_name = context["skill_name"]
    written: list[Path] = []

    # .claude-plugin/plugin.json
    plugin_dir = output_dir / ".claude-plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    content = env.get_template("plugin.json.j2").render(context)
    p = plugin_dir / "plugin.json"
    p.write_text(content)
    written.append(p)

    # skills/{name}/SKILL.md
    skill_dir = output_dir / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    content = env.get_template("skill.md.j2").render(context)
    p = skill_dir / "SKILL.md"
    p.write_text(content)
    written.append(p)

    # skills/{name}/CONTEXT.md
    content = env.get_template("context.md.j2").render(context)
    p = skill_dir / "CONTEXT.md"
    p.write_text(content)
    written.append(p)

    # skills/{name}/references/api-reference.md
    ref_dir = skill_dir / "references"
    ref_dir.mkdir(parents=True, exist_ok=True)
    content = env.get_template("api-reference.md.j2").render(context)
    p = ref_dir / "api-reference.md"
    p.write_text(content)
    written.append(p)

    # MCP mode only
    if options.get("mcp"):
        scripts_dir = output_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        content = env.get_template("mcp-server.py.j2").render(context)
        p = scripts_dir / "mcp-server.py"
        p.write_text(content)
        written.append(p)

        content = env.get_template("mcp-config.json.j2").render(context)
        p = output_dir / ".mcp.json"
        p.write_text(content)
        written.append(p)

    return written


def _render_cursor(
    env: jinja2.Environment,
    context: dict,
    output_dir: Path,
) -> list[Path]:
    """Render Cursor .cursorrules format."""
    output_dir.mkdir(parents=True, exist_ok=True)
    content = env.get_template("cursorrules.j2").render(context)
    p = output_dir / ".cursorrules"
    p.write_text(content)
    return [p]


def _render_windsurf(
    env: jinja2.Environment,
    context: dict,
    output_dir: Path,
) -> list[Path]:
    """Render Windsurf .windsurfrules format."""
    output_dir.mkdir(parents=True, exist_ok=True)
    content = env.get_template("windsurfrules.j2").render(context)
    p = output_dir / ".windsurfrules"
    p.write_text(content)
    return [p]


def _render_opencode(
    env: jinja2.Environment,
    context: dict,
    output_dir: Path,
) -> list[Path]:
    """Render OpenCode AGENTS.md format."""
    output_dir.mkdir(parents=True, exist_ok=True)
    content = env.get_template("agents-md.j2").render(context)
    p = output_dir / "AGENTS.md"
    p.write_text(content)
    return [p]


def render_templates(
    package_info: PackageInfo,
    tool_schemas: list[ToolSchema],
    options: dict,
    output_dir: Path,
) -> list[Path]:
    """Render all templates and write to the output directory.

    Args:
        package_info: The introspected package info.
        tool_schemas: Selected tools with schemas.
        options: CLI options dict (e.g., {'mcp': True, 'format': 'claude'}).
        output_dir: Directory to write output into.

    Returns:
        List of Path objects for all files written.
    """
    env = _make_env()
    skill_name = normalize_skill_name(package_info.name)

    context = {
        "package": package_info,
        "tools": tool_schemas,
        "options": options,
        "skill_name": skill_name,
        "timestamp": datetime.now(UTC).isoformat(),
        "pip_skill_version": __version__,
    }

    fmt = options.get("format", "claude")

    if fmt == "cursor":
        return _render_cursor(env, context, output_dir)
    elif fmt == "windsurf":
        return _render_windsurf(env, context, output_dir)
    elif fmt == "opencode":
        return _render_opencode(env, context, output_dir)
    else:
        return _render_claude(env, context, output_dir, options)
