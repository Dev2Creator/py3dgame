"""Metadata consistency and the no-dead-API rule."""

from __future__ import annotations

import tomllib
from pathlib import Path

import py3dgame as p3d

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_version_matches_package():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["name"] == "py3dgame"
    assert data["project"]["version"] == p3d.__version__


def test_extras_declared_are_the_ones_tested():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    extras = set(data["project"].get("optional-dependencies", {}))
    assert extras == {"window", "dev"}


def test_every_exported_name_exists():
    for name in p3d.__all__:
        assert hasattr(p3d, name), f"{name} is exported but missing"


def test_unimplemented_systems_are_not_exported():
    # 3D, physics-3D, audio and the editor are not implemented yet, so their
    # names must stay out of the public surface.
    for absent in ("Mesh", "RigidBody", "AudioClip", "Editor", "Shader"):
        assert not hasattr(p3d, absent), f"{absent} must not exist until it works"


def test_distributions_build_from_the_project_root():
    # The build backend is setuptools and packages are declared explicitly, so a
    # missing subpackage would silently drop from the wheel. Guard the list.
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = set(data["tool"]["setuptools"]["packages"])
    on_disk = {
        ".".join(path.parent.relative_to(ROOT).parts)
        for path in (ROOT / "py3dgame").rglob("__init__.py")
    }
    assert declared == on_disk, f"packaging mismatch: {declared ^ on_disk}"
