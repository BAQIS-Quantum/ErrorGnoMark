"""Smoke tests: import and version metadata."""

from __future__ import annotations

import pytest


@pytest.mark.smoke
def test_import_egm():
    import egm  # noqa: F401


@pytest.mark.smoke
def test_version_matches_pyproject():
    from importlib.metadata import version

    import egm

    assert egm.__version__ == version("errorgnomark")
