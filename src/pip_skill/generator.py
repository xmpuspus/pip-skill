"""Template rendering pipeline for pip-skill."""

from __future__ import annotations

import hashlib
import keyword
import logging
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

import jinja2

from pip_skill import __version__
from pip_skill.introspect import PackageInfo
from pip_skill.schema import ToolSchema
from pip_skill.utils import eval_default_safely, normalize_skill_name

# Stable placeholder used when --deterministic is set so the rendered
# plugin.json hashes to the same SHA-256 across machines and runs.
DETERMINISTIC_TIMESTAMP = "1970-01-01T00:00:00+00:00"

# Soft token budget for SKILL.md. SKILL.md is what the agent loads on every
# turn, so it should stay lean (detail lives in references/api-reference.md).
# This is advisory: sprawling SDKs with long docstrings can exceed it, and we
# warn rather than truncate so nothing is silently dropped.
SKILL_TOKEN_BUDGET = 5000


def estimate_tokens(text: str) -> int:
    """Rough token estimate for a string (~4 chars/token, as for English/code)."""
    return len(text) // 4


logger = logging.getLogger("pip_skill.generator")

# Tags an LLM may interpret as control directives in its context window.
_INJECTION_TAGS = re.compile(
    r"</?\s*(system|assistant|user|context|thinking|important|critical|"
    r"instructions|admin|tool_call|function_call|sandbox|inst|cmd|exec|"
    r"role|message|developer)\b[^>]*>",
    re.IGNORECASE,
)
_PY_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# reST/Sphinx markup that leaks from docstrings into the rendered skill as
# noise an agent has to read past. `:role:`target`` -> `target`; the
# `:role:`text <target>`` form keeps the human-readable text.
_REST_ROLE_WITH_TARGET = re.compile(r":[a-zA-Z:]+:`([^`<]+?)\s*<[^`>]+>`")
_REST_ROLE = re.compile(r":[a-zA-Z:]+:`([^`]+?)`")
_REST_DOUBLE_BACKTICK = re.compile(r"``([^`]+?)``")


def clean_rest_markup(text: str) -> str:
    """Convert leftover reST roles and double-backtick literals to plain text."""
    text = _REST_ROLE_WITH_TARGET.sub(r"`\1`", text)
    text = _REST_ROLE.sub(r"`\1`", text)
    text = _REST_DOUBLE_BACKTICK.sub(r"`\1`", text)
    return text


def sanitize_prose(text) -> str:
    """Neutralize prompt-injection patterns in package-supplied prose.

    A malicious package's docstring could contain `<system>...</system>` or
    `</thinking>...` tags that, when rendered into a SKILL.md the AI loads as
    authoritative skill instructions, are treated as a directive. This filter
    replaces those tags with bracketed labels (preserving readability while
    killing the directive) and breaks standalone `---` lines that would
    terminate YAML frontmatter.
    """
    if text is None:
        return ""
    s = str(text)
    s = _INJECTION_TAGS.sub(lambda m: "[" + re.sub(r"[^a-zA-Z]", "", m.group(0)) + "]", s)
    s = re.sub(r"^---+\s*$", "———", s, flags=re.MULTILINE)
    s = clean_rest_markup(s)
    return s


def is_safe_attr(name) -> bool:
    """True iff `name` is a single, non-keyword Python identifier.

    Used for the MCP `def <function_name>(...)` name and every parameter
    name — each must be exactly one identifier (no dots) and not a
    reserved word, or the generated `def class(...)` / `def a.b(...)` is a
    SyntaxError that breaks the whole server.
    """
    if not name:
        return False
    s = str(name)
    return bool(_PY_IDENT.match(s)) and not keyword.iskeyword(s)


def safe_identifier(name) -> bool:
    """True iff `name` is a non-keyword Python identifier or dotted path of them.

    Used to guard against attribute-name injection into the generated MCP
    server (which interpolates names directly into Python source). The
    dotted form is for `qualname` (``module.func``); single identifiers
    (function/param names) should use :func:`is_safe_attr`.
    """
    if not name:
        return False
    parts = str(name).split(".")
    return all(_PY_IDENT.match(part) and not keyword.iskeyword(part) for part in parts)


def tool_is_safe(tool: ToolSchema) -> bool:
    """True iff every name `tool` interpolates into Python source is safe.

    Guards the full set of names the MCP template emits into source: the
    function definition name, the dotted call target (`qualname`), and
    every parameter name (emitted both as a typed parameter and forwarded
    as `name=name`). Any unsafe name means the tool is skipped entirely
    rather than producing broken or injectable Python.
    """
    if not is_safe_attr(tool.function_name):
        return False
    if not safe_identifier(tool.qualname):
        return False
    return all(is_safe_attr(p.name) for p in tool.parameters)


