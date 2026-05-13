"""
Parse Quafu official calibration CSV into structured dataclasses.

The CSV is downloaded from:
    https://quafu-sqc.baqis.ac.cn/chipDetails?chip=<ChipName>

Key parsing challenge: the ``CZ fidelity`` column contains multi-line text
within a single quoted CSV cell, e.g.::

    "2_1: 0
    2_3: 0.986
    2_15: 0.986"

Python's ``csv.reader`` handles quoted newlines correctly.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class QubitCalibration:
    qubit_index: int
    t1_us: float
    t2_us: float
    frequency_ghz: float
    single_qubit_fidelity: float


@dataclass(frozen=True)
class CouplerCalibration:
    """A canonical undirected edge (qubit_a < qubit_b)."""

    qubit_a: int
    qubit_b: int
    cz_fidelity: float


@dataclass
class QuafuCalibrationData:
    chip_name: str
    calibration_time: datetime
    csv_filename: str
    qubits: List[QubitCalibration] = field(default_factory=list)
    couplers: List[CouplerCalibration] = field(default_factory=list)

    @property
    def num_qubits(self) -> int:
        return len(self.qubits)

    @property
    def num_couplers(self) -> int:
        return len(self.couplers)

    def summary(self) -> Dict[str, float]:
        """Compute median statistics matching Quafu's website summary."""
        import statistics

        t1_vals = [q.t1_us for q in self.qubits if q.t1_us > 0]
        t2_vals = [q.t2_us for q in self.qubits if q.t2_us > 0]
        sq_fid_vals = [q.single_qubit_fidelity for q in self.qubits if q.single_qubit_fidelity > 0]
        cz_vals = [c.cz_fidelity for c in self.couplers if c.cz_fidelity > 0]

        return {
            "median_t1_us": statistics.median(t1_vals) if t1_vals else 0.0,
            "median_t2_us": statistics.median(t2_vals) if t2_vals else 0.0,
            "median_sq_fidelity": statistics.median(sq_fid_vals) if sq_fid_vals else 0.0,
            "median_cz_fidelity": statistics.median(cz_vals) if cz_vals else 0.0,
            "median_1q_error": 1.0 - statistics.median(sq_fid_vals) if sq_fid_vals else 0.0,
            "median_2q_error": 1.0 - statistics.median(cz_vals) if cz_vals else 0.0,
        }


# ── filename → timestamp ─────────────────────────────────────────────────────

_FILENAME_TS_RE = re.compile(
    r"(\d{4})-(\d{2})-(\d{2})\s+(\d{2})[_:](\d{2})[_:](\d{2})"
)


def _parse_timestamp_from_string(text: str) -> Optional[datetime]:
    """
    Extract calibration timestamp from a string like:
        ``Baihua_calibration_2026-05-13 10_40_49.csv``
    or a directory name like ``2026-05-13_10-40-49``.
    """
    m = _FILENAME_TS_RE.search(text)
    if not m:
        return None
    year, month, day, hour, minute, second = (int(g) for g in m.groups())
    return datetime(year, month, day, hour, minute, second)


_DIR_TS_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})")


def _parse_timestamp_from_path(csv_path: str) -> Optional[datetime]:
    """
    Try filename first, then parent directory name for timestamp.

    Supports:
        ``Baihua_calibration_2026-05-13 10_40_49.csv``  (original download)
        ``fixtures/quafu/baihua/2026-05-13_10-40-49/Baihua_calibration.csv`` (archived)
    """
    ts = _parse_timestamp_from_string(Path(csv_path).name)
    if ts is not None:
        return ts
    parent = Path(csv_path).parent.name
    m = _DIR_TS_RE.search(parent)
    if m:
        year, month, day, hour, minute, second = (int(g) for g in m.groups())
        return datetime(year, month, day, hour, minute, second)
    return _parse_timestamp_from_string(parent)


def _parse_chip_name_from_filename(filename: str) -> str:
    """Extract chip name from filename like ``Baihua_calibration_...``."""
    stem = Path(filename).stem
    parts = stem.split("_calibration")
    return parts[0] if parts else "unknown"


# ── CZ fidelity cell → edges ─────────────────────────────────────────────────

_EDGE_RE = re.compile(r"(\d+)_(\d+)\s*:\s*([\d.]+(?:e[+-]?\d+)?)")


