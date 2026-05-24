"""pip-skill: Convert pip packages into AI coding assistant skills.

The high-level entry point is :func:`generate_skill`. Use it from
notebooks, eval harnesses, or CI jobs to call the same pipeline the
``pip-skill convert`` CLI runs:

    >>> from pip_skill import generate_skill
    >>> bundle = generate_skill("requests", deterministic=True)
    >>> bundle.tool_count
    20
    >>> bundle.manifest_path.name
    'MANIFEST.sha256'
"""

try:
    from importlib.metadata import version

    __version__ = version("pip-skill")
except Exception:
    __version__ = "0.0.0"

from pip_skill.api import SkillBundle, generate_skill

__all__ = ["SkillBundle", "__version__", "generate_skill"]
