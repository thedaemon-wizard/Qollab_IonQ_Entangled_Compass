"""Replay on the real records, and the JSON interface against a local simulator."""

import json
import math
from collections import Counter

import numpy as np
import pytest
from qiskit.providers.basic_provider import BasicSimulator

from compass import api, data, replay

IDEAL = {("ghz", 1): 1.0, ("ghz", 2): 1.0, ("ghz", 4): 1.0, ("mp", 4): 1.0}


def test_records():
    t, f = data.load("storm")
    assert len(f) == 2880 and t[0] == "2024-05-10T00:00" and t[-1] == "2024-05-11T23:59"
    assert f[0] == pytest.approx(51324.01) and f[-1] == pytest.approx(51334.46)
    steps = np.abs(np.diff(f))
    assert steps.max() == pytest.approx(118.82, abs=1e-6) and t[int(steps.argmax()) + 1] == "2024-05-11T02:07"
    assert int((steps > math.pi / (4 * 0.02)).sum()) == 20
    t, f = data.load("quiet")
    assert len(f) == 1440 and np.ptp(f) == pytest.approx(30.207, abs=1e-3)


def test_storm_exact_means():
    """Without shot noise: GHZ-4 alone slips 20 times; the cascade and independent qubits never."""
    t, f = data.load("storm")
    est = replay.track(f, 0.02, 1000, IDEAL, arms=("IND8", "GHZ4", "CASC"), exact=True)
    g4 = replay.metrics(f, est["GHZ4"], 0.02, 4)
    assert int(g4["slips"][0]) == 20 and int(g4["wrong"][0]) == 1115
    offsets = Counter(np.round(g4["err"][0] / g4["spacing"]).astype(int).tolist())
    assert offsets == {0: 1764, -1: 973, -2: 98, 1: 29, 2: 15}
    assert t[int(np.argmax(np.round(g4["err"][0] / g4["spacing"]) != 0)) + 1] == "2024-05-10T21:47"
    for arm in ("IND8", "CASC"):
        assert np.abs(est[arm][0] - f).max() < 1e-6


def test_quiet_day_gain_matches_sqrt_n():
    _, f = data.load("quiet")
    est = replay.track(f, 0.02, 1000, IDEAL, arms=("IND8", "GHZ4"), replicates=32, seed=0)
    i8 = replay.metrics(f, est["IND8"], 0.02, 1)["rmse"]
    g4 = replay.metrics(f, est["GHZ4"], 0.02, 4)["rmse"]
    assert replay.mean_2se(i8)["mean"] == pytest.approx(1 / (0.02 * math.sqrt(4000)), abs=0.02)  # 0.7906
    assert replay.mean_2se(g4)["mean"] == pytest.approx(1 / (4 * 0.02 * math.sqrt(1000)), abs=0.01)  # 0.3953
    assert replay.mean_2se(i8 / g4)["mean"] == pytest.approx(2.0, abs=0.05)


@pytest.mark.parametrize("gamma", [0.05, 0.10, 0.20])
def test_dephasing_gain_follows_theory(gamma):
    out = json.loads(api.replay_json(json.dumps({"dataset": "quiet", "noise": "indep", "gamma": gamma})))
    g = out["gain_ghz4"]
    assert g["theory"] == pytest.approx(2 * math.exp(-3 * gamma), rel=1e-9)
    assert g["mean"] == pytest.approx(g["theory"], abs=0.05)


def test_run_on_local_simulator():
    b = BasicSimulator()
    out = json.loads(
        api.run_json(b, json.dumps({"dataset": "storm", "minute": "2024-05-10T21:47", "shots": 2000}))
    )
    assert out["layout"] == "A" and out["n_qubits"] == 17 and out["canary"] == 1.0
    assert out["dF_nT"] == pytest.approx(44.59, abs=1e-6)
    arms = out["arms"]
    assert abs(arms["CASC"]["error_nT"]) < 5 and abs(arms["IND2"]["error_nT"]) < 10
    assert arms["GHZ4"]["error_nT"] == pytest.approx(-2 * math.pi / (4 * 0.02), abs=5)  # one fringe off
    assert all(abs(r["z"]) < 5 for r in out["registers"])


