# Approach B: Irresistible Demo Loop — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix broken features, add `--install` and `test` commands, polish README, publish to PyPI for mass adoption.

**Architecture:** Incremental fixes to existing CLI/introspect/generator pipeline. New `install_skill()` function in generator.py. New `cmd_test()` in cli.py. No new modules needed — all changes fit cleanly into existing file structure.

**Tech Stack:** Python 3.11+, argparse, jinja2, pathlib, logging, importlib

**Spec:** `docs/superpowers/specs/2026-03-29-approach-b-irresistible-demo-loop.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `src/pip_skill/cli.py` | Modify | Add `--select`, fix `build`, add `--install`, add `test` subcommand, add batch summary |
| `src/pip_skill/introspect.py` | Modify | Add `docs_url` to PackageInfo, add progress output in `walk_package_modules` |
| `src/pip_skill/generator.py` | Modify | Add `install_skill()` function |
| `src/pip_skill/selector.py` | Modify | Add logging to except blocks and scoring |
| `src/pip_skill/schema.py` | Modify | Add logging to except blocks and fallback chain |
| `tests/test_cli.py` | Modify | Tests for new CLI flags and commands |
| `tests/test_generator.py` | Modify | Tests for install_skill() |
| `tests/test_introspect.py` | Modify | Test for docs_url field |
| `README.md` | Modify | Restructure for LinkedIn shareability |

---

## Task 1: Wire `--select` into CLI

**Files:**
- Modify: `src/pip_skill/cli.py:42-59` (convert subparser), `src/pip_skill/cli.py:152-226` (cmd_convert)
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing test for --select flag**

In `tests/test_cli.py`, add a test that verifies `--select` is a recognized argument:

```python
def test_convert_select_flag_requires_api_key(capsys, monkeypatch):
    """--select flag should error when ANTHROPIC_API_KEY is not set."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from pip_skill.cli import main
    import sys
    monkeypatch.setattr(sys, "argv", ["pip-skill", "convert", "requests", "--select"])
    result = main()
    captured = capsys.readouterr()
    assert result != 0
    assert "ANTHROPIC_API_KEY" in captured.err
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py::test_convert_select_flag_requires_api_key -v`
Expected: FAIL — argparse doesn't recognize `--select`

- [ ] **Step 3: Add --select flag to convert subparser**

In `src/pip_skill/cli.py`, add to the convert subparser (after line 59):

```python
convert_parser.add_argument("--select", action="store_true",
                            help="Use LLM to curate function selection (requires ANTHROPIC_API_KEY)")
```

Then in `cmd_convert` (around line 170, after `selected = select_functions(...)`), add:

```python
if args.select:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: --select requires ANTHROPIC_API_KEY environment variable", file=sys.stderr)
        return 1
    try:
        from pip_skill.selector import llm_curate
        selected = llm_curate(selected, pkg_info, max_tools=args.max_tools, api_key=api_key)
    except ImportError:
        print("Error: --select requires pip-skill[llm] extra. Run: pip install pip-skill[llm]", file=sys.stderr)
        return 1
```

Add `import os` at top of cli.py if not already present.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli.py::test_convert_select_flag_requires_api_key -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest -q`
Expected: All 133+ tests pass

- [ ] **Step 6: Commit**

```bash
git add src/pip_skill/cli.py tests/test_cli.py
git commit -m "Wire --select flag into convert command"
```

---

## Task 2: Fix `build` Command Crash

**Files:**
- Modify: `src/pip_skill/cli.py:85` (build subparser), `src/pip_skill/cli.py:319-331` (cmd_build)

- [ ] **Step 1: Write failing test**

```python
def test_build_command_accepts_package_arg(monkeypatch):
    """build subparser should accept a package positional argument."""
    import sys
    from pip_skill.cli import main
    # Just verify argparse accepts it — TUI import may fail without textual
    monkeypatch.setattr(sys, "argv", ["pip-skill", "build", "requests"])
    # Should not raise SystemExit from argparse
    try:
        result = main()
    except (ImportError, SystemExit) as e:
        # ImportError from textual is OK, SystemExit(2) from argparse is NOT
        if isinstance(e, SystemExit) and e.code == 2:
            raise AssertionError("argparse rejected 'build requests'") from e
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py::test_build_command_accepts_package_arg -v`
Expected: FAIL — argparse exits with code 2 (unrecognized arguments)

- [ ] **Step 3: Fix build subparser and cmd_build**

In `src/pip_skill/cli.py`, change the build subparser (line 85) from:

```python
build_parser = subparsers.add_parser("build", help="Interactive skill builder")
```

To:

```python
build_parser = subparsers.add_parser("build", help="Interactive skill builder (requires pip-skill[tui])")
build_parser.add_argument("package", help="Package to build skill for")
```

In `cmd_build` (line 324), change `run_tui()` to `run_tui(args)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli.py::test_build_command_accepts_package_arg -v`
Expected: PASS (or ImportError from textual, which is acceptable)

- [ ] **Step 5: Commit**

```bash
git add src/pip_skill/cli.py tests/test_cli.py
git commit -m "Fix build command crash — add package arg, pass args to run_tui"
```

---

## Task 3: Add `docs_url` to PackageInfo

**Files:**
- Modify: `src/pip_skill/introspect.py:72-86` (PackageInfo dataclass), `src/pip_skill/introspect.py:140-169` (get_package_metadata)
- Test: `tests/test_introspect.py`

- [ ] **Step 1: Write failing test**

```python
def test_package_info_has_docs_url():
    """PackageInfo should have a docs_url field."""
    from pip_skill.introspect import PackageInfo
    fields = {f.name for f in PackageInfo.__dataclass_fields__.values()}
    assert "docs_url" in fields
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_introspect.py::test_package_info_has_docs_url -v`
Expected: FAIL — no docs_url field

- [ ] **Step 3: Add docs_url field and populate it**

In `src/pip_skill/introspect.py`, add to the PackageInfo dataclass (after `homepage` field, around line 78):

```python
docs_url: str | None = None
```

In `get_package_metadata` function (around line 163), after populating `homepage`, add:

```python
docs_url = None
project_urls = meta.get_all("Project-URL") or []
for url_entry in project_urls:
    label, _, url = url_entry.partition(",")
    if label.strip().lower() in ("documentation", "docs", "doc"):
        docs_url = url.strip()
        break
```

Then include `docs_url=docs_url` in the PackageInfo constructor call.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_introspect.py::test_package_info_has_docs_url -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass (templates already reference `package.docs_url`, now it's a real field)

- [ ] **Step 6: Commit**

```bash
git add src/pip_skill/introspect.py tests/test_introspect.py
git commit -m "Add docs_url to PackageInfo, populate from Project-URL metadata"
```

---

## Task 4: Progress Indicators During Introspection

**Files:**
- Modify: `src/pip_skill/introspect.py:197-230` (walk_package_modules)

- [ ] **Step 1: Add progress output to walk_package_modules**

In `src/pip_skill/introspect.py`, modify `walk_package_modules` to accept a `progress` callback and print to stderr:

At the top of the function (around line 197), add a `progress_callback` parameter:

```python
def walk_package_modules(pkg, import_name: str, progress_callback=None) -> list[ModuleInfo]:
```

Inside the `for modinfo in pkgutil.walk_packages(...)` loop (around line 219), add at the start:

```python
if progress_callback:
    progress_callback(modinfo.name)
```

In `introspect_package` (around line 548 where `walk_package_modules` is called), pass a stderr callback:

```python
def _progress(mod_name):
    print(f"  Scanning {mod_name}...", file=sys.stderr, end="\r", flush=True)

modules = walk_package_modules(pkg, import_name, progress_callback=_progress)
# Clear progress line
print(" " * 60, file=sys.stderr, end="\r", flush=True)
```

Add `import sys` at top if not present.

- [ ] **Step 2: Manually verify with a real package**

Run: `uv run pip-skill convert requests --dry-run`
Expected: See `Scanning requests.api...` etc. flickering on stderr before output

- [ ] **Step 3: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass (progress goes to stderr, doesn't affect stdout assertions)

- [ ] **Step 4: Commit**

```bash
git add src/pip_skill/introspect.py
git commit -m "Add progress indicators during package introspection"
```

---

## Task 5: Batch Summary Line

**Files:**
- Modify: `src/pip_skill/cli.py:229-290` (cmd_batch)

- [ ] **Step 1: Add summary tracking and output**

In `cmd_batch`, add counters before the ThreadPoolExecutor block:

```python
success_count = 0
fail_count = 0
```

In the results loop (around line 280), increment counters:

```python
for future in futures:
    pkg_name = futures[future]
    try:
        result = future.result()
        if result == 0:
            success_count += 1
            print(f"  [DONE] {pkg_name}")
        else:
            fail_count += 1
            print(f"  [FAIL] {pkg_name}")
    except Exception as e:
        fail_count += 1
        print(f"  [FAIL] {pkg_name}: {e}", file=sys.stderr)
```

After the loop, print summary:

```python
total = success_count + fail_count
elapsed = time.time() - t0
fail_msg = f" ({fail_count} failed)" if fail_count else ""
print(f"\nBatch complete: {success_count}/{total} succeeded{fail_msg} in {elapsed:.1f}s")
```

- [ ] **Step 2: Run existing batch tests**

Run: `uv run pytest tests/test_cli.py -k batch -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/pip_skill/cli.py
git commit -m "Add batch summary line with success/fail counts and timing"
```

---

## Task 6: Populate Logging Framework

**Files:**
- Modify: `src/pip_skill/introspect.py`, `src/pip_skill/selector.py`, `src/pip_skill/schema.py`

- [ ] **Step 1: Add logger calls to introspect.py**

At top of `introspect.py`, ensure:
```python
import logging
logger = logging.getLogger("pip_skill.introspect")
```

In `walk_package_modules`, inside each `except Exception` block, add:
```python
logger.debug("Skipping module %s: %s", modinfo.name, e)
```

In `extract_callable_info`, inside each `except Exception` block, add:
```python
logger.debug("Skipping callable %s: %s", name, e)
```

In `introspect_package`, add phase markers:
```python
logger.info("Introspecting package %s (import: %s)", name, import_name)
# ... after walk_package_modules:
logger.info("Found %d modules with %d callables", len(modules), sum(len(m.callables) for m in modules))
```

- [ ] **Step 2: Add logger calls to selector.py**

At top of `selector.py`, ensure:
```python
import logging
logger = logging.getLogger("pip_skill.selector")
```

In `select_functions`, add:
```python
logger.info("Scoring %d candidates, selecting top %d", len(candidates), max_tools)
```

In each `except Exception` block in scoring functions, add:
```python
logger.debug("Scoring error for %s: %s", fn_info.qualname, e)
```

- [ ] **Step 3: Add logger calls to schema.py**

At top of `schema.py`, ensure:
```python
import logging
logger = logging.getLogger("pip_skill.schema")
```

In schema fallback chain, add:
```python
logger.debug("Schema for %s: using %s strategy", ci.qualname, "TypeAdapter" if schema else "signature-based")
```

In each `except Exception` block, add:
```python
logger.debug("Schema generation skipped %s: %s", ci.qualname, e)
```

- [ ] **Step 4: Verify --log-level works**

Run: `uv run pip-skill --log-level DEBUG convert requests --dry-run 2>&1 | head -30`
Expected: See DEBUG lines from introspect, selector, schema phases

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass (logging goes to stderr via logging config)

- [ ] **Step 6: Commit**

```bash
git add src/pip_skill/introspect.py src/pip_skill/selector.py src/pip_skill/schema.py
git commit -m "Populate logging framework — make --log-level functional"
```

---

## Task 7: The Killer Feature — `--install`

**Files:**
- Modify: `src/pip_skill/cli.py:42-59` (convert subparser), `src/pip_skill/cli.py:152-226` (cmd_convert)
- Modify: `src/pip_skill/generator.py` (add install_skill function)
- Test: `tests/test_generator.py`

- [ ] **Step 1: Write failing test for install_skill**

In `tests/test_generator.py`, add:

```python
def test_install_skill_claude(tmp_path, fake_package_info, fake_tools):
    """install_skill should copy Claude skill to ~/.claude/skills/{pkg}/."""
    from pip_skill.generator import render_templates, install_skill

    output_dir = tmp_path / "output"
    render_templates(fake_package_info, fake_tools, {"format": "claude"}, output_dir)

    install_dir = tmp_path / "fake_claude_skills"
    install_skill(output_dir, "fake_package", "claude", force=True, install_base=install_dir)

    skill_dir = install_dir / "fake_package"
    assert skill_dir.exists()
    assert (skill_dir / "SKILL.md").exists()


def test_install_skill_cursor(tmp_path, fake_package_info, fake_tools):
    """install_skill should write .cursorrules for cursor format."""
    from pip_skill.generator import render_templates, install_skill

    output_dir = tmp_path / "output"
    render_templates(fake_package_info, fake_tools, {"format": "cursor"}, output_dir)

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    install_skill(output_dir, "fake_package", "cursor", force=True, install_base=project_dir)

    assert (project_dir / ".cursor" / "rules" / "fake_package.mdc").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_generator.py::test_install_skill_claude -v`
Expected: FAIL — `install_skill` not found

- [ ] **Step 3: Implement install_skill in generator.py**

Add to `src/pip_skill/generator.py`:

```python
def install_skill(output_dir: Path, package_name: str, fmt: str, force: bool = False, install_base: Path | None = None) -> Path:
    """Install generated skill to the appropriate tool directory.

    Returns the path where the skill was installed.
    """
    output_dir = Path(output_dir)

    if fmt == "claude":
        base = install_base or Path.home() / ".claude" / "skills"
        target = base / package_name
        if target.exists() and not force:
            raise FileExistsError(f"Skill already installed at {target}. Use --force to overwrite.")
        target.mkdir(parents=True, exist_ok=True)
        # Copy SKILL.md
        skill_src = output_dir / "skills" / package_name / "SKILL.md"
        if skill_src.exists():
            shutil.copy2(skill_src, target / "SKILL.md")
        # Copy references/ if present
        ref_src = output_dir / "skills" / package_name / "references"
        if ref_src.exists():
            ref_target = target / "references"
            if ref_target.exists():
                shutil.rmtree(ref_target)
            shutil.copytree(ref_src, ref_target)
        return target

    elif fmt == "cursor":
        base = install_base or Path.cwd()
        rules_dir = base / ".cursor" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        target = rules_dir / f"{package_name}.mdc"
        if target.exists() and not force:
            raise FileExistsError(f"Cursor rules already exist at {target}. Use --force to overwrite.")
        src = output_dir / ".cursorrules"
        if src.exists():
            shutil.copy2(src, target)
        return target

    elif fmt == "windsurf":
        base = install_base or Path.cwd()
        rules_dir = base / ".windsurf" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        target = rules_dir / f"{package_name}.md"
        if target.exists() and not force:
            raise FileExistsError(f"Windsurf rules already exist at {target}. Use --force to overwrite.")
        src = output_dir / ".windsurfrules"
        if src.exists():
            shutil.copy2(src, target)
        return target

    elif fmt == "opencode":
        base = install_base or Path.cwd()
        target = base / "AGENTS.md"
        if target.exists() and not force:
            raise FileExistsError(f"AGENTS.md already exists at {target}. Use --force to overwrite.")
        src = output_dir / "AGENTS.md"
        if src.exists():
            shutil.copy2(src, target)
        return target

    else:
        raise ValueError(f"Unknown format: {fmt}")
```

Add `import shutil` at top of generator.py.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_generator.py::test_install_skill_claude tests/test_generator.py::test_install_skill_cursor -v`
Expected: PASS

- [ ] **Step 5: Wire --install into CLI**

In `src/pip_skill/cli.py`, add to convert subparser (after --force):

```python
convert_parser.add_argument("--install", action="store_true",
                            help="Install skill directly into AI tool directory")
```

In `cmd_convert`, after `render_templates(...)` (around line 215), add:

```python
if args.install:
    from pip_skill.generator import install_skill
    fmt = getattr(args, "format", "claude") or "claude"
    try:
        target = install_skill(output_dir, pkg_info.name, fmt, force=args.force)
        print(f"Installed {pkg_info.name} skill to {target}")
    except FileExistsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
```

- [ ] **Step 6: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add src/pip_skill/generator.py src/pip_skill/cli.py tests/test_generator.py
git commit -m "Add --install flag to auto-place skills into AI tool directories"
```

---

## Task 8: `pip-skill test` Command

**Files:**
- Modify: `src/pip_skill/cli.py` (add test subparser + cmd_test)
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing test**

```python
def test_test_command_validates_skill(tmp_path, monkeypatch):
    """pip-skill test should validate a generated skill directory."""
    import subprocess, sys
    # First generate a skill for the fake_package fixture
    # Then run pip-skill test on it
    from pip_skill.cli import main
    monkeypatch.setattr(sys, "argv", ["pip-skill", "test", str(tmp_path / "nonexistent")])
    result = main()
    assert result == 1  # Should fail for nonexistent dir
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py::test_test_command_validates_skill -v`
Expected: FAIL — 'test' is not a recognized subcommand

- [ ] **Step 3: Add test subcommand and cmd_test**

In `src/pip_skill/cli.py`, add the subparser (after search, around line 104):

```python
test_parser = subparsers.add_parser("test", help="Validate generated skill works correctly",
                                     epilog="Example: pip-skill test ./my-requests-skill/")
test_parser.add_argument("plugin_dir", type=Path, help="Directory containing generated skill")
```

Add the command dispatch in main() (around line 127):

```python
elif args.command == "test":
    return cmd_test(args)
```

Add the cmd_test function:

```python
def cmd_test(args) -> int:
    """Validate that a generated skill's functions are importable and signatures match."""
    plugin_dir = Path(args.plugin_dir)
    plugin_json = plugin_dir / ".claude-plugin" / "plugin.json"

    if not plugin_json.exists():
        print(f"Error: No plugin.json found in {plugin_dir}", file=sys.stderr)
        return 1

    import json
    meta = json.loads(plugin_json.read_text())
    pkg_name = meta.get("sourcePackage", "")
    pkg_version = meta.get("sourceVersion", "")

    if not pkg_name:
        print("Error: plugin.json missing sourcePackage field", file=sys.stderr)
        return 1

    # Check package is installed
    try:
        import importlib.metadata as im
        installed_version = im.version(pkg_name)
    except im.PackageNotFoundError:
        print(f"Error: Package '{pkg_name}' is not installed. Run: pip install {pkg_name}", file=sys.stderr)
        return 1

    version_match = installed_version == pkg_version
    if not version_match:
        print(f"  [WARN] Version mismatch: skill={pkg_version}, installed={installed_version}", file=sys.stderr)

    # Find SKILL.md and extract function names
    skill_dirs = list((plugin_dir / "skills").glob("*/SKILL.md")) if (plugin_dir / "skills").exists() else []
    if not skill_dirs:
        print(f"Error: No SKILL.md found in {plugin_dir}/skills/*/", file=sys.stderr)
        return 1

    import re
    skill_md = skill_dirs[0].read_text()
    # Extract qualnames from ### headers like "### `requests.get`"
    qualnames = re.findall(r"###\s+`([^`]+)`", skill_md)

    if not qualnames:
        print("Error: No functions found in SKILL.md", file=sys.stderr)
        return 1

    print(f"Testing {pkg_name} skill (v{pkg_version})...")

    passed = 0
    failed = 0
    for qualname in qualnames:
        parts = qualname.rsplit(".", 1)
        if len(parts) != 2:
            print(f"  [SKIP] {qualname} — cannot parse module.name")
            continue
        mod_name, func_name = parts
        try:
            mod = importlib.import_module(mod_name)
            obj = getattr(mod, func_name)
            print(f"  [PASS] {qualname}")
            passed += 1
        except (ImportError, AttributeError) as e:
            print(f"  [FAIL] {qualname} — {e}")
            failed += 1

    # Check MCP server syntax if present
    mcp_server = plugin_dir / "scripts" / "mcp-server.py"
    if mcp_server.exists():
        import ast
        try:
            ast.parse(mcp_server.read_text())
            print(f"  [PASS] MCP server syntax OK")
            passed += 1
        except SyntaxError as e:
            print(f"  [FAIL] MCP server syntax error: {e}")
            failed += 1

    total = passed + failed
    stale_msg = f", {failed} stale" if failed else ""
    print(f"\nResult: {passed}/{total} passed{stale_msg}")
    return 1 if failed else 0
