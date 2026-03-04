# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Initial release
- `pip-skill convert` command: generate Claude Code plugin from pip package
- `pip-skill info` command: show package API surface summary
- `pip-skill validate` command: validate generated plugin directory
- Heuristic function selection with 10-signal scoring algorithm
- Optional LLM curation via `--select` flag
- JSON Schema generation from type annotations, signatures, and docstrings
- MCP server generation via `--mcp` flag
- Support for Pydantic models, dataclasses, C extensions
- Package tier auto-detection (Tier 1/2/3)
