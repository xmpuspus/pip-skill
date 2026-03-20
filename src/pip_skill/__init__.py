"""pip-skill: Convert pip packages into AI coding assistant skills."""

try:
    from importlib.metadata import version

    __version__ = version("pip-skill")
except Exception:
    __version__ = "0.0.0"
