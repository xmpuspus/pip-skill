"""Utility helpers for pip-skill."""

import re


def normalize_skill_name(name: str) -> str:
    """Normalize a package name to a valid skill name.

    Rules: lowercase, underscores -> hyphens, special chars -> hyphens,
    collapse consecutive hyphens, strip leading/trailing hyphens, max 64 chars.

    Args:
        name: Raw package name.

    Returns:
        Normalized skill name suitable for directory and plugin.json name field.
    """
    result = name.lower()
    result = re.sub(r"[^a-z0-9-]", "-", result)
    result = re.sub(r"-+", "-", result)
    result = result.strip("-")
    return result[:64]


def _format_type(annotation) -> str:
    """Format a type annotation as a human-readable string.

    Args:
        annotation: A type annotation object or string.

    Returns:
        Human-readable type string.
    """
    import inspect

    if annotation is None:
        return "None"
    if annotation is inspect.Parameter.empty:
        return ""
    if isinstance(annotation, str):
        return annotation
    if hasattr(annotation, "__name__"):
        return annotation.__name__
    # Handle typing generics (e.g., List[str], Optional[int])
    return str(annotation).replace("typing.", "")


def split_type_args(type_str: str) -> list[str]:
    """Split a comma-separated type argument string respecting brackets.

    Handles nested generics like 'dict[str, list[int]]'.

    Args:
        type_str: Comma-separated type arguments, possibly nested.

    Returns:
        List of individual type argument strings.
    """
    parts = []
    depth = 0
    current = []
    for char in type_str:
        if char in "([{":
            depth += 1
            current.append(char)
        elif char in ")]}":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        parts.append("".join(current).strip())
    return [p for p in parts if p]


def eval_default_safely(default_repr: str):
    """Safely evaluate a default value string representation.

    Only handles simple literals: strings, ints, floats, bools, None, lists, dicts.

    Args:
        default_repr: String representation of a default value (from repr()).

    Returns:
        The evaluated Python value.

    Raises:
        ValueError: If the value cannot be safely evaluated.
    """
    import ast

    try:
        return ast.literal_eval(default_repr)
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"Cannot safely evaluate default: {default_repr!r}") from e


def eval_literal_values(literal_args: str) -> list:
    """Extract values from a Literal[...] type argument string.

    Args:
        literal_args: The content inside Literal[...], e.g. '"a", "b", "c"'.

    Returns:
        List of literal values.
    """
    import ast

    try:
        # Wrap in a tuple and parse
        node = ast.parse(f"({literal_args},)", mode="eval")
        if isinstance(node.body, ast.Tuple):
            return [ast.literal_eval(elt) for elt in node.body.elts]
    except (ValueError, SyntaxError):
        pass
    # Fallback: split on commas and strip quotes
    parts = []
    for part in literal_args.split(","):
        part = part.strip().strip("\"'")
        if part:
            parts.append(part)
    return parts
