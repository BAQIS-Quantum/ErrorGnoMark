# examples/demo_incoherent_characterization.py

import numpy as np

# Backend Imports
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.backends.decoherence_backend import DecoherenceBackend

# Engine Import
from errorgnomark.engine.runner import Runner

# Experiment Imports
from errorgnomark.experiments.characterization.incoherent.pauli_twirling_experiment import PauliTwirlingExperiment
from errorgnomark.experiments.characterization.incoherent.t1_experiment import T1Experiment
from errorgnomark.experiments.characterization.incoherent.t2_echo_experiment import T2EchoExperiment

# Analysis Import
from errorgnomark.analysis.characterization.incoherent_analysis import analyze_t1, analyze_t2_echo


def print_header(title):
    """Helper function to print formatted headers."""
    print("-" * 60)
    print(f"{title}")
    print("-" * 60)

def main():
    """
    Main execution function for the demo.
    """
    print("=" * 60)
    print("  ERRORGNOMARK: INCOHERENT ERROR CHARACTERIZATION DEMO")
    print("=" * 60)
    print()

    # ============================================================
    # [1] Initializing Backends and Runner
    # ============================================================
    print_header("[1] Initializing Backends and Runner...")

    # A dummy backend that introduces a simple depolarizing error.
    gate_error_backend = DummyBackend(depolarizing_error=0.01)
    
    # A specialized backend that simulates T1/T2 decay.
    t1_time = 50.0  # in microseconds
    t2_time = 30.0  # in microseconds

    # --- THIS IS THE FIX ---
    # The DecoherenceBackend __init__ expects 't1' and 't2' as arguments, not 't1_time' and 't2_time'.
    decoherence_backend = DecoherenceBackend(t1=t1_time, t2=t2_time)
    
    print(f"  - Gate Error Backend: {gate_error_backend}")
    print(f"  - Decoherence Backend: Initialized with T1={t1_time}us, T2={t2_time}us")

    # Initialize runners for each backend
    gate_runner = Runner(backend=gate_error_backend)
    decoherence_runner = Runner(backend=decoherence_backend)
    print("  - Initialized Runners.")
    print()

    # ============================================================
    # [2] Running Pauli Twirling for a 'H' gate
    # ============================================================
    print_header("[2] Running Pauli Twirling for a 'H' gate...")
    
    target_qubit_pt = [0]
    shots_pt = 2048
    
    pt_exp = PauliTwirlingExperiment(
        backend=gate_error_backend,
        gate_name='H',
        qubits=target_qubit_pt
    )
    
    # The runner executes the experiment
    results_pt = gate_runner.run(experiment=pt_exp, shots=shots_pt)
    
    # The experiment object itself handles the analysis
    analysis_pt = pt_exp.analyze(results_pt)
    
    print(f"  > Pauli Twirling Analysis Complete.")
    print(f"    - Characterized Gate: '{analysis_pt['gate_name']}' on qubit {analysis_pt['qubit']}")
    print(f"    - Estimated Fidelity: {analysis_pt['fidelity']:.4f}")
    print(f"    - Depolarizing Parameter (p): {analysis_pt['depolarizing_parameter']:.4f}")
    print()

    # ============================================================
    # [3] Running T1 and T2 Echo experiments
    # ============================================================
    print_header("[3] Running T1 and T2 Echo experiments...")

    target_qubit_coherence = [0]
    shots_coherence = 1024
    delays = np.linspace(0, 2 * t1_time, 20) # Probe delays up to 2*T1

    # --- T1 Experiment ---
    t1_exp = T1Experiment(qubits=target_qubit_coherence, delays=delays, backend=decoherence_backend)
    results_t1 = decoherence_runner.run(experiment=t1_exp, shots=shots_coherence)
    # analysis_t1 = analyze_t1(results_t1, delays, target_qubit_coherence)
    analysis_t1 = analyze_t1(results_t1, delays, target_qubit_coherence, shots=shots_coherence)

    
    print(f"  > T1 Analysis Complete.")
    print(f"    - Qubit {analysis_t1['qubit']}: Fitted T1 = {analysis_t1['t1']:.2f} us (Expected: {t1_time:.2f} us)")

    # --- T2 Echo Experiment ---
    t2_exp = T2EchoExperiment(qubits=target_qubit_coherence, delays=delays, backend=decoherence_backend)
    results_t2 = decoherence_runner.run(experiment=t2_exp, shots=shots_coherence)
    # analysis_t2 = analyze_t2_echo(results_t2, delays, target_qubit_coherence)
    analysis_t2 = analyze_t2_echo(results_t2, delays, target_qubit_coherence, shots=shots_coherence)

    print(f"  > T2 Echo Analysis Complete.")
    print(f"    - Qubit {analysis_t2['qubit']}: Fitted T2 = {analysis_t2['t2']:.2f} us (Expected: {t2_time:.2f} us)")
    print()


if __name__ == "__main__":
    main()