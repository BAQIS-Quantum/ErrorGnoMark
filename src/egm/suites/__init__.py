"""
ErrorGnoMark (egm) Main Package
===============================

This is the root package for the 'egm' library.
"""

# Define the package version. This is a common and recommended practice.
# It is useful for package management and distribution.
__version__ = "2.0.0"

# You can also selectively expose core functionalities at the package level
# for easier access. For example, if a 'core' module has an important class
# 'CoreProcessor', you could import it here like so:
#
# from .core import CoreProcessor
#
# This would allow users to access it via 'import egm; egm.CoreProcessor'
# instead of the longer 'egm.core.CoreProcessor'.