def safe_default(default_repr) -> str:
    """Return `default_repr` only if it is a pure Python literal, else 'None'.

    Parameter defaults come from `repr(value)` of arbitrary package
    objects. A malicious package can ship a default whose `__repr__`
    returns executable code (``__import__('os').system(...)``); emitting
    that raw into a generated function signature is remote code execution
    the instant the server is imported. ``ast.literal_eval`` accepts only
    literals, so anything that isn't a plain str/int/float/bool/None/
    list/dict/tuple collapses to ``None``.
    """
    if default_repr is None:
        return "None"
    s = str(default_repr)
    if s == "None":
        return "None"
    try:
        eval_default_safely(s)
    except Exception:
        return "None"
    return s


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
            p += f" = {safe_default(param.default)}"
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
            p += f" = {safe_default(param.default)}"
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
        # JSON files use | tojson for safety; markdown prose uses | sanitize.
        # autoescape=True would HTML-escape every interpolation and break our
        # markdown / JSON / Python templates.
        autoescape=False,
    )
    env.filters["tools_signature"] = tools_signature
    env.filters["sanitize"] = sanitize_prose
    env.tests["safe_identifier"] = safe_identifier
    env.tests["safe_attr"] = is_safe_attr
    env.globals["tool_params_with_types"] = tool_params_with_types
    env.globals["tool_call_args"] = tool_call_args
    env.globals["safe_identifier"] = safe_identifier
    env.globals["is_safe_attr"] = is_safe_attr
    env.globals["tool_is_safe"] = tool_is_safe
    return env


def _build_context(
    package_info: PackageInfo,
    tool_schemas: list[ToolSchema],
    options: dict | None,
) -> dict:
    """Build the Jinja render context.

    When `options["deterministic"]` is truthy the `generatedAt`
    timestamp is replaced with `DETERMINISTIC_TIMESTAMP` so two
    consecutive renders against the same package version hash to the
    same bytes (required for reproducibility-citable workflows).
    """
    options = options or {}
    if options.get("deterministic"):
        timestamp = DETERMINISTIC_TIMESTAMP
    else:
        timestamp = datetime.now(UTC).isoformat()
    return {
        "package": package_info,
        "tools": tool_schemas,
        "options": options,
        "skill_name": normalize_skill_name(package_info.name),
        "timestamp": timestamp,
        "pip_skill_version": __version__,
    }


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
    context = _build_context(package_info, tool_schemas, options)
    return env.get_template("skill.md.j2").render(context)


def write_sha256_manifest(written: list[Path], output_dir: Path) -> Path:
    """Write a `MANIFEST.sha256` next to the generated bundle.

    Each line is `<sha256>  <relative path>` (BSD-coreutils format), so
    a downstream researcher can `sha256sum -c MANIFEST.sha256` and
    confirm the bundle was not altered. Paths are sorted so the file
    itself is reproducible.

    Args:
        written: List of files emitted by `render_templates`.
        output_dir: Bundle root; manifest is written here.

    Returns:
        The path to the written manifest.
    """
    entries: list[str] = []
    for path in sorted(written, key=lambda p: str(p)):
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rel = path.relative_to(output_dir).as_posix()
        entries.append(f"{digest}  {rel}")
    manifest = output_dir / "MANIFEST.sha256"
    manifest.write_text("\n".join(entries) + "\n", encoding="utf-8")
    return manifest


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
    p.write_text(content, encoding="utf-8")
    written.append(p)

    # skills/{name}/SKILL.md
    skill_dir = output_dir / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    content = env.get_template("skill.md.j2").render(context)
    p = skill_dir / "SKILL.md"
    p.write_text(content, encoding="utf-8")
    written.append(p)

    # skills/{name}/CONTEXT.md
    content = env.get_template("context.md.j2").render(context)
    p = skill_dir / "CONTEXT.md"
    p.write_text(content, encoding="utf-8")
    written.append(p)

    # skills/{name}/references/api-reference.md
    ref_dir = skill_dir / "references"
    ref_dir.mkdir(parents=True, exist_ok=True)
    content = env.get_template("api-reference.md.j2").render(context)
    p = ref_dir / "api-reference.md"
    p.write_text(content, encoding="utf-8")
    written.append(p)

    # MCP mode only
    if options.get("mcp"):
        scripts_dir = output_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        content = env.get_template("mcp-server.py.j2").render(context)
        p = scripts_dir / "mcp-server.py"
        p.write_text(content, encoding="utf-8")
        written.append(p)

        content = env.get_template("mcp-config.json.j2").render(context)
        p = output_dir / ".mcp.json"
        p.write_text(content, encoding="utf-8")
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
    p.write_text(content, encoding="utf-8")
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
    p.write_text(content, encoding="utf-8")
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
    p.write_text(content, encoding="utf-8")
    return [p]


