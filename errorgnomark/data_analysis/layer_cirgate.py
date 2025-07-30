# Third-party imports
import numpy as np  # For numerical operations
import scipy
from scipy import optimize  # For optimization tasks
from scipy.optimize import curve_fit  # For fitting functions to data

# Standard library imports
import itertools  # For efficient looping and combinatorics
import traceback

class MetricQuality:

    """
    A class for benchmarking the quality of quantum gates and circuits.

    Supported Methods:
        1. **Randomized Benchmarking (RB)**: Measures gate error rates.
        2. **Cross-Entropy Benchmarking (XEB)**: Evaluates gate fidelity.
        3. **Channel Spectrum Benchmarking (CSB)**: Analyzes channel spectral properties to detect coherent errors.
        4. **Multi-Qubit Benchmarks**: Includes GHZ state preparation, 
           Mirror Randomized Benchmarking (MRB), and Standard Quantum Volume (SQV).

    Features:
        - Supports single, two, and multi-qubit gate quality analysis.
        - Compatible with flexible circuit generation tools.
    """

    def __init__(self, all_results, ini_modes=['x', 'z']):
        """
        Initializes the MetricQuality class.

        Parameters:
            all_results (dict): Dictionary containing 'hardware' and 'simulation' results.
                                Each should be a 3-layer list of execution results, where the outer list represents qubit results,
                                the middle list represents circuit lengths, and the inner list represents the ncr circuits.
        """
        self.hardware_results = all_results.get('hardware', [])
        self.simulation_results = all_results.get('simulation', [])
        self.ini_modes = ini_modes

    @staticmethod
    def fit_rb(lengths, survival_probs, nqubit = 1):
        def decay_func(l, A, p):
            return A *  p ** l

        initial_guess = [1.0, 0.01]

        try:
            popt, pcov = curve_fit(decay_func, lengths, survival_probs, p0=initial_guess)
            A, p = popt
            error_rate = (2**nqubit - 1) * (1-p)/(2**nqubit)
        except Exception as e:
            print(f"Fitting failed with error: {e}")
            error_rate = np.nan

        return error_rate


    @staticmethod
    def fit_xeb(lengths, survival_probs, nqubit = 1):
        def decay_func(l, A, p):
            return A *  p ** l

        # initial_guess = [1.0, 0.01]
        initial_guess = [0.5, 0.01]

        try:
            popt, pcov = curve_fit(decay_func, lengths, survival_probs, p0=initial_guess)
            A, p = popt
            error_rate_average = (1-p) * (1-(1/2**nqubit))
        except Exception as e:
            print(f"Fitting failed for {nqubit} with error: {e}")
            error_rate_average = np.nan

        return error_rate_average

    @staticmethod
    def heavy_output_set(mqubits, probs):
        """
        Compute heavy outputs of an m-qubit circuit with measurement outcome
        probabilities given by probs, which is a dictionary with the probabilities
        ordered as '000', '001', ... '111'.

        Args:
        - mqubits (int): Number of qubits.
        - probs (dict): Dictionary with bit strings as keys and probabilities (or counts) as values.

        Returns:
        - heavy_outputs (dict): Dictionary of bit strings and their probabilities that are above the median.
        - prob_heavy_output (float): Total probability of the heavy outputs.
        """
        # If the values in probs are counts, normalize them to probabilities
        total_count = sum(probs.values())
        if total_count > 0:
            probs = {key: value / total_count for key, value in probs.items()}
        
        # Sort the probabilities in descending order
        sorted_probs = dict(sorted(probs.items(), key=lambda item: item[1], reverse=True))

        # Get the median value of the sorted probabilities
        median_value = np.median(list(sorted_probs.values()))

        # Filter bit strings with probabilities above the median
        heavy_outputs = {key: value for key, value in sorted_probs.items() if value > median_value}

        # Calculate the total probability of the heavy outputs
        prob_heavy_output = sum(heavy_outputs.values())

        return heavy_outputs, prob_heavy_output


    @staticmethod
    def _compute_S(counts, num_qubits, target_bitstring='0'):
        """
        Computes the effective polarization S for a given circuit based on counts and target bitstring.

        Parameters:
            counts (dict): Measurement counts, e.g., {'00': 500, '01': 300, '10': 200, '11': 0}.
            num_qubits (int): Number of qubits in the circuit.
            target_bitstring (str): The target bitstring for Hamming distance calculation.

        Returns:
            float: Effective polarization S value within [0, 1].
        """
        # Initialize h_k list
        h_k = [0] * (num_qubits + 1)

        for bitstring, count in counts.items():
            # Ensure bitstring has correct length
            if len(bitstring) != num_qubits:
                continue
            # Calculate Hamming distance
            distance = sum(1 for a, b in zip(bitstring, target_bitstring) if a != b)
            if 0 <= distance <= num_qubits:
                h_k[distance] += count

        # Normalize h_k to probabilities
        total_counts = sum(h_k)
        if total_counts == 0:
            return 0.0  # Avoid division by zero

        h_k = [hk / total_counts for hk in h_k]

        # Compute the sum term: sum [ (-1/2)^k * h_k ]
        sum_term = 0.0
        for k in range(num_qubits + 1):
            sum_term += ((-1/2) ** k) * h_k[k]

        # Apply the theoretical formula:
        # S = (4^n)/(4^n -1) * sum_term - 1/(4^n -1)
        numerator = (4 ** num_qubits)
        denominator = (4 ** num_qubits - 1)
        S = (numerator / denominator) * sum_term - (1 / denominator)

        # Ensure S is within [0,1]
        S = max(0.0, min(S, 1.0))

        return S


    def rbq1(self, length_max, step_size, active_qubits=None, mode='respective'):
        """
        Calculate the error rates for 1-qubit random benchmarking.

        Parameters:
            length_max (int): Maximum length of the benchmarking circuits.
            step_size (int): Step size for generating lengths.

        Returns:
            list: List of error rates for each qubit.
        """
        qubit_error_rates = []
        qubit_purities = []

        # Ensure hardware and simulation results have the same number of qubits
        if len(self.hardware_results) != len(self.simulation_results):
            raise ValueError("Hardware and simulation results have different number of qubits.")

        if mode == 'respective':
            # Iterate over each qubit's hardware result
            for qubit_idx in range(len(self.hardware_results)):
                qubit_real = self.hardware_results[qubit_idx]
                survival_probabilities = []
                purity_probabilities = []  # 新增

                # Iterate over the different lengths for the current qubit
                for length_idx, length_real in enumerate(qubit_real):
                    survival_probabilities_ncr = []
                    purity_ncr = []  # 新增

                    # Iterate over the results for each circuit count (ncr)
                    for ncr_idx, circuit_counts in enumerate(length_real):
                        if isinstance(circuit_counts, list):
                            # If circuit counts is a list, iterate over the results
                            for result in circuit_counts:
                                count_0 = result.get("0", 0)
                                count_1 = result.get("1", 0)
                                total_shots = count_0 + count_1
                                survival_probability = count_0 / total_shots if total_shots > 0 else 0
                                purity = (count_0 / total_shots) ** 2 + (
                                            count_1 / total_shots) ** 2 if total_shots > 0 else np.nan
                                survival_probabilities_ncr.append(survival_probability)
                                purity_ncr.append(purity)
                        elif isinstance(circuit_counts, dict):
                            # If circuit counts is a dictionary, extract the counts directly
                            count_0 = circuit_counts.get("0", 0)
                            count_1 = circuit_counts.get("1", 0)
                            total_shots = count_0 + count_1
                            survival_probability = count_0 / total_shots if total_shots > 0 else 0
                            purity = (count_0 / total_shots) ** 2 + (
                                        count_1 / total_shots) ** 2 if total_shots > 0 else np.nan
                            survival_probabilities_ncr.append(survival_probability)
                            purity_ncr.append(purity)
                        else:
                            raise ValueError(f"Unexpected data format: {type(circuit_counts)}")

                    # Calculate the average survival probability for this length
                    avg_survival_prob = np.mean(survival_probabilities_ncr) if survival_probabilities_ncr else np.nan
                    avg_purity = np.mean(purity_ncr) if purity_ncr else np.nan  # 新增
                    survival_probabilities.append(avg_survival_prob)
                    purity_probabilities.append(avg_purity)  # 新增

                # Generate the length list and calculate the error rate
                length_list = range(2, length_max + 1, step_size)

                # If there are too few survival probabilities, set error rate to NaN
                if len(survival_probabilities) < 3:
                    error_rate = np.nan
                else:
                    # Fit the random benchmarking data to get the error rate
                    error_rate = self.fit_rb(length_list, survival_probabilities, nqubit=1)
                # Append the error rate for this qubit
                qubit_error_rates.append(float(error_rate) if not np.isnan(error_rate) else np.nan)
                qubit_purities.append(np.mean(purity_probabilities))
            return qubit_error_rates, qubit_purities

        elif mode == 'simultaneous':
            # simultaneous相比于respective，没有qubit序号，只有一个list，故不需要最外层for循环
            qubit_real = self.hardware_results[0]
            survival_probabilities = []
            # TODO 针对simultaneous情况，每一个qubit要单独讨论
            target_qubits = active_qubits  # 你提取出来后顺序就是这个
            # 针对每个qubit，都要统计它为'0'的概率
            num_qubits = len(target_qubits)
            all_survival_curves = [[] for _ in range(num_qubits)]  # 放到length_idx外面，只初始化一次
            purity_curves = [[] for _ in range(len(active_qubits))]

            # Iterate over the different lengths for the current qubit
            for length_idx, length_real in enumerate(qubit_real):
                # 每个qubit各自的survival_probabilities_ncr
                survival_probabilities_ncr = [[] for _ in range(num_qubits)]  # 4个空list
                purity_ncr = [[] for _ in range(num_qubits)]
                # Iterate over the results for each circuit count (ncr)
                for ncr_idx, circuit_counts in enumerate(length_real):
                    total_shots = sum(circuit_counts.values())  # 随便选择一个dict计算总shots
                    for idx in range(num_qubits):  # idx为0~3，对应四个目标qubit
                        count_zero = 0
                        count_one = 0
                        for bitstring, count in circuit_counts.items():
                            if bitstring[idx] == '0':  # 如果该位是0
                                count_zero += count
                            elif bitstring[idx] == '1':
                                count_one += count
                        p0 = count_zero / total_shots if total_shots > 0 else 0
                        p1 = count_one / total_shots if total_shots > 0 else 0
                        survival_probabilities_ncr[idx].append(p0)
                        purity_ncr[idx].append(p0 ** 2 + p1 ** 2 if total_shots > 0 else np.nan)

                # ---- 统计平均值 ----
                avg_survival_prob_ncr = [
                    np.mean(survival_probabilities_ncr[idx]) if survival_probabilities_ncr[idx] else np.nan
                    for idx in range(num_qubits)
                ]
                avg_purity_ncr = [
                    np.mean(purity_ncr[idx]) if purity_ncr[idx] else np.nan
                    for idx in range(num_qubits)
                ]
                # 这里追加到每个qubit的“曲线”里
                for idx in range(num_qubits):
                    all_survival_curves[idx].append(avg_survival_prob_ncr[idx])
                    purity_curves[idx].append(avg_purity_ncr[idx])
            # 这里与 respective 完全对齐，分别拟合error rate和purity
            length_list = range(2, length_max + 1, step_size)
            qubit_error_rates = []
            qubit_purities = []
            for idx in range(num_qubits):
                curve = all_survival_curves[idx]
                # error rate用fit_rb拟合
                if len(curve) < 3:
                    error_rate = np.nan
                else:
                    error_rate = self.fit_rb(length_list, curve, nqubit=1)
                qubit_error_rates.append(float(error_rate) if not np.isnan(error_rate) else np.nan)
                # purity直接均值
                purity = np.mean(purity_curves[idx]) if purity_curves[idx] else np.nan
                qubit_purities.append(purity)
            return qubit_error_rates, qubit_purities

    def rbq2(self, length_max, step_size, qubit_connectivity=None, mode=None):
        """
        Calculates the average error rate for 2-qubit random benchmarking.

        Parameters:
            length_max (int): Maximum circuit length.
            step_size (int): Step size for generating circuits of different lengths.

        Returns:
            list: A list of average error rates for each qubit pair.
        """
        qubit_pair_error_rates = []
        if mode == 'respective':
            # Ensure that hardware and simulation results have the same number of qubit pairs
            if len(self.hardware_results) != len(self.simulation_results):
                raise ValueError("Hardware and simulation results have different number of qubit pairs.")

            # Iterate through each qubit pair
            for pair_idx in range(len(self.hardware_results)):
                qubit_pair_real = self.hardware_results[pair_idx]
                # Assuming we are not using simulation results for this function
                survival_probabilities = []

                # Iterate through each length for this qubit pair
                for length_idx, length_real in enumerate(qubit_pair_real):
                    survival_probabilities_ncr = []

                    # Iterate over the number of circuits (ncr) for this particular length
                    for ncr_idx, circuit_counts in enumerate(length_real):
                        # Handle both list and dict formats for the results
                        if isinstance(circuit_counts, list):
                            # Iterate over each result in the list
                            for result in circuit_counts:
                                count_00 = result.get("00", 0)
                                # count_11 = result.get("11", 0)
                                # total_shots = count_00 + count_11   # TODO 00和11不是完全的shots
                                total_shots = sum(result.values())  # sum over all '00','01','10','11'
                                survival_probability = count_00 / total_shots if total_shots > 0 else 0
                                survival_probabilities_ncr.append(survival_probability)
                        elif isinstance(circuit_counts, dict):
                            # Directly use the counts from the dictionary
                            count_00 = circuit_counts.get("00", 0)
                            # count_11 = circuit_counts.get("11", 0)
                            # total_shots = count_00 + count_11
                            total_shots = sum(circuit_counts.values())  # sum over all '00','01','10','11'
                            survival_probability = count_00 / total_shots if total_shots > 0 else 0
                            survival_probabilities_ncr.append(survival_probability)
                        else:
                            raise ValueError(f"Unexpected data format: {type(circuit_counts)}")

                    # Calculate the average survival probability for this length
                    avg_survival_prob = np.mean(survival_probabilities_ncr) if survival_probabilities_ncr else np.nan
                    survival_probabilities.append(avg_survival_prob)

                # Generate a list of circuit lengths
                length_list = range(2, length_max + 1, step_size)

                # If there are fewer than 3 survival probabilities, return NaN for error rate
                if len(survival_probabilities) < 3:
                    error_rate = np.nan
                else:
                    # Fit the survival probabilities to extract the error rate
                    error_rate = self.fit_rb(length_list, survival_probabilities, nqubit=2)

                # Append the error rate (or NaN if invalid) for this qubit pair
                qubit_pair_error_rates.append(float(error_rate) if not np.isnan(error_rate) else np.nan)

            return qubit_pair_error_rates

        elif mode == 'simultaneous':
            # Ensure that hardware and simulation results have the same number of qubit pairs
            if len(self.hardware_results) != len(self.simulation_results):
                raise ValueError("Hardware and simulation results have different number of qubit pairs.")

            all_qubits = sorted(set().union(*qubit_connectivity))  # e.g. [10, 21, 22, 23, 34]
            qubit_index_map = {q: idx for idx, q in enumerate(all_qubits)}  # e.g. {10:0, 21:1, 22:2, 23:3, 34:4}

            for pair_idx, qubit_pair in enumerate(qubit_connectivity):
                survival_probabilities = []
                # Iterate through each qubit pair
                for length_idx, length_real in enumerate(self.hardware_results[0]):
                    survival_probabilities_ncr = []
                    # 遍历不同depth
                    for ncr_idx, circuit_counts in enumerate(length_real):
                        # 统计两比特的bitstring
                        pair_idx_0 = qubit_index_map[qubit_pair[0]]
                        pair_idx_1 = qubit_index_map[qubit_pair[1]]
                        counts_2bit = {'00': 0, '01': 0, '10': 0, '11': 0}
                        total_shots = 0
                        for bitstring, count in circuit_counts.items():
                            b0 = bitstring[-(pair_idx_0 + 1)]  # 注意Qiskit输出低位在右，取倒数第几个
                            b1 = bitstring[-(pair_idx_1 + 1)]
                            key = b0 + b1
                            counts_2bit[key] += count
                            total_shots += count
                        survival_probability = counts_2bit['00'] / total_shots if total_shots > 0 else 0
                        survival_probabilities_ncr.append(survival_probability)

                    avg_survival_prob = np.mean(
                        survival_probabilities_ncr) if survival_probabilities_ncr else np.nan
                    survival_probabilities.append(avg_survival_prob)
                length_list = range(2, length_max + 1, step_size)

                # If there are fewer than 3 survival probabilities, return NaN for error rate
                if len(survival_probabilities) < 3:
                    error_rate = np.nan
                else:
                    # Fit the survival probabilities to extract the error rate
                    error_rate = self.fit_rb(length_list, survival_probabilities, nqubit=2)

                # Append the error rate (or NaN if invalid) for this qubit pair
                qubit_pair_error_rates.append(float(error_rate) if not np.isnan(error_rate) else np.nan)
            return qubit_pair_error_rates


    def xebq1(self, length_max, step_size, active_qubits=None, mode='respective'):
        """
        Calculates the average error rate for 1-qubit cross entropy benchmarking.

        Parameters:
            length_max (int): Maximum length of the benchmarking circuits.
            step_size (int): Step size for the length of the circuits.

        Returns:
            list: A list of average error rates for each qubit.
        """
        qubit_error_rates = []
        qubit_purities = []

        # Ensure that hardware and simulation results have the same number of qubits
        if len(self.hardware_results) != len(self.simulation_results):
            raise ValueError("Hardware and simulation results have different number of qubits.")

        if mode == 'respective':
            # Iterate through each qubit in the results
            for qubit_idx in range(len(self.hardware_results)):
                qubit_real = self.hardware_results[qubit_idx]
                qubit_ideal = self.simulation_results[qubit_idx]

                # Check that the number of lengths matches for real and ideal results
                if len(qubit_real) != len(qubit_ideal):
                    raise ValueError(f"Qubit {qubit_idx}: Hardware and simulation results have different number of lengths.")

                fidelities = []
                purities = []

                # Iterate through each circuit length
                for length_idx in range(len(qubit_real)):
                    length_real = qubit_real[length_idx]
                    length_ideal = qubit_ideal[length_idx]

                    # Check that the number of ncr matches between real and ideal for this length
                    if len(length_real) != len(length_ideal):
                        raise ValueError(f"Qubit {qubit_idx}, Length {length_idx}: Hardware and simulation have different ncr counts.")

                    fidelity_xeb_list = []
                    purity_list = []

                    # Iterate through each ncr circuit for this length
                    for ncr_idx in range(len(length_real)):
                        counts_real = length_real[ncr_idx]
                        counts_ideal = length_ideal[ncr_idx]

                        # Calculate total shots for normalization
                        total_shots_real = sum(counts_real.values())
                        total_shots_ideal = sum(counts_ideal.values())

                        # Normalize counts to probabilities based on total shots
                        p_real = {k: v / total_shots_real for k, v in counts_real.items()}
                        p_ideal = {k: v / total_shots_ideal for k, v in counts_ideal.items()}

                        # --- fidelity ---
                        # Calculate sum(p_real(x) * p_ideal(x)) for all possible outcomes
                        sum_p_real_p_ideal = sum(p_real.get(x, 0.0) * p_ideal.get(x, 0.0) for x in p_ideal)
                        # Calculate fidelity for this ncr, clipped to the range [0, 1]
                        fidelity_xeb = np.clip(2 * sum_p_real_p_ideal - 1, 0, 1)
                        fidelity_xeb_list.append(fidelity_xeb)

                        # --- purity ---
                        purity = sum([v ** 2 for v in p_real.values()])
                        purity_list.append(purity)

                    # Average fidelity for this length
                    avg_fidelity_length = np.mean(fidelity_xeb_list) if fidelity_xeb_list else np.nan
                    fidelities.append(avg_fidelity_length)

                    avg_purity_length = np.mean(purity_list) if purity_list else np.nan
                    purities.append(avg_purity_length)

                length_list = range(1, length_max + 1, step_size)

                # Fit the fidelities to extract the error rate, ensuring at least 3 fidelities
                if len(fidelities) < 3:
                    error_rate = np.nan
                else:
                    error_rate = self.fit_xeb(length_list, fidelities, nqubit=1)

                # Ensure the error rate is within the range [0, 1]
                qubit_error_rates.append(np.clip(float(error_rate) if not np.isnan(error_rate) else np.nan, 0, 1))
                qubit_purities.append(np.mean(purities))

            return qubit_error_rates, qubit_purities
        elif mode == 'simultaneous':
            qubit_real = self.hardware_results[0]  # shape = [length, ncr]
            qubit_ideal = self.simulation_results[0]
            num_qubits = len(active_qubits)  # 目标qubit个数
            all_fidelity_curves = [[] for _ in range(num_qubits)]  # 每个qubit一条曲线
            all_purity_curves = [[] for _ in range(num_qubits)]

            # 遍历不同length
            for length_idx, (length_real, length_ideal) in enumerate(zip(qubit_real, qubit_ideal)):
                # ncr内聚合
                # 每个qubit的ncr下fidelity
                fidelities_ncr = [[] for _ in range(num_qubits)]
                purity_ncr = [[] for _ in range(num_qubits)]
                # Iterate through each ncr circuit for this length
                for ncr_idx, (counts_real, counts_ideal) in enumerate(zip(length_real, length_ideal)):
                    # Calculate total shots for normalization
                    total_shots_real = sum(counts_real.values())
                    total_shots_ideal = sum(counts_ideal.values())

                    # 针对每个qubit，分别计算自己的XEB fidelity
                    for idx in range(num_qubits):
                        # 统计该qubit在所有bitstring下测得'0'/'1'的次数
                        count_real_0 = sum(v for k, v in counts_real.items() if k[idx] == '0')
                        count_real_1 = sum(v for k, v in counts_real.items() if k[idx] == '1')
                        count_ideal_0 = sum(v for k, v in counts_ideal.items() if k[idx] == '0')
                        count_ideal_1 = sum(v for k, v in counts_ideal.items() if k[idx] == '1')

                        p_real_0 = count_real_0 / total_shots_real if total_shots_real > 0 else 0
                        p_real_1 = count_real_1 / total_shots_real if total_shots_real > 0 else 0
                        p_ideal_0 = count_ideal_0 / total_shots_ideal if total_shots_ideal > 0 else 0
                        p_ideal_1 = count_ideal_1 / total_shots_ideal if total_shots_ideal > 0 else 0

                        # 完整单qubit XEB fidelity
                        fidelity_xeb = 2 * (p_real_0 * p_ideal_0 + p_real_1 * p_ideal_1) - 1
                        fidelity_xeb = np.clip(fidelity_xeb, 0, 1)
                        fidelities_ncr[idx].append(fidelity_xeb)

                        purity = p_real_0 ** 2 + p_real_1 ** 2 if total_shots_real > 0 else np.nan
                        purity_ncr[idx].append(purity)

                # ncr均值，得到每个length下每个qubit的平均fidelity
                avg_fidelities = [
                    np.mean(fidelities_ncr[idx]) if fidelities_ncr[idx] else np.nan
                    for idx in range(num_qubits)
                ]
                avg_purities = [
                    np.mean(purity_ncr[idx]) if purity_ncr[idx] else np.nan
                    for idx in range(num_qubits)
                ]
                for idx in range(num_qubits):
                    all_fidelity_curves[idx].append(avg_fidelities[idx])
                    all_purity_curves[idx].append(avg_purities[idx])

            length_list = list(range(1, length_max + 1, step_size))
            error_rates = []
            qubit_purities = []
            for idx in range(num_qubits):
                curve = all_fidelity_curves[idx]
                purity_curve = all_purity_curves[idx]
                # 判断数据点足够
                if len(curve) < 3:
                    error_rate = np.nan
                else:
                    error_rate = self.fit_xeb(length_list, curve, nqubit=1)
                error_rates.append(float(error_rate) if not np.isnan(error_rate) else None)
                qubit_purities.append(np.mean(purity_curve))

            return error_rates, qubit_purities

            # TODO 以下两行适合全局XEB分布
            # Calculate sum(p_real(x) * p_ideal(x)) for all possible outcomes
            # sum_p_real_p_ideal = sum(p_real.get(x, 0.0) * p_ideal.get(x, 0.0) for x in p_ideal)
            # Calculate fidelity for this ncr, clipped to the range [0, 1]
            # fidelity_xeb = np.clip(2 * sum_p_real_p_ideal - 1, 0, 1)
        else:
            pass

    def xebq2(self, length_max, step_size, qubit_connectivity=None, mode=None):
        """
        Calculates the average error rate for 2-qubit cross entropy benchmarking.

        Parameters:
            length_max (int): The maximum length of the benchmarking circuits.
            step_size (int): The step size for increasing the length of the benchmarking circuits.

        Returns:
            list: A list of average error rates for each qubit pair.
        """
        qubit_pair_error_rates = []  # List to store error rates for each qubit pair

        # Ensure that hardware and simulation results have the same number of qubit pairs
        if len(self.hardware_results) != len(self.simulation_results):
            raise ValueError("Hardware and simulation results have different number of qubit pairs.")

        if mode == 'respective':

            # Iterate through each qubit pair in the hardware results
            for pair_idx in range(len(self.hardware_results)):
                qubit_pair_real = self.hardware_results[pair_idx]  # Real (hardware) results for this qubit pair
                qubit_pair_ideal = self.simulation_results[pair_idx]  # Ideal (simulation) results for this qubit pair

                # Ensure that for each qubit pair, the number of lengths matches between real and ideal results
                if len(qubit_pair_real) != len(qubit_pair_ideal):
                    raise ValueError(f"Qubit Pair {pair_idx}: Hardware and simulation results have different number of lengths.")

                fidelities = []  # List to store fidelities for each length

                # Iterate through each length in the results
                for length_idx in range(len(qubit_pair_real)):
                    length_real = qubit_pair_real[length_idx]  # Real results for this length
                    length_ideal = qubit_pair_ideal[length_idx]  # Ideal results for this length

                    # Ensure that the number of ncr (number of circuits) matches for both real and ideal results
                    if len(length_real) != len(length_ideal):
                        raise ValueError(f"Qubit Pair {pair_idx}, Length {length_idx}: Hardware and simulation have different ncr counts.")

                    fidelity_xeb_list = []  # List to store fidelity values for each ncr

                    # Iterate through each ncr (circuit) for this length
                    for ncr_idx in range(len(length_real)):
                        counts_real = length_real[ncr_idx]  # Real counts for this ncr
                        counts_ideal = length_ideal[ncr_idx]  # Ideal counts for this ncr

                        # Calculate total shots for normalization
                        total_shots_real = sum(counts_real.values())
                        total_shots_ideal = sum(counts_ideal.values())

                        # Skip iteration if there are no shots in real or ideal counts
                        if total_shots_real == 0 or total_shots_ideal == 0:
                            fidelity_xeb_list.append(np.nan)  # Skip this iteration if shots are zero
                            continue

                        # Normalize counts to probabilities based on total shots
                        p_real = {k: v / total_shots_real for k, v in counts_real.items()}
                        p_ideal = {k: v / total_shots_ideal for k, v in counts_ideal.items()}

                        # Calculate sum_x p_real(x) * p_ideal(x)
                        sum_p_real_p_ideal = sum(p_real.get(x, 0.0) * p_ideal.get(x, 0.0) for x in p_ideal)

                        # Calculate fidelity_xeb and clip it to [0, 1] range
                        fidelity_xeb = np.clip(2 * sum_p_real_p_ideal - 1, 0, 1)

                        # Append the fidelity for this ncr to the list
                        fidelity_xeb_list.append(fidelity_xeb)

                    # Calculate average fidelity for this length and add it to the fidelities list
                    avg_fidelity_length = np.mean(fidelity_xeb_list) if fidelity_xeb_list else np.nan
                    fidelities.append(avg_fidelity_length)

                length_list = range(1, length_max + 1, step_size)  # Define the length list for fitting

                # Skip fitting if there are too few fidelities to analyze
                if len(fidelities) < 3:
                    error_rate = np.nan
                else:
                    # Fit the fidelities to extract the average error rate (for 2-qubit system)
                    error_rate = self.fit_xeb(length_list, fidelities, nqubit=2)

                # Ensure the error rate is within the [0, 1] range and add it to the list
                qubit_pair_error_rates.append(np.clip(float(error_rate) if not np.isnan(error_rate) else np.nan, 0, 1))

            return qubit_pair_error_rates  # Return the list of error rates for each qubit pair

        elif mode == 'simultaneous':

            all_qubits = sorted(set().union(*qubit_connectivity))  # 比如[10,21,22,23,34]
            qubit_index_map = {q: idx for idx, q in enumerate(all_qubits)}  # {10:0, 21:1, ...}
            qubit_pair_error_rates = []

            for pair_idx, qubit_pair in enumerate(qubit_connectivity):
                fidelities = []

                for length_idx in range(len(self.hardware_results[0])):
                    length_real = self.hardware_results[0][length_idx]
                    length_ideal = self.simulation_results[0][length_idx]
                    fidelity_xeb_list = []

                    for ncr_idx in range(len(length_real)):
                        counts_real = length_real[ncr_idx]
                        counts_ideal = length_ideal[ncr_idx]

                        # ------- 统计real -------
                        pair_idx_0 = qubit_index_map[qubit_pair[0]]
                        pair_idx_1 = qubit_index_map[qubit_pair[1]]
                        counts_2bit_real = {'00': 0, '01': 0, '10': 0, '11': 0}
                        total_shots_real = 0
                        for bitstring, count in counts_real.items():
                            b0 = bitstring[-(pair_idx_0 + 1)]  # Qiskit 右边是最低位
                            b1 = bitstring[-(pair_idx_1 + 1)]
                            key = b0 + b1
                            counts_2bit_real[key] += count
                            total_shots_real += count

                        # ------- 统计ideal -------
                        counts_2bit_ideal = {'00': 0, '01': 0, '10': 0, '11': 0}
                        total_shots_ideal = 0
                        for bitstring, count in counts_ideal.items():
                            b0 = bitstring[-(pair_idx_0 + 1)]
                            b1 = bitstring[-(pair_idx_1 + 1)]
                            key = b0 + b1
                            counts_2bit_ideal[key] += count
                            total_shots_ideal += count

                        if total_shots_real == 0 or total_shots_ideal == 0:
                            fidelity_xeb_list.append(np.nan)
                            continue

                        # 概率分布
                        p_real = {k: v / total_shots_real for k, v in counts_2bit_real.items()}
                        p_ideal = {k: v / total_shots_ideal for k, v in counts_2bit_ideal.items()}

                        sum_p_real_p_ideal = sum(p_real.get(x, 0.0) * p_ideal.get(x, 0.0) for x in p_ideal)
                        # Calculate fidelity_xeb and clip it to [0, 1] range
                        fidelity_xeb = np.clip(2 * sum_p_real_p_ideal - 1, 0, 1)

                        fidelity_xeb_list.append(fidelity_xeb)

                    avg_fidelity_length = np.mean(fidelity_xeb_list) if fidelity_xeb_list else np.nan
                    fidelities.append(avg_fidelity_length)

                length_list = range(1, length_max + 1, step_size)

                if len(fidelities) < 3:
                    error_rate = np.nan
                else:
                    error_rate = self.fit_xeb(length_list, fidelities, nqubit=2)

                qubit_pair_error_rates.append(np.clip(float(error_rate) if not np.isnan(error_rate) else np.nan, 0, 1))

            return qubit_pair_error_rates

    @staticmethod
    def matrix_pencil(data, L, N_poles, cutoff=1e-10):
        """Decompose time series data using the Matrix Pencil method."""
        N = len(data)
        if L >= N:
            raise ValueError("Parameter L must satisfy L < len(data).")
        
        # Normalize data
        # data = data / np.max(np.abs(data))
        
        # Construct Hankel matrix
        Y = np.array([data[i:L + i] for i in range(N - L)])
        U, S, Vh = scipy.linalg.svd(Y)
        
        # Filter singular values
        valid_singular_values = S[S > cutoff * S[0]]
        if len(valid_singular_values) < N_poles:
            N_poles = len(valid_singular_values)
        U = U[:, :N_poles]
        S = np.diag(S[:N_poles])
        Vh = Vh[:N_poles, :]
        
        # Compute shifted matrices
        Vh1 = np.matrix(Vh[:, :-1])
        Vh2 = np.matrix(Vh[:, 1:])
        Y_shifted = scipy.linalg.pinv(Vh1.H) @ Vh2.H
        poles, _ = scipy.linalg.eig(Y_shifted)
        poles = np.conjugate(poles)
        # Normalize poles
        poles = np.array([p / abs(p) if abs(p) > 1 else p for p in poles])
        
        # Compute amplitudes
        Z = np.array([[p**k for p in poles] for k in range(N)])
        amplitudes, _, _, _ = scipy.linalg.lstsq(Z, data)
        amp_max = np.max(np.abs(amplitudes))
        
        # Discard the poles with very small amplitudes
        poles_p = []
        for i in range(len(poles)):
            if np.abs(amplitudes[i]) / amp_max > 0.1:
                poles_p.append(poles[i])
    
        return poles_p, amplitudes, S

    @staticmethod
    def compute_csb(bitstring_counts, target_phase=np.pi / 2, rep=1, cutoff=1e-10, ini_modes=[]):
        """
        Compute CSB errors (process infidelity, stochastic infidelity, and angle error) from bitstring results.

        Parameters:
            bitstring_counts (list of dict): Measured bitstring counts for each circuit.
            target_phase (float): Target phase of the gate under test.
            rep (int): Number of repetitions of the target gate.
            cutoff (float): Singular value cutoff for matrix pencil decomposition.

        Returns:
            dict: Dictionary containing process infidelity, stochastic infidelity, and angle error.
        """
        # Combine bitstring results into probabilities
        probabilities = [counts.get('0', 0) / sum(counts.values()) for counts in bitstring_counts]

        # Split data into two modes and combine
        data_split  = np.split(np.array(probabilities), len(ini_modes))
        data_combined = sum(data_split)

        # Perform Matrix Pencil analysis
        len_data = len(data_combined)
        pencil_param_L = max(int(len_data * 0.4), 1)
        poles, amplitudes, singular_values = MetricQuality.matrix_pencil(
            data_combined, L=pencil_param_L, N_poles=4, cutoff=cutoff
        )

        # Process poles to calculate errors
        if len(poles) < 4:
            poles = np.append(poles, 1)
        amp = np.abs(poles)
        target_phase_p = (target_phase * rep) % (2 * np.pi)
        if target_phase_p - np.pi > 1e-4:
            target_phase_p -= 2 * np.pi
        phase = np.angle(poles)
        phase_dif = np.abs(phase - target_phase_p)
        angle_index = np.argmin(phase_dif)
        angle_error = (phase - target_phase_p)[angle_index]
        phase_dif2 = np.abs(np.abs(phase) - np.abs(target_phase_p))
        index_com = np.argwhere(phase_dif2 > np.abs(angle_error))

        res = []
        angle_error /= rep
        if np.abs(np.abs(target_phase) - np.pi) < 1e-4:
            angle_error = np.abs(angle_error)
        res.append(angle_error)
        res.append((amp[angle_index]) ** (1 / rep))
        if len(index_com) >= 2:
            res.append((amp[index_com[0][0]]) ** (1 / rep))
            res.append((amp[index_com[1][0]]) ** (1 / rep))
        elif len(index_com) == 1:
            res.append((amp[index_com[0][0]]) ** (1 / rep))
            res.append(0)  # Fill with zero if not enough poles
        else:
            res.append(0)
            res.append(0)
        r = 1 - (0.5 * res[1] * np.cos(res[0]) + 0.25 * (res[2] + res[3]))
        u = 1 - np.sqrt((2 * res[1]**2 + res[2]**2 + res[3]**2) / 4)

        return {
            "process_infidelity": r,
            "stochastic_infidelity": u,
            "angle_error": angle_error
        }

    def csbq1(self, target_phase=np.pi / 2, rep=1, cutoff=1e-10, csb_avg=None, active_qubits=None, mode='respective'):
        """
        Compute CSB fidelity based on hardware execution results.

        Parameters:
            target_phase (float): Target phase of the gate under test.
            rep (int): Number of repetitions of the target gate.
            cutoff (float): Singular value cutoff for matrix pencil decomposition.
            csb_avg (bool or None): Whether to compute and return average errors for all qubits.
                                    If None or False, average is not computed. If True, average is computed.

        Returns:
            dict: Dictionary containing process infidelity, stochastic infidelity, and angle error for each qubit,
                and optionally the average errors for all qubits if csb_avg=True.
        """
        process_infidelities = []
        stochastic_infidelities = []
        angle_errors = []

        # Helper function to ensure non-negative values
        def non_negative(value):
            return max(0, value) if value is not None else None

        def average(lst):
            valid = [x for x in lst if x is not None]
            return np.mean(valid) if valid else None

        if mode == 'respective':
            # Iterate through each qubit's circuits
            for qubit_idx, qubit_circuits in enumerate(self.hardware_results):
                # Attempt to compute CSB for the current qubit's circuits
                try:
                    csb_result = self.compute_csb(qubit_circuits, target_phase=target_phase, rep=rep,
                                                  cutoff=cutoff, ini_modes=self.ini_modes)
                    process_infidelities.append(csb_result["process_infidelity"])
                    stochastic_infidelities.append(csb_result["stochastic_infidelity"])
                    angle_errors.append(csb_result["angle_error"])
                except Exception as e:
                    # Handle errors gracefully: append None if an error occurs
                    print(f"Error processing qubit {qubit_idx}: {e}")
                    process_infidelities.append(None)
                    stochastic_infidelities.append(None)
                    angle_errors.append(None)

            # Apply non-negative function to each list of results
            process_infidelities = [non_negative(val) for val in process_infidelities]
            stochastic_infidelities = [non_negative(val) for val in stochastic_infidelities]
            angle_errors = [non_negative(val) for val in angle_errors]

            # Prepare the result dictionary with individual qubit error rates
            result = {
                "process_infidelities": process_infidelities,
                "stochastic_infidelities": stochastic_infidelities,
                "angle_errors": angle_errors
            }

            # If csb_avg is True, compute the average error rates across all qubits
            if csb_avg:

                # Compute the average error rates, ensuring non-negative values
                process_infidelity_avg = average(process_infidelities)
                stochastic_infidelity_avg = average(stochastic_infidelities)
                angle_error_avg = average(angle_errors)

                # Add average values to the result dictionary
                result["process_infidelity_avg"] = non_negative(process_infidelity_avg)
                result["stochastic_infidelity_avg"] = non_negative(stochastic_infidelity_avg)
                result["angle_error_avg"] = non_negative(angle_error_avg)

            return result
        elif mode == 'simultaneous':
            simultaneous_circuits = self.hardware_results[0]
            num_qubits = len(active_qubits)  # 你关心的 qubit 数量
            qubit_circuits = [[] for _ in range(num_qubits)]  # 每个qubit一组

            # length_circuits: ncr个dict，每个dict是bitstring: count
            for ncr_idx, circuit_counts in enumerate(simultaneous_circuits):
                # 统计每个qubit的0/1计数
                for idx in range(num_qubits):  # 对每个目标qubit
                    count_zero = 0
                    count_one = 0
                    for bitstring, count in circuit_counts.items():
                        bitstring_r = bitstring[::-1]  # Qiskit输出高位在左，反转后idx=0是最低位
                        if bitstring_r[idx] == '0':
                            count_zero += count
                        elif bitstring_r[idx] == '1':
                            count_one += count
                    # 以dict格式加入对应qubit的序列
                    qubit_circuits[idx].append({'0': count_zero, '1': count_one})

            # 每个qubit的序列都整理好，分别计算csb
            process_infidelities = [None] * num_qubits
            stochastic_infidelities = [None] * num_qubits
            angle_errors = [None] * num_qubits

            for qubit_idx in range(num_qubits):
                try:
                    csb_result = self.compute_csb(
                        qubit_circuits[qubit_idx],
                        target_phase=target_phase,
                        rep=rep,
                        cutoff=cutoff,
                        ini_modes=self.ini_modes
                    )

                    process_infidelities[qubit_idx] = non_negative(csb_result["process_infidelity"])
                    stochastic_infidelities[qubit_idx] = non_negative(csb_result["stochastic_infidelity"])
                    angle_errors[qubit_idx] = non_negative(csb_result["angle_error"])
                except Exception as e:
                    print(f"Error processing qubit {active_qubits[qubit_idx]}: {e}")

            result = {
                "process_infidelities": process_infidelities,
                "stochastic_infidelities": stochastic_infidelities,
                "angle_errors": angle_errors
            }
            return result
        else:
            pass


    def compute_csb_q2cz(self, bitstring_counts, target_phase=np.pi, rep=1, cutoff=1e-10):
        """
        Compute CSB error metrics for the 2-qubit CZ gate, including process infidelity, 
        stochastic infidelity, theta error, and phi error.

        Parameters:
            bitstring_counts (list of dict): List of bitstring counts for each circuit.
            target_phase (float): Target phase for the CZ gate, default is pi.
            rep (int): Number of repetitions of the CZ gate, default is 1.
            cutoff (float): Singular value cutoff for matrix pencil method, default is 1e-10.

        Returns:
            dict: A dictionary containing process infidelity, stochastic infidelity, 
                theta error, and phi error.
        """
        # Step 1: Convert bitstring counts to probabilities, focusing on '11' counts for CZ gate
        probabilities = [counts.get('11', 0) / sum(counts.values()) for counts in bitstring_counts]
        probabilities = np.array(probabilities)

        # Step 2: Apply matrix pencil method for analysis
        L = max(int(len(probabilities) * 0.4), 1)  # Use 40% of data length for L
        N_poles = 4  # Number of poles (adjust as needed)

        poles, amplitudes, singular_values = MetricQuality.matrix_pencil(
            probabilities, L=L, N_poles=N_poles, cutoff=cutoff
        )

        # Step 3: Process poles and calculate errors
        if len(poles) < N_poles:
            poles = np.append(poles, [1] * (N_poles - len(poles)))  # Pad with 1s if insufficient poles

        amps = np.abs(poles)
        phases = np.angle(poles)
        
        # Accumulate phase without modulo to preserve phase information
        target_phase_p = target_phase * rep
        target_phase_p = (target_phase_p + np.pi) % (2 * np.pi) - np.pi  # Adjust to [-pi, pi]

        # Compute phase differences and find the closest phase
        phase_difs = np.abs(phases - target_phase_p)
        angle_index = np.argmin(phase_difs)
        phase_error = phase_difs[angle_index] / rep  # Normalize by repetitions

        # Compute amplitude error (assuming ideal amplitude is 1)
        amplitude_error = 1 - amps[angle_index] ** (1 / rep)

        # Compute fidelity metrics
        f_mean = 1 - amplitude_error
        f_mean = min(f_mean, 1.0)  # Ensure fidelity does not exceed 1

        # Compute stochastic fidelity
        u_mean = 1 - amplitude_error  # Simplified assumption
        u_mean = min(u_mean, 1.0)  # Ensure fidelity does not exceed 1

        # Compute angle errors
        theta_error = phase_error
        phi_error = 0  # If there's no additional phase information, set phi_error to 0

        # Convert np.float64 to float before returning
        return {
            "process_infidelity": float(max(1 - f_mean, 0.0)),  # Ensure non-negative infidelity
            "stochastic_infidelity": float(max(1 - np.sqrt(u_mean), 0.0)),  # Ensure non-negative infidelity
            "theta_error": float(theta_error),
            "phi_error": float(phi_error)
        }

    def csbq2cz(self, phi=np.pi, ndeg=3, rep=1, cutoff=1e-10, qubit_connectivity=None, mode='respective'):
        """
        Computes the CSB (Cross-Entropy Benchmarking) errors for multiple 2-qubit CZ gates.

        Parameters:
            phi (float): The target phase for the CZ gate, default is pi.
            ndeg (int): The degree for the matrix pencil method, default is 3.
            rep (int): The number of repetitions for each circuit, default is 1.
            cutoff (float): Singular value cutoff for matrix operations, default is 1e-10.

        Returns:
            list: A list of dictionaries, each containing the error metrics for a qubit pair. 
                Each dictionary includes:
                - 'process_infidelity': Process infidelity of the gate.
                - 'stochastic_infidelity': Stochastic infidelity of the gate.
                - 'theta_error': Error in the theta parameter.
                - 'phi_error': Error in the phi parameter.
        """
        csb_results_list = []  # Initialize list to store CSB results for each qubit pair

        if mode == 'respective':
            # Iterate over the hardware results for each qubit pair
            for qubit_pair_index, qubit_circuits in enumerate(self.hardware_results):
                # Compute CSB metrics for the current qubit pair's circuits
                csb_result = self.compute_csb_q2cz(
                    qubit_circuits, target_phase=phi, rep=rep, cutoff=cutoff
                )

                # Append the results in a dictionary format
                csb_results_list.append({
                    "process_infidelity": float(csb_result["process_infidelity"]),
                    "stochastic_infidelity": float(csb_result["stochastic_infidelity"]),
                    "theta_error": float(csb_result["theta_error"]),
                    "phi_error": float(csb_result["phi_error"])
                })

            return csb_results_list

        elif mode == 'simultaneous':

            all_qubits = sorted(set(q for pair in qubit_connectivity for q in pair))
            qubit_index_map = {q: idx for idx, q in enumerate(all_qubits)}  # 全局比特序号到bitstring序号

            results_per_pair = []  # 外层list，每个qubit_pair的统计

            # 外层循环，每个qubit pair单独统计自己的比特对概率
            for pair_idx, qubit_pair in enumerate(qubit_connectivity):
                idx0 = qubit_index_map[qubit_pair[0]]
                idx1 = qubit_index_map[qubit_pair[1]]
                pair_stats = []  # 每个depth的list

                for depth_result in self.hardware_results:  # 这里hardware_results[depth]是ncr个dict的list
                    ncr_stats = []  # 统计所有ncr
                    for ncr_result in depth_result:  # ncr_result是dict
                        counts_2bit = {'00': 0, '01': 0, '10': 0, '11': 0}
                        for bitstring, count in ncr_result.items():
                            # 注意Qiskit bitstring的最低位在右边
                            b0 = bitstring[-(idx0 + 1)]
                            b1 = bitstring[-(idx1 + 1)]
                            key = b0 + b1
                            counts_2bit[key] += count
                        ncr_stats.append(counts_2bit)

                # 对于当前pair，把全部深度的统计结果传给CSB处理
                csb_result = self.compute_csb_q2cz(
                    ncr_stats, target_phase=phi, rep=rep, cutoff=cutoff
                )
                csb_results_list.append({
                    "process_infidelity": float(csb_result["process_infidelity"]),
                    "stochastic_infidelity": float(csb_result["stochastic_infidelity"]),
                    "theta_error": float(csb_result["theta_error"]),
                    "phi_error": float(csb_result["phi_error"])
                })

            return csb_results_list

    def csbq2cnot(self, phi=np.pi, ndeg=3, rep=1, cutoff=1e-10, qubit_connectivity=None, mode=None):
        """
        Computes the CSB (Channel Spectrum Benchmarking) errors for the 2-qubit CNOT gate.

        Parameters:
            phi (float): The target phase for the CNOT gate, default is pi.
            ndeg (int): The degree for the matrix pencil method, default is 3.
            rep (int): The number of repetitions for each circuit, default is 1.
            cutoff (float): Singular value cutoff for matrix operations, default is 1e-10.

        Returns:
            list: A list of dictionaries, each containing the error metrics for a qubit pair. 
                Each dictionary includes:
                - 'process_infidelity': Process infidelity of the gate.
                - 'stochastic_infidelity': Stochastic infidelity of the gate.
                - 'theta_error': Error in the theta parameter.
                - 'phi_error': Error in the phi parameter.
        """
        csb_results_list = []  # Initialize list to store CSB results for each qubit pair

        if mode == 'respective':

            # Iterate over the hardware results for each qubit pair
            for qubit_pair_index, qubit_circuits in enumerate(self.hardware_results):
                # Compute CSB metrics for the current qubit pair's circuits
                csb_result = self.compute_csb_q2cnot(
                    qubit_circuits, target_phase=phi, rep=rep, cutoff=cutoff
                )

                # Append the results in a dictionary format
                csb_results_list.append({
                    "process_infidelity": float(csb_result["process_infidelity"]),
                    "stochastic_infidelity": float(csb_result["stochastic_infidelity"]),
                    "theta_error": float(csb_result["theta_error"]),
                    "phi_error": float(csb_result["phi_error"])
                })

            return csb_results_list

        elif mode == 'simultaneous':

            all_qubits = sorted(set(q for pair in qubit_connectivity for q in pair))
            qubit_index_map = {q: idx for idx, q in enumerate(all_qubits)}  # 全局比特序号到bitstring序号

            results_per_pair = []  # 外层list，每个qubit_pair的统计

            # 外层循环，每个qubit pair单独统计自己的比特对概率
            for pair_idx, qubit_pair in enumerate(qubit_connectivity):
                idx0 = qubit_index_map[qubit_pair[0]]
                idx1 = qubit_index_map[qubit_pair[1]]
                pair_stats = []  # 每个depth的list

                for depth_result in self.hardware_results:  # 这里hardware_results[depth]是ncr个dict的list
                    ncr_stats = []  # 统计所有ncr
                    for ncr_result in depth_result:  # ncr_result是dict
                        counts_2bit = {'00': 0, '01': 0, '10': 0, '11': 0}
                        for bitstring, count in ncr_result.items():
                            # 注意Qiskit bitstring的最低位在右边
                            b0 = bitstring[-(idx0 + 1)]
                            b1 = bitstring[-(idx1 + 1)]
                            key = b0 + b1
                            counts_2bit[key] += count
                        ncr_stats.append(counts_2bit)

                # 对于当前pair，把全部深度的统计结果传给CSB处理
                csb_result = self.compute_csb_q2cz(
                    ncr_stats, target_phase=phi, rep=rep, cutoff=cutoff
                )
                csb_results_list.append({
                    "process_infidelity": float(csb_result["process_infidelity"]),
                    "stochastic_infidelity": float(csb_result["stochastic_infidelity"]),
                    "theta_error": float(csb_result["theta_error"]),
                    "phi_error": float(csb_result["phi_error"])
                })

            return csb_results_list

    def compute_csb_q2cnot(self, bitstring_counts, target_phase=np.pi, rep=1, cutoff=1e-10):
        """
        Compute CSB error metrics for the 2-qubit CNOT gate, including process infidelity, 
        stochastic infidelity, theta error, and phi error.

        Parameters:
            bitstring_counts (list of dict): List of bitstring counts for each circuit.
            target_phase (float): Target phase for the CNOT gate, default is pi.
            rep (int): Number of repetitions of the CNOT gate, default is 1.
            cutoff (float): Singular value cutoff for matrix operations, default is 1e-10.

        Returns:
            dict: A dictionary containing process infidelity, stochastic infidelity, 
                theta error, and phi error.
        """
        # Step 1: Convert bitstring counts to probabilities, focusing on '11' counts for CNOT gate
        probabilities = [counts.get('11', 0) / sum(counts.values()) for counts in bitstring_counts]
        probabilities = np.array(probabilities)

        # Step 2: Apply matrix pencil method for analysis
        L = max(int(len(probabilities) * 0.4), 1)  # Use 40% of data length for L
        N_poles = 4  # Number of poles (adjust as needed)

        poles, amplitudes, singular_values = MetricQuality.matrix_pencil(
            probabilities, L=L, N_poles=N_poles, cutoff=cutoff
        )

        # Step 3: Process poles and calculate errors
        if len(poles) < N_poles:
            poles = np.append(poles, [1] * (N_poles - len(poles)))  # Pad with 1s if insufficient poles

        amps = np.abs(poles)
        phases = np.angle(poles)
        
        # Accumulate phase without modulo to preserve phase information
        target_phase_p = target_phase * rep
        target_phase_p = (target_phase_p + np.pi) % (2 * np.pi) - np.pi  # Adjust to [-pi, pi]

        # Compute phase differences and find the closest phase
        phase_difs = np.abs(phases - target_phase_p)
        angle_index = np.argmin(phase_difs)
        phase_error = phase_difs[angle_index] / rep  # Normalize by repetitions

        # Compute amplitude error (assuming ideal amplitude is 1)
        amplitude_error = 1 - amps[angle_index] ** (1 / rep)

        # Compute fidelity metrics
        f_mean = 1 - amplitude_error
        f_mean = min(f_mean, 1.0)  # Ensure fidelity does not exceed 1

        # Compute stochastic fidelity
        u_mean = 1 - amplitude_error  # Simplified assumption
        u_mean = min(u_mean, 1.0)  # Ensure fidelity does not exceed 1

        # Compute angle errors
        theta_error = phase_error
        phi_error = 0  # If there's no additional phase information, set phi_error to 0

        # Convert np.float64 to float before returning
        return {
            "process_infidelity": float(max(1 - f_mean, 0.0)),  # Ensure non-negative infidelity
            "stochastic_infidelity": float(max(1 - np.sqrt(u_mean), 0.0)),  # Ensure non-negative infidelity
            "theta_error": float(theta_error),
            "phi_error": float(phi_error)
        }


    def ghzqm_fidelity(self):
        """
        Computes the fidelity of a GHZ state based on hardware results.

        The input `self.hardware_results` is expected to be a nested list structure:
        - The outer list represents different qubit pair selections.
        - The middle list represents different circuit lengths.
        - The inner list represents the `ncr` circuits with their corresponding bitstring counts.

        Returns:
            list: A list of fidelity values, one for each qubit pair selection.
        """
        fidelities_for_pair = []

        # Loop through each set of qubit pair selections (outer loop)
        for qubit_pair_results in self.hardware_results:

            fidelities_for_circuit = []

            # Dynamically determine the number of qubits in this set
            num_qubits = len(next(iter(qubit_pair_results[0].keys())))  # Get the bitstring length

            # Define the ideal outcomes for a GHZ state based on the number of qubits
            ideal_outcomes = {
                "0" * num_qubits: 0.5,  # |00...0>
                "1" * num_qubits: 0.5   # |11...1>
            }

            # Loop through each repeated circuit result (inner loop)
            for circuit_results in qubit_pair_results:

                # Aggregate the bitstring counts from all repetitions (ncr)
                total_counts = {}
                for bitstring, count in circuit_results.items():
                    total_counts[bitstring] = total_counts.get(bitstring, 0) + count

                # Normalize the total counts
                total_shots = sum(total_counts.values())
                normalized_counts = {bitstring: count / total_shots for bitstring, count in total_counts.items()}

                # Compute fidelity for this circuit
                fidelity = 0
                for bitstring, ideal_prob in ideal_outcomes.items():
                    fidelity += np.sqrt(normalized_counts.get(bitstring, 0) * ideal_prob)

                fidelities_for_circuit.append(fidelity)

            # Average fidelity for this qubit pair selection
            fidelities_for_pair.append(np.mean(fidelities_for_circuit))

        return fidelities_for_pair



    def stanqvqm(self, ncr=10):
        """
        Process the quantum volume circuits, compute heavy output probabilities, and calculate quantum volume.

        Args:
            ncr (int): The number of random circuits per qubit configuration.

        Returns:
            dict: A dictionary containing quantum volume results for each qubit configuration.
        """
        qv_results = {}  # Initialize an empty dictionary to store the results

        # Iterate over each qubit configuration
        for nq_idx, hardware_results in enumerate(self.hardware_results):
            nq = nq_idx + 2  # Qubit count starts from 2 (nq=2 for the first configuration)

            heavy_output_probabilities = []  # List to store heavy output probabilities for the current nq configuration

            # Iterate through all ncr circuits for the current qubit configuration
            for circuit_idx in range(ncr):
                # Retrieve the corresponding hardware or simulation results
                if circuit_idx < len(hardware_results):
                    probs_exp = hardware_results[circuit_idx]  # Safe access to the results
                else:
                    probs_exp = None  # Handle case when there are missing results

                # Skip the current iteration if results are missing
                if probs_exp is None:
                    continue

                # Compute heavy outputs and their probabilities using the heavy_output_set method
                heavy_outputs, prob_heavy_output = self.heavy_output_set(nq, probs_exp)

                # Append the heavy output probability for the current circuit
                heavy_output_probabilities.append(prob_heavy_output)

            # Skip the configuration if no valid probabilities were collected
            if not heavy_output_probabilities:
                continue

            # Calculate the mean probability of heavy outputs
            mean_prob_heavy_outputs = np.mean(heavy_output_probabilities)

            # Check if the mean probability exceeds the threshold for quantum volume (2/3)
            if mean_prob_heavy_outputs > 2 / 3:
                qv_value = 2 ** nq  # Quantum volume is 2^n
            else:
                qv_value = 0  # If threshold is not met, quantum volume is 0

            # Store the results for the current qubit configuration
            qv_results[f"nqubits_{nq}"] = {
                "total_qubits": nq,
                "quantum_volume": qv_value,
                "mean_heavy_output_probability": mean_prob_heavy_outputs
            }

        return qv_results


    def mrbqm(self):
        """
        Computes the effective polarization for each qubit group and circuit length
        using hardware execution results and corresponding simulation target bitstrings.

        Returns:
            list: A two-layer nested list where the first layer corresponds to qubit groups,
                and the second layer corresponds to different circuit lengths. Each element
                is the average effective polarization S for that qubit group and circuit length.
        """
        polarizations = []

        # Iterate over each qubit group (hardware and simulation results)
        for hardware_qg, simulation_qg in zip(self.hardware_results, self.simulation_results):
            if not hardware_qg or not simulation_qg:
                polarizations.append([])  # Append empty if no results
                continue

            # Determine the number of qubits from the hardware results (based on bitstring length)
            first_hardware_circuit = hardware_qg[0][0]
            if isinstance(first_hardware_circuit, dict):
                sample_bitstring = next(iter(first_hardware_circuit.keys()), '0')
                num_qubits = len(sample_bitstring)
            else:
                polarizations.append([])  # Append empty if the circuit structure is invalid
                continue

            polarizations_per_length = []

            # Iterate over the circuit lengths and compute polarization for each group
            for hardware_length_group, simulation_length_group in zip(hardware_qg, simulation_qg):
                sum_S = 0.0
                valid_circuits = 0

                # Iterate through circuits and calculate polarization
                for circuit_result, simulation_result in zip(hardware_length_group, simulation_length_group):
                    if isinstance(circuit_result, dict) and isinstance(simulation_result, dict):
                        # Extract the target bitstring with the highest frequency
                        target_bitstring = max(simulation_result, key=simulation_result.get)
                        # Compute the effective polarization S using the target bitstring
                        S = MetricQuality._compute_S(circuit_result, num_qubits, target_bitstring)
                        sum_S += S
                        valid_circuits += 1

                # Compute the average polarization for the current length
                average_S = sum_S / valid_circuits if valid_circuits > 0 else None
                polarizations_per_length.append(average_S)

            polarizations.append(polarizations_per_length)

        return polarizations



