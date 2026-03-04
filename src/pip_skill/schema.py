"""JSON Schema generation from Python function signatures."""

from __future__ import annotations

import contextlib
import importlib
import inspect
import re
import warnings
from dataclasses import dataclass
from typing import get_type_hints

from docstring_parser import parse as parse_docstring

from pip_skill.introspect import CallableInfo
from pip_skill.utils import eval_default_safely, eval_literal_values, split_type_args


@dataclass
class ToolParam:
    """A single parameter in a tool schema."""

    name: str
    type_str: str
    json_type: str
    description: str
    required: bool
    default: str | None


@dataclass
class ToolSchema:
    """Complete schema for a single tool."""

    name: str  # kebab-cased function name
    function_name: str  # original Python function name
    qualname: str  # module.function
    description: str  # short description from docstring
    long_description: str  # full docstring details
    input_schema: dict  # JSON Schema object
    output_hint: str  # return type description
    example: str | None  # usage example
    parameters: list[ToolParam]


SKIP_TYPES = {"Callable", "callable", "function", "Generator", "Iterator", "Coroutine"}
PATH_TYPES = {"Path", "PurePath", "PosixPath", "WindowsPath", "PathLike"}


def annotation_to_json_type(annotation_str: str) -> dict:
    """Convert an annotation string to a JSON Schema type dict.

    Args:
        annotation_str: String representation of a type annotation.

    Returns:
        JSON Schema dict (e.g., {"type": "string"}).
    """
    mapping = {
        "str": {"type": "string"},
        "int": {"type": "integer"},
        "float": {"type": "number"},
        "bool": {"type": "boolean"},
        "bytes": {"type": "string", "contentEncoding": "base64"},
        "None": {"type": "null"},
        "NoneType": {"type": "null"},
        "Any": {},
        "dict": {"type": "object"},
        "Dict": {"type": "object"},
        "list": {"type": "array"},
        "List": {"type": "array"},
        "tuple": {"type": "array"},
        "Tuple": {"type": "array"},
        "set": {"type": "array", "uniqueItems": True},
        "Set": {"type": "array", "uniqueItems": True},
    }

    clean = annotation_str.strip()

    if clean in mapping:
        return mapping[clean]

    # Path types -> string with format
    if any(t in clean for t in PATH_TYPES):
        return {"type": "string", "format": "path"}

    # X | None  (Python 3.10+ union syntax)
    if " | None" in clean or "None | " in clean:
        base = clean.replace(" | None", "").replace("None | ", "").strip()
        return {"anyOf": [annotation_to_json_type(base), {"type": "null"}]}

    # Optional[X]
    optional_match = re.match(r"Optional\[(.+)\]$", clean)
    if optional_match:
        inner = annotation_to_json_type(optional_match.group(1).strip())
        return {"anyOf": [inner, {"type": "null"}]}

    # list[X] or List[X]
    list_match = re.match(r"(?:list|List)\[(.+)\]$", clean)
    if list_match:
        return {"type": "array", "items": annotation_to_json_type(list_match.group(1).strip())}

    # dict[K, V] or Dict[K, V]
    dict_match = re.match(r"(?:dict|Dict)\[(.+)\]$", clean)
    if dict_match:
        args = split_type_args(dict_match.group(1))
        if len(args) == 2:
            return {
                "type": "object",
                "additionalProperties": annotation_to_json_type(args[1].strip()),
            }
        return {"type": "object"}

    # Union[X, Y, ...]
    union_match = re.match(r"Union\[(.+)\]$", clean)
    if union_match:
        types = split_type_args(union_match.group(1))
        return {"anyOf": [annotation_to_json_type(t.strip()) for t in types]}

    # Literal["a", "b"]
    literal_match = re.match(r"Literal\[(.+)\]$", clean)
    if literal_match:
        values = eval_literal_values(literal_match.group(1))
        if all(isinstance(v, str) for v in values):
            return {"type": "string", "enum": values}
        return {"enum": values}

    # Fallback
    return {"type": "string", "description": f"Python type: {clean}"}


def infer_type_from_default(default_repr: str | None) -> dict:
    """Infer JSON Schema type from a default value's string representation.

    Args:
        default_repr: repr() of the default value, or None.

    Returns:
        JSON Schema type dict.
    """
    if default_repr is None:
        return {"type": "string"}

    if default_repr == "None":
        return {}
    if default_repr in ("True", "False"):
        return {"type": "boolean"}
    if default_repr.startswith(("'", '"')):
        return {"type": "string"}
    try:
        int(default_repr)
        return {"type": "integer"}
    except ValueError:
        pass
    try:
        float(default_repr)
        return {"type": "number"}
    except ValueError:
        pass
    if default_repr.startswith(("[", "(")):
        return {"type": "array"}
    if default_repr.startswith("{"):
        return {"type": "object"}

    return {"type": "string"}


