"""Tests for pip_skill.cli."""

from unittest.mock import patch

import pytest

from pip_skill.cli import main


def test_cli_validate_pass(tmp_path):
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_text('{"name": "test"}')
    (tmp_path / "skills" / "test").mkdir(parents=True)
    (tmp_path / "skills" / "test" / "SKILL.md").write_text("---\nname: test\n---\n# Test\n")

    result = main(["validate", str(tmp_path)])
    assert result == 0


def test_cli_validate_missing_plugin_json(tmp_path):
    result = main(["validate", str(tmp_path)])
    assert result == 1


def test_cli_validate_invalid_json(tmp_path):
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_text("not json{{{")
    result = main(["validate", str(tmp_path)])
    assert result == 1


def test_cli_validate_missing_name_field(tmp_path):
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_text('{"version": "1"}')
    result = main(["validate", str(tmp_path)])
    assert result == 1


def test_cli_no_args(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code in (1, 2)


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0


def test_cli_convert_output_dir(tmp_path, fake_package_on_path):
    """Test convert command creates output in specified directory."""
    from unittest.mock import MagicMock

    out = tmp_path / "output"  # doesn't exist yet
    mock_pkg_info = MagicMock()
    mock_pkg_info.name = "fake-package"
    mock_pkg_info.import_name = "fake_package"
    mock_pkg_info.version = "1.0.0"
    mock_pkg_info.description = "A fake package"
    mock_pkg_info.modules = []
    mock_pkg_info.tier = 1
    mock_pkg_info.annotation_coverage = 1.0
    mock_pkg_info.dependencies = []
    mock_pkg_info.homepage = None

    mock_fn = MagicMock()
    mock_fn.name = "fetch"
    mock_selected = [(mock_fn, 80)]

    with (
        patch("pip_skill.introspect.introspect_package", return_value=mock_pkg_info),
        patch("pip_skill.selector.select_functions", return_value=mock_selected),
        patch("pip_skill.schema.build_tool_schemas", return_value=[MagicMock()]),
        patch(
            "pip_skill.generator.render_templates",
            return_value=[out / "skills" / "fake-package" / "SKILL.md"],
        ),
    ):
        result = main(["convert", "fake-package", "--output", str(out)])

    assert result == 0


def test_cli_convert_dry_run(tmp_path, capsys, fake_package_on_path):
    """Test dry-run mode doesn't write files."""
    from unittest.mock import MagicMock

    out = tmp_path / "dryrun"  # doesn't exist yet
    mock_pkg_info = MagicMock()
    mock_pkg_info.name = "fake-package"
    mock_pkg_info.import_name = "fake_package"
    mock_pkg_info.version = "1.0.0"
    mock_pkg_info.description = "A fake package"
    mock_pkg_info.modules = []
    mock_pkg_info.tier = 1
    mock_pkg_info.annotation_coverage = 1.0
    mock_pkg_info.dependencies = []

    mock_fn = MagicMock()
    mock_fn.name = "fetch"

    with (
        patch("pip_skill.introspect.introspect_package", return_value=mock_pkg_info),
        patch("pip_skill.selector.select_functions", return_value=[(mock_fn, 80)]),
        patch("pip_skill.schema.build_tool_schemas", return_value=[MagicMock()]),
    ):
        result = main(["convert", "fake-package", "--output", str(out), "--dry-run"])

    assert result == 0
    # No files should be created
    assert not (out / ".claude-plugin").exists()


def test_cli_convert_force_flag(tmp_path, fake_package_on_path):
    """--force allows overwriting existing output."""
    from unittest.mock import MagicMock

    # Pre-create the output directory to simulate existing plugin
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_text('{"name": "old"}')

    mock_pkg_info = MagicMock()
    mock_pkg_info.name = "fake-package"
    mock_pkg_info.import_name = "fake_package"
    mock_pkg_info.version = "1.0.0"
    mock_pkg_info.description = "A fake package"
    mock_pkg_info.modules = []
    mock_pkg_info.tier = 1
    mock_pkg_info.annotation_coverage = 1.0
    mock_pkg_info.dependencies = []
    mock_pkg_info.homepage = None

    mock_fn = MagicMock()
    mock_fn.name = "fetch"

    with (
        patch("pip_skill.introspect.introspect_package", return_value=mock_pkg_info),
        patch("pip_skill.selector.select_functions", return_value=[(mock_fn, 80)]),
        patch("pip_skill.schema.build_tool_schemas", return_value=[MagicMock()]),
        patch("pip_skill.generator.render_templates", return_value=[]),
    ):
        result = main(["convert", "fake-package", "--output", str(tmp_path), "--force"])

    assert result == 0


# --- batch command ---


def test_cli_batch_packages(tmp_path, fake_package_on_path):
    """Test batch command with explicit package names."""
    from unittest.mock import MagicMock

    mock_pkg_info = MagicMock()
    mock_pkg_info.name = "fake-package"
    mock_pkg_info.import_name = "fake_package"
    mock_pkg_info.version = "1.0.0"
    mock_pkg_info.description = "A fake package"
    mock_pkg_info.modules = []
    mock_pkg_info.tier = 1
    mock_pkg_info.annotation_coverage = 1.0
    mock_pkg_info.dependencies = []
    mock_pkg_info.homepage = None

    mock_fn = MagicMock()
    mock_fn.name = "fetch"

    with (
        patch("pip_skill.introspect.introspect_package", return_value=mock_pkg_info),
        patch("pip_skill.selector.select_functions", return_value=[(mock_fn, 80)]),
        patch("pip_skill.schema.build_tool_schemas", return_value=[MagicMock()]),
        patch("pip_skill.generator.render_templates", return_value=[]),
    ):
        result = main(["batch", "fake-package", "--output-dir", str(tmp_path), "--force"])

    assert result == 0


def test_cli_batch_requirements_file(tmp_path, fake_package_on_path):
    """Test batch command with a requirements.txt file."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("fake-package>=1.0\n# a comment\n-e some-editable\nother-pkg\n")

    from pip_skill.cli import _parse_requirements

    packages = _parse_requirements(req_file)
    assert "fake-package" in packages
    assert "other-pkg" in packages
    assert len(packages) == 2


def test_cli_batch_no_packages():
    """Test batch command with no packages shows error."""
    result = main(["batch"])
    assert result == 1


# --- format flag ---


def test_cli_convert_format_cursor(tmp_path, fake_package_on_path):
    """Test --format cursor is accepted."""
    from unittest.mock import MagicMock

    mock_pkg_info = MagicMock()
    mock_pkg_info.name = "fake-package"
    mock_pkg_info.import_name = "fake_package"
    mock_pkg_info.version = "1.0.0"
    mock_pkg_info.description = "A fake package"
    mock_pkg_info.modules = []
    mock_pkg_info.tier = 1
    mock_pkg_info.annotation_coverage = 1.0
    mock_pkg_info.dependencies = []
    mock_pkg_info.homepage = None

    mock_fn = MagicMock()
    mock_fn.name = "fetch"

    out = tmp_path / "cursor-out"
    with (
        patch("pip_skill.introspect.introspect_package", return_value=mock_pkg_info),
        patch("pip_skill.selector.select_functions", return_value=[(mock_fn, 80)]),
        patch("pip_skill.schema.build_tool_schemas", return_value=[MagicMock()]),
        patch(
            "pip_skill.generator.render_templates",
            return_value=[out / ".cursorrules"],
        ),
    ):
        result = main(
            [
                "convert",
                "fake-package",
                "--output",
                str(out),
                "--format",
                "cursor",
            ]
        )

    assert result == 0


# --- diff command ---


def test_cli_diff_no_changes(tmp_path, fake_package_on_path):
    """Test diff command when no API changes."""
    import json

    (tmp_path / ".claude-plugin").mkdir(parents=True)
    (tmp_path / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(
            {
                "name": "fake-package",
                "version": "1.0.0",
                "sourcePackage": "fake-package",
                "toolCount": 20,
            }
        )
    )

    ref_dir = tmp_path / "skills" / "fake-package" / "references"
    ref_dir.mkdir(parents=True)
    (ref_dir / "api-reference.md").write_text("## `fake_package.api.fetch`\n\nSome docs\n")

    with patch("pip_skill.introspect.introspect_package") as mock_introspect:
        from tests.conftest import _build_fake_package_info

        mock_introspect.return_value = _build_fake_package_info()
        result = main(["diff", str(tmp_path)])

    assert result == 0


# --- info command ---


def test_cli_info(capsys, fake_package_on_path):
    """Test info command shows package summary."""
    from unittest.mock import MagicMock

    mock_pkg_info = MagicMock()
    mock_pkg_info.name = "fake-package"
    mock_pkg_info.import_name = "fake_package"
    mock_pkg_info.version = "1.0.0"
    mock_pkg_info.description = "A fake package"
    mock_pkg_info.modules = []
    mock_pkg_info.tier = 1
    mock_pkg_info.annotation_coverage = 0.75

    with patch("pip_skill.introspect.introspect_package", return_value=mock_pkg_info):
        result = main(["info", "fake-package"])

    assert result == 0
    captured = capsys.readouterr()
    assert "fake-package" in captured.out
    assert "1.0.0" in captured.out


# --- search/install commands ---


def test_cli_search_empty(capsys):
    """Test search command when registry is unreachable."""
    with patch("pip_skill.registry.search_registry", return_value=[]):
        result = main(["search"])

    assert result == 0
    captured = capsys.readouterr()
    assert "empty" in captured.out.lower() or "no skills" in captured.out.lower()


def test_cli_install_not_found():
    """Test install command when skill not in registry."""
    with patch("pip_skill.registry.install_skill", side_effect=ValueError("not found")):
        result = main(["install", "nonexistent-pkg"])

    assert result == 1


# --- --select flag ---


def test_convert_select_flag_requires_api_key(capsys, monkeypatch):
    """--select flag should error when ANTHROPIC_API_KEY is not set."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from unittest.mock import MagicMock

    mock_pkg_info = MagicMock()
    mock_pkg_info.name = "fake-package"
    mock_pkg_info.import_name = "fake_package"
    mock_pkg_info.version = "1.0.0"
    mock_pkg_info.description = "A fake package"
    mock_pkg_info.modules = []
    mock_pkg_info.tier = 1
    mock_pkg_info.annotation_coverage = 1.0
    mock_pkg_info.dependencies = []

    mock_fn = MagicMock()
    mock_fn.name = "fetch"

    with (
        patch("pip_skill.introspect.introspect_package", return_value=mock_pkg_info),
        patch("pip_skill.selector.select_functions", return_value=[(mock_fn, 80)]),
    ):
        result = main(["convert", "fake-package", "--select"])

    assert result == 1
    captured = capsys.readouterr()
    assert "ANTHROPIC_API_KEY" in captured.err


# --- build command ---


def test_build_command_accepts_package_arg():
    """`build` accepts a positional package argument and routes to cmd_build.

    cmd_build is patched so the test is hermetic regardless of whether the
    `[tui]` extra is installed.
    """
    with patch("pip_skill.cli.cmd_build", return_value=0):
        result = main(["build", "requests"])
    assert result == 0

    # `build` without a package argument is rejected by argparse with exit 2.
    with pytest.raises(SystemExit) as exc_info:
        main(["build"])
    assert exc_info.value.code == 2


# --- test command ---


def test_test_command_nonexistent_dir(tmp_path):
    """pip-skill test should fail for nonexistent plugin dir."""
    result = main(["test", str(tmp_path / "nonexistent")])
    assert result == 1


def test_test_command_validates_skill(tmp_path):
    """pip-skill test should validate a generated skill directory by reading
    the structured `tools` manifest (not by regex-scraping markdown).

    `requests` is in dev extras (see pyproject.toml) because this test
    exercises the import path that pip-skill test takes against a real
    installed package.
    """
    import json

    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(
            {
                "name": "requests",
                "sourcePackage": "requests",
                "sourceVersion": "0.0.0",
                "tools": [
                    {
                        "name": "get",
                        "functionName": "get",
                        "qualname": "requests.get",
                        "module": "requests",
                        "isDestructive": False,
                        "isWrite": False,
                        "parameters": [],
                    },
                    {
                        "name": "post",
                        "functionName": "post",
                        "qualname": "requests.post",
                        "module": "requests",
                        "isDestructive": False,
                        "isWrite": True,
                        "parameters": [],
                    },
                ],
            }
        )
    )
    (tmp_path / "skills" / "requests").mkdir(parents=True)
    (tmp_path / "skills" / "requests" / "SKILL.md").write_text("# requests\n")

    result = main(["test", str(tmp_path)])
    assert result == 0


def test_test_command_rejects_legacy_skill_without_manifest(tmp_path):
    """A skill without the `tools` manifest must not silently pass — instruct
    the user to regenerate."""
    import json

    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "requests", "sourcePackage": "requests", "sourceVersion": "0.0.0"})
    )
    (tmp_path / "skills" / "requests").mkdir(parents=True)
    (tmp_path / "skills" / "requests" / "SKILL.md").write_text("# requests\n")

    result = main(["test", str(tmp_path)])
    assert result == 1
