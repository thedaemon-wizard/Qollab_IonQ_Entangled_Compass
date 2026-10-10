"""Twin sensors: one qubit at Boulder (A) and one at Tucson (B), about 1,000 km apart.

Entangled as (|01> + |10>)/sqrt(2), the pair picks up only the DIFFERENCE of the two phases,
delta_A - delta_B: a field change shared by both sites cancels (Ruster et al. 2017 used this with
two ions 6.2 mm apart to reject common magnetic noise). As (|00> + |11>)/sqrt(2) it picks up the
SUM instead. Two unentangled qubits measure each site on its own.

This is a what-if: sharing entanglement between observatories needs a quantum network that does
not exist; the field records are real.

Circuit "T" (13 qubits): canary q0; DIFF pair X (q1 at A, q2 at B) and Y (q3, q4); SUM pair X
(q5, q6) and Y (q7, q8); single qubits A-X q9, A-Y q10, B-X q11, B-Y q12.
"""

from __future__ import annotations

import math

import numpy as np
from qiskit import QuantumCircuit

from compass.estimators import theta

PAIRS = {"DIFFX": (1, 2), "DIFFY": (3, 4), "SUMX": (5, 6), "SUMY": (7, 8)}
SINGLES = {"AX": 9, "AY": 10, "BX": 11, "BY": 12}
N_QUBITS = 13


def build(delta_a: float, delta_b: float) -> QuantumCircuit:
    qc = QuantumCircuit(N_QUBITS, N_QUBITS, name="compass_twin")
    qc.x(0)
    for name, (a, b) in PAIRS.items():
        qc.h(a)
        qc.cx(a, b)
        if name.startswith("DIFF"):
            qc.x(b)  # |00> + |11>  ->  |01> + |10>
        qc.rz(delta_a, a)
        qc.rz(delta_b, b)
        if name.endswith("Y"):
            qc.sdg(a)
        qc.h(a)
        qc.h(b)
    for name, q in SINGLES.items():
        qc.h(q)
        qc.rz(delta_a if name.startswith("A") else delta_b, q)
        if name.endswith("Y"):
            qc.sdg(q)
        qc.h(q)
    qc.measure(range(N_QUBITS), range(N_QUBITS))
    return qc


def parities(counts: dict[str, int]) -> dict:
    n = N_QUBITS
    keys = {k.replace(" ", "").zfill(n): v for k, v in counts.items()}
    total = sum(keys.values())
    canary = sum(v for k, v in keys.items() if k[n - 1] == "1") / total
    groups = {**{k: v for k, v in PAIRS.items()}, **{k: (q,) for k, q in SINGLES.items()}}
    out = {}
    for name, qubits in groups.items():
        s = sum(v if sum(k[n - 1 - q] == "1" for q in qubits) % 2 == 0 else -v for k, v in keys.items())
        out[name] = s / total
    return {"shots": total, "canary": canary, "mean": out}


def track(f_a, f_b, scale, shots, replicates=32, seed=0, visibility=1.0):
    """Track the gradient F_A - F_B for one minute at a time with the same 4 qubits per shot:
    DIFF (the entangled pair read in X and in Y) or IND (one qubit per site read in X and in Y,
    the gradient being the difference of the two estimates)."""
    rng = np.random.default_rng(seed)
    g = f_a - f_b
    n = len(g)
    diff = np.empty((replicates, n))
    est_a = np.empty((replicates, n))
    est_b = np.empty((replicates, n))
    diff[:, 0], est_a[:, 0], est_b[:, 0] = g[0], f_a[0], f_b[0]

    def read(delta):
        x = 2 * rng.binomial(shots, (1 + visibility * np.cos(delta)) / 2) / shots - 1
        y = 2 * rng.binomial(shots, (1 + visibility * np.sin(delta)) / 2) / shots - 1
        return theta(x, y)

    for t in range(1, n):
        diff[:, t] = diff[:, t - 1] + read(scale * (g[t] - diff[:, t - 1])) / scale
        est_a[:, t] = est_a[:, t - 1] + read(scale * (f_a[t] - est_a[:, t - 1])) / scale
        est_b[:, t] = est_b[:, t - 1] + read(scale * (f_b[t] - est_b[:, t - 1])) / scale
    return {"DIFF": diff, "IND": est_a - est_b}


def step_statistics(f_a, f_b) -> dict:
    da, db = np.diff(f_a), np.diff(f_b)
    dg = da - db
    return {
        "corr_one_minute_changes": float(np.corrcoef(da, db)[0, 1]),
        "std_step_a_nt": float(da.std()),
        "std_step_b_nt": float(db.std()),
        "std_step_gradient_nt": float(dg.std()),
        "largest_step_a_nt": float(np.abs(da).max()),
        "largest_step_gradient_nt": float(np.abs(dg).max()),
        "common_fraction": float(1 - dg.var() / (da.var() + db.var()))
        if da.var() + db.var() > 0
        else math.nan,
    }
