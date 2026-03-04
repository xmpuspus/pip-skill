"""Docstring parsing utilities for pip-skill."""

from __future__ import annotations

from dataclasses import dataclass

from docstring_parser import parse as _parse_docstring


@dataclass
class ParamDoc:
    """Parsed documentation for a single parameter."""

    name: str
    type_name: str | None
    description: str | None
    default: str | None
    is_optional: bool


def parse_params(docstring: str | None) -> list[ParamDoc]:
    """Parse parameter documentation from a docstring.

    Supports Google, NumPy, and reST styles via docstring-parser.

    Args:
        docstring: Raw docstring text, or None.

    Returns:
        List of ParamDoc objects for each documented parameter.
    """
    if not docstring:
        return []

    parsed = _parse_docstring(docstring)
    result = []
    for p in parsed.params:
        result.append(
            ParamDoc(
                name=p.arg_name,
                type_name=p.type_name,
                description=p.description,
                default=p.default,
                is_optional=p.is_optional,
            )
        )
    return result


def extract_examples(docstring: str | None) -> list[str]:
    """Extract usage examples from a docstring.

    Args:
        docstring: Raw docstring text, or None.

    Returns:
        List of example strings (may be empty).
    """
    if not docstring:
        return []

    parsed = _parse_docstring(docstring)
    examples = []

    # From parsed examples section
    for ex in parsed.examples or []:
        if ex.description:
            examples.append(ex.description.strip())

    # From doctest blocks (>>> style)
    if not examples:
        lines = docstring.split("\n")
        in_example = False
        current: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(">>>"):
                in_example = True
                code = stripped[4:] if stripped.startswith(">>> ") else stripped[3:]
                current.append(code)
            elif in_example and stripped.startswith("..."):
                code = stripped[4:] if stripped.startswith("... ") else stripped[3:]
                current.append(code)
            elif in_example:
                if current:
                    examples.append("\n".join(current))
                    current = []
                in_example = False
        if current:
            examples.append("\n".join(current))

    return examples


def get_param_description(docstring: str | None, param_name: str) -> str | None:
    """Get the description for a specific parameter from a docstring.

    Args:
        docstring: Raw docstring text, or None.
        param_name: Name of the parameter to look up.

    Returns:
        Description string, or None if not found.
    """
    for p in parse_params(docstring):
        if p.name == param_name:
            return p.description
    return None
