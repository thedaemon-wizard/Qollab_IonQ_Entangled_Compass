"""Twin sensors (Boulder and Tucson): exact circuit parities, the sqrt(2) gain for the
difference, the measured correlation of the storm, and the shared one-IonQ-job guard."""

import json
import math

import pytest
from qiskit.providers.basic_provider import BasicSimulator
from qiskit.quantum_info import Statevector

from compass import api, data, twin


def test_pairs_read_difference_and_sum():
    da, db = 0.3, -0.2
    qc = twin.build(da, db).remove_final_measurements(inplace=False)
    probs = Statevector(qc).probabilities_dict()
    n = twin.N_QUBITS

    def parity(qubits):
        return sum(p if sum(k[n - 1 - q] == "1" for q in qubits) % 2 == 0 else -p for k, p in probs.items())

    assert parity(twin.PAIRS["DIFFX"]) == pytest.approx(math.cos(da - db), abs=1e-12)
    assert parity(twin.PAIRS["DIFFY"]) == pytest.approx(math.sin(da - db), abs=1e-12)
    assert parity(twin.PAIRS["SUMX"]) == pytest.approx(math.cos(da + db), abs=1e-12)
    assert parity(twin.PAIRS["SUMY"]) == pytest.approx(math.sin(da + db), abs=1e-12)
    assert parity((twin.SINGLES["AY"],)) == pytest.approx(math.sin(da), abs=1e-12)
    assert parity((twin.SINGLES["BX"],)) == pytest.approx(math.cos(db), abs=1e-12)


def test_storm_is_not_common_across_900_km():
    _, f_a, f_b = data.load_pair()
    st = twin.step_statistics(f_a, f_b)
    assert st["corr_one_minute_changes"] == pytest.approx(0.331, abs=0.001)
    assert st["std_step_gradient_nt"] == pytest.approx(7.95, abs=0.01)
    assert st["common_fraction"] < 0.3


def test_entangled_pair_is_sqrt2_better_for_the_difference():
    out = json.loads(api.twin_replay_json("{}"))
    assert out["gain"]["mean"] == pytest.approx(math.sqrt(2), abs=0.03)
    assert out["rmse"]["DIFF"]["mean"] == pytest.approx(1 / (0.02 * math.sqrt(1000)), abs=0.03)


def test_twin_run_and_shared_ionq_guard(monkeypatch):
    out = json.loads(
        api.twin_run_json(BasicSimulator(), json.dumps({"minute": "2024-05-10T17:06", "shots": 4000}))
    )
    assert out["canary"] == 1.0
    assert out["reads"]["difference"]["true_nT"] == pytest.approx(12.56 - 21.52, abs=1e-6)
    assert abs(out["reads"]["difference"]["error_nT"]) < 3 and abs(out["reads"]["sum"]["error_nT"]) < 3

    class FakeIonQ:
        name = "ionq_simulator"

        def run(self, qc, shots):
            return BasicSimulator().run(qc, shots=shots)

    monkeypatch.setitem(api._jobs, "guarded", 0)
    req = json.dumps({"dataset": "quiet", "minute": "2026-10-01T12:00", "shots": 100})
    assert "error" not in json.loads(api.run_json(FakeIonQ(), req))
    refused = json.loads(api.twin_run_json(FakeIonQ(), json.dumps({"minute": "2024-05-10T17:06"})))
    assert refused["error"] == "one_job_per_run"
