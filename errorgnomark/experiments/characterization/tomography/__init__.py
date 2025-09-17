# File Path: errorgnomark/experiments/characterization/tomography/__init__.py

"""
Tomography Sub-package
======================

This __init__.py file makes the primary tomography sub-packages
(like state_tomography and process_tomography) available under this namespace.

It intentionally does not import specific classes from the sub-packages
to maintain a clean and hierarchical structure. Users should import
directly from the specific sub-package they need.

Example:
`from errorgnomark.experiments.characterization.tomography.state_tomography import ArbitraryStateTomographyExperiment`
"""

# --- [MODIFIED] ---
# Removed the incorrect relative import that was causing the ModuleNotFoundError.
# This __init__.py should not be responsible for importing classes from its sub-packages.
# The previous line `from .base_state_tomography import ...` was incorrect
# because base_state_tomography.py is located in the 'state_tomography' subdirectory.

# By keeping this file minimal or even empty, we rely on Python's standard
# module resolution, which is more robust. We can optionally define __all__
# if we want to control `from . import *` behavior.

__all__ = [
    'state_tomography',
    'process_tomography'
]