class MetricSpeed:
    """
    MetricSpeed calculates CLOPS (Circuit Layer Operations Per Second) using the formula:
    
    CLOPS = (M × K × S × D) / time_taken
    
    where:
    M = number of templates (default is 100)
    K = number of parameter updates (default is 10)
    S = number of shots (default is 100)
    D = number of QV layers (default is 5, based on log2(QV) where QV = 32)
    """
    
    def __init__(self, all_results):
        """
        Initializes the MetricSpeed class.
    
        Parameters:
            all_results (dict): Dictionary containing 'hardware' and 'simulation' results.
                                Each should be a 3-layer list of execution results, where the outer list represents qubit results,
                                the middle list represents circuit lengths, and the inner list represents the NCR circuits.
        """
        self.hardware_results = all_results.get('hardware', [])
        self.simulation_results = all_results.get('simulation', [])
    
    def clopsqm(self, num_templates=10, num_updates=10, num_shots=1024, num_layers=5):
        """
        Calculates CLOPSQM using only hardware results.

        Args:
            num_templates (int, optional): Number of templates (M). Default is 100.
            num_updates (int, optional): Number of parameter updates (K). Default is 10.
            num_shots (int, optional): Number of shots (S). Default is 1024.
            num_layers (int, optional): Number of QV layers (D). Default is 5.

        Returns:
            float: The calculated CLOPSQM value.
        """

        """
        CLOPSQM is calculated using the formula:

        CLOPSQM = (M × K × S × D) / total_elapsed_time

        Only 'hardware' results are used for the calculation.
        """

        # Initialize total_elapsed_time to 0
        total_elapsed_time = 0

        # Iterate over the hardware results (assumed to be a dictionary or a list of nested lists)
        for value in self.hardware_results:  # Traverse all values in the hardware results
            if isinstance(value, list):  # If the value is a list
                for sublist in value:  # Traverse elements within the list
                    if isinstance(sublist, list):  # If the element is a list
                        for ncr_time in sublist:  # Traverse nested list elements
                            total_elapsed_time += ncr_time  # Add the time to total_elapsed_time
                    else:
                        total_elapsed_time += sublist  # If it's not a list, directly add the value
            else:
                total_elapsed_time += value  # If it's not a list, directly add the value

        # Calculate CLOPSQM using the provided formula
        clopsqm_value = (num_templates * num_updates * num_shots * num_layers) / total_elapsed_time

        # Return the calculated CLOPSQM value
        return clopsqm_value
