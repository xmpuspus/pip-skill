"""Tests for `--deterministic` mode and SHA-256 manifest emission."""

import hashlib
import importlib
import json

from pip_skill.generator import DETERMINISTIC_TIMESTAMP, render_templates
from pip_skill.introspect import extract_callable_info
from pip_skill.schema import build_tool_schema


def _fetch_tool(fake_package_on_path):
    mod = importlib.import_module("fake_package.api")
    info = extract_callable_info("fetch", mod.fetch, "fake_package.api")
    return build_tool_schema(info)


def test_deterministic_pins_timestamp(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    render_templates(
        fake_package_info,
        [tool],
        {"deterministic": True, "format": "claude"},
        tmp_path,
    )
    pj = json.loads((tmp_path / ".claude-plugin" / "plugin.json").read_text())
    assert pj["generatedAt"] == DETERMINISTIC_TIMESTAMP


def test_deterministic_emits_manifest(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    render_templates(
        fake_package_info,
        [tool],
        {"deterministic": True, "format": "claude"},
        tmp_path,
    )
    manifest = tmp_path / "MANIFEST.sha256"
    assert manifest.exists()
    lines = [line for line in manifest.read_text().splitlines() if line]
    assert len(lines) >= 4  # plugin.json, SKILL.md, CONTEXT.md, api-reference.md

    # Every recorded digest must match the file content.
    for line in lines:
        digest, _, rel = line.partition("  ")
        assert digest, line
        assert rel, line
        actual = hashlib.sha256((tmp_path / rel).read_bytes()).hexdigest()
        assert actual == digest, f"manifest digest mismatch for {rel}"


def test_non_deterministic_skips_manifest(tmp_path, fake_package_info, fake_package_on_path):
    tool = _fetch_tool(fake_package_on_path)
    render_templates(fake_package_info, [tool], {"format": "claude"}, tmp_path)
    assert not (tmp_path / "MANIFEST.sha256").exists()


def test_two_deterministic_runs_produce_identical_bytes(
    tmp_path, fake_package_info, fake_package_on_path
):
    tool = _fetch_tool(fake_package_on_path)
    a = tmp_path / "a"
    b = tmp_path / "b"
    render_templates(fake_package_info, [tool], {"deterministic": True}, a)
    render_templates(fake_package_info, [tool], {"deterministic": True}, b)

    files_a = sorted(p.relative_to(a) for p in a.rglob("*") if p.is_file())
    files_b = sorted(p.relative_to(b) for p in b.rglob("*") if p.is_file())
    assert files_a == files_b

    for rel in files_a:
        assert (a / rel).read_bytes() == (b / rel).read_bytes(), f"divergence in {rel}"
