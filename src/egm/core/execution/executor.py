from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

from egm.core.backends.base_backend import BaseBackend
from egm.core.backends.ideal_backend import IdealBackend
from egm.core.circuits.circuit import QuantumCircuit

logger = logging.getLogger(__name__)


class Executor:
    """
    Orchestrates circuit execution on a noisy backend alongside an ideal reference.

    Provides two execution paths:
    - Noisy: delegates to the provided backend.
    - Ideal: uses an internal IdealBackend for reference probabilities.
    """

    def __init__(self, backend: BaseBackend) -> None:
        if not isinstance(backend, BaseBackend):
            raise TypeError("backend must be a subclass of BaseBackend.")
        self.backend = backend
        self._ideal = IdealBackend()
        logger.info("QuantumEngine initialized with backend '%s'.", backend.name)

    # ------------------------------------------------------------------
    # Single-circuit execution (backward-compatible)
    # ------------------------------------------------------------------

    def run(
        self, circuit: QuantumCircuit, shots: int
    ) -> Tuple[Optional[np.ndarray], Dict[str, int]]:
        """Execute a single circuit on the noisy backend."""
        return self.backend.run(circuit, shots=shots)

    # ------------------------------------------------------------------
    # Ideal reference utilities
    # ------------------------------------------------------------------

    def get_ideal_probs(self, circuit: QuantumCircuit) -> Dict[str, float]:
        """Return ideal probability distribution for a circuit."""
        statevector, _ = self._ideal.run(circuit)
        return self._ideal.statevector_to_probs(statevector)

    # ------------------------------------------------------------------
    # Batch execution
    # ------------------------------------------------------------------

    def execute_with_ideal(
        self, circuits: List[QuantumCircuit], shots: int
    ) -> List[Tuple[Dict[str, float], Dict[str, int]]]:
        """
        Execute a list of circuits, returning (ideal_probs, noisy_counts) per circuit.

        Used by all benchmarking experiments that need an ideal reference.
        """
        n = len(circuits)
        logger.info(
            "Executing %d circuits (%d shots each) on backend '%s'.",
            n, shots, self.backend.name,
        )
        results = []
        for i, circuit in enumerate(circuits):
            ideal_probs = self.get_ideal_probs(circuit)
            _, noisy_counts = self.backend.run(circuit, shots=shots)
            results.append((ideal_probs, noisy_counts))
            if (i + 1) % 10 == 0 or i == n - 1:
                logger.debug("  %d / %d circuits done.", i + 1, n)
        logger.info("All %d circuits executed.", n)
        return results


# ---------------------------------------------------------------------------
# TODO: 迁移清单（完成后删除此 alias 和本注释）
#
# QuantumEngine 是旧名称，现统一改为 Executor。
# 在删除此 alias 之前，需完成以下迁移：
#
#   1. egm/core/experiments/base.py
#      - 修复 import 路径：egm.engine.executor → egm.core.execution.executor
#      - 将类型注解 QuantumEngine → Executor
#
#   2. egm/core/experiments/physical/benchmarking/*.py（rb, xeb, mrb 等）
#      - 同上：import 路径 + 类型注解
#
#   3. egm/core/engine/executor.py
#      - 确认无其他引用后，整个目录可废弃删除
#
# 全部完成后，删除下方一行即可。
# ---------------------------------------------------------------------------
QuantumEngine = Executor
