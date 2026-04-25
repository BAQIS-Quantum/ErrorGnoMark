# File Path: errorgnomark/backends/__init__.py
# This file makes the 'backends' directory a Python package and exposes
# the primary classes for external use.

from .base_backend import BaseBackend

__all__ = [
    "BaseBackend",
]