"""Circuits, decoding and estimators against exact values (test vectors checked independently
in Qiskit 2.5.2 / Aer 0.17.2 on 2026-10-10)."""

import math

import numpy as np
import pytest
from qiskit.quantum_info import Statevector

from compass import circuits, estimators, model
from compass.decode import BitOrderError, decode


def parities_exact(lay, delta, gamma=0.0):
    """Mean parity of each register from the exact output distribution (density of keys)."""
    qc = circuits.build(lay, delta, gamma).remove_final_measurements(inplace=False)
    probs = Statevector(qc).probabilities_dict()
    out = {}
    n = lay.n_qubits
    for reg in lay.registers:
        s = 0.0
        for key, p in probs.items():
            ones = sum(key[n - 1 - q] == "1" for q in reg.qubits)
            s += p if ones % 2 == 0 else -p
        out[reg.name] = s
    canary = sum(p for k, p in probs.items() if k[n - 1] == "1")
    return out, canary


@pytest.mark.parametrize(
    ("layout", "gamma", "expected"),
    [
        (
            "A",
            0.0,
            {
                "G1X": 0.9553364891,
                "G1Y": 0.2955202067,
                "G2X": 0.8253356149,
                "G2Y": 0.5646424734,
                "G4X": 0.3623577545,
                "G4Y": 0.9320390860,
                "MP4X": 0.3623577545,
                "MP4Y": 0.9320390860,
            },
        ),
        (
            "B",
            0.05,
            {
                "G1X": 0.9087441788,
                "G1Y": 0.2811075161,
                "G2X": 0.7467945468,
                "G2Y": 0.5109096377,
                "G4X": 0.2966734372,
                "G4Y": 0.7630890628,
            },
        ),
    ],
)
def test_packed_circuit_parities(layout, gamma, expected):
    lay = circuits.layout(layout)
    got, canary = parities_exact(lay, 0.3, gamma)
    assert canary == pytest.approx(1.0, abs=1e-12)
    for name, value in expected.items():
        assert got[name] == pytest.approx(value, abs=1e-9), name


def test_layout_sizes_fit_every_simulator():
    assert circuits.layout("A").n_qubits == 17
    assert circuits.layout("B").n_qubits == 21  # built-in simulator: 24, IonQ Aria models: 25


def test_closed_form_parities():
    # T1: delta = 0.1, gamma = 0.05
    for m, v, px, py in [
        (4, 0.8187307531, 0.7541009613, 0.3188287727),
        (1, 0.9512294245, 0.9464772395, 0.0949644835),
        (2, 0.9048374180, 0.8868009118, 0.1797634443),
    ]:
        vis = model.dephasing_visibility(m, 0.05)
        assert vis == pytest.approx(v, abs=1e-9)
        assert model.parity(m, "X", 0.1, vis) == pytest.approx(px, abs=1e-9)
        assert model.parity(m, "Y", 0.1, vis) == pytest.approx(py, abs=1e-9)


def test_documented_gate_noise_visibilities():
    a1, a2 = model.IONQ_DOCUMENTED["aria-1"], model.IONQ_DOCUMENTED["aria-2"]
    assert model.gate_visibility(1, a1["r1"], a1["r2"]) == pytest.approx(0.999000, abs=5e-7)
    assert model.gate_visibility(2, a1["r1"], a1["r2"]) == pytest.approx(0.985221, abs=5e-7)
    assert model.gate_visibility(4, a1["r1"], a1["r2"]) == pytest.approx(0.958229, abs=5e-7)
    assert model.gate_visibility(4, a2["r1"], a2["r2"]) == pytest.approx(0.942244, abs=5e-7)
    reg = circuits.layout("A").register("MP4X")
    assert circuits.model_visibility(reg, r1=a1["r1"], r2=a1["r2"]) == pytest.approx(0.999000, abs=5e-7)


def test_decode_by_position():
    lay = circuits.layout("A")
    counts = {"00000000000000001": 600, "10000100110001011": 400}
    got = decode(counts, lay)
    means = {k: v["mean"] for k, v in got["registers"].items()}
    assert means == pytest.approx(
        {"G1X": 0.2, "G1Y": 1.0, "G2X": 0.2, "G2Y": 1.0, "G4X": 1.0, "G4Y": 0.2, "MP4X": 1.0, "MP4Y": 0.2}
    )
    assert got["canary"] == 1.0
    with pytest.raises(BitOrderError, match=r"canary fraction 0\.400"):
        decode({k[::-1]: v for k, v in counts.items()}, lay)
    spaced = {k[:8] + " " + k[8:]: v for k, v in counts.items()}
    assert decode(spaced, lay)["registers"]["G4Y"]["mean"] == pytest.approx(0.2)


def test_estimators():
    def means(delta):
        return {m: (math.cos(m * delta), math.sin(m * delta)) for m in (1, 2, 4)}

    for delta, ghz_alone in [(0.123, 0.123), (2.9, 2.9 - math.pi), (-3.0, -3.0 + math.pi)]:
        th = {m: estimators.theta(*xy) for m, xy in means(delta).items()}
        assert float(estimators.cascade(th[1], th[2], th[4])) == pytest.approx(delta, abs=1e-12)
        assert th[4] / 4 == pytest.approx(ghz_alone, abs=1e-12)


def test_delta_method():
    s = 1000
    x, y = 0.9, 0.3
    vx, vy = (1 - x * x) / s, (1 - y * y) / s
    assert estimators.var_theta(x, y, vx, vy) == pytest.approx(9.311111e-4, rel=1e-6)
    assert estimators.visibility(x, y, vx, vy) == pytest.approx(0.948103, abs=1e-6)


def test_wrap_range():
    xs = np.linspace(-20, 20, 401)
    w = estimators.wrap(xs)
    assert (w >= -math.pi).all() and (w < math.pi).all()
    assert np.allclose(np.cos(w), np.cos(xs)) and np.allclose(np.sin(w), np.sin(xs))
