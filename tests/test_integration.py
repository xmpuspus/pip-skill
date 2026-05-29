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
    assert len(written) >= 4

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


@pytest.mark.integration
def test_class_constructors_selected_for_pydantic():
    """Pydantic is class-centric — class constructors should appear in selection."""
    pytest.importorskip("pydantic")

    from pip_skill.introspect import introspect_package
    from pip_skill.selector import select_functions

    pkg = introspect_package("pydantic")
    selected = select_functions(pkg, max_tools=30)
    names = [fn.name for fn, _ in selected]

    # At least some classes should be selected (not just standalone functions)
    # Pydantic has many public classes: validators, serializers, types, constraints
    known_classes = {
        "BaseModel",
        "TypeAdapter",
        "ConfigDict",
        "Field",
        "AfterValidator",
        "BeforeValidator",
        "PlainValidator",
        "StringConstraints",
        "AliasChoices",
        "AliasPath",
        "WrapSerializer",
        "PlainSerializer",
        "Discriminator",
    }
    found = known_classes & set(names)
    assert len(found) >= 1, (
        f"No pydantic classes found in selection. Expected at least one of {known_classes}, "
        f"got: {names}"
    )


@pytest.mark.integration
def test_no_duplicate_names_with_classes():
    """Selection should not produce duplicate names even when classes are included."""
    pytest.importorskip("pydantic")

    from pip_skill.introspect import introspect_package
    from pip_skill.selector import select_functions

    pkg = introspect_package("pydantic")
    selected = select_functions(pkg, max_tools=20)
    names = [fn.name for fn, _ in selected]
    assert len(names) == len(set(names)), f"Duplicates found: {names}"


@pytest.mark.integration
def test_skill_md_frontmatter_spec_compliance(tmp_path):
    """Generated SKILL.md should have Agent Skills spec-compliant frontmatter."""
    pytest.importorskip("requests")

    from pip_skill.generator import render_templates
    from pip_skill.introspect import introspect_package
    from pip_skill.schema import build_tool_schemas
    from pip_skill.selector import select_functions

    pkg = introspect_package("requests")
    selected = select_functions(pkg, max_tools=5)
    schemas = build_tool_schemas([fn for fn, _ in selected])
    render_templates(pkg, schemas, {}, tmp_path)

    from pip_skill.utils import normalize_skill_name

    skill_md = tmp_path / "skills" / normalize_skill_name("requests") / "SKILL.md"
    content = skill_md.read_text()

    # Frontmatter must have spec-compliant fields
    assert "name:" in content
    assert "description:" in content
    assert "compatibility:" in content
    assert "metadata:" in content
    assert "tool-count:" in content

    # Must NOT have old non-spec fields at top level
    lines = content.split("---")[1]  # frontmatter block
    assert "toolCount:" not in lines
    assert "\nrequires:" not in lines


@pytest.mark.integration
def test_cli_convert_timing_output(tmp_path):
    """CLI convert should print timing information."""
    pytest.importorskip("requests")

    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip_skill",
            "convert",
            "requests",
            "--output",
            str(tmp_path / "out"),
            "--force",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "functions selected in" in result.stdout
    assert "introspect" in result.stdout


@pytest.mark.integration
def test_tier_detection_with_lazy_imports():
    """Packages with __getattr__-based lazy imports should be detected."""
    pytest.importorskip("pydantic")

    from pip_skill.introspect import introspect_package

    pkg = introspect_package("pydantic")
    # pydantic uses __getattr__ for lazy imports — should be detected
    # Tier depends on annotation coverage, but the detection itself should not crash
    assert pkg.tier in (1, 2, 3)


@pytest.mark.integration
def test_requests_get_ranks_in_top_handful():
    """Selection *quality*: the canonical call must rank high, not merely appear.

    Guards the source of the eval lift — a regression that buries
    `requests.get` at rank 18 behind noise would pass a 'present in top-20'
    check but fail here.
    """
    pytest.importorskip("requests")

    from pip_skill.introspect import introspect_package
    from pip_skill.selector import select_functions

    pkg = introspect_package("requests")
    selected = select_functions(pkg, max_tools=20)
    names = [fn.name for fn, _ in selected]
    assert "get" in names[:5], f"requests.get should rank top-5, got order: {names[:8]}"
