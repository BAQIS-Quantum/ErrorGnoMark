# errorgnomark/experiments/characterization/incoherent/__init__.py

"""
Incoherent Error Characterization Experiments
"""

"""
1. T2* vs. T2: At-a-Glance Conclusion
Experiment	Measures Dephasing From...	Result	Key Takeaway
T2* (Ramsey)	All Noise (Slow + Fast)	Shorter Coherence Time	Shows the qubit's performance in a "real-world," unprotected scenario.
T2 (Hahn Echo)	Fast Noise Only	Longer Coherence Time	Reveals the qubit's intrinsic coherence limit by canceling slow noise.
Diagnostic Rule:

If T2* << T2, your main problem is slow, environmental noise.
If T2* ≈ T2, your main problem is fast, intrinsic noise.
2. Main Noise Sources: At-a-Glance Conclusion
Noise Type	Limits...	Caused By...
Slow / Quasi-Static	T2*	• Magnetic field drifts<br>• Charge noise (trapped electrons)<br>• Temperature fluctuations
Fast / Stochastic	T2	• Thermal noise (phonons, photons)<br>• Control electronics noise<br>• Material defects (TLS)
"""
from .t1_experiment import T1Experiment
from .t2_ramsey_experiment import T2RamseyExperiment
from .t2_echo_experiment import T2EchoExperiment
from .pauli_twirling_experiment import PauliTwirlingExperiment

__all__ = [
    "T1Experiment",
    "T2RamseyExperiment",
    "T2EchoExperiment",
    "PauliTwirlingExperiment",
]