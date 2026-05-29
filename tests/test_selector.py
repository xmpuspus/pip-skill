"""Tests for pip_skill.selector."""

from pip_skill.selector import (
    score_canonical,
    score_module_depth,
    score_name,
    score_param_count,
    score_uniqueness,
    select_functions,
)


def test_scoring_top_level(fake_package_info):
    selected = select_functions(fake_package_info)
    names = [fn.name for fn, _ in selected]
    assert "fetch" in names
    assert "create_item" in names


def test_deprecated_penalized(fake_package_info):
    selected = select_functions(fake_package_info)
    names = [fn.name for fn, _ in selected]
    # `fetch` is canonical and must be selected; the deprecated variant must
    # either be dropped entirely or rank strictly below it. Asserting the
    # contract unconditionally (not gated behind an `if`) so the test can't
    # pass vacuously if the fixture changes.
    assert "fetch" in names
    if "deprecated_func" in names:
        assert names.index("deprecated_func") > names.index("fetch")


def test_internal_excluded(fake_package_info):
    selected = select_functions(fake_package_info)
    names = [fn.name for fn, _ in selected]
    assert "_internal_helper" not in names


def test_max_tools_limit(fake_package_info):
    selected = select_functions(fake_package_info, max_tools=2)
    assert len(selected) <= 2


def test_include_filter(fake_package_info):
    selected = select_functions(fake_package_info, include_patterns=["fetch*"])
    names = [fn.name for fn, _ in selected]
    assert all("fetch" in n for n in names)


def test_exclude_filter(fake_package_info):
    selected = select_functions(fake_package_info, exclude_patterns=["fetch"])
    names = [fn.name for fn, _ in selected]
    assert "fetch" not in names


def test_scores_in_range(fake_package_info):
    selected = select_functions(fake_package_info)
    for _, score in selected:
        assert 0 <= score <= 100


def test_score_module_depth_top_level():
    score = score_module_depth("requests.get", "requests")
    assert score == 15


def test_score_module_depth_submodule():
    score = score_module_depth("requests.api.get", "requests")
    assert score == 12


def test_score_module_depth_deep():
    score = score_module_depth("requests.a.b.c.get", "requests")
    assert score >= 0


def test_score_name_verb_prefix():

    score = score_name("get_data")
    assert score > score_name("data_getter")


def test_score_name_underscore_prefix():
    assert score_name("_private") < score_name("public")


def test_score_name_long():
    assert score_name("a" * 31) < score_name("short_name")


def test_score_param_count_sweet_spot():

    # Build a fake CallableInfo with 3 params
    ci = _make_callable_info_with_n_params(3)
    assert score_param_count(ci) == 8


def test_score_param_count_zero():
    ci = _make_callable_info_with_n_params(0)
    assert score_param_count(ci) == 3


def test_score_param_count_many():
    ci = _make_callable_info_with_n_params(15)
    assert score_param_count(ci) == 1


def test_score_uniqueness_unique():

    ci = _make_callable_info("unique_func", ["x", "y"])
    assert score_uniqueness(ci, []) == 10


def test_score_uniqueness_similar_name():
    ci1 = _make_callable_info("get_data", ["url"])
    ci2 = _make_callable_info("getdata", ["url"])
    assert score_uniqueness(ci2, [ci1]) == 0


def test_score_uniqueness_same_params():
    ci1 = _make_callable_info("get_item", ["id", "key"])
    ci2 = _make_callable_info("fetch_item", ["id", "key"])
    result = score_uniqueness(ci2, [ci1])
    assert result == 2


def test_no_duplicates_in_result(fake_package_info):
    selected = select_functions(fake_package_info)
    names = [fn.name for fn, _ in selected]
    assert len(names) == len(set(names))


def test_score_canonical_penalizes_experimental():
    # Canonical surface should outscore the experimental variant by 20pts —
    # the gap that drove h3 to ship polygon_to_cells_experimental ahead of
    # polygon_to_cells under v0.2.
    assert score_canonical("polygon_to_cells_experimental") == -20
    assert score_canonical("polygon_to_cells") == 0


def test_score_canonical_penalizes_versioned_variants():
    assert score_canonical("get_v1") == -20
    assert score_canonical("get_v2") == -20
    assert score_canonical("legacy_handler") == 0  # word, not suffix
    assert score_canonical("handler_legacy") == -20


def test_score_canonical_penalizes_scaffolding_substrings():
    assert score_canonical("_build_tlz") == -10
    assert score_canonical("TlzLoader") == -10
    # Plain canonical names get 0
    assert score_canonical("merge") == 0
    assert score_canonical("curry") == 0


def test_score_canonical_is_case_insensitive():
    assert score_canonical("LATLNG_TO_CELL_V1") == -20
    assert score_canonical("LatLng_To_Cell") == 0


# Helpers


def _make_callable_info_with_n_params(n: int):
    from pip_skill.introspect import CallableInfo, ParamInfo

    params = [
        ParamInfo(
            name=f"p{i}",
            annotation=None,
            default=None,
            has_default=False,
            kind="positional_or_keyword",
        )
        for i in range(n)
    ]
    return CallableInfo(
        name="test_func",
        qualname="pkg.test_func",
        module="pkg",
        signature=f"({', '.join(f'p{i}' for i in range(n))})",
        parameters=params,
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


def _make_callable_info(name: str, param_names: list[str]):
    from pip_skill.introspect import CallableInfo, ParamInfo

    params = [
        ParamInfo(
            name=p,
            annotation=None,
            default=None,
            has_default=False,
            kind="positional_or_keyword",
        )
        for p in param_names
    ]
    return CallableInfo(
        name=name,
        qualname=f"pkg.{name}",
        module="pkg",
        signature=f"({', '.join(param_names)})",
        parameters=params,
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
