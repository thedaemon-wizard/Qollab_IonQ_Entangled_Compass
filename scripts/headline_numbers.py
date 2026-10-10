"""Recompute every number the README quotes (model replay, local; no backend needed).

Usage: PYTHONPATH=. python scripts/headline_numbers.py  -> results/headline_numbers.json
"""

from __future__ import annotations

import json
import math
import platform
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import qiskit

from compass import api, challenge, data, model, replay

ROOT = Path(__file__).resolve().parent.parent
S, SHOTS = api.SCALE, 1000


def gain(gate_model: str, gamma: float, seed: int = 0) -> dict:
    out = json.loads(
        api.replay_json(
            json.dumps(
                {
                    "dataset": "quiet",
                    "noise": "indep" if gamma else "off",
                    "gamma": gamma,
                    "gate_model": gate_model,
                    "seed": seed,
                }
            )
        )
    )
    return {
        **out["gain_ghz4"],
        "rmse_ind8": out["arms"]["IND8"]["rmse"],
        "rmse_ghz4": out["arms"]["GHZ4"]["rmse"],
    }


def main() -> None:
    ideal_vis = {("ghz", 1): 1.0, ("ghz", 2): 1.0, ("ghz", 4): 1.0, ("mp", 4): 1.0}
    _, f = data.load("storm")
    exact = replay.track(f, S, SHOTS, ideal_vis, arms=("IND8", "GHZ4", "CASC"), exact=True)
    g4 = replay.metrics(f, exact["GHZ4"], S, 4)
    noisy = replay.track(f, S, SHOTS, ideal_vis, arms=("GHZ4", "CASC", "IND8"), replicates=200, seed=3)
    m4 = replay.metrics(f, noisy["GHZ4"], S, 4)
    setup = json.loads(api.challenge_setup_json("{}"))
    out = {
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "qiskit": qiskit.__version__,
        "numpy": np.__version__,
        "scale_rad_per_nt": S,
        "shots_per_register_per_minute": SHOTS,
        "ramsey_time_us_electron": model.ramsey_time_us(S),
        "ghz4_range_nt_per_minute": math.pi / (4 * S),
        "quiet_day_gain_ghz4_vs_8_independent": {
            "ideal": gain("none", 0.0),
            "ionq_aria1_documented": gain("aria-1", 0.0),
            "dephasing_0.05": gain("none", 0.05),
            "dephasing_0.10": gain("none", 0.10),
            "dephasing_0.20": gain("none", 0.20),
        },
        "crossover_gamma_fixed_interrogation": {str(n): model.crossover_gamma(n) for n in (2, 4, 8)},
        "storm_exact_means": {
            "ghz4_slips": int(g4["slips"][0]),
            "ghz4_wrong_minutes": int(g4["wrong"][0]),
            "ghz4_fringe_offsets": dict(Counter(np.round(g4["err"][0] / g4["spacing"]).astype(int).tolist())),
            "cascade_max_error_nt": float(np.abs(exact["CASC"][0] - f).max()),
            "ind8_max_error_nt": float(np.abs(exact["IND8"][0] - f).max()),
        },
        "storm_shot_noise_200_replays": {
            "ghz4_slips": dict(Counter(m4["slips"].tolist())),
            "ghz4_wrong_minutes_median": float(np.median(m4["wrong"])),
            "ghz4_wrong_minutes_range": [int(m4["wrong"].min()), int(m4["wrong"].max())],
            "cascade_slips_max": int(replay.metrics(f, noisy["CASC"], S, 1)["slips"].max()),
            "ind8_slips_max": int(replay.metrics(f, noisy["IND8"], S, 1)["slips"].max()),
        },
        "challenge_fixed_strategies": {c: v["mean_score"] for c, v in setup["always"].items()},
        "challenge_rounds_with_a_step_beyond_ghz4_range": [
            k + 1 for k in range(challenge.ROUNDS) if challenge.largest_step(k) > math.pi / (4 * S)
        ],
    }
    dest = ROOT / "results" / "headline_numbers.json"
    dest.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
