"""Closed forms: parities, visibilities, Fisher information and the gains they imply.

Conventions (Qiskit): Rz(phi) = diag(exp(-i phi/2), exp(i phi/2)). A GHZ register of m qubits
after Rz(delta) on every qubit is (|0..0> + exp(i m delta)|1..1>)/sqrt(2); measured after H on
every qubit, its parity has mean V cos(m delta); with Sdg on the first qubit before the H
layer, V sin(m delta). V is the visibility (1 for an ideal register).
"""

from __future__ import annotations

import math

# Electron spin: gamma_e / 2pi = 28.0249513861 GHz/T (CODATA 2022) = 28.0249513861 Hz/nT.
GAMMA_E_HZ_PER_NT = 28.0249513861

# IonQ's documented noise models: depolarizing after each one- and two-qubit gate
# (docs.ionq.com/features/simulation-with-noise-models, read 2026-10-10). The documented
# parameters apply to the Aria models and to Forte jobs before mid-September 2025; the current
# Forte models are not publicly documented, so they are not listed here.
IONQ_DOCUMENTED = {
    "aria-1": {"label": "IonQ Aria 1 (documented)", "r1": 0.0005, "r2": 0.0133},
    "aria-2": {"label": "IonQ Aria 2 (documented)", "r1": 0.000657333, "r2": 0.01856},
    "forte-1-2025": {"label": "IonQ Forte 1 (documented, before Sept 2025)", "r1": 0.000267, "r2": 0.00495},
}


def ramsey_time_us(scale_rad_per_nt: float) -> float:
    """Interrogation time that maps 1 nT to `scale` rad for an electron spin."""
    return scale_rad_per_nt / (2 * math.pi * GAMMA_E_HZ_PER_NT) * 1e6


def parity(m: int, basis: str, delta: float, v: float = 1.0) -> float:
    """Mean parity of an m-qubit GHZ register (m = 1 is a single qubit)."""
    return v * (math.cos(m * delta) if basis == "X" else math.sin(m * delta))


def gate_counts(m: int, knob: bool) -> tuple[int, int]:
    """One- and two-qubit gates that touch the data qubits of one register.

    H on the first qubit, a CX ladder (m - 1), H on every qubit at the end; the dephasing knob
    adds two CX (it is built as CX.Rz.CX with its ancilla). Rz and Sdg are Z rotations and are
    treated as noise-free (virtual), as in IonQ's description of its compiler. IonQ compiles
    abstract gates to its native gates before it simulates a noise model, and whether its
    noise-model simulator charges noise to Z rotations is not documented, so this count gives an
    estimate (the visibility measured in a run is reported as measured).
    """
    return m + 1, m - 1 + (2 if knob else 0)


def gate_visibility(m: int, r1: float, r2: float, knob: bool = False) -> float:
    """Visibility left by depolarizing after each gate: (1 - r1)^n1 (1 - r2)^n2."""
    n1, n2 = gate_counts(m, knob)
    return (1 - r1) ** n1 * (1 - r2) ** n2


def dephasing_visibility(m: int, gamma: float) -> float:
    """Independent dephasing, coherence exp(-gamma) per qubit: a GHZ register keeps exp(-m gamma)."""
    return math.exp(-m * gamma)


def knob_angle(m: int, gamma: float) -> float:
    """Angle b of the CX.Rz(b).CX knob with an ancilla in |+>: coherence factor cos(b) = exp(-m gamma)."""
    return math.acos(math.exp(-m * gamma))


def fisher_parity(n: int, v: float, phi: float) -> float:
    """Fisher information of one parity outcome, P(+-) = (1 +- V cos n phi)/2."""
    c = v * math.cos(n * phi)
    s = v * n * math.sin(n * phi)
    return 0.0 if 1 - c * c <= 0 else s * s / (1 - c * c)


def gain_independent_dephasing(n: int, gamma: float) -> float:
    """Best-case gain in standard deviation of an n-qubit GHZ state over n independent qubits.

    GHZ: Fisher n^2 exp(-2 n gamma); n independent qubits: n exp(-2 gamma). Ratio of standard
    deviations: sqrt(n) exp(-(n - 1) gamma).
    """
    return math.sqrt(n) * math.exp(-(n - 1) * gamma)


def crossover_gamma(n: int) -> float:
    """Dephasing at which the GHZ state stops beating independent qubits: ln n / (2 (n - 1))."""
    return math.log(n) / (2 * (n - 1))


def fringe_spacing_nt(m: int, scale: float) -> float:
    """Field change that moves an m-qubit GHZ register by one full fringe (2 pi)."""
    return 2 * math.pi / (m * scale)
