"""A fake package for testing pip-skill introspection."""

__version__ = "1.0.0"
__all__ = ["fetch", "create_item", "Config", "process"]

from fake_package.api import create_item, fetch, process
from fake_package.models import Config
