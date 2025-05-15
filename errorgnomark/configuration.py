# Standard library imports
import sys  # For system-specific parameters and functions

# Third-party imports
import numpy as np  # For numerical operations
from scipy.optimize import curve_fit, minimize  # For optimization
from tqdm import tqdm  # For progress bar visualization
from joblib import Parallel, delayed  # For parallel processing

# Qiskit-related imports
from qiskit import QuantumCircuit, transpile  # For circuit creation and transpilation
from qiskit.circuit.library import EfficientSU2  # Predefined quantum circuit templates
from qiskit.quantum_info import SparsePauliOp  # For representing Pauli operators
from qiskit_aer import AerSimulator  # For simulating quantum circuits
from qiskit.primitives import Estimator  # For estimating circuit properties


from errorgnomark.cirpulse_generator.circuit_generator import CircuitGenerator  # For circuit generation
from errorgnomark.execute import QuantumJobRunner  # For executing quantum jobs
from errorgnomark.data_analysis.layer_cirgate import MetricQuality, MetricSpeed  # For analyzing circuit metrics


class QualityQ1Gate:
    def __init__(self, qubit_index_list, result_get='noisysimulation'):
        """
        Initializes the QualityQ1Gate class with the given qubit indices and result type.

        Parameters:
            qubit_index_list (list): List of qubit indices to be used in 1-qubit random benchmarking circuits.
            result_get (str): Type of result to retrieve ('hardware' or 'noisysimulation').
        """
        self.qubit_index_list = qubit_index_list
        self.result_get = result_get

    def q1rb(self, length_max=20, step_size=4, use_fake_data=None):
        """
        Generates and runs 1-qubit random benchmarking circuits, and calculates error rates.

        Parameters:
            length_max (int): Maximum length of the circuits.
            step_size (int): Step size for the lengths of the circuits.
            use_fake_data (str or bool): Whether to generate fake data instead of executing on real hardware.

        Returns:
            dict: A dictionary containing qubit indices and their corresponding error rates.
                Format:
                {
                    "qubit_<i>": {
                        "error_rate": float  # Error rate for the given qubit
                    }
                }
        """
        # Step 1: Generate the circuits
        circuit_gen = CircuitGenerator(
            qubit_select=self.qubit_index_list,
            qubit_connectivity=[],  # Not used for 1-qubit circuits
            length_max=length_max,
            step_size=step_size
        )
        circuits = circuit_gen.rbq1_circuit(ncr=20)

        # Step 2: Execute circuits and collect results
        total_qubits = len(self.qubit_index_list)  # Number of qubit indices

        if use_fake_data == 'fake_dataq1':
            # If using fake data, execute all circuits at once
            job_runner = QuantumJobRunner(circuits)
            results = job_runner.quarkstudio_run()
            all_results = results
        else:
            # Sequential execution of circuits
            all_results = []
            for qubit_circuit in tqdm(circuits, desc="Running Q1RB Tasks", unit="qubit"):
                length_results = []
                for length_circuits in qubit_circuit:
                    job_runner = QuantumJobRunner(length_circuits)
                    if self.result_get == 'hardware':
                        results = job_runner.quarkstudio_run(compile=False)
                    elif self.result_get == 'noisysimulation':
                        results = job_runner.simulation_ideal_qiskit(noise_model=True)
                    length_results.append(results)
                all_results.append(length_results)
        
        # print('rbq1results', all_results)
        
        # Step 3: Data analysis using MetricQuality
        metric = MetricQuality(all_results={
            'hardware': all_results,
            'simulation': all_results  # Assuming simulation data is same as hardware for RB
        })

        # Compute the error rates for each qubit
        error_rates = metric.rbq1(length_max, step_size)
        
        # Step 4: Clean error rates, convert to float, and remove NaNs
        cleaned_error_rates = {}
        for qubit_index, error_rate in zip(self.qubit_index_list, error_rates):
            cleaned_error_rates[f"qubit_{qubit_index}"] = {
                "error_rate": float(error_rate) if not np.isnan(error_rate) else None
            }
        # print ('rbq1cleaned_error_rates',cleaned_error_rates)
        return cleaned_error_rates


        

    def q1xeb(self, length_max=32, step_size=4, use_fake_data=None):
        """
        Generates and runs 1-qubit XEB circuits, including both hardware/fake data execution
        and ideal simulation, and calculates error rates.

        Parameters:
            use_fake_data (str or bool): Whether to generate fake data instead of executing on real hardware.

        Returns:
            dict: Dictionary containing 'hardware' average error rates for each qubit.
        """
        # Step 1: Generate the circuits
        circuit_gen = CircuitGenerator(
            qubit_select=self.qubit_index_list, 
            qubit_connectivity=[],  # Not used for 1-qubit
            length_max=length_max,
            step_size=step_size
        )
        circuits_xeb1 = circuit_gen.xebq1_circuit(ncr=30)  # Returns [qubit][length][ncr circuits]

        # Step 2: Execute circuits and collect results
        total_steps = len(circuits_xeb1)  # Total number of qubits
        all_results_simulation = []  # Initialize simulation results as [qubit][length][ncr]
        all_results_hardware = []  # Initialize hardware results


        with tqdm(total=total_steps, desc="Running Q1XEB Tasks", unit="qubit") as pbar:  # Progress bar
            if use_fake_data == 'fake_dataq1':  # If using fake data
                job_runner = QuantumJobRunner(circuits_xeb1)  # Pass the circuits directly without looping
                results = job_runner.quarkstudio_run()  # Execute the circuits and get results
                all_results_hardware = results  # Store the results for hardware execution
                pbar.update(total_steps)  # Complete progress bar since fake data runs as a single task

            else:  # If not using fake data, execute on real hardware
                for qubit_idx, qubit_circuits in enumerate(circuits_xeb1):
                    qubit_sim_results = []  # Store simulation results for this qubit
                    qubit_hardware_results = []  # Store hardware results for this qubit

                    for length_circuits in qubit_circuits:
                        # Run simulation for ncr circuits at this qubit and length
                        job_runner_simulation = QuantumJobRunner(length_circuits)
                        simulation_results = job_runner_simulation.simulation_ideal_qiskit()  # Ideal simulation results
                        qubit_sim_results.append(simulation_results)

                        # Run hardware or noisy simulation
                        job_runner_hardware = QuantumJobRunner(length_circuits)
                        if self.result_get == 'hardware':
                            hardware_results = job_runner_hardware.quarkstudio_run(compile=False)  # Execute on hardware
                        elif self.result_get == 'noisysimulation':
                            hardware_results = job_runner_hardware.simulation_ideal_qiskit(noise_model=True)  # Simulate with noise
                        qubit_hardware_results.append(hardware_results)

                    all_results_simulation.append(qubit_sim_results)
                    all_results_hardware.append(qubit_hardware_results)
                    pbar.update(1)  # Update progress bar for each qubit
        
        # pint ('rbq2results',  all_results_hardware)
        # Step 3: Data analysis using MetricQuality
        metric = MetricQuality(all_results={
            'hardware': all_results_hardware,
            'simulation': all_results_simulation
        })
        error_rates = metric.xebq1(length_max, step_size)  # Calculate error rates from the results

        # Clean error rates: convert to float and remove NaNs
        clean_error_rates = [float(rate) if not np.isnan(rate) else None for rate in error_rates]

        return {
            'hardware': clean_error_rates,  # List of error rates for hardware results
            'use_fake_data': use_fake_data  # Show if fake data was used
        }




    def q1csb_pi_over_2_x(self, csb_avg=True):
        """
        Generate and execute π/2-x direction CSB circuits, then calculate and return the error rates.
        """
        # Generate π/2-x direction CSB circuits
        circuit_gen = CircuitGenerator(
            qubit_select=self.qubit_index_list,
            qubit_connectivity=[],
            length_max=40,
            step_size=4  # Not used for 1-qubit circuits
        )
        pi_over_2_x_circuits = circuit_gen.generate_pi_over_2_x_csb_circuits()

        # Execute circuits and collect results
        total_steps = len(pi_over_2_x_circuits)  # Total number of qubits
        hardware_results = []

        # Loop through each qubit's circuits
        with tqdm(total=total_steps, desc="Running Q1CSB π/2-x Tasks", unit="qubit") as pbar:
            for qubit_idx, qubit_circuits in enumerate(pi_over_2_x_circuits):
                # Check if there are any circuits for this qubit
                if not qubit_circuits:
                    print(f"Warning: No circuits found for qubit {qubit_idx}")
                    hardware_results.append(None)
                    pbar.update(1)
                    continue

                # Check if the circuits are valid
                if any(circuit is None for circuit in qubit_circuits):
                    print(f"Error: Invalid circuit(s) for qubit {qubit_idx}. Skipping execution.")
                    hardware_results.append(None)
                    pbar.update(1)
                    continue

                # Run the job for this qubit's circuits
                job_runner = QuantumJobRunner(qubit_circuits)
                try:
                    if self.result_get == 'hardware':
                        results = job_runner.quarkstudio_run(compile=False)
                    elif self.result_get == 'noisysimulation':
                        results = job_runner.simulation_ideal_qiskit(noise_model=True)

                    if results is None:
                        print(f"Error: No results returned for qubit {qubit_idx}")
                        hardware_results.append(None)
                    else:
                        hardware_results.append(results)

                except Exception as e:
                    print(f"Error processing qubit {qubit_idx}: {e}")
                    hardware_results.append(None)

                pbar.update(1)

        # Calculate CSB error rates
        all_results = {
            'hardware': hardware_results,
            'simulation': hardware_results  # Placeholder for simulation data if available
        }

        metric_quality = MetricQuality(all_results)
        csb_errors = metric_quality.csbq1(csb_avg=csb_avg)

        # Compute average error rates if csb_avg=True
        if csb_avg:
            # Extract relevant error rates from the csb_errors dictionary
            process_infidelities = csb_errors.get('process_infidelities', [])
            stochastic_infidelities = csb_errors.get('stochastic_infidelities', [])
            angle_errors = csb_errors.get('angle_errors', [])

            avg_process_infidelity = np.mean([x for x in process_infidelities if x is not None]) if process_infidelities else None
            avg_stochastic_infidelity = np.mean([x for x in stochastic_infidelities if x is not None]) if stochastic_infidelities else None
            avg_angle_error = np.mean([x for x in angle_errors if x is not None]) if angle_errors else None

            csb_errors['process_infidelity_avg'] = avg_process_infidelity
            csb_errors['stochastic_infidelity_avg'] = avg_stochastic_infidelity
            csb_errors['angle_error_avg'] = avg_angle_error

        return csb_errors




    def q1csb_gate(self, gate_name, rep=1, cutoff=1e-10, target_phase=np.pi):
        """
        Generate and execute CSB circuits for a specified quantum gate, then calculate and return the error rates.

        Parameters:
            gate_name (str): The name of the quantum gate, e.g., 'XGate', 'YGate', 'ZGate', etc.
            rep (int): Number of repetitions for the rotation gate.
            cutoff (float): Singular value cutoff threshold for the matrix pencil method.
            target_phase (float): Target rotation angle for the gate under test.

        Returns:
            dict: A dictionary containing process infidelity, stochastic infidelity, and angle error for each qubit.
        """
        # Step 1: Generate CSB circuits for the specified gate
        circuit_gen = CircuitGenerator(
            qubit_select=self.qubit_index_list, 
            qubit_connectivity=[],  # Not used for 1-qubit circuits
        )
        
        csb_circuits = circuit_gen.generate_csbcircuit_for_gate(gate_name=gate_name, ini_modes=['x', 'z'], rep=rep)

        # Step 2: Execute circuits and collect results
        hardware_results = []

        for qubit_idx, qubit_circuits in enumerate(csb_circuits):
            job_runner = QuantumJobRunner(qubit_circuits)
            
            # Execute on hardware or simulation based on the `result_get` flag
            if self.result_get == 'hardware':
                results = job_runner.quarkstudio_run(compile=False)
            elif self.result_get == 'noisysimulation':
                results = job_runner.simulation_ideal_qiskit(noise_model=True)
            
            hardware_results.append(results)

        # Step 3: Calculate CSB error rates using MetricQuality
        all_results = {
            'hardware': hardware_results,
            'simulation': []  # Placeholder for simulation data if available
        }
        
        metric_quality = MetricQuality(all_results)
        csb_errors = metric_quality.csbq1()

        # Step 4: Return error results in dictionary format
        result = {
            'qubit_index': self.qubit_index_list,  # Include qubit indices for clarity
            'process_infidelities': csb_errors.get('process_infidelities', []),
            'stochastic_infidelities': csb_errors.get('stochastic_infidelities', []),
            'angle_errors': csb_errors.get('angle_errors', [])
        }

        # If error averages are needed, include them in the result
        if 'process_infidelity_avg' in csb_errors:
            result['process_infidelity_avg'] = csb_errors.get('process_infidelity_avg')
        if 'stochastic_infidelity_avg' in csb_errors:
            result['stochastic_infidelity_avg'] = csb_errors.get('stochastic_infidelity_avg')
        if 'angle_error_avg' in csb_errors:
            result['angle_error_avg'] = csb_errors.get('angle_error_avg')

        return result




