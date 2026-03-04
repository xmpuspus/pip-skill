"""pip-skill: Convert pip packages to Claude Code plugins."""

try:
    from importlib.metadata import version
    __version__ = version("pip-skill")
except Exception:
    __version__ = "0.0.0"
