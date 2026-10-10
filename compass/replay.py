"""Track a field record minute by minute with each sensor arm (numpy Monte Carlo).

Hybrid loop, per arm and minute t: a classical predictor says "the field is what I estimated a
minute ago"; the sensor measures the residual phase delta = s * (F_t - estimate); the estimate
moves by delta_hat / s. Shot noise is binomial with the register's visibility, the same model
the circuits follow (tests check it against circuit results).

Arms (qubits per shot -> what one minute costs):
  IND8   8 single qubits, 4 read X and 4 read Y      (unentangled, same X/Y split)
  GHZ4   one GHZ-4 read X and one read Y = 8 qubits    (entangled)
  CASC   GHZ-1, GHZ-2, GHZ-4, each read X and Y = 14   (entangled, unwraps the fringe)
  IND14  14 single qubits, 7 X and 7 Y                 (unentangled, same cost as CASC)
  MP4    1 qubit read X and 1 read Y, 4 passes each    (no entanglement, 4x the phase)
"""

from __future__ import annotations

import math

import numpy as np

from compass.estimators import cascade, theta

ARMS = {
    "IND8": {"regs": [(1, 4)], "qubits": 8, "label": "8 independent qubits"},
    "GHZ4": {"regs": [(4, 1)], "qubits": 8, "label": "GHZ-4 (entangled)"},
    "CASC": {"regs": [(1, 1), (2, 1), (4, 1)], "qubits": 14, "label": "Cascade 1-2-4 (entangled)"},
    "IND14": {"regs": [(1, 7)], "qubits": 14, "label": "14 independent qubits"},
    "MP4": {"regs": [(4, 1)], "qubits": 2, "label": "1 qubit, 4 passes", "multipass": True},
}


def _measure(rng, m, k, shots, delta, v, exact):
    """Mean X and Y parity of k copies of an m-register, S shots each."""
    px = (1 + v * np.cos(m * delta)) / 2
    py = (1 + v * np.sin(m * delta)) / 2
    n = k * shots
    if exact:
        return 2 * px - 1, 2 * py - 1
    return 2 * rng.binomial(n, px) / n - 1, 2 * rng.binomial(n, py) / n - 1


def track(
    f, scale, shots, vis, arms=("IND8", "GHZ4", "CASC"), replicates=32, seed=0, exact=False, start_offset=0.0
):
    """Run the loop over the record `f` (nT). `vis[(kind, m)]` gives each register's visibility,
    kind "ghz" or "mp". The estimate starts `start_offset` nT away from f[0]. Returns estimates with
    shape (replicates, len(f)) per arm."""
    rng = np.random.default_rng(seed)
    r = 1 if exact else replicates
    out = {}
    for name in arms:
        spec = ARMS[name]
        kind = "mp" if spec.get("multipass") else "ghz"
        est = np.empty((r, len(f)))
        est[:, 0] = f[0] + start_offset
        for t in range(1, len(f)):
            delta = scale * (f[t] - est[:, t - 1])
            thetas = {}
            for m, k in spec["regs"]:
                x, y = _measure(rng, m, k, shots, delta, vis[(kind, m)], exact)
                thetas[m] = theta(x, y)
            if name == "CASC":
                dhat = cascade(thetas[1], thetas[2], thetas[4])
            else:
                (m,) = thetas
                dhat = thetas[m] / m
            est[:, t] = est[:, t - 1] + dhat / scale
        out[name] = est
    return out


def metrics(f, est, scale, m_max):
    """RMSE (nT), minutes on a wrong fringe and slip events, per replicate."""
    err = est[:, 1:] - f[1:]
    spacing = 2 * math.pi / (m_max * scale)
    fringe = np.round(err / spacing)
    wrong = fringe != 0
    slips = (np.diff(fringe, axis=1) != 0).sum(axis=1)
    rmse = np.sqrt((err**2).mean(axis=1))
    ok = np.where(wrong, np.nan, err)
    rmse_ok = np.sqrt(np.nanmean(ok**2, axis=1)) if (~wrong).any() else np.full(len(err), np.nan)
    return {
        "err": err,
        "rmse": rmse,
        "rmse_ok": rmse_ok,
        "wrong": wrong.sum(axis=1),
        "slips": slips,
        "spacing": spacing,
    }


def mean_2se(x) -> dict:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {"mean": None, "two_se": None}
    se = x.std(ddof=1) / math.sqrt(len(x)) if len(x) > 1 else 0.0
    return {"mean": float(x.mean()), "two_se": float(2 * se)}