def test_run_with_dephasing_layout_b():
    out = json.loads(
        api.run_json(
            BasicSimulator(),
            json.dumps({"dataset": "quiet", "minute": "2026-10-01T12:00", "noise": "indep", "gamma": 0.1}),
        )
    )
    assert out["layout"] == "B" and out["n_qubits"] == 21
    assert out["visibility"]["4"]["hat"] == pytest.approx(math.exp(-0.4), abs=0.08)


class _FakeIonQ:
    name = "ionq_simulator"

    def __init__(self):
        self.calls = 0

    def run(self, qc, shots):
        self.calls += 1
        return BasicSimulator().run(qc, shots=shots)


class _FakeQPU:
    name = "ionq_qpu.forte-1"


def test_one_ionq_job_per_run_and_no_hardware(monkeypatch):
    monkeypatch.setitem(api._jobs, "ionq", 0)
    ionq = _FakeIonQ()
    req = json.dumps({"dataset": "quiet", "minute": "2026-10-01T12:00", "shots": 200})
    first = json.loads(api.run_json(ionq, req))
    assert "error" not in first and first["backend"]["kind"] == "ionq"
    assert set(first["ops"]) <= {"rz", "cx", "h", "x", "measure"}
    second = json.loads(api.run_json(ionq, req))
    assert second["error"] == "one_job_per_run" and ionq.calls == 1
    assert json.loads(api.run_json(_FakeQPU(), req))["error"] == "hardware"


def test_storm_challenge_rounds_and_carry_over():
    setup = json.loads(api.challenge_setup_json("{}"))
    assert len(setup["rounds"]) == 12
    assert (
        setup["rounds"][0]["start"] == "2024-05-10T16:00" and setup["rounds"][-1]["end"] == "2024-05-11T15:59"
    )
    always = {c: v["mean_score"] for c, v in setup["always"].items()}
    assert always["CASC"] < always["IND8"] < always["GHZ4"]  # GHZ-4 alone is ruined by the jumps
    # round 3 (20:00-22:00) contains the 21:47 jump: GHZ-4 slips and the error carries over
    r = json.loads(api.challenge_json(json.dumps({"round": 2, "choice": "GHZ4", "offset_nt": 0.0})))
    assert r["result"]["slips"] >= 1 and abs(r["result"]["end_offset_nt"]) > 30
    nxt = json.loads(
        api.challenge_json(
            json.dumps({"round": 3, "choice": "IND8", "offset_nt": r["result"]["end_offset_nt"]})
        )
    )
    assert abs(nxt["result"]["end_offset_nt"]) < 5  # a wide-range sensor re-anchors
    # same start and random draws for every option
    assert nxt["others"]["IND8"]["score"] == pytest.approx(nxt["result"]["score"])


@pytest.mark.parametrize(
    ("gamma", "theory"), [(0.0, math.sqrt(2)), (math.log(2) / 6, 1.0), (0.2, math.sqrt(2) * math.exp(-0.6))]
)
def test_gain_over_standard_quantum_limit(gamma, theory):
    """The strong baseline: the SQL for the same 8 qubits x S shots. GHZ-4 beats it by sqrt(2)
    ideally, and no longer at gamma = ln 2 / 6."""
    out = json.loads(api.replay_json(json.dumps({"dataset": "quiet", "noise": "indep", "gamma": gamma})))
    g = out["sql"]["gain_ghz4"]
    assert g["theory"] == pytest.approx(theory, rel=1e-9)
    assert g["mean"] == pytest.approx(theory, abs=0.03)
    assert out["sql"]["nt"] == pytest.approx(math.exp(gamma) / (0.02 * math.sqrt(8000)), rel=1e-9)
