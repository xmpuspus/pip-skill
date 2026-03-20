"""Tests for pip_skill.registry."""

from unittest.mock import patch

import pytest

from pip_skill.registry import install_skill, search_registry


def test_search_registry_empty():
    """search_registry returns empty list when registry unavailable."""
    with patch("pip_skill.registry._fetch_json", return_value=None):
        results = search_registry()
    assert results == []


def test_search_registry_returns_all():
    """search_registry returns all entries when no query."""
    index = [
        {"name": "requests", "version": "2.31", "description": "HTTP library"},
        {"name": "boto3", "version": "1.28", "description": "AWS SDK"},
    ]
    with patch("pip_skill.registry._fetch_json", return_value=index):
        results = search_registry()
    assert len(results) == 2


def test_search_registry_filters_by_query():
    """search_registry filters by name and description."""
    index = [
        {"name": "requests", "version": "2.31", "description": "HTTP library"},
        {"name": "boto3", "version": "1.28", "description": "AWS SDK"},
        {"name": "httpx", "version": "0.25", "description": "Async HTTP client"},
    ]
    with patch("pip_skill.registry._fetch_json", return_value=index):
        results = search_registry("http")
    # "http" matches requests (in description "HTTP library"), httpx (in name and description)
    assert len(results) == 2
    names = [r["name"] for r in results]
    assert "requests" in names
    assert "httpx" in names
    assert "boto3" not in names


def test_search_registry_case_insensitive():
    """search_registry is case-insensitive."""
    index = [{"name": "Boto3", "version": "1.0", "description": "AWS SDK"}]
    with patch("pip_skill.registry._fetch_json", return_value=index):
        results = search_registry("boto")
    assert len(results) == 1


def test_install_skill_not_found(tmp_path):
    """install_skill raises ValueError when skill not in registry."""
    index = [{"name": "requests", "version": "2.31"}]
    with (
        patch("pip_skill.registry._fetch_json", return_value=index),
        pytest.raises(ValueError, match="not found"),
    ):
        install_skill("nonexistent", tmp_path)


def test_install_skill_registry_unavailable(tmp_path):
    """install_skill raises ValueError when registry is down."""
    with (
        patch("pip_skill.registry._fetch_json", return_value=None),
        pytest.raises(ValueError, match="unavailable"),
    ):
        install_skill("requests", tmp_path)