```

Add `import importlib` at top if not present.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli.py::test_test_command_validates_skill -v`
Expected: PASS

- [ ] **Step 5: Write integration test for test command**

```python
def test_test_command_on_real_skill(tmp_path, monkeypatch):
    """Full pipeline: convert requests, then test the output."""
    import sys
    from pip_skill.cli import main

    # Generate skill
    output = tmp_path / "requests-skill"
    monkeypatch.setattr(sys, "argv", ["pip-skill", "convert", "requests", "--output", str(output)])
    result = main()
    assert result == 0

    # Test skill
    monkeypatch.setattr(sys, "argv", ["pip-skill", "test", str(output)])
    result = main()
    assert result == 0
```

- [ ] **Step 6: Run both tests**

Run: `uv run pytest tests/test_cli.py -k "test_command" -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/pip_skill/cli.py tests/test_cli.py
git commit -m "Add pip-skill test command for skill validation"
```

---

## Task 9: README Glow-up

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read current README**

Read `README.md` fully to understand current structure.

- [ ] **Step 2: Restructure README**

Key changes:
1. **Hero section**: Keep one-liner + badges. Add PyPI badge: `[![PyPI](https://img.shields.io/pypi/v/pip-skill)](https://pypi.org/project/pip-skill/)`
2. **"Try it in 30 seconds"** section right after hero:
   ```
   pip install pip-skill
   pip-skill convert requests --install
   # Done. Your AI assistant now knows the requests library.
   ```
