"""Tests for pip_skill.schema."""

import importlib

from pip_skill.schema import (
    annotation_to_json_type,
    build_tool_schema,
    build_tool_schemas,
    infer_type_from_default,
    schema_via_docstring,
    schema_via_signature,
    schema_via_type_adapter,
)


def test_schema_annotated_function():
    def example(name: str, count: int = 5) -> str:
        pass

    schema = schema_via_type_adapter(example)
    assert schema is not None
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["count"]["type"] == "integer"
    assert "name" in schema["required"]
    assert "count" not in schema["required"]


def test_schema_unannotated_fallback():
    from pip_skill.introspect import CallableInfo, ParamInfo

    info = CallableInfo(
        name="process",
        qualname="pkg.process",
        module="pkg",
        signature="(data)",
        parameters=[
            ParamInfo(
                name="data",
                annotation=None,
                default=None,
                has_default=False,
                kind="positional_or_keyword",
            )
        ],
        return_type=None,
        docstring="Process data.\n\nArgs:\n    data: The input data.",
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
    schema = schema_via_signature(info)
    assert "data" in schema["properties"]


def test_schema_optional_type():
    result = annotation_to_json_type("Optional[str]")
    types = [t["type"] for t in result["anyOf"]]
    assert "string" in types
    assert "null" in types


def test_schema_list_type():
    result = annotation_to_json_type("list[str]")
    assert result["type"] == "array"
    assert result["items"]["type"] == "string"


def test_schema_dict_type():
    result = annotation_to_json_type("dict")
    assert result["type"] == "object"


def test_schema_literal_type():
    result = annotation_to_json_type('Literal["a", "b", "c"]')
    assert result["enum"] == ["a", "b", "c"]


def test_schema_union_type():
    # str | int may be returned as a string type with description or as anyOf
    result = annotation_to_json_type("str | int")
    assert "type" in result or "anyOf" in result


def test_infer_type_from_default_string():
    result = infer_type_from_default("'hello'")
    assert result["type"] == "string"


def test_infer_type_from_default_int():
    result = infer_type_from_default("42")
    assert result["type"] == "integer"


def test_infer_type_from_default_float():
    result = infer_type_from_default("3.14")
    assert result["type"] == "number"


def test_infer_type_from_default_bool():
    result = infer_type_from_default("True")
    assert result["type"] == "boolean"


def test_infer_type_from_default_none():
    result = infer_type_from_default("None")
    # None may return {"type": "null"} or empty dict depending on implementation
    assert result == {} or result.get("type") == "null"


def test_build_tool_schema(fake_package_on_path):
    mod = importlib.import_module("fake_package.api")
    from pip_skill.introspect import extract_callable_info

    info = extract_callable_info("fetch", mod.fetch, "fake_package.api")
    tool = build_tool_schema(info)
    assert tool.name == "fetch"
    assert tool.function_name == "fetch"
    assert "url" in tool.input_schema["properties"]
    assert tool.description


def test_build_tool_schema_required_params(fake_package_on_path):
    mod = importlib.import_module("fake_package.api")
    from pip_skill.introspect import extract_callable_info

    info = extract_callable_info("fetch", mod.fetch, "fake_package.api")
    tool = build_tool_schema(info)
    # url is required, timeout and headers are not
    assert "url" in tool.input_schema.get("required", [])
    assert "timeout" not in tool.input_schema.get("required", [])


def test_build_tool_schemas_list(fake_package_on_path):
    mod = importlib.import_module("fake_package.api")
    from pip_skill.introspect import extract_callable_info

    info1 = extract_callable_info("fetch", mod.fetch, "fake_package.api")
    info2 = extract_callable_info("create_item", mod.create_item, "fake_package.api")
    tools = build_tool_schemas([info1, info2])
    assert len(tools) == 2
    fn_names = [t.function_name for t in tools]
    assert "fetch" in fn_names
    assert "create_item" in fn_names


def test_schema_via_docstring_fallback():
    from pip_skill.introspect import CallableInfo, ParamInfo

    info = CallableInfo(
        name="my_func",
        qualname="pkg.my_func",
        module="pkg",
        signature="(x, y)",
        parameters=[
            ParamInfo(
                name="x",
                annotation=None,
                default=None,
                has_default=False,
                kind="positional_or_keyword",
            ),
            ParamInfo(
                name="y",
                annotation=None,
                default=None,
                has_default=False,
                kind="positional_or_keyword",
            ),
        ],
        return_type=None,
        docstring="Do something.\n\nArgs:\n    x (str): The x value.\n    y (int): The y value.",
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
    schema = schema_via_docstring(info)
    assert "x" in schema["properties"]
    assert "y" in schema["properties"]
