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

from compass import circuits, console, data, model, replay, twin
from compass.decode import BitOrderError, decode
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
# Jobs submitted in this Run to backends that allow only one (IonQ, and anything unrecognised).
_jobs = {"guarded": 0}
GUARDED = ("ionq", "unknown")


def _backend_kind(backend) -> str:
    """Simulators this app knows; hardware is refused; anything else is run with care (one job)."""
    name = (getattr(backend, "name", "") or "").lower()
    cls = type(backend).__name__.lower()
    module = type(backend).__module__.lower()
    if "qpu" in name:
        return "hardware"
    if "ionq" in name or module.startswith("qiskit_ionq"):
        return "ionq" if "simulator" in name else "hardware"
    if "braket" in cls or "braket" in module:
        return "braket" if "local" in cls else "hardware"
    if name.startswith("fake") or cls.startswith("fake"):
        return "ibm_fake"
    if cls in ("basicsimulator", "aersimulator", "statevectorsimulator") or name in (
        "basic_simulator",
        "aer_simulator",
    ):
        return "local"
    return "unknown"


def _guard(kind: str):
    """None if a job may be submitted; otherwise the error to return."""
    if kind == "hardware":
        return {"error": "hardware", "message": "This project runs on simulators only."}
    if kind in GUARDED and _jobs["guarded"] >= 1:
        return {
            "error": "one_job_per_run",
            "message": "This backend allows one job per Run. Press Stop, then Run again for another minute.",
        }
    return None


def _shots(kind: str, requested: int) -> int:
    # IBM noise models run in Aer inside the browser: keep them short.
    return min(requested, 200) if kind == "ibm_fake" else requested


