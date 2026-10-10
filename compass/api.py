"""The JSON interface the browser calls (strings in, strings out).

run_json is the only function that touches the backend Qollab injects: it submits ONE circuit
as ONE job. Everything else is numpy on recorded field data.
"""

from __future__ import annotations

import json
import math
import time

import numpy as np
from qiskit import transpile

from compass import circuits, data, model, replay
from compass.decode import decode
from compass.estimators import cascade, theta, var_theta, visibility, wrap

SCALE = 0.02  # rad per nT, fixed: the slip counts and ranges quoted in the app depend on it
SHOTS = [100, 200, 500, 1000, 2000]
GAMMA_MAX = 0.30
PRESETS = [
    {
        "dataset": "quiet",
        "minute": "2026-10-01T12:00",
        "note": "quiet field: every sensor is on the right fringe",
    },
    {"dataset": "storm", "minute": "2024-05-10T17:06", "note": "storm onset (+12.6 nT in one minute)"},
    {
        "dataset": "storm",
        "minute": "2024-05-10T21:47",
        "note": "first minute where GHZ-4 alone jumps a fringe (+44.6 nT)",
    },
    {
        "dataset": "storm",
        "minute": "2024-05-11T02:07",
        "note": "largest step (+118.8 nT): GHZ-4 alone is off by two fringes",
    },
]
_jobs = {"ionq": 0}


def _backend_kind(backend) -> str:
    name = (getattr(backend, "name", "") or "").lower()
    cls = type(backend).__name__.lower()
    module = type(backend).__module__.lower()
    if "qpu" in name:
        return "hardware"
    if "ionq" in name or module.startswith("qiskit_ionq"):
        return "ionq"
    if "braket" in cls or "braket" in module:
        return "braket"
    if name.startswith("fake") or "fake" in cls:
        return "ibm_fake"
    return "local"


def _noise_model_name(backend):
    opts = getattr(backend, "options", None)
    value = getattr(opts, "noise_model", None) if opts is not None else None
    return str(value) if value else None


def backend_info_json(backend) -> str:
    kind = _backend_kind(backend)
    return json.dumps(
        {
            "name": getattr(backend, "name", None) or type(backend).__name__,
            "kind": kind,
            "noise_model": _noise_model_name(backend),
            "default_shots": 200 if kind == "ionq" else 1000,
            "ionq_jobs_used": _jobs["ionq"],
        }
    )


def _minute_index(times, minute):
    if minute not in times:
        raise ValueError(f"minute {minute} is not in this record")
    i = times.index(minute)
    if i == 0:
        raise ValueError("pick a minute after the first one (the step is measured from the previous minute)")
    return i


def init_json() -> str:
    sets = {}
    for key, spec in data.DATASETS.items():
        times, f = data.load(key)
        steps = np.abs(np.diff(f))
        sets[key] = {
            "label": spec["label"],
            "minutes": len(f),
            "start": times[0],
            "end": times[-1],
            "range_nt": round(float(f.max() - f.min()), 2),
            "largest_step_nt": round(float(steps.max()), 2),
        }
    return json.dumps(
        {
            "datasets": sets,
            "presets": PRESETS,
            "scale": {
                "value": SCALE,
                "ramsey_us": round(model.ramsey_time_us(SCALE), 1),
                "ghz4_range_nt": round(math.pi / (4 * SCALE), 2),
            },
            "shots": SHOTS,
            "gamma_max": GAMMA_MAX,
            "documented_models": {"aria-1": model.IONQ_DOCUMENTED["aria-1"]["label"]},
            "crossover_gamma": {str(n): round(model.crossover_gamma(n), 4) for n in (2, 4, 8)},
        }
    )


def series_json(dataset: str) -> str:
    times, f = data.load(dataset)
    return json.dumps({"times": times, "F": [round(float(x), 3) for x in f]})


def _visibilities(gate_model: str, gamma: float, measured: dict | None) -> dict:
    """Visibility of each register type for the replay (GHZ m = 1, 2, 4 and multi-pass 4)."""
    if gate_model == "measured" and measured:
        base = {
            ("ghz", 1): measured["1"],
            ("ghz", 2): measured["2"],
            ("ghz", 4): measured["4"],
            ("mp", 4): measured.get("MP4", measured["1"]),
        }
        return {k: float(min(1.0, max(0.0, v))) for k, v in base.items()}
    rates = model.IONQ_DOCUMENTED.get(gate_model, {"r1": 0.0, "r2": 0.0})
    knob = gamma > 0
    vis = {}
    for m in (1, 2, 4):
        vis[("ghz", m)] = model.gate_visibility(
            m, rates["r1"], rates["r2"], knob
        ) * model.dephasing_visibility(m, gamma)
    vis[("mp", 4)] = (
        (1 - rates["r1"]) ** 2
        * ((1 - rates["r2"]) ** 2 if knob else 1.0)
        * model.dephasing_visibility(4, gamma)
    )
    return vis