class QualityQ2Gate:
    def __init__(self, qubit_pair_list, result_get='hardware'):
        """
        Initializes the QualityQ2Gate class with the given qubit pairs.

        Parameters:
            qubit_pair_list (list of tuples): List of qubit pairs for 2-qubit random benchmarking circuits.
            result_get (str): Type of result to retrieve ('hardware' or 'noisysimulation').
        """
        self.qubit_pair_list = qubit_pair_list
        self.result_get = result_get



    def q2rb(self, length_max=24, step_size=4, use_fake_data=None):
        """
        Generates and runs 2-qubit random benchmarking circuits, and calculates error rates.

        Parameters:
            length_max (int): Maximum length of the circuits.
            step_size (int): Step size for the circuit length.
            use_fake_data (str or bool): Whether to generate fake data instead of executing on real hardware.

        Returns:
            dict: Dictionary of error rates for each qubit pair. Includes keys for the error rates 
                of each pair and optionally the average error rate across all pairs.
        """
        # Step 1: Generate circuits using CircuitGenerator
        circuit_gen = CircuitGenerator(
            qubit_select=[],  # Not used for 2-qubit circuits
            qubit_connectivity=self.qubit_pair_list,  # Define qubit pairs
            length_max=length_max,
            step_size=step_size
        )

        circuits = circuit_gen.rbq2_circuit(ncr=20)  # Generate 2-qubit RB circuits

        # Step 2: Execute circuits and collect results sequentially
        total_qubit_pairs = len(circuits)  # Total number of qubit pairs
        all_results = []

        if use_fake_data == 'fake_dataq2':
            # If using fake data, execute all circuits at once
            job_runner = QuantumJobRunner(circuits)
            results = job_runner.quarkstudio_run()
            all_results = results
        else:
            # Sequential execution for real hardware or noisy simulation
            for qubit_pair_circuit in tqdm(circuits, desc="Running Q2RB Tasks", unit="pair"):
                length_results = []
                for length_circuits in qubit_pair_circuit:
                    job_runner = QuantumJobRunner(length_circuits)
                    if self.result_get == 'hardware':
                        results = job_runner.quarkstudio_run(compile=False)
                    elif self.result_get == 'noisysimulation':
                        results = job_runner.simulation_ideal_qiskit(noise_model=True)
                    length_results.append(results)
                all_results.append(length_results)

        # print('rbq2results', all_results)

        # Step 3: Data analysis using MetricQuality
        metric = MetricQuality(all_results={
            'hardware': all_results,
            'simulation': all_results  # Assuming simulation data is same as hardware for RB
        })
        error_rates = metric.rbq2(length_max, step_size)
        # print('error_rates', error_rates)

        # Step 4: Prepare the results in a dictionary format
        result_dict = {}

        for qubit_pair_idx, error_rate in enumerate(error_rates):
            qubit_pair = self.qubit_pair_list[qubit_pair_idx]  # Get the qubit pair index
            result_dict[str(qubit_pair)] = {
                "error_rate": float(error_rate) if not np.isnan(error_rate) else None
            }

        # Optionally, compute average error rates across all pairs
        avg_error_rate = (
            np.mean([rate for rate in error_rates if not np.isnan(rate)])
            if error_rates else None
        )
        result_dict['average_error_rate'] = avg_error_rate

        return result_dict



    def q2xeb(self, length_max=32, step_size=4, use_fake_data=None):
        """
        Generates and runs 2-qubit XEB (cross-entropy benchmarking) circuits, including both hardware/fake data execution
        and ideal simulation, and calculates error rates.

        Parameters:
            length_max (int): Maximum circuit length for the benchmarking.
            step_size (int): Step size for generating circuits of different lengths.
            use_fake_data (str or bool): Whether to generate fake data instead of executing on real hardware.

        Returns:
            dict: Dictionary containing 'hardware' average error rates for each qubit pair, 
                and a flag indicating if fake data was used.
        """
        # Step 1: Generate the circuits for benchmarking
        circuit_gen = CircuitGenerator(
            qubit_select=[], 
            qubit_connectivity=self.qubit_pair_list,  # Define qubit pairs
            length_max=length_max,
            step_size=step_size
        )
        circuits_xeb2 = circuit_gen.xebq2_circuit(ncr=30)  # Returns [qubit pair][length][ncr circuits]

        # Initialize containers for hardware and simulation results
        all_results_simulation = []  # [qubit pair][length][ncr]
        all_results_hardware = []  # [qubit pair][length][ncr]

        # Total number of qubit pairs to process
        total_steps = len(circuits_xeb2)

        with tqdm(total=total_steps, desc="Running Q2XEB Tasks", unit="pair") as pbar:  # Progress bar
            if use_fake_data == 'fake_dataq2':  # If using fake data
                job_runner = QuantumJobRunner(circuits_xeb2)  # Pass the circuits directly without looping
                results = job_runner.quarkstudio_run()
                all_results_hardware = results  # Assign the results directly to hardware results
                pbar.update(total_steps)  # Complete progress bar since fake data runs as a single task
            else:  # If executing on real hardware or noisy simulation
                for qubit_idx, qubit_circuits in enumerate(circuits_xeb2):
                    qubit_sim_results = []
                    qubit_hardware_results = []

                    # Run for each length of the circuits
                    for length_circuits in qubit_circuits:
                        # Run simulation for ncr circuits at this qubit pair and length
                        job_runner_simulation = QuantumJobRunner(length_circuits)
                        simulation_results = job_runner_simulation.simulation_ideal_qiskit()
                        qubit_sim_results.append(simulation_results)

                        # Run hardware or noisy simulation
                        job_runner_hardware = QuantumJobRunner(length_circuits)
                        if self.result_get == 'hardware':
                            hardware_results = job_runner_hardware.quarkstudio_run(compile=False)
                        elif self.result_get == 'noisysimulation':
                            hardware_results = job_runner_hardware.simulation_ideal_qiskit(noise_model=True)
                        qubit_hardware_results.append(hardware_results)

                    # Append the results for this qubit pair
                    all_results_simulation.append(qubit_sim_results)
                    all_results_hardware.append(qubit_hardware_results)
                    pbar.update(1)  # Update the progress bar for each qubit pair
        
        # print ('xebq2results', all_results_hardware)
        # Step 3: Data analysis using MetricQuality
        metric = MetricQuality(all_results={
            'hardware': all_results_hardware,
            'simulation': all_results_simulation
        })
        error_rates = metric.xebq2(length_max=length_max, step_size=step_size)

        # Clean error rates: convert to float and remove NaNs
        clean_error_rates = [float(rate) if not np.isnan(rate) else None for rate in error_rates]

        # Return a dictionary with the results
        return {
            'hardware': clean_error_rates,  # Hardware error rates for each qubit pair
            'use_fake_data': use_fake_data  # Flag indicating if fake data was used
        }


    def q2csb_cz(self):
        """
        Calculates the CSB error (process purity, random purity, theta error, and phi error) for 2-qubit CZ gates.

        Returns:
            dict: A dictionary containing the source of results and the error metrics for each qubit pair.
        """
        # Step 1: Determine qubit connectivity based on result_get
        if self.result_get == 'noisysimulation':
            # Generate a connectivity list with [0, 1] for each qubit pair in qubit_pair_list
            qubit_connectivity = [[0, 1] for _ in self.qubit_pair_list]
        else:
            # Use the original qubit_pair_list
            qubit_connectivity = self.qubit_pair_list

        # Step 2: Generate circuits using CircuitGenerator
        generator = CircuitGenerator(
            qubit_select=[],  # Not used in current implementation
            qubit_connectivity=qubit_connectivity,
            length_max=24,    # Adjust as necessary
            step_size=4      # Adjust as necessary
        )
        circuits_nested = generator.generate_csbcircuit_for_czgate()

        # Step 3: Execute the circuits and collect results
        total_steps = len(circuits_nested)  # Total number of qubit pairs
        hardware_results = []

        with tqdm(total=total_steps, desc="Running Q2CSB CZ Tasks", unit="pair") as pbar:  # Initialize progress bar
            for qubit_pair_circuits in circuits_nested:
                job_runner = QuantumJobRunner(qubit_pair_circuits)  # Assuming QuantumJobRunner is implemented correctly
                
                # Choose the method of result retrieval based on result_get
                if self.result_get == 'hardware':
                    results = job_runner.quarkstudio_run(compile=False)
                elif self.result_get == 'noisysimulation':
                    results = job_runner.simulation_ideal_qiskit(noise_model=True)
                else:
                    raise ValueError(f"Unknown result_get option: {self.result_get}")

                hardware_results.append(results)
                pbar.update(1)  # Update progress bar for each qubit pair
        
        # print ('csbq2results', hardware_results)
        # Step 4: Compute CSB error using MetricQuality
        metric = MetricQuality(all_results={
            'hardware': hardware_results,
            'simulation': hardware_results  # Assuming hardware results are compared to themselves for now
        })
        csb_results = metric.csbq2cz()

        # Step 5: Return the results with source information
        csb_results_with_source = {
            "source": self.result_get,  # Dynamic source, could be 'simulation' or 'hardware'
            "qubit_pairs_results": csb_results  # Error metrics for each qubit pair
        }

        return csb_results_with_source

    def q2csb_cnot(self):
        """
        Calculates the CSB error (process purity, random purity, theta error, and phi error) for 2-qubit CNOT gates.

        Returns:
            dict: A dictionary containing the source of results and the error metrics for each qubit pair.
        """
        # Step 1: Determine qubit connectivity based on result_get
        if self.result_get == 'noisysimulation':
            qubit_connectivity = [[0, 1] for _ in self.qubit_pair_list]
        else:
            qubit_connectivity = self.qubit_pair_list

        # Step 2: Generate circuits using CircuitGenerator
        generator = CircuitGenerator(
            qubit_select=[],  # Not used in current implementation
            qubit_connectivity=qubit_connectivity,
            length_max=30,
            step_size=4
        )
        circuits_nested = generator.generate_csbcircuit_for_cnotgate()

        # Step 3: Execute the circuits and collect results
        total_steps = len(circuits_nested)
        hardware_results = []

        with tqdm(total=total_steps, desc="Running Q2CSB CNOT Tasks", unit="pair") as pbar:
            for qubit_pair_circuits in circuits_nested:
                job_runner = QuantumJobRunner(qubit_pair_circuits)
                if self.result_get == 'hardware':
                    results = job_runner.quarkstudio_run(compile=False)
                elif self.result_get == 'noisysimulation':
                    results = job_runner.simulation_ideal_qiskit(noise_model=True)
                else:
                    raise ValueError(f"Unknown result_get option: {self.result_get}")

                hardware_results.append(results)
                pbar.update(1)

        # Step 4: Compute CSB error using MetricQuality
        metric = MetricQuality(all_results={
            'hardware': hardware_results,
            'simulation': hardware_results
        })
        csb_results = metric.csbq2cnot()

        # Step 5: Return the results with source information
        csb_results_with_source = {
            "source": self.result_get,
            "qubit_pairs_results": csb_results
        }

        return csb_results_with_source




