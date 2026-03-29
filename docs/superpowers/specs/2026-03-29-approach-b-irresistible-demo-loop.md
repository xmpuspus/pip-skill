# Approach B: Irresistible Demo Loop

**Date:** 2026-03-29
**Goal:** Mass adoption (stars + installs) targeting AI-assisted devs
**Scope:** 1-2 day polish sprint, then publish to PyPI
**Author:** Xavier Puspus

---

## Context

pip-skill is feature-complete at its core (133 tests, 10-signal scoring, 4 output formats, MCP generation). Product audit scored it 59/100 overall, with key gaps in observability (30), feature completeness (55), and performance (55). Two documented features are broken (`--select`, `build`). The tool has never been published to PyPI.

The strategy: fix embarrassments, add one viral feature (`--install`), add one confidence feature (`test`), seed the registry, polish the README, and ship.

---

## Part 1: Fix the Broken (Half Day)

### 1.1 Wire `--select` into CLI
- Add `--select` flag to `convert` subparser in `cli.py`
- Require `ANTHROPIC_API_KEY` env var when flag is used
- Call `llm_curate()` from `selector.py:420` after heuristic selection
- Error message if key missing: `"Error: --select requires ANTHROPIC_API_KEY environment variable"`

### 1.2 Fix `build` command crash
- Add `package` positional arg to `build` subparser (`cli.py:85`)
- Pass `args` to `run_tui(args)` in `cmd_build` (`cli.py:324`)

### 1.3 Add `docs_url` to PackageInfo
- New field: `docs_url: str | None = None` on `PackageInfo` dataclass
- Populate from `Project-URL: Documentation` in package metadata (`introspect.py`)
- Templates already reference `package.docs_url` — they'll start working

### 1.4 Progress indicators during introspection
- In `walk_package_modules` (`introspect.py:219`), print to stderr: `"  Scanning {mod_name}..."` with `\r` overwrite
- Clear line on completion
- Gate behind `not quiet` (respect future `--quiet` flag)

### 1.5 Batch summary line
- At end of `cmd_batch`, print: `"Batch complete: {success}/{total} succeeded in {elapsed:.1f}s"`
- If any failures: `"({failures} failed)"`

### 1.6 Populate logging framework
- Add `logger.debug()` calls in `introspect.py` (module import attempts, callable extraction)
- Add `logger.debug()` in `selector.py` (scoring decisions, threshold adjustments)
- Add `logger.warning()` in all `except Exception` blocks (what was skipped and why)
- Add `logger.info()` for phase transitions (introspection started/done, selection started/done)
- This makes `--log-level DEBUG` functional

---

## Part 2: The Killer Feature — `--install` (Half Day)

### 2.1 CLI Flag
- Add `--install` flag to `convert` subparser
- Compatible with all `--format` values

### 2.2 Install Targets

| Format | Target | Strategy |
|--------|--------|----------|
| Claude | `~/.claude/skills/{package}/` | Create dir, copy SKILL.md + references/ |
| Cursor | `.cursor/rules/{package}.mdc` or `.cursorrules` | Write to project-local dir |
| Windsurf | `.windsurf/rules/{package}.md` or `.windsurfrules` | Write to project-local dir |
| OpenCode | `./AGENTS.md` | Append section to project-local file |

### 2.3 Behavior
- Generate skill to `--output` dir as normal
- Then copy/install to target location
- If target exists: prompt `"Skill for {pkg} already installed. Overwrite? [y/N]"` unless `--force`
- Success message: `"Installed {pkg} skill to {target} — ready to use"`
- For Claude: skill is auto-discovered on next Claude Code session
- For Cursor/Windsurf/OpenCode: project-local, takes effect immediately

### 2.4 Implementation
- New function `install_skill(output_dir, package_name, format, force)` in `generator.py`
- Called from `cmd_convert` after `render_templates` when `--install` is set
- Uses `pathlib` for all path operations
- Expands `~` properly on all platforms

---

## Part 3: `pip-skill test` Command (Quarter Day)

### 3.1 CLI
- New subcommand: `pip-skill test <plugin-dir>`
- Exit code 0 = all pass, 1 = any fail

### 3.2 Validation Steps
1. Read `plugin.json` to get package name and version
2. Verify package is installed and version matches
3. For each function in the skill:
   - Import the module
   - Resolve the callable via `getattr`
   - Compare signature params against what's in the skill
4. If MCP server exists: `python -c "import ast; ast.parse(open('mcp-server.py').read())"` — syntax check

### 3.3 Output
```
Testing {package} skill (v{version})...
  [PASS] {qualname} — signature matches
  [FAIL] {qualname} — {reason}

Result: {pass}/{total} passed{, N stale if any}
```

---

## Part 4: Pre-built Skill Gallery (Quarter Day)

### 4.1 Generate skills for top packages
Run `pip-skill batch` for: requests, httpx, boto3, pydantic, pillow, click, rich, stripe, fastapi, sqlalchemy, pandas, numpy, beautifulsoup4, paramiko, celery

### 4.2 Publish to registry
- Create/update `xmpuspus/pip-skill-registry` repo
- Each skill as a tarball with `index.json` manifest
- `pip-skill search` and `pip-skill install` work day one

---

## Part 5: README Glow-up + Publish (Quarter Day)

### 5.1 README restructure
- Hero: one-liner + `pip install pip-skill` + demo GIF
- "Try it in 30 seconds" — 3 copy-paste commands ending with `--install`
- Before/after: "Without pip-skill" (hallucination) vs "With pip-skill" (accurate)
- Move 12 real-world examples above the fold
- Badges: PyPI version, downloads, Python versions, license

### 5.2 Publish
- `git tag v0.1.0 && git push origin v0.1.0`
- Verify `pip install pip-skill` works
- Verify `pip-skill convert requests --install` works end-to-end

---

## Out of Scope (v0.2.0)

- `pip-skill update` (skill lifecycle/merge)
- `pip-skill publish` (community contributions)
- Private registry support
- JSON output for CI/CD
- Config file support (`pyproject.toml [tool.pip-skill]`)
- Shell completions
- Windows CI testing
- Jinja2 sandboxing (security hardening)
- Module count limits for performance (boto3 optimization)
- `--quiet` flag

---

## Success Criteria

1. `pip install pip-skill && pip-skill convert requests --install` works in < 30 seconds
2. All 133+ tests pass (plus new tests for added features)
3. `pip-skill test` validates generated skills
4. `pip-skill search` returns 10+ pre-built skills
5. README has a "try it in 30 seconds" section that actually works
6. LinkedIn post has a concrete before/after demo to screenshot
