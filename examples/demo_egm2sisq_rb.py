# =============================================================================
# File    : examples/demo_egm2sisq_rb.py
# Version : v1.0.0 - EGM-to-SISQ Conversion Demo
# =============================================================================
"""
Demo: Converting EGM Randomized Benchmarking Circuits to SISQ Format
--------------------------------------------------------------------

This script demonstrates the full workflow of:
1. Generating RB circuits using the EGM framework.
2. Converting them to SISQ QiProgram format using SISQBackend.
3. Verifying the conversion output.

Usage
-----
    cd errorgnomark
    python examples/demo_egm2sisq_rb.py
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# --- Framework Imports ---
try:
    from egm.core.circuits.circuit import QuantumCircuit, Gate
    from egm.core.backends.convert_egm2sisq import SISQBackend, egm_to_sisq
    from egm.core.experiments.benchmarking.rb import StandardRBExperiment
except ImportError as e:
    print(f"ImportError: {e}")
    print("Please ensure 'errorgnomark' and 'pyquiet' are installed.")
    print("  pip install -e .   (from the errorgnomark directory)")
    sys.exit(1)


# =========================================================================
# Test 1: Manual Circuit Conversion (Functional API)
# =========================================================================
def test_manual_circuit():
    """Build a small circuit by hand and convert it to SISQ."""
    print("\n" + "=" * 70)
    print(" Test 1: Manual Circuit Conversion (egm_to_sisq function)")
    print("=" * 70)

    # Build a simple 2-qubit Bell-state circuit
    circuit = QuantumCircuit(qubits=[0, 1])
    circuit.add_gate(Gate("H", (0,)))
    circuit.add_gate(Gate("CNOT", (0, 1)))
    circuit.measure_all()

    print(f"\n[EGM Circuit] {circuit}")
    print(f"  Gates: {[g.name for g in circuit.gates]}")

    # Convert using the standalone function
    qi_program = egm_to_sisq(
        circuit,
        file_name="bell_state.sisq",
        qubit_name_map={0: "q0", 1: "q1"},
    )

    print(f"\n[SISQ Output]")
    print(qi_program)
    print("\n\u2705 Test 1 passed: Manual circuit converted successfully.")
    return True


# =========================================================================
# Test 2: SISQBackend with Custom Qubit Mapping
# =========================================================================
def test_sisq_backend():
    """Use SISQBackend (inherits BaseBackend) to convert a circuit."""
    print("\n" + "=" * 70)
    print(" Test 2: SISQBackend Conversion (BaseBackend subclass)")
    print("=" * 70)

    # Build a 2-qubit circuit with various gate types
    circuit = QuantumCircuit(qubits=[0, 1])
    circuit.add_gate(Gate("H", (0,)))
    circuit.add_gate(Gate("S", (0,)))
    circuit.add_gate(Gate("CZ", (0, 1)))
    circuit.add_gate(Gate("Rx", (1,), (3.14159,)))
    circuit.measure_all()

    print(f"\n[EGM Circuit] {circuit}")
    print(f"  Gates: {[g.name for g in circuit.gates]}")

    # Use SISQBackend with physical qubit mapping
    backend = SISQBackend(
        file_name="mixed_gates.sisq",
        qubit_name_map={0: "q5", 1: "q6"},
    )
    print(f"\n[Backend] {backend}")

    qi_program, _ = backend.run(circuit)

    print(f"\n[SISQ Output]")
    print(qi_program)
    print("\n\u2705 Test 2 passed: SISQBackend conversion successful.")
    return True


# =========================================================================
# Test 3: RB Circuit Generation + SISQ Conversion
# =========================================================================
def test_rb_to_sisq():
    """Generate an RB circuit using StandardRBExperiment, then convert."""
    print("\n" + "=" * 70)
    print(" Test 3: RB Circuit Generation + SISQ Conversion")
    print("=" * 70)

    # Generate a single 2-qubit Standard RB circuit
    rb_exp = StandardRBExperiment(
        qubits=[0, 1],
        seed=42,
    )

    print("\nGenerating a single 2-qubit RB circuit (depth=5)...")
    # rb_circuit = rb_exp.generate_single_circuit(depth=5)  # KeruiLi-pulse API
    rb_circuit = rb_exp.generate_single_standard_rb_circuit(depth=5, with_measurement=True)  # wuqingyuan API

    print(f"[EGM RB Circuit] {rb_circuit}")
    print(f"  Number of gates : {len(rb_circuit.gates)}")
    print(f"  Metadata        : {getattr(rb_circuit, 'metadata', 'N/A')}")

    # Convert to SISQ
    backend = SISQBackend(file_name="rb_circuit.sisq")
    qi_program, _ = backend.run(rb_circuit)

    print(f"\n[SISQ Output]")
    print(qi_program)
    print("\n\u2705 Test 3 passed: RB circuit converted to SISQ successfully.")
    return True


# =========================================================================
# Test 4: Batch Conversion
# =========================================================================
def test_batch_conversion():
    """Convert multiple RB circuits in batch using SISQBackend.execute()."""
    print("\n" + "=" * 70)
    print(" Test 4: Batch Conversion of Multiple RB Circuits")
    print("=" * 70)

    rb_exp = StandardRBExperiment(
        qubits=[0, 1],
        depths=[2, 5, 10],
        circuits_per_depth=2,
        seed=42,
    )

    print("\nGenerating batch of RB circuits (depths=[2, 5, 10], 2 per depth)...")
    # all_circuits = rb_exp.circuits()  # KeruiLi-pulse API
    all_circuits = rb_exp.generate_standard_rb_circuits(with_measurement=True)  # wuqingyuan API

    print(f"  Total circuits generated: {len(all_circuits)}")

    # Batch convert
    backend = SISQBackend(file_name="rb_batch.sisq")
    results = backend.execute(all_circuits)

    print(f"  Total programs converted: {len(results)}")

    # Show the first converted program as a sample
    print(f"\n[Sample SISQ Output - Circuit 1]")
    print(results[0][0])

    print(f"\n\u2705 Test 4 passed: Batch conversion of {len(results)} circuits successful.")
    return True


# =========================================================================
# Main
# =========================================================================
def main():
    """Run all conversion tests."""
    print("\n" + "=" * 70)
    print("  EGM-to-SISQ Conversion Demo")
    print("=" * 70)

    tests = [
        ("Manual Circuit", test_manual_circuit),
        ("SISQBackend", test_sisq_backend),
        ("RB to SISQ", test_rb_to_sisq),
        ("Batch Conversion", test_batch_conversion),
    ]

    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append(passed)
        except Exception as e:
            print(f"\n\u274c Test '{name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # --- Summary ---
    print("\n" + "=" * 70)
    print("  Test Results Summary")
    print("=" * 70)
    for (name, _), passed in zip(tests, results):
        status = "\u2705 PASS" if passed else "\u274c FAIL"
        print(f"  {status}  {name}")

    total = len(results)
    passed_count = sum(results)
    print(f"\n  Passed: {passed_count}/{total}")

    if all(results):
        print("\n\U0001f389 All tests passed! EGM-to-SISQ conversion is working correctly.")
        return 0
    else:
        print("\n\u26a0\ufe0f Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
