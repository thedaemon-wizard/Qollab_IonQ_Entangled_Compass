"""Recompute the model-replay numbers the README quotes (local; no backend needed).

Usage: PYTHONPATH=. python scripts/headline_numbers.py  -> results/headline_numbers.json

Covered: the quiet-day gains (against the matched sensor and the SQL), the storm (exact means,
200 replays, the 3D compass replay and the Overview's quick estimate), the challenge strategies,
the two observatories, the quiet-day record itself, and the standard errors of the visibilities
of the recorded IonQ Aria 1 run. Not covered: the circuit runs in "Where it ran", which come from
results/qollab/*.json (values recorded on Qollab).
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
        "sql_nt": out["sql"]["nt"],
        "gain_over_sql": out["sql"]["gain_ghz4"],
    }


CHALLENGE_SEEDS = range(7, 13)  # the app plays seed 7
STORMY_ROUNDS = (3, 4, 6, 8, 9)  # rounds with a one-minute step beyond GHZ-4's range (checked below)


def game(picks: list[str], seed: int) -> float:
    """Mean score of one challenge game played with the app's own rules (api.challenge_json)."""
    offset, previous, scores = 0.0, None, []
    for k, choice in enumerate(picks):
        params = {"round": k, "choice": choice, "offset_nt": offset, "previous_choice": previous}
        params["seed"] = seed
        r = json.loads(api.challenge_json(json.dumps(params)))["result"]
        previous, offset = choice, r["end_offset_nt"]
        scores.append(r["score"])
    return float(np.mean(scores))


def reactive_game(seed: int) -> float:
    """Cascade after a round whose largest step was beyond GHZ-4's range, GHZ-4 otherwise."""
    rng = math.pi / (4 * S)
    after = ["CASC" if challenge.largest_step(k - 1) > rng else "GHZ4" for k in range(1, challenge.ROUNDS)]
    picks = ["GHZ4", *after]
    return game(picks, seed)


def challenge_strategies() -> dict:
    switch_from_3 = ["GHZ4", "GHZ4"] + ["CASC"] * (challenge.ROUNDS - 2)
    hindsight = ["CASC" if k + 1 in STORMY_ROUNDS else "GHZ4" for k in range(challenge.ROUNDS)]
    fixed = {
        s: json.loads(api.challenge_setup_json(json.dumps({"seed": s})))["always"] for s in CHALLENGE_SEEDS
    }
    out = {
        "score": "mean over the 12 rounds of RMS error x sqrt(qubits / 8); lower is better",
        "seeds": list(CHALLENGE_SEEDS),
        "always_by_seed": {str(s): {c: v["mean_score"] for c, v in a.items()} for s, a in fixed.items()},
        "ghz4_rounds_1_2_then_cascade_by_seed": {str(s): game(switch_from_3, s) for s in CHALLENGE_SEEDS},
        "hindsight_cascade_in_stormy_rounds_by_seed": {str(s): game(hindsight, s) for s in CHALLENGE_SEEDS},
        "reactive_cascade_after_a_step_beyond_range_seed_7": reactive_game(7),
    }
    return out


def storm3d_summary(f) -> dict:
    """The replay the 3D compass shows and how all 32 replays (seed 0) are spread."""
    shown = json.loads(api.storm3d_json("{}"))
    vis = api._visibilities("none", 0.0, None)
    names = tuple(a for a, _, _ in api.STORM3D_ARMS)
    est = replay.track(f, S, SHOTS, vis, arms=names, replicates=32, seed=0)
    g4 = replay.metrics(f, est["GHZ4"], S, 4)
    pairs = Counter(zip(g4["slips"].tolist(), g4["wrong"].tolist(), strict=True))
    return {
        "seed": shown["seed"],
        "replays": shown["replay"]["of"],
        "shown_replay": shown["replay"]["shown"],
        "shown_ghz4": shown["totals"]["GHZ4"],
        "mean_ghz4_slips": shown["replay"]["mean_slips"],
        "mean_ghz4_wrong_minutes": shown["replay"]["mean_wrong"],
        "ghz4_outcomes": [
            {"fringe_changes": s, "wrong_minutes": w, "replays": n} for (s, w), n in sorted(pairs.items())
        ],
    }


def overview_numbers() -> dict:
    """The Overview tiles: 16 quiet-day replays (seed 1) and a quick 8-replay storm estimate (seed 2)."""
    o = json.loads(api.overview_json())
    return {
        "quiet_gain_ideal_16_replays": {k: o["ideal"][k] for k in ("mean", "two_se")},
        "quiet_gain_aria1_16_replays": {k: o["aria1"][k] for k in ("mean", "two_se")},
        "quiet_gain_dephasing_0.20_16_replays": {k: o["dephasing_0_2"][k] for k in ("mean", "two_se")},
        "storm_ghz4_wrong_minutes_8_replays": o["storm"]["ghz4_wrong_minutes"],
        "storm_ghz4_slips_8_replays": o["storm"]["ghz4_slips"],
    }


def onset_1706() -> dict:
    """True one-minute changes at 17:06 UTC on 10 May 2024 (the twin circuit's minute)."""
    times, f_a, f_b = data.load_pair()
    i = times.index("2024-05-10T17:06")
    a, b = float(f_a[i] - f_a[i - 1]), float(f_b[i] - f_b[i - 1])
    return {"boulder_nt": a, "tucson_nt": b, "difference_nt": a - b, "sum_nt": a + b}