def install_skill(
    output_dir: Path,
    package_name: str,
    fmt: str,
    force: bool = False,
    install_base: Path | None = None,
) -> Path:
    """Install generated skill to the appropriate tool directory.

    `package_name` is normalized internally (Pillow -> pillow, PyYAML -> pyyaml,
    discord.py -> discord-py) so this works on case-sensitive filesystems
    (Linux) the same way it works on macOS (APFS, case-insensitive).

    For Claude format, the entire skill bundle is copied — SKILL.md,
    CONTEXT.md, references/, AND the .claude-plugin/plugin.json — so the
    skill becomes a self-contained Claude Code plugin auto-discovered on
    the next session.

    Args:
        output_dir: Directory containing the generated skill files.
        package_name: Name of the package (will be normalized).
        fmt: Output format (claude, cursor, windsurf, opencode).
        force: Overwrite existing skill if True.
        install_base: Override default install location (for testing).

    Returns:
        Path where the skill was installed.
    """
    output_dir = Path(output_dir)
    skill_name = normalize_skill_name(package_name)

    if fmt == "claude":
        # Mirror the generated bundle exactly: a Claude plugin is
        # `.claude-plugin/plugin.json` + `skills/{name}/SKILL.md` (+ refs).
        base = install_base or Path.home() / ".claude" / "plugins"
        target = base / skill_name
        if target.exists() and not force:
            raise FileExistsError(f"Skill already installed at {target}. Use --force to overwrite.")
        if target.exists() and force:
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)

        # Copy plugin manifest
        plugin_src = output_dir / ".claude-plugin"
        if plugin_src.exists():
            shutil.copytree(plugin_src, target / ".claude-plugin")

        # Copy the entire skills/{skill_name}/ tree (SKILL.md, CONTEXT.md, references/)
        skill_src = output_dir / "skills" / skill_name
        if skill_src.exists():
            shutil.copytree(skill_src, target / "skills" / skill_name)

        # Copy MCP server + .mcp.json if present
        scripts_src = output_dir / "scripts"
        if scripts_src.exists():
            shutil.copytree(scripts_src, target / "scripts")
        mcp_json_src = output_dir / ".mcp.json"
        if mcp_json_src.exists():
            shutil.copy2(mcp_json_src, target / ".mcp.json")

        return target

    elif fmt == "cursor":
        base = install_base or Path.cwd()
        rules_dir = base / ".cursor" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        target = rules_dir / f"{skill_name}.mdc"
        if target.exists() and not force:
            raise FileExistsError(
                f"Cursor rules already exist at {target}. Use --force to overwrite."
            )
        src = output_dir / ".cursorrules"
        if src.exists():
            shutil.copy2(src, target)
        return target

    elif fmt == "windsurf":
        base = install_base or Path.cwd()
        rules_dir = base / ".windsurf" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        target = rules_dir / f"{skill_name}.md"
        if target.exists() and not force:
            raise FileExistsError(
                f"Windsurf rules already exist at {target}. Use --force to overwrite."
            )
        src = output_dir / ".windsurfrules"
        if src.exists():
            shutil.copy2(src, target)
        return target

    elif fmt == "opencode":
        base = install_base or Path.cwd()
        target = base / "AGENTS.md"
        if target.exists() and not force:
            raise FileExistsError(
                f"AGENTS.md already exists at {target}. Use --force to overwrite."
            )
        src = output_dir / "AGENTS.md"
        if src.exists():
            shutil.copy2(src, target)
        return target

    else:
        raise ValueError(f"Unknown format: {fmt}")


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
        options: CLI options dict (e.g., {'mcp': True, 'format': 'claude',
            'deterministic': True}). When `deterministic` is truthy the
            generated `plugin.json` uses a fixed timestamp and a
            `MANIFEST.sha256` is emitted next to the bundle.
        output_dir: Directory to write output into.

    Returns:
        List of Path objects for all files written.
    """
    env = _make_env()
    context = _build_context(package_info, tool_schemas, options)

    fmt = options.get("format", "claude")

    if fmt == "cursor":
        written = _render_cursor(env, context, output_dir)
    elif fmt == "windsurf":
        written = _render_windsurf(env, context, output_dir)
    elif fmt == "opencode":
        written = _render_opencode(env, context, output_dir)
    else:
        written = _render_claude(env, context, output_dir, options)

    if options.get("deterministic"):
        manifest_path = write_sha256_manifest(written, output_dir)
        written.append(manifest_path)

    return written
