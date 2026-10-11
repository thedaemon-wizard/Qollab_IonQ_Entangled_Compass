"""Each result also returns one line for Qollab's run console, where judges look first."""

import json

from qiskit.providers.basic_provider import BasicSimulator

from compass import api


def test_circuit_run_reports_its_readings():
    params = {"minute": "2024-05-10T21:47", "dataset": "storm", "shots": 1000, "noise": "off"}
    r = json.loads(api.run_json(BasicSimulator(), json.dumps(params)))
    line = r["console_line"]
    assert line.startswith("[Entangled Compass] One-minute circuit on basic_simulator (17 qubits, 1000 shots")
    assert f"cascade error {r['arms']['CASC']['error_nT']:+.2f} nT" in line
    assert f"GHZ-4 alone {r['arms']['GHZ4']['error_nT']:+.2f} nT" in line


def test_replay_reports_the_gain():
    r = json.loads(api.replay_json(json.dumps({"dataset": "quiet", "shots": 1000, "noise": "off",
                                               "gate_model": "none", "replicates": 4})))
    line = r["console_line"]
    g, a = r["gain_ghz4"], r["arms"]
    # the gain is measured only on the right-fringe minutes; the line says so and adds whole-record RMS
    gain = f"{g['mean']:.2f}× (± {g['two_se']:.2f}, 2 SE over 4 replays)"
    assert f"On the minutes GHZ-4 stays on the right fringe it is {gain}" in line
    assert f"{a['GHZ4']['rmse']['mean']:.2f} nT for GHZ-4 alone" in line


def test_circuit_run_names_the_two_qubit_arm():
    params = {"minute": "2024-05-10T21:47", "dataset": "storm", "shots": 200, "noise": "off"}
    r = json.loads(api.run_json(BasicSimulator(), json.dumps(params)))
    assert f"2 independent qubits {r['arms']['IND2']['error_nT']:+.2f} nT" in r["console_line"]
    assert "one qubit" not in r["console_line"]


def test_challenge_round_and_twin_replay_reach_the_console():
    c = json.loads(api.challenge_json(json.dumps({"round": 0, "choice": "GHZ4"})))
    assert c["console_line"].startswith("[Entangled Compass] Storm challenge round 1 of 12")
    assert f"scores {c['result']['score']:.2f}" in c["console_line"]
    t = json.loads(api.twin_replay_json(json.dumps({"replicates": 4})))
    assert t["console_line"].startswith("[Entangled Compass] Two observatories")
    assert "2 SE over 4 replays" in t["console_line"]