def docstring_type_to_json(type_str: str) -> dict:
    """Convert a docstring type notation string to JSON Schema.

    Args:
        type_str: Type string from docstring (e.g., 'str', 'int or None').

    Returns:
        JSON Schema dict.
    """
    clean = type_str.strip()
    lower = clean.lower()

    mapping = {
        "str": {"type": "string"},
        "string": {"type": "string"},
        "int": {"type": "integer"},
        "integer": {"type": "integer"},
        "float": {"type": "number"},
        "number": {"type": "number"},
        "bool": {"type": "boolean"},
        "boolean": {"type": "boolean"},
        "dict": {"type": "object"},
        "list": {"type": "array"},
        "tuple": {"type": "array"},
        "bytes": {"type": "string"},
        "none": {"type": "null"},
        "callable": {"type": "string", "description": "Python callable"},
    }

    if lower in mapping:
        return mapping[lower]

    if "optional" in lower or "or none" in lower:
        base = re.sub(r",?\s*optional|or\s+none", "", clean, flags=re.IGNORECASE).strip()
        base_schema = docstring_type_to_json(base)
        return {"anyOf": [base_schema, {"type": "null"}]}

    return {"type": "string", "description": f"Python type: {clean}"}


def _resolve_callable(callable_info: CallableInfo):
    """Resolve a CallableInfo to its live Python object.

    Args:
        callable_info: The callable to resolve.

    Returns:
        The callable object, or None.
    """
    try:
        mod = importlib.import_module(callable_info.module)
        obj = getattr(mod, callable_info.name, None)
        if callable(obj):
            return obj
    except Exception:
        pass
    return None


def schema_via_type_adapter(fn) -> dict | None:
    """Generate JSON Schema using Pydantic TypeAdapter.

    Works when all parameters have type annotations.

    Args:
        fn: The callable to generate schema for.

    Returns:
        JSON Schema dict, or None if any parameter is unannotated.
    """
    try:
        from pydantic import create_model

        hints = get_type_hints(fn)
    except Exception:
        return None

    try:
        sig = inspect.signature(fn, eval_str=True)
    except (ValueError, TypeError):
        return None

    fields = {}
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue

        annotation = hints.get(name)
        if annotation is None:
            return None  # unannotated param -> fall back to strategy 2

        if param.default is not param.empty:
            fields[name] = (annotation, param.default)
        else:
            fields[name] = (annotation, ...)

    if not fields:
        return {"type": "object", "properties": {}}

    try:
        model = create_model(f"{fn.__name__}_Input", **fields)
        schema = model.model_json_schema()
    except Exception:
        return None

    schema.pop("title", None)
    schema.pop("$defs", None)

    return schema


def schema_via_signature(callable_info: CallableInfo) -> dict:
    """Build JSON Schema manually from CallableInfo (strategy 2).

    Works when signature is available but annotations are incomplete.

    Args:
        callable_info: The callable to generate schema for.

    Returns:
        JSON Schema dict.
    """
    from pip_skill.docstrings import get_param_description

    properties = {}
    required = []

    for param in callable_info.parameters:
        if param.name == "self":
            continue

        prop: dict = {}

        if param.annotation:
            prop.update(annotation_to_json_type(param.annotation))
        else:
            prop.update(infer_type_from_default(param.default))

        doc_desc = get_param_description(callable_info.docstring, param.name)
        if doc_desc:
            prop["description"] = doc_desc

        if param.has_default and param.default is not None and param.default != "None":
            with contextlib.suppress(ValueError, Exception):
                prop["default"] = eval_default_safely(param.default)

        properties[param.name] = prop

        if not param.has_default:
            required.append(param.name)

    schema: dict = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required

    return schema


def schema_via_docstring(callable_info: CallableInfo) -> dict:
    """Build schema purely from docstring parameter docs (strategy 3).

    Args:
        callable_info: The callable to generate schema for.

    Returns:
        JSON Schema dict.
    """
    if not callable_info.docstring:
        return {"type": "object", "properties": {}}

    parsed = parse_docstring(callable_info.docstring)
    properties = {}
    required = []

    for doc_param in parsed.params:
        prop: dict = {}

        if doc_param.type_name:
            prop.update(docstring_type_to_json(doc_param.type_name))
        else:
            prop["type"] = "string"

        if doc_param.description:
            prop["description"] = doc_param.description.strip()

        if doc_param.default:
            with contextlib.suppress(ValueError, Exception):
                prop["default"] = eval_default_safely(doc_param.default)

        properties[doc_param.arg_name] = prop

        if not doc_param.is_optional and not doc_param.default:
            required.append(doc_param.arg_name)

    schema: dict = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def empty_schema() -> dict:
    """Return an empty JSON Schema object (last resort fallback).

    Returns:
        Minimal valid JSON Schema.
    """
    return {"type": "object", "properties": {}}


