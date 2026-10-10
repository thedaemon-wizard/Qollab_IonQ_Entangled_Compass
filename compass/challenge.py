"""Storm challenge: twelve two-hour rounds through the May 2024 storm (16:00 UTC on 10 May to
16:00 UTC on 11 May). Before each round the player picks a sensor; the round is then replayed
with that sensor.

Rules: keeping the same sensor keeps its estimate, so a GHZ-4 that jumped a fringe stays off
until another jump happens to bring it back. Switching to a different sensor starts it from a
fresh absolute fix (we assume a slow absolute reference, like the observatory's own instrument,
is available when you switch). Without that fix, an offset of two GHZ-4 fringes (157 nT) is
exactly at the edge of what even a single qubit can resolve, and the estimate could lock 314 nT
off for good.

Score per round: RMS error times sqrt(qubits / 8), so that every sensor is charged for the
qubits it uses (shot noise falls as 1/sqrt(qubits)); lower is better.
"""

from __future__ import annotations

import math

import numpy as np

from compass import data, replay

START = "2024-05-10T16:00"
ROUND_MIN = 120
ROUNDS = 12
CHOICES = {
    "IND8": {"label": "8 independent qubits", "qubits": 8, "m_max": 1},
    "GHZ4": {"label": "GHZ-4 (entangled)", "qubits": 8, "m_max": 4},
    "CASC": {"label": "Cascade 1-2-4 (entangled)", "qubits": 14, "m_max": 1},
}


def _window(k: int):
    times, f = data.load("storm")
    a = times.index(START) + k * ROUND_MIN
    # the round covers minutes a .. a+119; the estimate enters at minute a-1
    return times[a - 1 : a + ROUND_MIN], f[a - 1 : a + ROUND_MIN]


def play(k: int, choice: str, offset_nt: float, vis: dict, scale: float, shots: int, seed: int) -> dict:
    times, f = _window(k)
    est = replay.track(
        f, scale, shots, vis, arms=(choice,), replicates=1, seed=seed + 1000 * k, start_offset=offset_nt
    )[choice][0]
    err = est[1:] - f[1:]
    spacing = 2 * math.pi / (CHOICES[choice]["m_max"] * scale)
    fringe = np.round(err / spacing)
    rmse = float(np.sqrt(np.mean(err**2)))
    return {
        "choice": choice,
        "rmse_nt": rmse,
        "score": rmse * math.sqrt(CHOICES[choice]["qubits"] / 8),
        "slips": int((np.diff(np.concatenate([[round(offset_nt / spacing)], fringe])) != 0).sum()),
        "wrong_minutes": int((fringe != 0).sum()),
        "end_offset_nt": float(err[-1]),
        "times": times[1:],
        "error_nt": [round(float(x), 3) for x in err],
    }


def largest_step(k: int) -> float:
    _, f = _window(k)
    return float(np.abs(np.diff(f)).max())


def always(choice: str, vis: dict, scale: float, shots: int, seed: int) -> dict:
    offset, scores = 0.0, []
    for k in range(ROUNDS):
        r = play(k, choice, offset, vis, scale, shots, seed)
        offset = r["end_offset_nt"]
        scores.append(r["score"])
    return {"choice": choice, "mean_score": float(np.mean(scores)), "scores": scores}
