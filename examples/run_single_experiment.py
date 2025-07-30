# examples/run_single_qubit_xeb.py

import random
from errorgnomark.circuits.circuit import Gate
from errorgnomark.experiments.benchmarking.xeb import XEBExperiment
from errorgnomark.experiments.benchmarking.gate_sets import SingleQubitGateSet

# Assume a simple runner exists for demonstration purposes.
# In the full framework, this would be `DeviceCharacterizer` from `api.py`.
def simple_runner(experiment: XEBExperiment):
    """A placeholder for the actual experiment execution engine."""
    print("\n" + "="*50)
    print(f"RUNNING EXPERIMENT: {experiment.experiment_type}")
    
    # The core logic of the experiment is to generate the circuits
    circuits = experiment.generate_circuits()
    
    # In a real scenario, you would now compile and run these circuits on a backend.
    # For this example, we'll just print the first circuit of the last depth.
    print("\nSample circuit generated:")
    print(circuits[-1])
    print("="*50 + "\n")


def main():
    """Main function to demonstrate different ways to run 1Q XEB."""
    
    target_qubit = 0
    depths = [1, 5, 10]
    num_circuits_per_depth = 3

    # --- SCENARIO 1: Using a pre-defined gate set by name ("clifford") ---
    xeb_clifford = XEBExperiment(
        qubits=[target_qubit],
        depths=depths,
        num_circuits=num_circuits_per_depth,
        gate_set="clifford"  # Simple string identifier
    )
    simple_runner(xeb_clifford)
    
    # --- SCENARIO 2: Using another pre-defined gate set by name ("xy") ---
    xeb_xy = XEBExperiment(
        qubits=[target_qubit],
        depths=depths,
        num_circuits=num_circuits_per_depth,
        gate_set="xy"
    )
    simple_runner(xeb_xy)

    # --- SCENARIO 3: Defining and using a CUSTOM gate set ---
    #
    # SYNTAX AND REQUIREMENTS FOR A CUSTOM GATE SET:
    # 1. Create a class that inherits from `SingleQubitGateSet`.
    # 2. Implement the `get_random_gate(self, qubit: int) -> Gate` method.
    # 3. This method MUST return a valid `Gate` object.
    
    class CustomPauliGateSet(SingleQubitGateSet):
        """A user-defined gate set of random Pauli gates (X, Y, Z)."""
        def get_random_gate(self, qubit: int) -> Gate:
            """Returns a random Pauli gate."""
            pauli_gate_name = random.choice(['x', 'y', 'z'])
            return Gate(name=pauli_gate_name, qubits=(qubit,))

    # Now, instantiate your custom gate set
    my_custom_gate_set = CustomPauliGateSet()

    # Pass the INSTANCE of your custom class to the experiment
    xeb_custom = XEBExperiment(
        qubits=[target_qubit],
        depths=depths,
        num_circuits=num_circuits_per_depth,
        gate_set=my_custom_gate_set
    )
    simple_runner(xeb_custom)


if __name__ == "__main__":
    main()