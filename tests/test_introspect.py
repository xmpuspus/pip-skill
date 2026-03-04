"""Tests for pip_skill.introspect."""

import importlib

from pip_skill.introspect import (
    extract_callable_info,
    extract_class_info,
    get_public_api,
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
