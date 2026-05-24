"""Tests for `pip-skill eval` and the eval harness."""

import json
from pathlib import Path

import pytest

from pip_skill import generate_skill
from pip_skill.eval import (
    BACKEND_API,
    BACKEND_AUTO,
    BACKEND_CLAUDE_CLI,
    EvalItem,
    extract_qualname,
    load_eval_set,
    run_eval,
    select_backend,
)


def _fake_eval_set(tmp_path: Path) -> Path:
    """Eval set targeting the fixture package's `fake_package.api.fetch`."""
    p = tmp_path / "fake_eval.jsonl"
    p.write_text(
        json.dumps(
            {
                "task": "Fetch a record by id",
                "expected_qualname": "fake_package.api.fetch",
            }
        )
        + "\n"
    )
    return p


def test_load_eval_set_parses_jsonl(tmp_path):
    p = _fake_eval_set(tmp_path)
    items = load_eval_set(p)
    assert len(items) == 1
    assert isinstance(items[0], EvalItem)
    assert items[0].expected_qualname == "fake_package.api.fetch"


def test_load_eval_set_skips_blank_and_comments(tmp_path):
    p = tmp_path / "with_comments.jsonl"
    p.write_text(
        '# this is a comment\n\n{"task": "x", "expected_qualname": "fake_package.api.fetch"}\n'
    )
    items = load_eval_set(p)
    assert len(items) == 1


def test_load_eval_set_rejects_missing_fields(tmp_path):
    p = tmp_path / "bad.jsonl"
    p.write_text('{"task": "missing expected_qualname"}\n')
    with pytest.raises(ValueError):
        load_eval_set(p)


def test_extract_qualname_finds_first_pkg_call():
    code = "requests.get('https://example.com', timeout=30)"
    assert extract_qualname(code, "requests") == "requests.get"


def test_extract_qualname_ignores_other_packages():
    code = "import os\nos.path.exists('x')\nrequests.get('y')"
    assert extract_qualname(code, "requests") == "requests.get"


def test_extract_qualname_returns_none_for_no_match():
    code = "open('file.txt').read()"
    assert extract_qualname(code, "requests") is None


def test_extract_qualname_handles_syntax_error_gracefully():
    code = "this is not python"
    assert extract_qualname(code, "requests") is None


def test_extract_qualname_nested_attribute_chain():
    code = "requests.Session().get('https://x.com')"
    # Session() is a call; outer call is .get on the result. Walk picks
    # the first Call in AST order, which is Session().
    qual = extract_qualname(code, "requests")
    assert qual == "requests.Session"


def test_extract_qualname_strips_inline_backticks():
    code = "`requests.get('https://example.com')`"
    assert extract_qualname(code, "requests") == "requests.get"


def test_extract_qualname_strips_fenced_code_block():
    code = "```python\nrequests.get('https://example.com')\n```"
    assert extract_qualname(code, "requests") == "requests.get"


def test_extract_qualname_strips_fenced_block_without_lang():
    code = "```\nrequests.post('https://x.com', json={'a': 1})\n```"
    assert extract_qualname(code, "requests") == "requests.post"


def test_extract_qualname_accepts_pl_alias_for_polars():
    code = "pl.read_json('data.json')"
    assert extract_qualname(code, "polars") == "polars.read_json"


def test_extract_qualname_accepts_pd_alias_for_pandas():
    code = "pd.read_csv('x.csv')"
    assert extract_qualname(code, "pandas") == "pandas.read_csv"


def test_extract_qualname_canonical_name_takes_priority_over_alias():
    code = "polars.cum_count()"
    assert extract_qualname(code, "polars") == "polars.cum_count"


def test_extract_qualname_no_alias_collision_across_packages():
    """`pl.read_csv` must NOT match `pandas` (no alias collision)."""
    code = "pl.read_csv('x.csv')"
    assert extract_qualname(code, "pandas") is None


