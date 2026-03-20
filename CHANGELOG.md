# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-03-20

### Core
- `pip-skill convert` command: generate AI coding assistant skills from installed pip packages
- Heuristic function selection with 10-signal scoring algorithm
- JSON Schema generation from type annotations, signatures, and docstrings
- Package tier auto-detection (Tier 1: well-annotated, Tier 2: partial, Tier 3: dynamic/stateful)
- Support for Pydantic models, dataclasses, and C extensions

### Multi-Format Output
- Claude Code (default): SKILL.md + plugin.json + CONTEXT.md + api-reference.md
- Cursor: .cursorrules via `--format cursor`
- Windsurf: .windsurfrules via `--format windsurf`
- OpenCode: AGENTS.md via `--format opencode`
- MCP server generation via `--mcp` flag

### CLI Commands
- `pip-skill batch`: convert multiple packages in parallel from names or requirements.txt
- `pip-skill info`: show package API surface summary
- `pip-skill diff`: detect API changes between installed package and previously generated skill
- `pip-skill build`: interactive TUI builder (requires pip-skill[tui])
- `pip-skill validate`: validate generated plugin directory
- `pip-skill search` / `pip-skill install`: skill registry for pre-built skills

### Quality
- Rich plugin.json metadata: version, author, homepage, license, tool count, generation timestamp
- YAML frontmatter in SKILL.md with prerequisites and dependency list
- CONTEXT.md agent guidelines with context window tips and error handling patterns
- Safety callouts: [CAUTION] for destructive operations, [NOTE] for write operations
- External documentation links extracted from package metadata
- Progress indicators during introspection with timing output

[0.1.0]: https://github.com/xmpuspus/pip-skill/releases/tag/v0.1.0
