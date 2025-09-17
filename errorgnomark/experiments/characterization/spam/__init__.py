# errorgnomark/experiments/characterization/spam/__init__.py

# This file makes the SPAMCharacterization class available for direct import
# from the 'spam' package, like so:
# from errorgnomark.experiments.characterization.spam import SPAMCharacterization

# --- FIX: Changed 'SpamCharacterizationExperiment' to 'SPAMCharacterization' ---
from .spam_characterization import SPAMCharacterization

# This makes the name available when someone does 'from ... import *'
__all__ = [
    "SPAMCharacterization"
]