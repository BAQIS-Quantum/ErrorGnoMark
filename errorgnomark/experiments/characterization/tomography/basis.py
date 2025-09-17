# File Path: errorgnomark/experiments/characterization/tomography/basis.py

import numpy as np
from typing import Dict, Tuple

# 依赖于 circuits 模块，这是一个健康的、向下的依赖关系
from errorgnomark.circuits.circuit import get_matrix

SINGLE_QUBIT_BASIS_MAP: Dict[str, np.ndarray] = {
    'Z': get_matrix('id'),
    'X': get_matrix('h'),
    'Y': get_matrix('h') @ get_matrix('sdg')
}

TOMOGRAPHY_BASIS_MAP: Dict[str, Tuple[np.ndarray, ...]] = {}

basis_labels = ['X', 'Y', 'Z']
for q1_label in basis_labels:
    for q2_label in basis_labels:
        key = f"{q1_label}{q2_label}"
        value = (
            SINGLE_QUBIT_BASIS_MAP[q1_label],
            SINGLE_QUBIT_BASIS_MAP[q2_label]
        )
        TOMOGRAPHY_BASIS_MAP[key] = value