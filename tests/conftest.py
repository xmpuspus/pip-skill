"""Shared fixtures for pip-skill tests."""

import sys
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def fake_package_on_path():
    """Make fake_package importable during tests."""
    sys.path.insert(0, str(FIXTURES_DIR))
    yield
    if str(FIXTURES_DIR) in sys.path:
        sys.path.remove(str(FIXTURES_DIR))
    for key in list(sys.modules):
        if key.startswith("fake_package"):
            del sys.modules[key]


@pytest.fixture
def fake_package_info():
    """Pre-built PackageInfo for fake_package."""
    return _build_fake_package_info()


def _build_fake_package_info():
    """Construct PackageInfo manually for the fake package."""

    from pip_skill.introspect import (
        ModuleInfo,
        PackageInfo,
        extract_callable_info,
        extract_class_info,
        get_public_api,
        walk_package_modules,
    )

    modules_data = walk_package_modules("fake_package")

    modules = []
    for mod_name, mod, error in modules_data:
        if error or mod is None:
            continue
        functions, classes, has_all = get_public_api(mod)
        callables = [extract_callable_info(n, f, mod_name) for n, f in functions]
        class_infos = [extract_class_info(n, c, mod_name) for n, c in classes]
        modules.append(
            ModuleInfo(
                name=mod_name,
                is_package=hasattr(mod, "__path__"),
                callables=callables,
                classes=class_infos,
                has_all=has_all,
                all_names=getattr(mod, "__all__", None),
            )
        )

    return PackageInfo(
        name="fake-package",
        import_name="fake_package",
        version="1.0.0",
        description="A fake package for testing",
        author="Test Author",
        homepage=None,
        docs_url=None,
        license="MIT",
        dependencies=[],
        modules=modules,
        tier=1,
        annotation_coverage=0.75,
    )
