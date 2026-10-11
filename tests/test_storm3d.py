"""The 3D compass draws numbers that the replay model computed (compass/api.py storm3d_json)."""

import json

import numpy as np
import pytest

from compass import api, replay
from compass.estimators import wrap


@pytest.fixture(scope="module")
def storm():
    return json.loads(api.storm3d_json(json.dumps({"dataset": "storm"})))


def test_shape_and_shown_replay(storm):
    n = len(storm["times"])
    assert n == 2880 and len(storm["dF_nT"]) == n
    for arm in ("IND8", "GHZ4", "CASC"):
        a = storm["arms"][arm]
        assert all(len(a[k]) == n for k in ("turn", "true_phase", "reading", "fringe", "slips_so_far"))
    rp = storm["replay"]
    assert 1 <= rp["shown"] <= rp["of"] == 32


def test_slips_match_the_replay_metrics(storm):
    _, f = api.data.load("storm")
    est = replay.track(f, api.SCALE, 1000, api._visibilities("none", 0.0, None),
                       arms=("IND8", "GHZ4", "CASC"), replicates=32, seed=0)
    k = storm["replay"]["shown"] - 1
    g4 = replay.metrics(f, est["GHZ4"][k : k + 1], api.SCALE, 4)
    slips = storm["arms"]["GHZ4"]["slips_so_far"][-1]
    assert storm["totals"]["GHZ4"]["slips"] == int(g4["slips"][0]) == slips
    assert storm["totals"]["GHZ4"]["wrong_minutes"] == int(g4["wrong"][0])
    # the cascade and the independent qubits never leave their fringe in the storm
    assert storm["totals"]["CASC"]["slips"] == 0 and storm["totals"]["IND8"]["slips"] == 0


def test_reading_is_the_wrapped_true_turn_up_to_shot_noise(storm):
    for arm in ("IND8", "GHZ4", "CASC"):
        a = storm["arms"][arm]
        diff = np.abs(wrap(np.array(a["reading"][1:]) - np.array(a["true_phase"][1:])))
        assert np.median(diff) < 0.1 and np.mean(diff < 0.4) > 0.98


def test_first_ghz4_slip_turns_past_half_a_turn(storm):
    g = storm["arms"]["GHZ4"]
    first = next(i for i, x in enumerate(g["fringe"]) if x != 0)
    assert abs(g["true_phase"][first]) > np.pi
    assert storm["times"][first] == "2024-05-10T21:47"
    assert storm["arms"]["CASC"]["fringe"][first] == 0


def test_console_line(storm):
    assert storm["console_line"].startswith("[Entangled Compass] 3D compass, replay")


def test_turn_is_the_field_step_and_true_phase_adds_the_whole_turns_off(storm):
    # the arc is drawn from `turn` = m s dF; `true_phase` (against the prediction) matches it only
    # while the previous estimate was on the right fringe, and is off by whole turns otherwise
    df = np.array(storm["dF_nT"])
    for arm in ("IND8", "GHZ4", "CASC"):
        a = storm["arms"][arm]
        turn, tp, fr = np.array(a["turn"]), np.array(a["true_phase"]), np.array(a["fringe"])
        assert np.allclose(turn, a["m"] * storm["scale"] * df, atol=2e-3 * a["m"])
        prev_ok = np.concatenate([[True], fr[:-1] == 0])
        assert np.abs(tp - turn)[prev_ok].max() < 0.3
    g = storm["arms"]["GHZ4"]
    wrong = np.array(g["fringe"][:-1]) != 0
    extra = (np.array(g["true_phase"]) - np.array(g["turn"]))[1:][wrong]
    assert np.median(np.abs(extra)) > np.pi  # about a whole turn on the wrong-fringe minutes