class QualityQmgate:

    def __init__(self, qubit_connectivity, qubit_index_list, result_get='noisysimulation'):
        """
        Initializes the PropertyQ2Gate class with the given qubit pairs.
        
        Parameters:
           qubit_connectivity : List of qubit pairs for 2-qubit
        """
        self. qubit_connectivity = qubit_connectivity
        self. qubit_index_list = qubit_index_list
        self. result_get = result_get


    def qmghz_fidelity(self, ncr=3, use_fake_data=None):
        """
        Generates GHZ circuits, executes them, and calculates the fidelity.

        Parameters:
            nqubit_ghz (int): Number of qubits for the GHZ circuit.
            ncr (int): Number of circuits to generate (repeated execution for fidelity calculation).
            use_fake_data (str or bool): Whether to generate fake data instead of executing on real hardware.

        Returns:
            dict: Dictionary containing the 'fidelity' of the GHZ state, with information about qubit index and source.
        """
        # Step 1: Generate GHZ circuits
        circuit_gen = CircuitGenerator(
            qubit_select=self.qubit_index_list,
            qubit_connectivity=self.qubit_connectivity
        )

        nqghz_list = [3, 4, 5, 6, 7, 8]  # List of qubit sizes for GHZ circuits
        ghz_circuits = circuit_gen.ghz_circuits(nqghz_list, ncr)
        # print (' ghz_circuits ', ghz_circuits[0][0])
        # Step 2: Execute circuits and collect results
        total_circuits = len(ghz_circuits)  # Total number of GHZ circuits
        hardware_results = []

        # Iterate over circuits and execute
        for circuits in tqdm(ghz_circuits, desc="Running GHZ Fidelity Tasks", unit="circuit", total=total_circuits):
            if use_fake_data == 'fake_data_ghz':  # Use fake data generation
                from FakeDataGenerator import generate_fake_ghz_data
                all_results = generate_fake_ghz_data(circuits)
            else:  # Execute on real hardware or noisy simulation
                job_runner = QuantumJobRunner(circuits)
                if self.result_get == 'hardware':
                    results = job_runner.quarkstudio_run(compile=False)
                elif self.result_get == 'noisysimulation':
                    results = job_runner.simulation_ideal_qiskit(noise_model=True)
            hardware_results.append(results)
        # print ('hardware_resultsghz',hardware_results)
        # Step 3: Prepare results for analysis
        all_results = {
            'hardware': hardware_results,
            'simulation': hardware_results  # Can be adjusted based on simulation needs
        }
        
        # print ('ghzrestults',all_results )
        # Step 4: Analyze GHZ fidelity using MetricQuality
        metric = MetricQuality(all_results=all_results)
        fidelity = metric.ghzqm_fidelity()

        # Return results in dictionary format
        return {
            'fidelity': fidelity,
            'qubit_index': self.qubit_index_list,  # Include qubit index information
            'source': self.result_get  # Indicate the source of the data (hardware or simulation)
        }

    def qmmrb(self, density_cz=0.75, ncr=5):
        """
        Generates and executes quantum circuits based on the provided CZ gate density and number of circuits.

        Parameters:
            density_cz (float): Density of CZ gates in the circuit (0 < density_cz <= 1).
            ncr (int): Number of circuits to generate for each length in the length list.

        Returns:
            dict: A nested dictionary where the first layer corresponds to qubit groups,
                and the second layer corresponds to different circuit lengths. 
                Each element is a dictionary with the qubit list and corresponding MRB results.
                Structure: 
                {
                    'hardware': {
                        'qubit_group_1': {
                            'length_1': {'qubits': [qubit_list], 'mrb_result': average_S},
                            'length_2': {'qubits': [qubit_list], 'mrb_result': average_S},
                            ...
                        },
                        ...
                    },
                    'simulation': { ... }
                }
        """
        # Initialize results containers for hardware and simulation
        all_hardware = []   # Structure: [qubit_group][length][ncr_circuit]
        all_simulation = [] # Structure: [qubit_group][length][ncr_circuit]

        # Initialize CircuitGenerator and generate MRB circuits
        circuit_gen = CircuitGenerator(
            qubit_select=self.qubit_index_list,
            qubit_connectivity=self.qubit_connectivity
        )
        generated_circuits, qubits_for_length = circuit_gen.mrbqm_circuit(ncr=ncr)  # Structure: [qubit_group][length][ncr]

        # Total number of tasks for the progress bar
        total_steps = sum(len(length_circuits) for qubit_group_circuits in generated_circuits for length_circuits in qubit_group_circuits)

        # Execute circuits and collect results
        with tqdm(total=total_steps, desc="Running MRB Tasks", unit="circuit") as pbar:
            for qubit_group_circuits in generated_circuits:
                result_hardware_len = []
                result_noisysim_len = []

                for length_circuits in qubit_group_circuits:
                    job_runner = QuantumJobRunner(circuits=length_circuits)

                    # Execute on hardware or noisy simulation
                    if self.result_get == 'hardware':   
                        execution_results = job_runner.quarkstudio_run(compile=True)
                    elif self.result_get == 'noisysimulation':
                        execution_results = job_runner.simulation_ideal_qiskit(noise_model=True)
                    result_hardware_len.append(execution_results)

                    # Execute on noiseless simulation
                    simulation_results = job_runner.simulation_ideal_qiskit(compile=True,noise_model=None)
                    result_noisysim_len.append(simulation_results)

                    pbar.update(1)  # Increment progress bar for each length of circuits

                all_hardware.append(result_hardware_len)
                all_simulation.append(result_noisysim_len)

        # Prepare all results in a dictionary format with clear qubit index information
        all_results = {
            'hardware': all_hardware,
            'simulation': all_simulation
        }
        
        # print ('all_results',all_results)
        # Initialize MetricQuality and compute effective polarization
        metric_quality = MetricQuality(all_results=all_results)
        polarizations = metric_quality.mrbqm()
        polarization_results = {'polarizations': polarizations, 'qubits_for_length': qubits_for_length}
        return polarization_results 


    def qmstanqv(self, ncr=5, nqubits_max=5):
        """
        Generates Quantum Volume (QV) circuits, executes them, and evaluates the Quantum Volume (QV).

        Parameters:
            ncr (int): Number of random circuits per qubit configuration.
            nqubits_max (int): Maximum number of qubits for the quantum circuits.

        Returns:
            dict: A dictionary containing QV results for each qubit configuration, structured as:
                {
                    "nqubits_<i>": {
                        "total_qubits": int,  # Total number of qubits
                        "quantum_volume": int,  # Quantum volume value (2^log2(QV))
                        "error": float,  # The error for this configuration (if available)
                        "fidelity": float  # The fidelity of the circuit execution (if available)
                    }
                }
        """
        # Step 1: Generate QV circuits
        circuit_gen = CircuitGenerator(
            qubit_select=self.qubit_index_list,  # Use the provided qubit indices
            qubit_connectivity=self.qubit_connectivity
        )

        # Generate QV circuits using the stanqvqm_circuit method
        all_circuits = circuit_gen.stanqvqm_circuit(ncr=ncr, nqubits_max=nqubits_max)  # Generates a dictionary of circuits
        
        # Step 2: Execute the circuits and collect hardware results
        total_tasks = len(all_circuits)  # Number of qubit configurations
        results_all = []

        with tqdm(total=total_tasks, desc="Running QV Tasks", unit="config") as pbar:
            for qi in range(len(all_circuits)):
                hardware_results = {}  # To store the hardware execution results

                # Submit ncr circuits for the current qubit configuration
                job_runner = QuantumJobRunner(all_circuits[qi])

                # Store execution results for the current configuration
                if self.result_get == 'hardware':
                    hardware_results = job_runner.quarkstudio_run(compile=True)  # Execute the circuits and get results
                elif self.result_get == 'noisysimulation':
                    hardware_results = job_runner.simulation_ideal_qiskit(noise_model=True)  # Execute the circuits and get results
                
                results_all.append(hardware_results)
                pbar.update(1)  # Increment progress bar for each configuration

        # Step 3: Use MetricQuality to analyze the results and calculate Quantum Volume
        metric = MetricQuality(all_results={
            'hardware': results_all  # Pass the hardware results to MetricQuality
        })

        # Step 4: Get the Quantum Volume results
        qv_results = metric.stanqvqm(ncr=ncr)  # This function handles heavy output probability analysis and QV calculation

        # Format the output results
        formatted_results = {}

        for nq, result in qv_results.items():
            # Include the qubit index and result information in the output dictionary
            formatted_results[f"nqubits_{nq}"] = {
                "total_qubits": result["total_qubits"],
                "quantum_volume": result["quantum_volume"],
                "error": result.get("error", None),  # Include error if available
                "fidelity": result.get("fidelity", None)  # Include fidelity if available
            }

        return formatted_results




