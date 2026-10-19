"""Structural tests for the ResolveIA package."""

import resolveia


def test_package_exposes_version() -> None:
    """The package exposes its current semantic version."""
    assert resolveia.__version__ == "0.1.0"
