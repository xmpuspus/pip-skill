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

    assert len(written) == 3
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