3. **Before/After** comparison section:
   - Without pip-skill: "AI hallucinates `requests.fetch()` which doesn't exist"
   - With pip-skill: "AI uses `requests.get()` with correct parameters from actual API"
4. **Move the 12 real-world examples higher** — right after "Try it in 30 seconds"
5. **New Commands section** highlighting `--install`, `test`, `batch`, `--select`
6. **Keep** existing detailed sections below the fold

- [ ] **Step 3: Verify links and badges render**

Review the README renders correctly on GitHub.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "Restructure README for LinkedIn shareability"
```

---

## Task 10: Final Verification + Publish

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest -q`
Expected: All tests pass (133+ original + new tests)

- [ ] **Step 2: Run linter**

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: Clean

- [ ] **Step 3: Verify end-to-end flow**

```bash
uv run pip-skill convert requests --install --force
uv run pip-skill test ~/.claude/skills/requests/   # or wherever it installed
uv run pip-skill info boto3
uv run pip-skill batch requests httpx click --format claude
```

Expected: All commands work, output looks polished.

- [ ] **Step 4: Tag and publish**

```bash
git tag v0.1.0
git push origin main --tags
```

Wait for GitHub Actions to publish to PyPI.

- [ ] **Step 5: Verify PyPI install**

```bash
pip install pip-skill
pip-skill convert requests --install
```

Expected: Works from PyPI install.

---

## Out of Scope (v0.2.0 backlog)

- `pip-skill update` (skill lifecycle/merge)
- `pip-skill publish` (community contributions)
- Private registry support
- JSON output for CI/CD (`--output-format json`)
- Config file support (`pyproject.toml [tool.pip-skill]`)
- Shell completions
- Windows CI testing
- Jinja2 sandboxing
- Module count limits for performance
- `--quiet` flag
- Async function handling in MCP templates
