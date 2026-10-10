"""From register parities to field estimates.

Each sensor gives an angle theta_m = atan2(<Y>, <X>), an estimate of m*delta modulo 2 pi (the
visibility cancels). A GHZ-4 register alone knows delta only modulo 2 pi / 4; the 1-2-4 cascade
(Kimmel, Low and Yoder 2015) unwraps it with the coarser registers.
"""

from __future__ import annotations

import math

import numpy as np


def wrap(x):
    """Map an angle into [-pi, pi)."""
    return (np.asarray(x) + math.pi) % (2 * math.pi) - math.pi


def theta(x, y):
    return np.arctan2(y, x)


def cascade(t1, t2, t4):
    """Unwrap with the 1-2-4 ladder: each finer register refines the coarser estimate."""
    e = np.asarray(t1, dtype=float)
    e = e + wrap(np.asarray(t2) - 2 * e) / 2
    return e + wrap(np.asarray(t4) - 4 * e) / 4


def var_theta(x: float, y: float, vx: float, vy: float, cxy: float = 0.0) -> float:
    """Delta-method variance of atan2(y, x)."""
    r2 = x * x + y * y
    if r2 == 0:
        return math.inf
    return (y * y * vx + x * x * vy - 2 * x * y * cxy) / (r2 * r2)


def visibility(x: float, y: float, vx: float, vy: float) -> float:
    """Bias-corrected visibility sqrt(x^2 + y^2 - Var x - Var y), clipped at 0."""
    return math.sqrt(max(0.0, x * x + y * y - vx - vy))