def replay_json(params_json: str) -> str:
    p = json.loads(params_json)
    scale, shots = SCALE, int(p.get("shots", 1000))
    gamma = float(p.get("gamma", 0.0)) if p.get("noise") == "indep" else 0.0
    vis = _visibilities(p.get("gate_model", "none"), gamma, p.get("measured"))
    times, f = data.load(p.get("dataset", "quiet"))
    arms = ("IND8", "GHZ4", "CASC", "IND14", "MP4")
    t0 = time.time()
    est = replay.track(
        f, scale, shots, vis, arms=arms, replicates=int(p.get("replicates", 32)), seed=int(p.get("seed", 0))
    )
    out = {}
    m_max = {"IND8": 1, "GHZ4": 4, "CASC": 1, "IND14": 1, "MP4": 4}
    for a in arms:
        mt = replay.metrics(f, est[a], scale, m_max[a])
        out[a] = {
            "label": replay.ARMS[a]["label"],
            "qubits": replay.ARMS[a]["qubits"],
            "rmse": replay.mean_2se(mt["rmse"]),
            "rmse_ok": replay.mean_2se(mt["rmse_ok"]),
            "wrong_minutes": replay.mean_2se(mt["wrong"]),
            "slips": replay.mean_2se(mt["slips"]),
            "trace": [round(float(x), 3) for x in est[a][0]],
        }
    # gain on the minutes where GHZ-4 is on the right fringe, per replicate
    g4 = replay.metrics(f, est["GHZ4"], scale, 4)
    ok = np.where(np.round(g4["err"] / g4["spacing"]) != 0, np.nan, 1.0)
    i8 = replay.metrics(f, est["IND8"], scale, 1)["err"]
    gain = np.sqrt(np.nanmean((i8 * ok) ** 2, axis=1)) / np.sqrt(np.nanmean((g4["err"] * ok) ** 2, axis=1))
    ic = replay.metrics(f, est["IND14"], scale, 1)["rmse"] / replay.metrics(f, est["CASC"], scale, 1)["rmse"]
    return json.dumps(
        {
            "times": times,
            "F": [round(float(x), 3) for x in f],
            "arms": out,
            "gain_ghz4": {**replay.mean_2se(gain), "theory": 2 * vis[("ghz", 4)] / vis[("ghz", 1)]},
            "gain_cascade": {**replay.mean_2se(ic), "theory_ideal": 2 * math.sqrt(8 / 14)},
            "visibility": {f"{k[0]}{k[1]}": v for k, v in vis.items()},
            "band_nt": {
                "IND8": 1 / (scale * vis[("ghz", 1)] * math.sqrt(4 * shots)),
                "GHZ4": 1 / (4 * scale * vis[("ghz", 4)] * math.sqrt(shots)),
            },
            "fringe_nt": {"GHZ4": model.fringe_spacing_nt(4, scale)},
            "seconds": round(time.time() - t0, 3),
        }
    )


def _transpiled(qc, backend, kind):
    if kind in ("ionq", "braket"):
        return transpile(qc, basis_gates=["rz", "cx", "h", "x", "measure"], optimization_level=0)
    if kind == "ibm_fake":
        return transpile(qc, backend=backend, optimization_level=1, seed_transpiler=11)
    return transpile(qc, backend=backend, optimization_level=0)


def _dials(thetas: dict, vis: dict, delta: float) -> list[dict]:
    """Compass needles: angle = the measured phase atan2(<Y>, <X>) = m*delta mod 2 pi,
    length = the measured visibility; `true_deg` is where an ideal needle would point."""
    out = []
    for label, name in [("1", "1 qubit"), ("2", "GHZ-2"), ("4", "GHZ-4"), ("MP4", "1 qubit, 4 passes")]:
        if label not in thetas:
            continue
        angle, var, m = thetas[label]
        true = float(wrap(m * delta))
        out.append(
            {
                "label": name,
                "m": m,
                "angle_deg": math.degrees(angle),
                "true_deg": math.degrees(true),
                "length": vis[label]["hat"],
                "se_deg": math.degrees(math.sqrt(var)) if math.isfinite(var) else None,
                "wrapped": abs(m * delta) > math.pi,
            }
        )
    return out


def _fringes(scale: float, d_f: float, span_nt: float = 160.0, points: int = 321) -> dict:
    """Ideal X parity cos(m s dF) against the field step, for m = 1, 2, 4 (model curves)."""
    xs = np.linspace(-span_nt, span_nt, points)
    return {
        "dF": [round(float(x), 3) for x in xs],
        "curves": {str(m): [round(float(np.cos(m * scale * x)), 5) for x in xs] for m in (1, 2, 4)},
        "half_range_nT": {str(m): math.pi / (m * scale) for m in (1, 2, 4)},
        "this_minute_dF": d_f,
    }


