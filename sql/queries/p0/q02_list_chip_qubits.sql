-- p1-step2 API-02 / Q2 minimal: qubits for a chip
SELECT qubit_id, chip_id, qubit_index, qubit_label
FROM qubit
WHERE chip_id = %(chip_id)s::uuid
ORDER BY qubit_index;
