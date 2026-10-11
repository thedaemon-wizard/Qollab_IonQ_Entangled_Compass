"""Final UI fixes: both baselines named next to the GHZ-4 gain, keyboard focus kept after a
control disables itself, one name for the fringe-change count, and the typographic minus."""

import json
import re
from pathlib import Path

from compass import api

ROOT = Path(__file__).resolve().parent.parent
UI = {p.name: p.read_text(encoding="utf-8") for p in (ROOT / "ui").glob("*.js")}


def test_replay_carries_both_gains_the_tracker_status_shows():
    """The tracker status line prints gain_ghz4 (matched) and sql.gain_ghz4 (standard quantum
    limit); on the ideal quiet day they are 2 and sqrt(2)."""
    r = json.loads(api.replay_json(json.dumps({"dataset": "quiet", "replicates": 8})))
    g, q = r["gain_ghz4"], r["sql"]["gain_ghz4"]
    for d in (g, q):
        assert {"mean", "two_se", "theory"} <= d.keys()
    assert abs(g["mean"] - 2) < 0.05 and abs(q["mean"] - 2**0.5) < 0.05
    status = UI["tracker.js"]
    assert "lastReplay.sql.gain_ghz4" in status
    assert "8 independent qubits read the same way (matched" in status
    assert "against the standard quantum limit: ${fmt.pm(q)}×" in status


def test_console_lines_name_the_matched_baseline_and_the_sql():
    o = json.loads(api.overview_json())
    line = o["console_line"]
    assert "8 independent qubits read the same way (matched" in line
    assert f"{o['ideal']['over_sql']['mean']:.2f}× the standard quantum limit" in line
    assert f"{o['dephasing_0_2']['over_sql']['mean']:.2f}× the SQL" in line
    r = json.loads(api.replay_json(json.dumps({"dataset": "quiet", "replicates": 4})))
    assert "read the same way (matched; model at zero field step" in r["console_line"]
    assert f"{r['sql']['gain_ghz4']['mean']:.2f}× (± " in r["console_line"]


def test_overview_tile_names_the_baseline_of_the_textbook_two():
    tile = UI["overview.js"]
    assert "read the same X/Y way (matched)" in tile
    assert "holds against this matched baseline" in tile


def test_controls_that_disable_themselves_keep_focus():
    """Every button that is disabled while its action runs hands focus back (or to its status
    line when it stays disabled); the 3D record select is never disabled."""
    for name, buttons in {
        "tracker.js": ["replayBtn", "runBtn"],
        "twin.js": ["replayBtn", "runBtn"],
        "challenge.js": ["startBtn"],
    }.items():
        src = UI[name]
        for b in buttons:
            assert f"{b}.disabled = true" in src
            assert re.search(rf"keepFocus\({b}, \w+\)", src), (name, b)
    assert "keepFocus(roundBox.querySelector('button'), status)" in UI["challenge.js"]
    assert "dataset.disabled" not in UI["compass3d.js"]
    assert "runOut.setAttribute('aria-busy', 'true')" in UI["twin.js"]


def test_quiet_record_disables_the_first_fringe_change_button():
    src = UI["compass3d.js"]
    assert "toFirst.disabled = first <= 0;" in src
    assert "'aria-describedby': 'ec3-summary'" in src and "id: 'ec3-summary'" in src


def test_one_name_for_the_fringe_change_count():
    for name, src in UI.items():
        assert "Fringe jumps" not in src, name
        assert "jumps a fringe" not in src, name
    assert all("jumps a fringe" not in p["note"] for p in json.loads(api.init_json())["presets"])


def test_numbers_use_the_typographic_minus():
    dom = UI["dom.js"]
    assert "export const minus = (s) => String(s).replace(/^-/, '\\u2212');" in dom
    assert "minus(x.toFixed(d))" in dom and "minus(o.mean.toFixed(d))" in dom
    assert "text: minus(v)" in UI["chart.js"]
    assert "String(Math.round(x))" not in UI["tracker.js"]


def test_round_card_running_score_uses_the_fixed_strategies_round_scores():
    """The round card compares your mean so far with each fixed strategy over the same rounds;
    challenge_setup gives one score per round for each, and their mean is the final card's."""
    s = json.loads(api.challenge_setup_json(json.dumps({"shots": 1000, "gate_model": "none", "seed": 7})))
    for c, a in s["always"].items():
        assert len(a["scores"]) == len(s["rounds"]) == 12, c
        assert sum(a["scores"]) / 12 == a["mean_score"]
    src = UI["challenge.js"]
    assert "setup.always[c].scores.slice(0, n)" in src
    assert "Your mean score so far:" in src