class SpeedQmgate:
    """
    SpeedQmgate class to calculate CLOPSQM by generating circuits, executing them on QuarkStudio,
    and computing the CLOPSQM metric.
    """
    
    def __init__(self, qubit_connectivity, qubit_index_list, result_get='hardware'):
        """
        Initializes the SpeedQmgate class.

        Parameters:
            qubit_connectivity (list of tuples): Qubit connections (e.g., [(0, 1), (1, 2)]).
            qubit_index_list (list): List of qubit indices (e.g., [0, 1, 2, 3]).
            result_get (str, optional): Specifies whether to get 'hardware' results or 'noisysimulation'. Default is 'hardware'.
        """
        self.qubit_connectivity = qubit_connectivity
        self.qubit_index_list = qubit_index_list
        self.result_get = result_get
    
    def qmclops(self, num_templates=5, num_updates=5, num_layers=5, num_qubits=5, num_shots=1):
        """
        Calculates CLOPSQM (Circuit Layer Optimization for Quantum Simulation Metric).

        Parameters:
            num_templates (int): Number of templates (M).
            num_updates (int): Number of parameter updates (K).
            num_shots (int): Number of shots (S).
            num_layers (int): Number of QV layers (D).
            num_qubits (int): Number of qubits involved in the circuit.

        Returns:
            dict: A dictionary containing the CLOPSQM metric.
        """

        # Step 1: Generate CLOPSQM circuits
        circuit_gen = CircuitGenerator(
            qubit_select=self.qubit_index_list,  # Use the provided qubit indices
            qubit_connectivity=self.qubit_connectivity  # Use the provided qubit connectivity
        )
        # Generate the circuits using the clopsqm_circuit function
        generated_circuits = circuit_gen.clopsqm_circuit(
            num_templates=num_templates, 
            num_updates=num_updates, 
            num_qubits=num_qubits
        )

        # Step 2: Execute the generated circuits on hardware or noisy simulation
        hardware_results = []
        elapsed_times = []
        total_layers = len(generated_circuits)

        for layer_idx, layer_circuits in enumerate(generated_circuits):
            for template_circuits in layer_circuits:
                # Flatten template circuits to execute as a batch
                flattened_circuits = [circuit for circuit in template_circuits]
                job_runner = QuantumJobRunner(circuits=flattened_circuits)

                if self.result_get == 'hardware':
                    # Execute circuits on hardware and get results and elapsed time
                    execution_results, execution_time = job_runner.quarkstudio_run(
                        compile=True,
                        shots=num_shots,
                        elapsed_time=True
                    )
                elif self.result_get == 'noisysimulation':
                    # Execute circuits using noisy simulation and get results and elapsed time
                    execution_results, execution_time = job_runner.simulation_ideal_qiskit(
                        noise_model=None,
                        elapsed_time=True,
                        shots=num_shots
                    )
                hardware_results.append(execution_results)
                elapsed_times.append(execution_time)

        # Step 3: Calculate CLOPSQM metric
        # MetricSpeed is used to calculate CLOPSQM based on the execution times
        metric_speed = MetricSpeed(all_results={"hardware": elapsed_times})
        clopsqm_value = metric_speed.clopsqm(
            num_templates=num_templates, 
            num_updates=num_updates, 
            num_shots=num_shots, 
            num_layers=num_layers
        )

        # Step 4: Return only CLOPSQM value as a dictionary
        return {"CLOPSQM": clopsqm_value}