def _finite(obj):
    """JSON has no Infinity or NaN: send null instead (the UI shows a dash)."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _finite(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_finite(v) for v in obj]
    return obj


def _noise_model_name(backend):
    opts = getattr(backend, "options", None)
    value = getattr(opts, "noise_model", None) if opts is not None else None
    return str(value) if value else None


def backend_info_json(backend) -> str:
    kind = _backend_kind(backend)
    info = {
        "name": getattr(backend, "name", None) or type(backend).__name__,
        "kind": kind,
        "noise_model": _noise_model_name(backend),
        "default_shots": 200 if kind in ("ionq", "ibm_fake", "unknown") else 1000,
        "guarded_jobs_used": _jobs["guarded"],
    }
    info["console_line"] = console.started(info)
    return json.dumps(info)


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
                # half-range of one GHZ-m reading per minute, pi / (m s), for the figures
                "range_nt": {str(m): round(math.pi / (m * SCALE), 2) for m in (1, 2, 4)},
            },
            "qubits": {
                "A": circuits.layout("A").n_qubits,
                "B": circuits.layout("B").n_qubits,
                "twin": twin.N_QUBITS,
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
        # measured gate-only visibilities, times the dephasing chosen for this replay
        base = {
            ("ghz", 1): measured["1"],
            ("ghz", 2): measured["2"],
            ("ghz", 4): measured["4"],
            ("mp", 4): measured.get("MP4", measured["1"]),
        }
        return {
            (kind, m): float(min(1.0, max(0.0, v))) * model.dephasing_visibility(m, gamma)
            for (kind, m), v in base.items()
        }
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
    # Standard quantum limit for the same 8 qubits x S shots: the best any unentangled strategy can
    # reach (each qubit read at its most sensitive point, same visibility as a single qubit here).
    sql_nt = 1 / (scale * vis[("ghz", 1)] * math.sqrt(8 * shots))
    ghz_ok = np.sqrt(np.nanmean((g4["err"] * ok) ** 2, axis=1))
    result = (
        {
            "times": times,
            "F": [round(float(x), 3) for x in f],
            "arms": out,
            "gain_ghz4": {**replay.mean_2se(gain), "theory": 2 * vis[("ghz", 4)] / vis[("ghz", 1)]},
            "gain_cascade": {**replay.mean_2se(ic), "theory_ideal": 2 * math.sqrt(8 / 14)},
            "sql": {
                "nt": sql_nt,
                "gain_ghz4": {
                    **replay.mean_2se(sql_nt / ghz_ok),
                    "theory": math.sqrt(2) * vis[("ghz", 4)] / vis[("ghz", 1)],
                },
            },
            "visibility": {f"{k[0]}{k[1]}": v for k, v in vis.items()},
            "band_nt": {
                "IND8": 1 / (scale * vis[("ghz", 1)] * math.sqrt(4 * shots)),
                "GHZ4": 1 / (4 * scale * vis[("ghz", 4)] * math.sqrt(shots)),
            },
            "fringe_nt": {"GHZ4": model.fringe_spacing_nt(4, scale)},
            "seconds": round(time.time() - t0, 3),
        }
    )
    result["console_line"] = console.replay(p, result)
    return json.dumps(result)


STORM3D_ARMS = (  # arm, needle register m, fringe range m (the cascade reads with the 1-qubit range)
    ("IND8", 1, 1),
    ("GHZ4", 4, 4),
    ("CASC", 4, 1),
)


def storm3d_json(params_json: str) -> str:
    """Minute by minute, what each sensor's needle shows, for the 3D compass (one model replay).

    `true_phase` is the phase the field step turns the needle register by, m s (F_t - previous
    estimate), not wrapped: it can exceed half a turn. `reading` is the angle the register can
    read back, that phase wrapped to [-pi, pi) plus shot noise (recovered from the replay's own
    estimate). `fringe` is how many fringe spacings the estimate is off; a change is a slip.
    """
    p = json.loads(params_json)
    dataset, shots, seed = p.get("dataset", "storm"), int(p.get("shots", 1000)), int(p.get("seed", 0))
    replicates = int(p.get("replicates", 32))
    times, f = data.load(dataset)
    vis = _visibilities("none", 0.0, None)
    names = tuple(a for a, _, _ in STORM3D_ARMS)
    est = replay.track(f, SCALE, shots, vis, arms=names, replicates=replicates, seed=seed)
    # Show the replay closest to the average of all of them for GHZ-4 (slips and wrong minutes),
    # so the one animation is typical rather than lucky or unlucky.
    g4 = replay.metrics(f, est["GHZ4"], SCALE, 4)
    sl, wr = g4["slips"].astype(float), g4["wrong"].astype(float)
    score = ((sl - sl.mean()) / max(sl.std(), 1e-9)) ** 2 + ((wr - wr.mean()) / max(wr.std(), 1e-9)) ** 2
    k = int(np.argmin(score))
    arms, totals = {}, {}
    for name, m, m_range in STORM3D_ARMS:
        e = est[name][k]
        true_phase = np.concatenate([[0.0], m * SCALE * (f[1:] - e[:-1])])
        reading = np.concatenate([[0.0], wrap(m * SCALE * np.diff(e))])
        mt = replay.metrics(f, est[name][k : k + 1], SCALE, m_range)
        fringe = np.concatenate([[0], np.round(mt["err"][0] / mt["spacing"]).astype(int)])
        slips = np.concatenate([[0], np.cumsum(np.diff(fringe) != 0)])
        arms[name] = {
            "label": replay.ARMS[name]["label"],
            "m": m,
            "true_phase": [round(float(x), 3) for x in true_phase],
            "reading": [round(float(x), 3) for x in reading],
            "fringe": [int(x) for x in fringe],
            "slips_so_far": [int(x) for x in slips],
        }
        totals[name] = {"slips": int(slips[-1]), "wrong_minutes": int((fringe != 0).sum())}
    out = {
        "dataset": dataset,
        "label": data.DATASETS[dataset]["label"],
        "times": times,
        "dF_nT": [0.0] + [round(float(x), 2) for x in np.diff(f)],
        "scale": SCALE,
        "shots": shots,
        "seed": seed,
        "replay": {
            "shown": k + 1,
            "of": replicates,
            "mean_slips": float(sl.mean()),
            "mean_wrong": float(wr.mean()),
        },
        "arms": arms,
        "totals": totals,
    }
    out["console_line"] = console.storm3d(out)
    return json.dumps(out)


def _transpiled(qc, backend, kind):
    if kind in ("ionq", "braket", "unknown"):
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
    refused = _guard(kind)
    if refused:
        return json.dumps(refused)
    scale, shots = SCALE, _shots(kind, int(p.get("shots", 1000)))
    gamma = float(p.get("gamma", 0.0)) if p.get("noise") == "indep" else 0.0
    times, f = data.load(p.get("dataset", "storm"))
    i = _minute_index(times, p["minute"])
    d_f = float(f[i] - f[i - 1])
    delta = scale * d_f
    lay = circuits.layout("B" if gamma > 0 else "A")
    qc = circuits.build(lay, delta, gamma)
    compiled = _transpiled(qc, backend, kind)
    if kind in GUARDED:
        _jobs["guarded"] += 1
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
    result = (
        _finite(
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
                "guarded_jobs_used": _jobs["guarded"],
            }
        )
    )
    result["console_line"] = console.run(result)
    return json.dumps(result)


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
    sql = 1 / (scale * vis[("ghz", 1)] * math.sqrt(8 * shots))
    return {
        **replay.mean_2se(i8 / g4),
        "theory": 2 * vis[("ghz", 4)] / vis[("ghz", 1)],
        "over_sql": {**replay.mean_2se(sql / g4), "theory": math.sqrt(2) * vis[("ghz", 4)] / vis[("ghz", 1)]},
    }


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
    result = (
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
    result["console_line"] = console.overview(result)
    return json.dumps(result)


def challenge_json(params_json: str) -> str:
    """One round of the storm challenge: the player's pick and, from the same starting point and
    the same random draws, what the other two sensors would have done."""
    from compass import challenge

    p = json.loads(params_json)
    k = int(p["round"])
    shots = int(p.get("shots", 1000))
    vis = _visibilities(p.get("gate_model", "none"), 0.0, p.get("measured"))
    offset = float(p.get("offset_nt", 0.0))
    previous = p.get("previous_choice")
    seed = int(p.get("seed", 7))

    def start(c):  # keep the estimate when the sensor stays, a fresh absolute fix when it changes
        return offset if previous in (None, c) else 0.0

    results = {c: challenge.play(k, c, start(c), vis, SCALE, shots, seed) for c in challenge.CHOICES}
    times, _ = challenge._window(k)
    return json.dumps(
        {
            "round": k,
            "rounds": challenge.ROUNDS,
            "start": times[1],
            "end": times[-1],
            "choice": p["choice"],
            "reanchored": previous not in (None, p["choice"]) and offset != 0.0,
            "start_offset_nt": start(p["choice"]),
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


def twin_replay_json(params_json: str) -> str:
    """Track the Boulder - Tucson field difference through the storm with the entangled pair and
    with one qubit per site (same 4 qubits per shot)."""

    p = json.loads(params_json)
    shots = int(p.get("shots", 1000))
    times, f_a, f_b = data.load_pair()
    est = twin.track(
        f_a, f_b, SCALE, shots, replicates=int(p.get("replicates", 32)), seed=int(p.get("seed", 0))
    )
    g = f_a - f_b
    rmse = {k: np.sqrt(((v[:, 1:] - g[1:]) ** 2).mean(axis=1)) for k, v in est.items()}
    return json.dumps(
        {
            "times": times,
            "gradient": [round(float(x - g[0]), 3) for x in g],
            "boulder": [round(float(x - f_a[0]), 3) for x in f_a],
            "tucson": [round(float(x - f_b[0]), 3) for x in f_b],
            "traces": {k: [round(float(x - g[0]), 3) for x in v[0]] for k, v in est.items()},
            "rmse": {k: replay.mean_2se(v) for k, v in rmse.items()},
            "gain": {**replay.mean_2se(rmse["IND"] / rmse["DIFF"]), "theory": math.sqrt(2)},
            # best single-pass unentangled estimate of a difference with 4 qubits per shot
            "sql_difference_nt": 1 / (SCALE * math.sqrt(shots)),
            "steps": twin.step_statistics(f_a, f_b),
            "scale": SCALE,
            "shots": shots,
        }
    )


def twin_run_json(backend, params_json: str) -> str:
    """One minute of the twin sensors as ONE job (shares the one-IonQ-job guard with run_json)."""

    p = json.loads(params_json)
    kind = _backend_kind(backend)
    refused = _guard(kind)
    if refused:
        return json.dumps(refused)
    shots = _shots(kind, int(p.get("shots", 1000)))
    times, f_a, f_b = data.load_pair()
    i = _minute_index(times, p["minute"])
    d_a, d_b = float(f_a[i] - f_a[i - 1]), float(f_b[i] - f_b[i - 1])
    qc = twin.build(SCALE * d_a, SCALE * d_b)
    compiled = _transpiled(qc, backend, kind)
    if kind in GUARDED:
        _jobs["guarded"] += 1
    t0 = time.time()
    counts = dict(backend.run(compiled, shots=shots).result().get_counts())
    wall = time.time() - t0
    dec = twin.parities(counts)
    if dec["canary"] < 0.9:
        raise BitOrderError(
            f"canary fraction {dec['canary']:.3f}: the bit order of the result is not the expected one"
        )
    m = dec["mean"]
    reads = {
        "difference": (float(theta(m["DIFFX"], m["DIFFY"])) / SCALE, d_a - d_b),
        "sum": (float(theta(m["SUMX"], m["SUMY"])) / SCALE, d_a + d_b),
        "boulder": (float(theta(m["AX"], m["AY"])) / SCALE, d_a),
        "tucson": (float(theta(m["BX"], m["BY"])) / SCALE, d_b),
    }
    result = (
        _finite(
            {
                "backend": {"name": getattr(backend, "name", None) or type(backend).__name__, "kind": kind},
                "minute": p["minute"],
                "shots": dec["shots"],
                "wall_s": round(wall, 3),
                "canary": dec["canary"],
                "n_qubits": twin.N_QUBITS,
                "parities": m,
                "reads": {
                    k: {"estimate_nT": a, "true_nT": b, "error_nT": a - b} for k, (a, b) in reads.items()
                },
                "independent_difference_nT": reads["boulder"][0] - reads["tucson"][0],
                "ops": {k: int(v) for k, v in compiled.count_ops().items()},
                "guarded_jobs_used": _jobs["guarded"],
            }
        )
    )
    result["console_line"] = console.twin_run(result)
    return json.dumps(result)
