# Contributing to pip-skill

Thanks for your interest in contributing.

## Getting Started

1. Create an issue describing the change you want to make
2. Wait for discussion and a `ready for work` label
3. Fork the repo and create a branch
4. Make your changes
5. Submit a PR referencing the issue

## Development Setup

```bash
git clone https://github.com/xmpuspus/pip-skill.git
cd pip-skill
uv sync --all-extras --dev
pre-commit install
```

## Running Tests

```bash
uv run pytest
```

## Linting

```bash
uv run ruff check .
uv run ruff format --check .
```

## PR Guidelines

- Reference the issue number in your PR
- Keep PRs small and focused
- Add tests for new functionality
- Run the full test suite before submitting
- Self-review your diff before requesting review