def test_run_eval_coverage_passes_when_tool_in_manifest(tmp_path, fake_package_on_path):
    bundle = generate_skill("fake-package", output_dir=tmp_path / "fake", max_tools=5)
    # Build an eval set targeting one of the tools the heuristic picked.
    target = bundle.tool_names[0]
    eval_path = tmp_path / "eval.jsonl"
    eval_path.write_text(json.dumps({"task": "do the thing", "expected_qualname": target}) + "\n")
    summary = run_eval(bundle.bundle_dir, eval_path, ["coverage"])
    assert summary.per_condition_pass["coverage"] == 1
    assert summary.per_condition_rate["coverage"] == 1.0


def test_run_eval_coverage_fails_for_missing_tool(tmp_path, fake_package_on_path):
    bundle = generate_skill("fake-package", output_dir=tmp_path / "fake", max_tools=5)
    eval_path = tmp_path / "eval.jsonl"
    eval_path.write_text(
        json.dumps({"task": "x", "expected_qualname": "fake_package.does_not_exist"}) + "\n"
    )
    summary = run_eval(bundle.bundle_dir, eval_path, ["coverage"])
    assert summary.per_condition_pass["coverage"] == 0
    assert summary.per_condition_rate["coverage"] == 0.0


def test_run_eval_api_backend_requires_api_key(tmp_path, fake_package_on_path):
    bundle = generate_skill("fake-package", output_dir=tmp_path / "fake", max_tools=5)
    p = _fake_eval_set(tmp_path)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        run_eval(bundle.bundle_dir, p, ["skill"], api_key=None, backend=BACKEND_API)


def test_run_eval_auto_backend_with_neither_available(tmp_path, fake_package_on_path, monkeypatch):
    """auto backend without API key AND without `claude` on PATH must error."""
    monkeypatch.setenv("PATH", "")  # hide claude from PATH
    bundle = generate_skill("fake-package", output_dir=tmp_path / "fake", max_tools=5)
    p = _fake_eval_set(tmp_path)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        run_eval(bundle.bundle_dir, p, ["skill"], api_key=None, backend=BACKEND_AUTO)


def test_select_backend_api_with_key():
    assert select_backend(BACKEND_API, api_key="sk-x") == BACKEND_API


def test_select_backend_api_without_key_raises():
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        select_backend(BACKEND_API, api_key=None)


def test_select_backend_auto_prefers_api_when_key_present(monkeypatch):
    monkeypatch.setenv("PATH", "")  # would force claude-cli if no key
    assert select_backend(BACKEND_AUTO, api_key="sk-x") == BACKEND_API


def test_select_backend_claude_cli_requires_binary(monkeypatch):
    monkeypatch.setenv("PATH", "")
    with pytest.raises(ValueError, match="claude"):
        select_backend(BACKEND_CLAUDE_CLI, api_key=None)


def test_run_eval_coverage_only_skips_backend_check(tmp_path, fake_package_on_path, monkeypatch):
    """coverage condition is offline and must work with no key and no CLI."""
    monkeypatch.setenv("PATH", "")
    bundle = generate_skill("fake-package", output_dir=tmp_path / "fake", max_tools=5)
    target = bundle.tool_names[0]
    eval_path = tmp_path / "eval.jsonl"
    eval_path.write_text(json.dumps({"task": "x", "expected_qualname": target}) + "\n")
    summary = run_eval(bundle.bundle_dir, eval_path, ["coverage"])
    assert summary.per_condition_pass["coverage"] == 1
    assert summary.backend is None  # no model backend resolved for coverage-only


def test_run_eval_rejects_unknown_condition(tmp_path, fake_package_on_path):
    bundle = generate_skill("fake-package", output_dir=tmp_path / "fake", max_tools=5)
    p = _fake_eval_set(tmp_path)
    with pytest.raises(ValueError, match="Unknown condition"):
        run_eval(bundle.bundle_dir, p, ["bogus"])


def test_ships_real_requests_eval_set():
    """The README references this path; make sure it stays present and parses."""
    path = Path(__file__).parent.parent / "examples" / "eval" / "requests.jsonl"
    items = load_eval_set(path)
    assert len(items) >= 10
    # Every item must target the requests package.
    for item in items:
        assert item.expected_qualname.startswith("requests.")