# Define cost function for VQE
def cost_func(params, ansatz, hamiltonian, backend):
    """Estimate energy using Qiskit Aer simulator.

    Args:
        params (np.ndarray): Array of ansatz parameters.
        ansatz (QuantumCircuit): Parameterized ansatz circuit.
        hamiltonian (SparsePauliOp): Hamiltonian as a SparsePauliOp.
        backend (Backend): Qiskit Aer simulator backend.

    Returns:
        float: Energy estimate.
    """
    param_dict = dict(zip(ansatz.parameters, params))
    bound_ansatz = ansatz.assign_parameters(param_dict)
    estimator = Estimator()
    result = estimator.run(bound_ansatz, hamiltonian).result()
    energy = result.values[0]

    # Record history
    cost_history["iterations"] += 1
    cost_history["last_params"] = params
    cost_history["history"].append(energy)

    return energy


# VQE Configuration and Execution
class ApplicationQmgate:
    def __init__(self, qubit_connectivity, qubit_index_list, result_get='noisysimulation'):
        # Define the Hamiltonian
        self.hamiltonian = SparsePauliOp.from_list([
            ("YZ", 0.3980), ("ZI", -0.3980), ("ZZ", -0.0113), ("XX", 0.1810)
        ])

        # Define the ansatz
        self.ansatz = EfficientSU2(self.hamiltonian.num_qubits)
        self.num_params = self.ansatz.num_parameters

        # Set the backend
        self.result_get = result_get
        self.qubit_index_list = qubit_index_list
        self.qubit_connectivity = qubit_connectivity
        # self.runner = CirpulseRunner(range(self.hamiltonian.num_qubits), self.backend)

        # Transpile the ansatz for the backend if using Qiskit simulator
        if self.result_get == 'noisysimulation':
            self.ansatz_transpiled = transpile(self.ansatz, AerSimulator(), optimization_level=3)
        else:
            self.ansatz_transpiled = self.ansatz

        # History tracking
        global cost_history
        cost_history = {
            "last_params": None,
            "iterations": 0,
            "history": []
        }

    def qmVQE(self):
        # Initial parameters
        initial_params = 2 * np.pi * np.random.random(self.num_params)

        # Minimize the cost function
        result = minimize(
            fun=cost_func,
            x0=initial_params,
            args=(self.ansatz_transpiled, self.hamiltonian, self.result_get),
            method="COBYLA"
        )

        # Final energy
        final_energy = result.fun

        # Problem description
        problem_description = self.get_problem_description()

        # Check results
        assert np.allclose(cost_history["last_params"], result.x)
        assert cost_history["iterations"] == result.nfev

        # Optionally plot the cost function history
        self.plot_cost_history(show=False)

        print("Final Energy:", final_energy, "Problem Description:", problem_description)

        # Store final energy and problem description in a single variable
        result_summary = {
            "Final Energy": final_energy,
            "Problem Description": problem_description
        }

        # Return the result summary
        return result_summary

    def plot_cost_history(self, show=False):
        if show:
            plt.plot(range(cost_history["iterations"]), cost_history["history"])
            plt.xlabel("Iterations")
            plt.ylabel("Cost (Energy)")
            plt.title("VQE Cost Function History")
            plt.show()

    def get_problem_description(self):
        """Generate a simple parameterization description of the problem."""
        num_qubits = self.hamiltonian.num_qubits
        ansatz_type = type(self.ansatz).__name__
        hamiltonian_terms = len(self.hamiltonian)
        description = (
            f"Hamiltonian with {hamiltonian_terms} terms "
            f"on {num_qubits} qubits using {ansatz_type} ansatz."
        )
        return description

