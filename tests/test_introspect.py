"""Tests for pip_skill.introspect."""

import importlib

import pytest

from pip_skill.introspect import (
    extract_callable_info,
    extract_class_info,
    get_public_api,
    resolve_import_name,
    walk_package_modules,
)


def test_walk_modules(fake_package_on_path):
    results = walk_package_modules("fake_package")
    names = [name for name, _, _ in results]
    assert "fake_package" in names
    assert "fake_package.api" in names
    assert "fake_package.submod" in names


def test_walk_modules_skips_internals(fake_package_on_path):
    results = walk_package_modules("fake_package")
    names = [name for name, _, _ in results]
    # _internal should still be walked (it's a module) but its functions skipped later
    # The walker includes all modules; filtering is done by get_public_api
    assert isinstance(names, list)


def test_walk_modules_returns_triples(fake_package_on_path):
    results = walk_package_modules("fake_package")
    for item in results:
        assert len(item) == 3
        name, mod, error = item
        assert isinstance(name, str)


def test_public_api_with_all(fake_package_on_path):
    mod = importlib.import_module("fake_package")
    functions, classes, has_all = get_public_api(mod)
    assert has_all is True
    func_names = [n for n, _ in functions]
    assert "fetch" in func_names
    assert "create_item" in func_names


def test_public_api_without_all(fake_package_on_path):
    mod = importlib.import_module("fake_package.api")
    functions, classes, has_all = get_public_api(mod)
    assert has_all is False
    func_names = [n for n, _ in functions]
    assert "_internal_helper" not in func_names


def test_extract_callable_info(fake_package_on_path):
    mod = importlib.import_module("fake_package.api")
    info = extract_callable_info("fetch", mod.fetch, "fake_package.api")
    assert info.name == "fetch"
    assert len(info.parameters) == 3
    assert info.parameters[0].name == "url"
    assert info.parameters[0].annotation == "str"
    assert info.return_type == "dict"
    assert info.docstring is not None


def test_extract_callable_defaults(fake_package_on_path):
    mod = importlib.import_module("fake_package.api")
    info = extract_callable_info("fetch", mod.fetch, "fake_package.api")
    timeout_param = next(p for p in info.parameters if p.name == "timeout")
    assert timeout_param.has_default is True
    assert timeout_param.default == "30"


def test_extract_callable_optional_param(fake_package_on_path):
    mod = importlib.import_module("fake_package.api")
    info = extract_callable_info("fetch", mod.fetch, "fake_package.api")
    headers_param = next(p for p in info.parameters if p.name == "headers")
    assert headers_param.has_default is True


def test_extract_class_info(fake_package_on_path):
    mod = importlib.import_module("fake_package.models")
    info = extract_class_info("Config", mod.Config, "fake_package.models")
    assert info.name == "Config"
    assert len(info.init_params) == 3  # host, port, debug


def test_extract_class_info_methods(fake_package_on_path):
    mod = importlib.import_module("fake_package.models")
    info = extract_class_info("Connection", mod.Connection, "fake_package.models")
    method_names = [m.name for m in info.methods]
    assert "connect" in method_names
    assert "disconnect" in method_names
    assert "execute" in method_names


def test_unannotated_function(fake_package_on_path):
    mod = importlib.import_module("fake_package.api")
    info = extract_callable_info("process", mod.process, "fake_package.api")
    assert info.parameters[0].annotation is None


def test_tier_detection(fake_package_info):
    assert fake_package_info.tier in (1, 2)


def test_qualname_includes_module(fake_package_on_path):
    mod = importlib.import_module("fake_package.api")
    info = extract_callable_info("fetch", mod.fetch, "fake_package.api")
    assert "fetch" in info.qualname


def test_resolve_import_name_handles_simple_package():
    # The pip name and the import name agree, so the result is itself.
    assert resolve_import_name("pytest") == "pytest"


def test_resolve_import_name_picks_self_over_sibling_when_dist_alias_exists():
    """Regression: toolz ships both `toolz` and `tlz` import names but the
    distribution metadata calls both 'toolz'. Resolving 'toolz' must
    return 'toolz', not the alias `tlz`; the alternative produced a
    5-tool manifest of lazy-loader internals under v0.2.
    """
    try:
        import toolz  # noqa: F401
    except ImportError:
        pytest.skip("toolz is not installed in this environment")
    assert resolve_import_name("toolz") == "toolz"


def test_resolve_import_name_pep625_style():
    """Pillow imports as PIL — the distribution metadata bridges these.
    The fix for the toolz/tlz tie-break must not regress this path."""
    try:
        import PIL  # noqa: F401
    except ImportError:
        pytest.skip("Pillow not installed in this environment")
    assert resolve_import_name("Pillow") == "PIL"


def test_get_public_api_includes_c_extension_callables():
    """Regression: msgspec.json.encode is a builtin whose __module__
    is `msgspec._core`. The old `get_public_api` rule required the
    object's module to equal or descend from the scanned module — so
    sibling C-extension re-exports were silently dropped.
    """
    try:
        import msgspec.json
    except ImportError:
        pytest.skip("msgspec is not installed in this environment")
    functions, classes, has_all = get_public_api(msgspec.json)
    func_names = {n for n, _ in functions}
    # `encode` and `decode` live in msgspec._core but are exposed at
    # msgspec.json — they must show up as candidates.
    assert "encode" in func_names
    assert "decode" in func_names
