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
    g = r["gain_ghz4"]
    assert f"GHZ-4 gain over 8 independent qubits {g['mean']:.2f} ± {g['two_se']:.2f}" in line