def extract_description(callable_info: CallableInfo) -> tuple[str, str]:
    """Extract short and long descriptions from a callable's docstring.

    Args:
        callable_info: The callable to extract descriptions from.

    Returns:
        Tuple of (short_description, long_description).
    """
    if not callable_info.docstring:
        return (f"Call {callable_info.qualname}", "")

    parsed = parse_docstring(callable_info.docstring)
    short = parsed.short_description or callable_info.docstring.split("\n")[0]

    long_parts = []
    if parsed.long_description:
        long_parts.append(parsed.long_description)

    if parsed.params:
        long_parts.append("\nParameters:")
        for p in parsed.params:
            type_str = f" ({p.type_name})" if p.type_name else ""
            default_str = f" (default: {p.default})" if p.default else ""
            long_parts.append(f"  {p.arg_name}{type_str}: {p.description or ''}{default_str}")

    if parsed.returns:
        long_parts.append(f"\nReturns: {parsed.returns.description or ''}")

    for example in parsed.examples or []:
        if example.description:
            long_parts.append(f"\nExample:\n{example.description}")

    return (short.strip(), "\n".join(long_parts).strip())


def extract_example(callable_info: CallableInfo) -> str | None:
    """Extract a usage example from the callable's docstring.

    Args:
        callable_info: The callable to extract an example from.

    Returns:
        Example string, or None if not found.
    """
    if not callable_info.docstring:
        return None

    parsed = parse_docstring(callable_info.docstring)

    if parsed.examples:
        return parsed.examples[0].description

    lines = callable_info.docstring.split("\n")
    example_lines = []
    in_example = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(">>>"):
            in_example = True
            code = stripped[4:] if stripped.startswith(">>> ") else stripped[3:]
            example_lines.append(code)
        elif in_example and stripped.startswith("..."):
            code = stripped[4:] if stripped.startswith("... ") else stripped[3:]
            example_lines.append(code)
        elif in_example and stripped:
            break

    if example_lines:
        return "\n".join(example_lines)

    return None


def build_tool_schema(callable_info: CallableInfo) -> ToolSchema:
    """Build a complete ToolSchema from a CallableInfo.

    Args:
        callable_info: The callable to build a schema for.

    Returns:
        ToolSchema with full metadata and JSON Schema.
    """
    fn = _resolve_callable(callable_info)

    # Fallback chain for input schema
    input_schema = None
    if fn is not None:
        input_schema = schema_via_type_adapter(fn)
    if input_schema is None:
        input_schema = schema_via_signature(callable_info)

    # Merge docstring descriptions into schema properties
    if callable_info.docstring:
        parsed = parse_docstring(callable_info.docstring)
        doc_params = {p.arg_name: p for p in parsed.params}
        for prop_name, prop in input_schema.get("properties", {}).items():
            if prop_name in doc_params and "description" not in prop:
                desc = doc_params[prop_name].description
                if desc:
                    prop["description"] = desc.strip()

    short_desc, long_desc = extract_description(callable_info)
    example = extract_example(callable_info)

    # Build ToolParam list
    tool_params = []
    for param in callable_info.parameters:
        if param.name == "self":
            continue
        prop = input_schema.get("properties", {}).get(param.name, {})
        tool_params.append(
            ToolParam(
                name=param.name,
                type_str=param.annotation or "any",
                json_type=prop.get("type", "string"),
                description=prop.get("description", ""),
                required=param.name in input_schema.get("required", []),
                default=param.default,
            )
        )

    tool_name = callable_info.name.replace("_", "-")

    return ToolSchema(
        name=tool_name,
        function_name=callable_info.name,
        qualname=callable_info.qualname,
        description=short_desc,
        long_description=long_desc,
        input_schema=input_schema,
        output_hint=callable_info.return_type or "unknown",
        example=example,
        parameters=tool_params,
    )


def build_tool_schemas(callables: list[CallableInfo]) -> list[ToolSchema]:
    """Build ToolSchemas for a list of callables.

    Skips any that fail schema generation and logs a warning.

    Args:
        callables: List of CallableInfo objects.

    Returns:
        List of ToolSchema objects.
    """
    result = []
    for ci in callables:
        try:
            result.append(build_tool_schema(ci))
        except Exception as e:
            warnings.warn(f"Skipping {ci.qualname}: {e}", stacklevel=2)
    return result
