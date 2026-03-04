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
