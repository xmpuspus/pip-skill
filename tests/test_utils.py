"""Tests for pip_skill.utils."""

from pip_skill.utils import normalize_skill_name


def test_normalize_basic():
    assert normalize_skill_name("requests") == "requests"


def test_normalize_uppercase():
    assert normalize_skill_name("Pillow") == "pillow"


def test_normalize_hyphens():
    assert normalize_skill_name("python-dateutil") == "python-dateutil"


def test_normalize_underscores():
    assert normalize_skill_name("my_package") == "my-package"


def test_normalize_special_chars():
    assert normalize_skill_name("foo.bar!baz") == "foo-bar-baz"


def test_normalize_consecutive_hyphens():
    assert normalize_skill_name("foo--bar") == "foo-bar"


def test_normalize_max_length():
    long_name = "a" * 100
    result = normalize_skill_name(long_name)
    assert len(result) <= 64


def test_normalize_strip_leading_trailing():
    assert normalize_skill_name("-foo-") == "foo"


def test_normalize_pip_package_format():
    assert normalize_skill_name("scikit-learn") == "scikit-learn"


def test_normalize_number_in_name():
    assert normalize_skill_name("h2o") == "h2o"
