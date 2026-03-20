"""Skill registry for discovering and installing pre-built skills.

The registry is backed by a GitHub repository containing pre-built skill
packages. Users can search for available skills and install them directly.
"""

from __future__ import annotations

import json
import shutil
import subprocess  # noqa: S404
import tarfile
import tempfile
from pathlib import Path

REGISTRY_REPO = "xmpuspus/pip-skill-registry"
REGISTRY_URL = f"https://api.github.com/repos/{REGISTRY_REPO}"
RAW_URL = f"https://raw.githubusercontent.com/{REGISTRY_REPO}/main"


def _fetch_json(url: str) -> dict | list | None:
    """Fetch JSON from a URL using curl."""
    try:
        result = subprocess.run(
            ["curl", "-sf", "-H", "Accept: application/json", url],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def search_registry(query: str = "") -> list[dict]:
    """Search the skill registry for available pre-built skills.

    Args:
        query: Search query to filter skills. Empty string returns all.

    Returns:
        List of skill metadata dicts with name, version, description, toolCount.
    """
    index = _fetch_json(f"{RAW_URL}/index.json")
    if not index or not isinstance(index, list):
        return []

    if not query:
        return index

    query_lower = query.lower()
    return [
        entry
        for entry in index
        if query_lower in entry.get("name", "").lower()
        or query_lower in entry.get("description", "").lower()
    ]


def install_skill(package_name: str, output_dir: Path) -> str:
    """Install a pre-built skill from the registry.

    Downloads the skill archive from the registry repo and extracts it
    to the output directory.

    Args:
        package_name: Name of the package/skill to install.
        output_dir: Directory to install the skill into.

    Returns:
        Success message describing what was installed.

    Raises:
        ValueError: If the skill is not found in the registry.
        RuntimeError: If download or extraction fails.
    """
    # Check if skill exists in registry
    index = _fetch_json(f"{RAW_URL}/index.json")
    if not index or not isinstance(index, list):
        raise ValueError(
            f"Registry unavailable. Generate locally instead: pip-skill convert {package_name}"
        )

    entry = None
    for item in index:
        if item.get("name", "").lower() == package_name.lower():
            entry = item
            break

    if entry is None:
        raise ValueError(
            f"'{package_name}' not found in registry. "
            f"Generate locally: pip-skill convert {package_name}"
        )

    # Download the skill tarball
    skill_url = f"{RAW_URL}/skills/{package_name}.tar.gz"

    with tempfile.TemporaryDirectory() as tmpdir:
        tarball = Path(tmpdir) / f"{package_name}.tar.gz"
        result = subprocess.run(
            ["curl", "-sfL", "-o", str(tarball), skill_url],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to download skill '{package_name}'. "
                f"Generate locally: pip-skill convert {package_name}"
            )

        # Extract to output dir (with path traversal protection)
        extract_dir = Path(tmpdir) / "extracted"
        extract_dir.mkdir()
        resolved_dest = extract_dir.resolve()
        with tarfile.open(tarball) as tf:
            for member in tf.getmembers():
                member_path = (extract_dir / member.name).resolve()
                if not str(member_path).startswith(str(resolved_dest)):
                    raise RuntimeError(f"Unsafe path in archive: {member.name}")
                if member.issym() or member.islnk():
                    raise RuntimeError(f"Symlinks not allowed in archive: {member.name}")
            tf.extractall(extract_dir, filter="data")

        # Copy contents to output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        for item in extract_dir.iterdir():
            dest = output_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

    version = entry.get("version", "unknown")
    tool_count = entry.get("toolCount", "?")
    return f"Installed {package_name} v{version} ({tool_count} functions) to {output_dir}/"
