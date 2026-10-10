"""Regression tests for the issues found in the independent review (2026-10-10)."""

import json
import math

import pytest
from qiskit.providers.basic_provider import BasicSimulator

from compass import api


def test_measured_visibilities_keep_the_chosen_dephasing():
    measured = {"1": 1.0, "2": 1.0, "4": 1.0, "MP4": 1.0}
    out = json.loads(
        api.replay_json(
            json.dumps(
                {
                    "dataset": "quiet",
                    "noise": "indep",
                    "gamma": 0.2,
                    "gate_model": "measured",
                    "measured": measured,
                }
            )
        )
    )
    assert out["visibility"]["ghz4"] == pytest.approx(math.exp(-0.8), rel=1e-9)
    assert out["gain_ghz4"]["mean"] == pytest.approx(2 * math.exp(-0.6), abs=0.05)


def test_switching_sensor_reanchors_but_staying_keeps_the_offset():
    # round 8 (06:00-08:00) with GHZ-4 from 0 ends about two fringes (157 nT) off
    r8 = json.loads(api.challenge_json(json.dumps({"round": 7, "choice": "GHZ4", "offset_nt": 0.0})))
    off = r8["result"]["end_offset_nt"]
    assert abs(off) > 100
    switched = json.loads(
        api.challenge_json(
            json.dumps({"round": 8, "choice": "CASC", "offset_nt": off, "previous_choice": "GHZ4"})
        )
    )
    assert switched["reanchored"] and switched["start_offset_nt"] == 0.0
    assert abs(switched["result"]["end_offset_nt"]) < 5
    stayed = json.loads(
        api.challenge_json(
            json.dumps({"round": 8, "choice": "GHZ4", "offset_nt": off, "previous_choice": "GHZ4"})
        )
    )
    assert not stayed["reanchored"] and stayed["start_offset_nt"] == off


class _Named:
    def __init__(self, name, cls_name=None, module=None):
        self.name = name
        if cls_name or module:
            self.__class__ = type(cls_name or "X", (), {"__module__": module or __name__})
            self.name = name


@pytest.mark.parametrize(
    ("name", "cls_name", "module", "kind"),
    [
        ("ionq_simulator", None, None, "ionq"),
        ("ionq_qpu.forte-1", None, None, "hardware"),
        ("forte-1", "IonQBackend", "qiskit_ionq.ionq_backend", "hardware"),
        ("default", "BraketLocalBackend", "qiskit_braket_provider.providers", "braket"),
        ("SV1", "BraketAwsBackend", "qiskit_braket_provider.providers", "hardware"),
        ("fake_fez", "FakeFez", "qiskit_ibm_runtime.fake_provider", "ibm_fake"),
        ("basic_simulator", None, None, "local"),
        ("mystery_backend", None, None, "unknown"),
    ],
)
def test_backend_kinds(name, cls_name, module, kind):
    b = _Named(name, cls_name, module)
    assert api._backend_kind(b) == kind


def test_unknown_backends_get_one_job_and_hardware_none(monkeypatch):
    monkeypatch.setitem(api._jobs, "guarded", 0)

    class Mystery:
        name = "mystery_backend"

        def run(self, qc, shots):
            return BasicSimulator().run(qc, shots=shots)

    req = json.dumps({"dataset": "quiet", "minute": "2026-10-01T12:00", "shots": 100})
    assert "error" not in json.loads(api.run_json(Mystery(), req))
    assert json.loads(api.run_json(Mystery(), req))["error"] == "one_job_per_run"


def test_twin_run_stops_on_a_wrong_bit_order(monkeypatch):
    monkeypatch.setitem(api._jobs, "guarded", 0)

    class Reversed:
        name = "reversed_test_backend"

        def run(self, qc, shots):
            res = BasicSimulator().run(qc, shots=shots).result()

            class R:
                def result(self):
                    class C:
                        def get_counts(self):
                            return {k[::-1]: v for k, v in res.get_counts().items()}

                    return C()

            return R()

    with pytest.raises(Exception, match="canary fraction"):
        api.twin_run_json(Reversed(), json.dumps({"minute": "2024-05-10T17:06", "shots": 200}))


def test_non_finite_numbers_become_null():
    assert api._finite({"a": math.inf, "b": [1.0, math.nan], "c": "x"}) == {
        "a": None,
        "b": [1.0, None],
        "c": "x",
    }


def test_ibm_noise_models_are_capped_at_200_shots():
    assert api._shots("ibm_fake", 1000) == 200 and api._shots("local", 1000) == 1000
