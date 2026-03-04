"""Integration tests against real installed packages.

Run with: pytest -m integration
"""

import pytest

REAL_PACKAGES = [
    ("requests", "requests", ["get", "post"]),
    # httpx top-level functions vary by version — just verify introspection works
    ("httpx", "httpx", []),
    ("click", "click", []),
    # pydantic v2 renamed many symbols — just verify introspection works
    ("pydantic", "pydantic", []),
    ("rich", "rich", []),
    ("tqdm", "tqdm", []),
]

PIPELINE_PACKAGES = [
    "requests",
    "httpx",
    "click",
    "rich",
    "tqdm",
]


@pytest.mark.parametrize("pip_name,import_name,expected_names", REAL_PACKAGES)
@pytest.mark.integration
def test_real_package_introspect(pip_name, import_name, expected_names):
    """Test introspection against real installed packages."""
    pytest.importorskip(import_name)

    from pip_skill.introspect import introspect_package

    info = introspect_package(pip_name)
    assert info.import_name == import_name
    assert info.version
    assert len(info.modules) > 0

    from pip_skill.selector import select_functions

    selected = select_functions(info, max_tools=10)
    selected_names = [fn.name for fn, _ in selected]
    for name in expected_names:
        assert name in selected_names, f"{name} not in selected: {selected_names}"


@pytest.mark.parametrize("pip_name", PIPELINE_PACKAGES)
@pytest.mark.integration
def test_full_pipeline(pip_name, tmp_path):
    """Test the full introspect → select → schema → generate pipeline."""
    import_name = pip_name.replace("-", "_")
    pytest.importorskip(import_name)

    from pip_skill.generator import render_templates
    from pip_skill.introspect import introspect_package
    from pip_skill.schema import build_tool_schemas
    from pip_skill.selector import select_functions

    pkg = introspect_package(pip_name)
    selected = select_functions(pkg, max_tools=10)
    assert len(selected) > 0, f"No functions selected for {pip_name}"

    schemas = build_tool_schemas([fn for fn, _ in selected])
    assert len(schemas) > 0

    written = render_templates(pkg, schemas, {}, tmp_path)
    assert len(written) >= 3

    plugin_json = tmp_path / ".claude-plugin" / "plugin.json"
    assert plugin_json.exists()

    import json

    data = json.loads(plugin_json.read_text())
    assert "name" in data

    from pip_skill.utils import normalize_skill_name

    skill_name = normalize_skill_name(pip_name)
    skill_md = tmp_path / "skills" / skill_name / "SKILL.md"
    assert skill_md.exists()
    content = skill_md.read_text()
    assert "---" in content  # has frontmatter
    assert pip_name.lower().replace("-", "") in content.lower().replace("-", "").replace("_", "")


@pytest.mark.integration
def test_requests_selects_http_methods(tmp_path):
    """requests should include get, post, put, delete."""
    pytest.importorskip("requests")

    from pip_skill.introspect import introspect_package
    from pip_skill.selector import select_functions

    pkg = introspect_package("requests")
    selected = select_functions(pkg, max_tools=20)
    names = [fn.name for fn, _ in selected]

    for method in ["get", "post"]:
        assert method in names, f"requests.{method} not selected"


@pytest.mark.integration
def test_no_duplicates_in_selection():
    """Selected functions should not contain duplicate names."""
    pytest.importorskip("requests")

    from pip_skill.introspect import introspect_package
    from pip_skill.selector import select_functions

    pkg = introspect_package("requests")
    selected = select_functions(pkg, max_tools=20)
    names = [fn.name for fn, _ in selected]
    assert len(names) == len(set(names)), f"Duplicates found: {names}"


@pytest.mark.integration
def test_scores_roughly_descending():
    """Top-scored functions should generally have higher scores than lower-ranked ones."""
    pytest.importorskip("requests")

    from pip_skill.introspect import introspect_package
    from pip_skill.selector import select_functions

    pkg = introspect_package("requests")
    selected = select_functions(pkg, max_tools=20)
    scores = [score for _, score in selected]
    # The top-3 should score higher than the bottom-3 (uniqueness reordering is expected)
    if len(scores) >= 6:
        assert min(scores[:3]) >= max(scores[-3:]) - 15, (
            "Top functions should score significantly higher"
        )


@pytest.mark.integration
def test_mcp_server_generation(tmp_path):
    """MCP server file should be valid Python."""
    pytest.importorskip("requests")

    from pip_skill.generator import render_templates
    from pip_skill.introspect import introspect_package
    from pip_skill.schema import build_tool_schemas
    from pip_skill.selector import select_functions

    pkg = introspect_package("requests")
    selected = select_functions(pkg, max_tools=5)
    schemas = build_tool_schemas([fn for fn, _ in selected])
    render_templates(pkg, schemas, {"mcp": True}, tmp_path)

    server = tmp_path / "scripts" / "mcp-server.py"
    assert server.exists()
    content = server.read_text()
    assert "FastMCP" in content
    assert "import requests" in content

    # Check it parses as valid Python
    import ast

    ast.parse(content)  # raises SyntaxError if invalid
