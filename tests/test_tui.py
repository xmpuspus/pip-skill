"""Tests for the interactive TUI builder."""

from __future__ import annotations

import pytest

from pip_skill.introspect import CallableInfo, ModuleInfo, PackageInfo, ParamInfo
from pip_skill.tui import FunctionRow, PipSkillBuilder


@pytest.fixture()
def sample_package_info():
    """Minimal PackageInfo for TUI testing."""
    params = [
        ParamInfo(
            name="url",
            annotation="str",
            default=None,
            has_default=False,
            kind="positional_or_keyword",
        ),
    ]
    callables = [
        CallableInfo(
            name="get",
            qualname="requests.get",
            module="requests",
            signature="(url: str) -> Response",
            parameters=params,
            return_type="Response",
            docstring="Send a GET request.",
            is_async=False,
            is_method=False,
            is_classmethod=False,
            is_staticmethod=False,
            is_property=False,
            has_varargs=False,
            has_varkw=True,
            decorators=[],
            source_available=True,
        ),
        CallableInfo(
            name="post",
            qualname="requests.post",
            module="requests",
            signature="(url: str) -> Response",
            parameters=params,
            return_type="Response",
            docstring="Send a POST request.",
            is_async=False,
            is_method=False,
            is_classmethod=False,
            is_staticmethod=False,
            is_property=False,
            has_varargs=False,
            has_varkw=True,
            decorators=[],
            source_available=True,
        ),
        CallableInfo(
            name="head",
            qualname="requests.api.head",
            module="requests.api",
            signature="(url: str) -> Response",
            parameters=params,
            return_type="Response",
            docstring="Send a HEAD request.",
            is_async=False,
            is_method=False,
            is_classmethod=False,
            is_staticmethod=False,
            is_property=False,
            has_varargs=False,
            has_varkw=True,
            decorators=[],
            source_available=True,
        ),
    ]
    return PackageInfo(
        name="requests",
        import_name="requests",
        version="2.31.0",
        description="HTTP for Humans",
        author="Kenneth Reitz",
        homepage="https://requests.readthedocs.io",
        docs_url="https://requests.readthedocs.io",
        license="Apache-2.0",
        dependencies=["urllib3", "certifi"],
        modules=[
            ModuleInfo(
                name="requests",
                is_package=True,
                callables=callables[:2],
                classes=[],
                has_all=True,
                all_names=["get", "post"],
            ),
            ModuleInfo(
                name="requests.api",
                is_package=False,
                callables=callables[2:],
                classes=[],
                has_all=False,
                all_names=None,
            ),
        ],
        tier=2,
        annotation_coverage=0.6,
    )


class TestFunctionRow:
    def test_defaults(self):
        ci = CallableInfo(
            name="foo",
            qualname="mod.foo",
            module="mod",
            signature="()",
            parameters=[],
            return_type=None,
            docstring=None,
            is_async=False,
            is_method=False,
            is_classmethod=False,
            is_staticmethod=False,
            is_property=False,
            has_varargs=False,
            has_varkw=False,
            decorators=[],
            source_available=True,
        )
        row = FunctionRow(callable_info=ci, score=42)
        assert row.selected is False
        assert row.module == "mod"
        assert row.score == 42

    def test_module_auto_set(self):
        ci = CallableInfo(
            name="bar",
            qualname="deep.nested.bar",
            module="deep.nested",
            signature="()",
            parameters=[],
            return_type=None,
            docstring=None,
            is_async=False,
            is_method=False,
            is_classmethod=False,
            is_staticmethod=False,
            is_property=False,
            has_varargs=False,
            has_varkw=False,
            decorators=[],
            source_available=True,
        )
        row = FunctionRow(callable_info=ci, score=10, selected=True)
        assert row.module == "deep.nested"
        assert row.selected is True


class TestPipSkillBuilderUnit:
    """Unit tests for PipSkillBuilder methods (no full app run)."""

    def test_visible_rows_no_filter(self, sample_package_info):
        app = PipSkillBuilder(package_name="requests")
        app.rows = [
            FunctionRow(callable_info=ci, score=50 - i * 10)
            for i, ci in enumerate(_all_callables(sample_package_info))
        ]
        visible = app._visible_rows()
        assert len(visible) == 3
        # Default sort is score descending
        assert visible[0].score >= visible[1].score

    def test_visible_rows_module_filter(self, sample_package_info):
        app = PipSkillBuilder(package_name="requests")
        app.rows = [
            FunctionRow(callable_info=ci, score=50) for ci in _all_callables(sample_package_info)
        ]
        app.module_filter = "requests.api"
        visible = app._visible_rows()
        assert len(visible) == 1
        assert visible[0].callable_info.name == "head"

    def test_visible_rows_search(self, sample_package_info):
        app = PipSkillBuilder(package_name="requests")
        app.rows = [
            FunctionRow(callable_info=ci, score=50) for ci in _all_callables(sample_package_info)
        ]
        app.search_query = "post"
        visible = app._visible_rows()
        assert len(visible) == 1
        assert visible[0].callable_info.name == "post"

    def test_visible_rows_sort_name(self, sample_package_info):
        app = PipSkillBuilder(package_name="requests")
        app.rows = [
            FunctionRow(callable_info=ci, score=50 - i * 10)
            for i, ci in enumerate(_all_callables(sample_package_info))
        ]
        app.sort_mode = "name"
        visible = app._visible_rows()
        names = [r.callable_info.name for r in visible]
        assert names == sorted(names, key=str.lower)

    def test_visible_rows_sort_module(self, sample_package_info):
        app = PipSkillBuilder(package_name="requests")
        app.rows = [
            FunctionRow(callable_info=ci, score=50 - i * 10)
            for i, ci in enumerate(_all_callables(sample_package_info))
        ]
        app.sort_mode = "module"
        visible = app._visible_rows()
        modules = [r.module for r in visible]
        # Module groups should be together
        assert modules == sorted(modules)


def _all_callables(info: PackageInfo) -> list[CallableInfo]:
    result = []
    for mod in info.modules:
        result.extend(mod.callables)
    return result