def _parse_cz_fidelity_cell(cell_text: str) -> List[Tuple[int, int, float]]:
    """
    Parse a multi-line CZ fidelity cell into a list of (qubit_a, qubit_b, fidelity).

    Each line looks like ``2_3: 0.986``.  Returns canonical edges with a < b.
    """
    edges = []
    for m in _EDGE_RE.finditer(cell_text):
        i, j = int(m.group(1)), int(m.group(2))
        fid = float(m.group(3))
        a, b = min(i, j), max(i, j)
        edges.append((a, b, fid))
    return edges


# ── main parser ───────────────────────────────────────────────────────────────

def parse_quafu_csv(csv_path: str) -> QuafuCalibrationData:
    """
    Parse a Quafu calibration CSV file into ``QuafuCalibrationData``.

    Parameters
    ----------
    csv_path : str
        Path to the CSV file (may contain spaces in filename).

    Returns
    -------
    QuafuCalibrationData
        Parsed calibration data with deduplicated coupler edges.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.
    ValueError
        If the CSV header does not match expectations.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    filename = path.name
    chip_name = _parse_chip_name_from_filename(filename)
    cal_time = _parse_timestamp_from_path(csv_path)
    if cal_time is None:
        raise ValueError(
            f"Cannot parse calibration timestamp from path: {csv_path}"
        )

    qubits: List[QubitCalibration] = []
    seen_edges: Dict[Tuple[int, int], float] = {}

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)

        expected_cols = {"Qubit", "T1(us)", "T2(us)", "Frequency(GHz)",
                         "Single qubit fidelity", "CZ fidelity"}
        actual_cols = {h.strip() for h in header}
        if not expected_cols.issubset(actual_cols):
            raise ValueError(
                f"CSV header mismatch. Expected columns {expected_cols}, "
                f"got {actual_cols}"
            )

        col_idx = {h.strip(): i for i, h in enumerate(header)}

        for row_num, row in enumerate(reader, start=2):
            if not row or not row[0].strip():
                continue

            try:
                qubit_index = int(row[col_idx["Qubit"]])
                t1 = float(row[col_idx["T1(us)"]])
                t2 = float(row[col_idx["T2(us)"]])
                freq = float(row[col_idx["Frequency(GHz)"]])
                sq_fid = float(row[col_idx["Single qubit fidelity"]])
            except (ValueError, IndexError) as exc:
                raise ValueError(f"Row {row_num}: failed to parse qubit fields: {exc}") from exc

            qubits.append(QubitCalibration(
                qubit_index=qubit_index,
                t1_us=t1,
                t2_us=t2,
                frequency_ghz=freq,
                single_qubit_fidelity=sq_fid,
            ))

            cz_cell = row[col_idx["CZ fidelity"]] if col_idx["CZ fidelity"] < len(row) else ""
            for a, b, fid in _parse_cz_fidelity_cell(cz_cell):
                if (a, b) not in seen_edges:
                    seen_edges[(a, b)] = fid

    couplers = [
        CouplerCalibration(qubit_a=a, qubit_b=b, cz_fidelity=fid)
        for (a, b), fid in sorted(seen_edges.items())
    ]

    return QuafuCalibrationData(
        chip_name=chip_name,
        calibration_time=cal_time,
        csv_filename=filename,
        qubits=qubits,
        couplers=couplers,
    )


# ── CLI smoke test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python quafu_csv_parser.py <path_to_csv>")
        sys.exit(1)

    data = parse_quafu_csv(sys.argv[1])
    print(f"Chip:        {data.chip_name}")
    print(f"Calibration: {data.calibration_time.isoformat()}")
    print(f"Qubits:      {data.num_qubits}")
    print(f"Couplers:    {data.num_couplers}")
    print()

    summary = data.summary()
    for k, v in summary.items():
        print(f"  {k}: {v:.6f}")

    print()
    print("Sample qubits:")
    for q in data.qubits[:5]:
        print(f"  Q{q.qubit_index}: T1={q.t1_us:.3f}us  T2={q.t2_us:.3f}us  "
              f"freq={q.frequency_ghz:.3f}GHz  SQ_fid={q.single_qubit_fidelity:.4f}")

    print()
    print("Sample couplers:")
    for c in data.couplers[:5]:
        print(f"  ({c.qubit_a}, {c.qubit_b}): CZ_fid={c.cz_fidelity:.4f}")