def first_step_beyond_range(times, f) -> dict:
    d = np.diff(f)
    i = int(np.flatnonzero(np.abs(d) > math.pi / (4 * S))[0])
    return {"utc": times[i + 1], "step_nt": float(d[i])}


def quiet_record() -> dict:
    """How quiet the quiet day is, from its own record (no geomagnetic index was checked)."""
    times, f = data.load("quiet")
    _, storm = data.load("storm")
    return {
        "date": times[0][:10],
        "range_nt": float(f.max() - f.min()),
        "largest_one_minute_step_nt": float(np.abs(np.diff(f)).max()),
        "storm_range_nt": float(storm.max() - storm.min()),
        "storm_largest_one_minute_step_nt": float(np.abs(np.diff(storm)).max()),
    }


def recorded_visibility_se() -> dict:
    """Delta-method standard error of each visibility V = sqrt(x^2 + y^2) of the recorded IonQ Aria 1
    run (results/qollab/compass_runs_20261010.json, 13:57 UTC): SE(V) = sqrt(x^2 sx^2 + y^2 sy^2) / V."""
    path = ROOT / "results" / "qollab" / "compass_runs_20261010.json"
    runs = json.loads(path.read_text(encoding="utf-8"))
    run = next(r for r in runs["runs"] if r["utc"] == "2026-10-10T13:57Z")
    par = run["register_parities"]
    out = {"run_utc": run["utc"], "shots": run["shots"]}
    for name, key in (("GHZ-1", "G1"), ("GHZ-2", "G2"), ("GHZ-4", "G4")):
        (x, sx), (y, sy) = par[key + "X"], par[key + "Y"]
        v = math.hypot(x, y)
        out[name] = {"visibility": v, "se": math.sqrt((x * sx) ** 2 + (y * sy) ** 2) / v}
    return out


def main() -> None:
    ideal_vis = {("ghz", 1): 1.0, ("ghz", 2): 1.0, ("ghz", 4): 1.0, ("mp", 4): 1.0}
    storm_times, f = data.load("storm")
    exact = replay.track(f, S, SHOTS, ideal_vis, arms=("IND8", "GHZ4", "CASC"), exact=True)
    g4 = replay.metrics(f, exact["GHZ4"], S, 4)
    noisy = replay.track(f, S, SHOTS, ideal_vis, arms=("GHZ4", "CASC", "IND8"), replicates=200, seed=3)
    m4 = replay.metrics(f, noisy["GHZ4"], S, 4)
    setup = json.loads(api.challenge_setup_json("{}"))
    stormy = [k + 1 for k in range(challenge.ROUNDS) if challenge.largest_step(k) > math.pi / (4 * S)]
    if tuple(stormy) != STORMY_ROUNDS:
        raise SystemExit(f"stormy rounds changed: {stormy}")
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
            "ionq_aria1_documented_plus_dephasing_0.20": gain("aria-1", 0.20),
        },
        "crossover_gamma_fixed_interrogation": {str(n): model.crossover_gamma(n) for n in (2, 4, 8)},
        "crossover_gamma_vs_sql_ghz4": math.log(2) / 6,
        "storm_exact_means": {
            "ghz4_slips": int(g4["slips"][0]),
            "ghz4_wrong_minutes": int(g4["wrong"][0]),
            "ghz4_fringe_offsets": dict(Counter(np.round(g4["err"][0] / g4["spacing"]).astype(int).tolist())),
            "cascade_max_error_nt": float(np.abs(exact["CASC"][0] - f).max()),
            "ind8_max_error_nt": float(np.abs(exact["IND8"][0] - f).max()),
            "first_step_beyond_ghz4_range": first_step_beyond_range(storm_times, f),
        },
        "storm_3d_compass_replays": storm3d_summary(f),
        "overview_tiles": overview_numbers(),
        "storm_shot_noise_200_replays": {
            "ghz4_slips": dict(Counter(m4["slips"].tolist())),
            "ghz4_wrong_minutes_median": float(np.median(m4["wrong"])),
            "ghz4_wrong_minutes_range": [int(m4["wrong"].min()), int(m4["wrong"].max())],
            "cascade_slips_max": int(replay.metrics(f, noisy["CASC"], S, 1)["slips"].max()),
            "ind8_slips_max": int(replay.metrics(f, noisy["IND8"], S, 1)["slips"].max()),
        },
        "two_observatories": {
            k: v
            for k, v in json.loads(api.twin_replay_json("{}")).items()
            if k in ("rmse", "gain", "steps", "sql_difference_nt")
        },
        "two_observatories_onset_1706": onset_1706(),
        "challenge_fixed_strategies": {c: v["mean_score"] for c, v in setup["always"].items()},
        "challenge_rounds_with_a_step_beyond_ghz4_range": stormy,
        "challenge_strategies": challenge_strategies(),
        "quiet_day_record": quiet_record(),
        "recorded_ionq_aria1_visibility_se": recorded_visibility_se(),
    }
    dest = ROOT / "results" / "headline_numbers.json"
    dest.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