def run_json(backend, params_json: str) -> str:
    p = json.loads(params_json)
    kind = _backend_kind(backend)
    if kind == "hardware":
        return json.dumps({"error": "hardware", "message": "This project runs on simulators only."})
    if kind == "ionq" and _jobs["ionq"] >= 1:
        return json.dumps(
            {
                "error": "one_job_per_run",
                "message": "IonQ allows one job per Run. Press Stop, then Run again for another minute.",
            }
        )
    scale, shots = SCALE, int(p.get("shots", 1000))
    gamma = float(p.get("gamma", 0.0)) if p.get("noise") == "indep" else 0.0
    times, f = data.load(p.get("dataset", "storm"))
    i = _minute_index(times, p["minute"])
    d_f = float(f[i] - f[i - 1])
    delta = scale * d_f
    lay = circuits.layout("B" if gamma > 0 else "A")
    qc = circuits.build(lay, delta, gamma)
    compiled = _transpiled(qc, backend, kind)
    if kind == "ionq":
        _jobs["ionq"] += 1
    t0 = time.time()
    counts = dict(backend.run(compiled, shots=shots).result().get_counts())
    wall = time.time() - t0
    dec = decode(counts, lay)
    regs = dec["registers"]
    rows = []
    for reg in lay.registers:
        v_model = circuits.model_visibility(reg, gamma)
        p_model = model.parity(reg.m, reg.basis, delta, v_model)
        r = regs[reg.name]
        se_model = math.sqrt(max(1e-12, 1 - p_model * p_model) / dec["shots"])
        rows.append(
            {
                "name": reg.name,
                "m": reg.m,
                "kind": reg.kind,
                "basis": reg.basis,
                "qubits": list(reg.qubits),
                "mean": r["mean"],
                "se": r["se"],
                "ideal_model": p_model,
                "z": (r["mean"] - p_model) / se_model,
            }
        )
    vis, thetas = {}, {}
    for label, xn, yn, m in [
        ("1", "G1X", "G1Y", 1),
        ("2", "G2X", "G2Y", 2),
        ("4", "G4X", "G4Y", 4),
        ("MP4", "MP4X", "MP4Y", 4),
    ]:
        if xn not in regs:
            continue
        x, y = regs[xn], regs[yn]
        knob_vis = model.dephasing_visibility(m, gamma) if gamma > 0 else 1.0
        vhat = visibility(x["mean"], y["mean"], x["var"], y["var"])
        vis[label] = {"hat": vhat, "gate_only": vhat / knob_vis, "model": knob_vis}
        thetas[label] = (
            float(theta(x["mean"], y["mean"])),
            var_theta(x["mean"], y["mean"], x["var"], y["var"]),
            m,
        )
    arms = {
        "IND2": thetas["1"][0],
        "GHZ4": thetas["4"][0] / 4,
        "CASC": float(cascade(thetas["1"][0], thetas["2"][0], thetas["4"][0])),
    }
    if "MP4" in thetas:
        arms["MP4"] = thetas["MP4"][0] / 4
    se = {
        "IND2": math.sqrt(thetas["1"][1]),
        "GHZ4": math.sqrt(thetas["4"][1]) / 4,
        "CASC": math.sqrt(thetas["4"][1]) / 4,
    }
    if "MP4" in thetas:
        se["MP4"] = math.sqrt(thetas["MP4"][1]) / 4
    v1, v4 = vis["1"]["hat"], vis["4"]["hat"]
    return json.dumps(
        {
            "backend": {
                "name": getattr(backend, "name", None) or type(backend).__name__,
                "kind": kind,
                "noise_model": _noise_model_name(backend),
            },
            "layout": lay.name,
            "n_qubits": lay.n_qubits,
            "shots": dec["shots"],
            "wall_s": round(wall, 3),
            "minute": p["minute"],
            "dataset": p.get("dataset", "storm"),
            "dF_nT": d_f,
            "delta_rad": delta,
            "scale": scale,
            "gamma": gamma,
            "canary": dec["canary"],
            "registers": rows,
            "visibility": vis,
            "arms": {
                k: {
                    "delta_hat": v,
                    "se_rad": se[k],
                    "estimate_nT": v / scale,
                    "error_nT": v / scale - d_f,
                    "se_nT": se[k] / scale,
                }
                for k, v in arms.items()
            },
            "gain_from_visibility": 2 * v4 / v1 if v1 > 0 else None,
            "dials": _dials(thetas, vis, delta),
            "fringes": _fringes(scale, d_f),
            "ops": {k: int(v) for k, v in compiled.count_ops().items()},
            "depth": compiled.depth(),
            "ionq_jobs_used": _jobs["ionq"],
        }
    )


