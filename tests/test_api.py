"""Tests for the high-level Python API exposed at `pip_skill.generate_skill`."""

import pytest

from pip_skill import SkillBundle, generate_skill


def test_generate_skill_returns_bundle(tmp_path, fake_package_on_path):
    out = tmp_path / "fake"
    bundle = generate_skill("fake-package", output_dir=out, max_tools=5)
    assert isinstance(bundle, SkillBundle)
    assert bundle.bundle_dir == out
    assert bundle.tool_count >= 1
    assert bundle.tool_names
    assert bundle.tool_names[0].startswith("fake_package.")
    # Default mode does NOT emit a manifest.
    assert bundle.manifest_path is None


def test_generate_skill_deterministic_emits_manifest(tmp_path, fake_package_on_path):
    out = tmp_path / "fake-det"
    bundle = generate_skill(
        "fake-package",
        output_dir=out,
        max_tools=5,
        deterministic=True,
    )
    assert bundle.manifest_path is not None
    assert bundle.manifest_path.name == "MANIFEST.sha256"
    assert bundle.manifest_path.exists()


def test_generate_skill_refuses_overwrite(tmp_path, fake_package_on_path):
    out = tmp_path / "fake"
    generate_skill("fake-package", output_dir=out, max_tools=3)
    with pytest.raises(FileExistsError):
        generate_skill("fake-package", output_dir=out, max_tools=3)


def test_generate_skill_force_overwrite(tmp_path, fake_package_on_path):
    out = tmp_path / "fake"
    generate_skill("fake-package", output_dir=out, max_tools=3)
    # Should not raise.
    bundle = generate_skill("fake-package", output_dir=out, max_tools=3, force=True)
    assert bundle.bundle_dir == out


def test_generate_skill_select_requires_api_key(tmp_path, fake_package_on_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        generate_skill(
            "fake-package",
            output_dir=tmp_path / "fake",
            max_tools=3,
            select=True,
        )
