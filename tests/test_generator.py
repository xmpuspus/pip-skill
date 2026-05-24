"""Tests for pip_skill.generator."""

import importlib
import json

from pip_skill.generator import (
    render_templates,
    tool_call_args,
    tool_params_with_types,
    tools_signature,
)
from pip_skill.introspect import extract_callable_info
from pip_skill.schema import build_tool_schema


def _fetch_tool(fake_package_on_path):
    mod = importlib.import_module("fake_package.api")
    info = extract_callable_info("fetch", mod.fetch, "fake_package.api")
    return build_tool_schema(info)


def test_render_plugin_json(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    render_templates(fake_package_info, [tool], {"mcp": False}, tmp_path)

    pj = tmp_path / ".claude-plugin" / "plugin.json"
    assert pj.exists()
    data = json.loads(pj.read_text())
    assert data["name"] == "fake-package"
    assert data["version"] == "1.0.0"
    assert data["sourcePackage"] == "fake-package"
    assert data["importName"] == "fake_package"
    assert data["toolCount"] == 1
    assert "generatedBy" in data
    assert "generatedAt" in data


def test_render_skill_md(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    render_templates(fake_package_info, [tool], {"mcp": False}, tmp_path)

    skill = tmp_path / "skills" / "fake-package" / "SKILL.md"
    assert skill.exists()
    content = skill.read_text()
    assert "---" in content
    assert "fake-package" in content
    assert "fetch" in content


def test_render_skill_md_frontmatter(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    render_templates(fake_package_info, [tool], {"mcp": False}, tmp_path)

    content = (tmp_path / "skills" / "fake-package" / "SKILL.md").read_text()
    lines = content.splitlines()
    assert lines[0] == "---"
    assert any("name:" in line for line in lines)
    assert any("description:" in line for line in lines)
    assert any("compatibility:" in line for line in lines)
    assert any("tool-count:" in line for line in lines)


def test_render_api_reference(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    render_templates(fake_package_info, [tool], {"mcp": False}, tmp_path)

    ref = tmp_path / "skills" / "fake-package" / "references" / "api-reference.md"
    assert ref.exists()
    content = ref.read_text()
    assert "JSON Schema" in content
    assert "fetch" in content


def test_render_mcp_server(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    render_templates(fake_package_info, [tool], {"mcp": True}, tmp_path)

    server = tmp_path / "scripts" / "mcp-server.py"
    assert server.exists()
    content = server.read_text()
    assert "FastMCP" in content
    assert "@mcp.tool()" in content

    mcp_json = tmp_path / ".mcp.json"
    assert mcp_json.exists()


def test_no_mcp_without_flag(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    render_templates(fake_package_info, [tool], {"mcp": False}, tmp_path)

    assert not (tmp_path / "scripts" / "mcp-server.py").exists()
    assert not (tmp_path / ".mcp.json").exists()


def test_render_returns_paths(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    written = render_templates(fake_package_info, [tool], {"mcp": False}, tmp_path)

    assert len(written) == 4
    for p in written:
        assert p.exists()


def test_tools_signature_full():
    from pip_skill.schema import ToolParam, ToolSchema

    tool = ToolSchema(
        name="fetch",
        qualname="pkg.fetch",
        function_name="fetch",
        description="Fetch data.",
        long_description=None,
        parameters=[
            ToolParam(
                name="url",
                type_str="str",
                json_type="string",
                required=True,
                default=None,
                description="The URL.",
            ),
            ToolParam(
                name="timeout",
                type_str="int",
                json_type="integer",
                required=False,
                default="30",
                description="Timeout.",
            ),
        ],
        output_hint="dict",
        example=None,
        input_schema={"type": "object", "properties": {}, "required": []},
    )
    sig = tools_signature(tool)
    assert "url: str" in sig
    assert "timeout: int = 30" in sig
    assert "-> dict" in sig


def test_tool_params_with_types_optional():
    from pip_skill.schema import ToolParam, ToolSchema

    tool = ToolSchema(
        name="get",
        qualname="pkg.get",
        function_name="get",
        description="Get.",
        long_description=None,
        parameters=[
            ToolParam(
                name="key",
                type_str="str",
                json_type="string",
                required=False,
                default="None",
                description=None,
            )
        ],
        output_hint=None,
        example=None,
        input_schema={"type": "object", "properties": {}},
    )
    result = tool_params_with_types(tool)
    assert "str | None" in result
    assert "= None" in result


def test_tool_call_args():
    from pip_skill.schema import ToolParam, ToolSchema

    tool = ToolSchema(
        name="get",
        qualname="pkg.get",
        function_name="get",
        description="Get.",
        long_description=None,
        parameters=[
            ToolParam(
                name="x",
                type_str="str",
                json_type="string",
                required=True,
                default=None,
                description=None,
            ),
            ToolParam(
                name="y",
                type_str="int",
                json_type="integer",
                required=True,
                default=None,
                description=None,
            ),
        ],
        output_hint=None,
        example=None,
        input_schema={"type": "object", "properties": {}},
    )
    args = tool_call_args(tool)
    assert args == "x=x, y=y"


def test_render_context_md(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    render_templates(fake_package_info, [tool], {"mcp": False}, tmp_path)

    ctx = tmp_path / "skills" / "fake-package" / "CONTEXT.md"
    assert ctx.exists()
    content = ctx.read_text()
    assert "Agent Guidelines" in content
    assert "fake_package" in content
    assert "Context Window" in content


def test_render_skill_md_has_prerequisites(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    render_templates(fake_package_info, [tool], {"mcp": False}, tmp_path)

    content = (tmp_path / "skills" / "fake-package" / "SKILL.md").read_text()
    assert "## Prerequisites" in content
    assert "pip install" in content


def test_render_skill_md_has_safety(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    render_templates(fake_package_info, [tool], {"mcp": False}, tmp_path)

    content = (tmp_path / "skills" / "fake-package" / "SKILL.md").read_text()
    assert "## Safety Guidelines" in content
    assert "API keys" in content


def test_render_mcp_server_has_error_handling(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    render_templates(fake_package_info, [tool], {"mcp": True}, tmp_path)

    content = (tmp_path / "scripts" / "mcp-server.py").read_text()
    assert "import json" in content
    assert "except Exception" in content
    assert "json.dumps" in content


# --- multi-format output ---


def test_render_cursor_format(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    written = render_templates(fake_package_info, [tool], {"format": "cursor"}, tmp_path)

    assert len(written) == 1
    cursorrules = tmp_path / ".cursorrules"
    assert cursorrules.exists()
    content = cursorrules.read_text()
    assert "fake-package" in content
    assert "fetch" in content
    assert "pip install" in content


def test_render_windsurf_format(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    written = render_templates(fake_package_info, [tool], {"format": "windsurf"}, tmp_path)

    assert len(written) == 1
    windsurfrules = tmp_path / ".windsurfrules"
    assert windsurfrules.exists()
    content = windsurfrules.read_text()
    assert "fake-package" in content
    assert "fetch" in content


def test_render_opencode_format(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    written = render_templates(fake_package_info, [tool], {"format": "opencode"}, tmp_path)

    assert len(written) == 1
    agents_md = tmp_path / "AGENTS.md"
    assert agents_md.exists()
    content = agents_md.read_text()
    assert "fake-package" in content
    assert "fetch" in content
    assert "Parameter" in content


def test_render_claude_format_is_default(tmp_path, fake_package_info, fake_package_on_path):
    """Default format (no format key or format=claude) produces Claude skill layout."""
    tool = _fetch_tool(fake_package_on_path)
    written = render_templates(fake_package_info, [tool], {"mcp": False}, tmp_path)

    assert len(written) == 4
    assert (tmp_path / ".claude-plugin" / "plugin.json").exists()
    assert (tmp_path / "skills" / "fake-package" / "SKILL.md").exists()


# --- install_skill ---


def test_install_skill_claude(tmp_path, fake_package_info, fake_package_on_path):
    """install_skill should copy the entire Claude plugin bundle so it is
    self-contained and auto-discovered by Claude Code on next session.

    That means: plugin.json AND skills/{name}/SKILL.md AND CONTEXT.md AND
    references/, mirroring the generated layout exactly.
    """
    from pip_skill.generator import install_skill

    output_dir = tmp_path / "output"
    tool = _fetch_tool(fake_package_on_path)
    render_templates(fake_package_info, [tool], {"mcp": False}, output_dir)

    install_dir = tmp_path / "fake_claude_plugins"
    install_skill(output_dir, "fake-package", "claude", force=True, install_base=install_dir)

    plugin_root = install_dir / "fake-package"
    assert plugin_root.exists()
    # Plugin manifest must be present so Claude Code can discover the plugin
    assert (plugin_root / ".claude-plugin" / "plugin.json").exists()
    # The skill bundle (SKILL.md + CONTEXT.md + references/) must be copied
    skill_dir = plugin_root / "skills" / "fake-package"
    assert (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "CONTEXT.md").exists()
    assert (skill_dir / "references" / "api-reference.md").exists()


def test_install_skill_claude_normalizes_package_name(
    tmp_path, fake_package_info, fake_package_on_path
):
    """install_skill must normalize names so case-mismatched packages
    (Pillow -> pillow, PyYAML -> pyyaml) work on case-sensitive filesystems."""
    from pip_skill.generator import install_skill

    output_dir = tmp_path / "out"
    tool = _fetch_tool(fake_package_on_path)
    render_templates(fake_package_info, [tool], {"mcp": False}, output_dir)

    install_dir = tmp_path / "plugins"
    # Pass a deliberately mis-cased name to mimic the Pillow/PyYAML scenario
    target = install_skill(
        output_dir, "Fake-Package", "claude", force=True, install_base=install_dir
    )

    # Target should land under the normalized name, with a complete bundle
    assert target.name == "fake-package"
    assert (target / ".claude-plugin" / "plugin.json").exists()
    assert (target / "skills" / "fake-package" / "SKILL.md").exists()


def test_install_skill_cursor(tmp_path, fake_package_info, fake_package_on_path):
    """install_skill should write .cursorrules for cursor format."""
    from pip_skill.generator import install_skill

    output_dir = tmp_path / "output"
    tool = _fetch_tool(fake_package_on_path)
    render_templates(fake_package_info, [tool], {"format": "cursor"}, output_dir)

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    install_skill(output_dir, "fake-package", "cursor", force=True, install_base=project_dir)

    assert (project_dir / ".cursor" / "rules" / "fake-package.mdc").exists()