def circuit_text_json(layout_name: str) -> str:
    """Qiskit's text drawing of the packed circuit (for the Method view), at delta = 0.3 rad."""
    lay = circuits.layout(layout_name)
    qc = circuits.build(lay, 0.3, 0.1 if layout_name == "B" else 0.0)
    return json.dumps(
        {
            "layout": layout_name,
            "n_qubits": lay.n_qubits,
            "text": str(qc.draw(output="text", fold=-1)),
            "ops": {k: int(v) for k, v in qc.count_ops().items()},
            "registers": [
                {
                    "name": r.name,
                    "kind": r.kind,
                    "m": r.m,
                    "basis": r.basis,
                    "qubits": list(r.qubits),
                    "ancilla": r.ancilla,
                }
                for r in lay.registers
            ],
        }
    )


def _gain_quiet(vis: dict, scale: float = 0.02, shots: int = 1000) -> dict:
    _, f = data.load("quiet")
    est = replay.track(f, scale, shots, vis, arms=("IND8", "GHZ4"), replicates=16, seed=1)
    i8 = replay.metrics(f, est["IND8"], scale, 1)["rmse"]
    g4 = replay.metrics(f, est["GHZ4"], scale, 4)["rmse"]
    return {**replay.mean_2se(i8 / g4), "theory": 2 * vis[("ghz", 4)] / vis[("ghz", 1)]}


def overview_json() -> str:
    """The four answers on the Overview, computed when the page opens (model replay)."""
    t0 = time.time()
    ideal = _gain_quiet(_visibilities("none", 0.0, None))
    aria = _gain_quiet(_visibilities("aria-1", 0.0, None))
    deph = _gain_quiet(_visibilities("none", 0.2, None))
    _, f = data.load("storm")
    est = replay.track(
        f, 0.02, 1000, _visibilities("none", 0.0, None), arms=("GHZ4", "CASC"), replicates=8, seed=2
    )
    g4 = replay.metrics(f, est["GHZ4"], 0.02, 4)
    casc = replay.metrics(f, est["CASC"], 0.02, 1)
    return json.dumps(
        {
            "ideal": ideal,
            "aria1": aria,
            "dephasing_0_2": deph,
            "storm": {
                "ghz4_slips": replay.mean_2se(g4["slips"]),
                "ghz4_wrong_minutes": replay.mean_2se(g4["wrong"]),
                "cascade_slips": replay.mean_2se(casc["slips"]),
                "scale": 0.02,
                "shots": 1000,
            },
            "seconds": round(time.time() - t0, 2),
        }
    )


def challenge_json(params_json: str) -> str:
    """One round of the storm challenge: the player's pick and, from the same starting point and
    the same random draws, what the other two sensors would have done."""
    from compass import challenge

    p = json.loads(params_json)
    k = int(p["round"])
    shots = int(p.get("shots", 1000))
    vis = _visibilities(p.get("gate_model", "none"), 0.0, p.get("measured"))
    offset = float(p.get("offset_nt", 0.0))
    seed = int(p.get("seed", 7))
    results = {c: challenge.play(k, c, offset, vis, SCALE, shots, seed) for c in challenge.CHOICES}
    times, _ = challenge._window(k)
    return json.dumps(
        {
            "round": k,
            "rounds": challenge.ROUNDS,
            "start": times[1],
            "end": times[-1],
            "choice": p["choice"],
            "result": results[p["choice"]],
            "others": {
                c: {kk: v for kk, v in r.items() if kk not in ("times", "error_nt")}
                for c, r in results.items()
            },
            "largest_step_nt": challenge.largest_step(k),
            "next_round_previous_step_nt": challenge.largest_step(k) if k + 1 < challenge.ROUNDS else None,
            "choices": challenge.CHOICES,
        }
    )


def challenge_setup_json(params_json: str) -> str:
    """Round list and the three 'always the same sensor' benchmarks."""
    from compass import challenge

    p = json.loads(params_json)
    shots = int(p.get("shots", 1000))
    vis = _visibilities(p.get("gate_model", "none"), 0.0, p.get("measured"))
    seed = int(p.get("seed", 7))
    rounds = []
    for k in range(challenge.ROUNDS):
        times, _ = challenge._window(k)
        rounds.append({"start": times[1], "end": times[-1]})
    return json.dumps(
        {
            "rounds": rounds,
            "choices": challenge.CHOICES,
            "always": {c: challenge.always(c, vis, SCALE, shots, seed) for c in challenge.CHOICES},
            "scale": SCALE,
            "ghz4_range_nt": math.pi / (4 * SCALE),
        }
    )
