"""Tests for pip_skill.docstrings."""

from pip_skill.docstrings import extract_examples, get_param_description, parse_params


def test_parse_google_style():
    doc = """Do something.

    Args:
        name: The name.
        value: The value.
    """
    params = parse_params(doc)
    assert len(params) == 2
    assert params[0].name == "name"
    assert params[0].description == "The name."


def test_parse_numpy_style():
    doc = """Do something.

    Parameters
    ----------
    name : str
        The name.
    value : int
        The value.
    """
    params = parse_params(doc)
    assert len(params) == 2
    assert params[0].type_name == "str"


def test_parse_no_docstring():
    params = parse_params(None)
    assert params == []


def test_parse_empty_string():
    params = parse_params("")
    assert params == []


def test_extract_examples_doctest():
    doc = """Do something.

    Example:
        >>> do_something("hello")
        'world'
    """
    examples = extract_examples(doc)
    assert len(examples) >= 1
    assert "do_something" in examples[0]


def test_extract_examples_none():
    examples = extract_examples(None)
    assert examples == []


def test_extract_examples_no_examples():
    doc = "Just a plain docstring with no examples."
    examples = extract_examples(doc)
    assert examples == []


def test_get_param_description():
    doc = """Fetch data.

    Args:
        url: The URL to fetch from.
        timeout: Seconds to wait.
    """
    desc = get_param_description(doc, "url")
    assert desc == "The URL to fetch from."


def test_get_param_description_missing():
    desc = get_param_description(None, "url")
    assert desc is None


def test_parse_rest_style():
    doc = """Do something.

    :param name: The name.
    :type name: str
    :param value: The value.
    :type value: int
    """
    params = parse_params(doc)
    assert len(params) == 2
    assert params[0].name == "name"
