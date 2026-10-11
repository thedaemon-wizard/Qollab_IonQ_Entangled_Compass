"""Physics and request settings shown in the views come from Python (init_json and the results),
not from numbers typed into the JavaScript; the Python values are the ones the README quotes."""

import copy
import json
import math
import re
from pathlib import Path

from compass import api, console, data, model, twin

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
# method.js explains the model choice in prose (s, the electron-spin Ramsey time, the fringe
# example) and is checked by the documentation tests; every other view takes its numbers from data.
VIEWS = {p.name: p.read_text(encoding="utf-8") for p in (ROOT / "ui").glob("*.js") if p.name != "method.js"}
VIEWS["main.js"] = (ROOT / "main.js").read_text(encoding="utf-8")


def test_init_carries_the_settings_and_they_are_the_documented_ones():
    init = json.loads(api.init_json())
    assert init["scale"]["value"] == api.SCALE == 0.02
    assert init["scale"]["ramsey_us"] == round(model.ramsey_time_us(api.SCALE), 1) == 113.6
    assert init["scale"]["ghz4_range_nt"] == round(math.pi / (4 * api.SCALE), 2) == 39.27
    assert init["defaults"] == {"shots": 1000, "replicates": 32, "seed": 0, "challenge_seed": 7}
    assert init["challenge_rounds"] == 12
    assert init["qubits"] == {"A": 17, "B": 21, "twin": twin.N_QUBITS} and twin.N_QUBITS == 13
    assert round(init["crossover_gamma"]["4"], 2) == 0.23
    assert init["crossover_gamma"]["4"] == round(math.log(4) / 6, 4)
    for quoted in ("s = 0.02", "113.6 µs", "±39.27 nT", "+44.6 nT"):
        assert quoted in README, quoted


def test_circuit_minutes_carry_their_field_step_from_the_record():
    init = json.loads(api.init_json())
    steps = {p["minute"]: p["step_nt"] for p in init["presets"]}
    assert steps == {
        "2026-10-01T12:00": -0.1,
        "2024-05-10T17:06": 12.6,
        "2024-05-10T21:47": 44.6,
        "2024-05-11T02:07": 118.8,
    }
    for p in init["presets"]:
        times, f = data.load(p["dataset"])
        i = times.index(p["minute"])
        assert p["step_nt"] == round(float(f[i] - f[i - 1]), 1)
        assert not re.search(r"\d\.\d|nT", p["note"]), p["note"]  # the step is the data's, not the note's
    assert steps["2024-05-11T02:07"] == round(init["datasets"]["storm"]["largest_step_nt"], 1)
    # the first step beyond GHZ-4's range of the storm record
    assert 39.27 < steps["2024-05-10T21:47"] < 2 * 39.27


def test_overview_result_carries_its_own_settings():
    o = json.loads(api.overview_json())
    assert (o["dephasing_gamma"], o["quiet_replicates"], o["shots"]) == (0.2, 16, 1000)
    assert (o["storm"]["replicates"], o["storm"]["scale"], o["storm"]["shots"]) == (8, 0.02, 1000)
    line = o["console_line"]
    assert "(model replay, 1000 shots per register per minute)" in line
    assert "2 SE over 16 replays" in line and "with dephasing 0.2 " in line
    assert "(quick estimate, 8 replays)" in line
    # the console line prints what the result says, not numbers of its own
    other = copy.deepcopy(o)
    other.update(dephasing_gamma=0.3, quiet_replicates=12, shots=500)
    other["storm"]["replicates"] = 4
    line = console.overview(other)
    assert "500 shots" in line and "over 12 replays" in line and "dephasing 0.3 " in line
    assert "(quick estimate, 4 replays)" in line


def test_replay_and_twin_results_name_their_replicates():
    t = json.loads(api.twin_replay_json(json.dumps({"replicates": 4})))
    assert t["replicates"] == 4 and "2 SE over 4 replays" in t["console_line"]
    r = json.loads(api.replay_json(json.dumps({"dataset": "quiet", "replicates": 4})))
    assert "2 SE over 4 replays" in r["console_line"] and "(1000 shots," in r["console_line"]
    s = json.loads(api.challenge_setup_json("{}"))
    assert (s["shots"], s["seed"]) == (1000, 7)


def test_views_type_no_physics_or_request_numbers():
    typed = [
        r"\b0\.02\s*(rad|\$)",  # the phase per nT
        r"113\.6",
        r"39\.(27|3)\b",
        r"\b1000 shots",
        r"shots: 1000",
        r"seed: [07]\b",
        r"replicates: 32",
        r"\b32 (replays|times)",
        r"average of 32",
        r"averages 32",
        r"\b(17|21|13) qubits",
        r"21 with dephasing",
        r"approx 0\.23",
        r"gamma = 0\.2\$",
        r"[+−-]?44\.6",
        r"\b12 rounds",
    ]
    for name, src in VIEWS.items():
        for pattern in typed:
            assert not re.search(pattern, src), (name, pattern)


def test_views_read_the_numbers_from_data():
    src = VIEWS
    assert "init.scale.value" in src["overview.js"] and "init.crossover_gamma['4']" in src["overview.js"]
    assert "a.dephasing_gamma" in src["overview.js"] and "a.storm.replicates" in src["overview.js"]
    assert "init.defaults.replicates" in src["tracker.js"] and "init.defaults.seed" in src["tracker.js"]
    assert "init.qubits.A" in src["tracker.js"] and "init.qubits.B" in src["tracker.js"]
    assert (
        "init.defaults.challenge_seed" in src["challenge.js"] and "setup.rounds.length" in src["challenge.js"]
    )
    assert "init.qubits.twin" in src["twin.js"] and "r.replicates" in src["twin.js"]
    assert "init.scale.value" in src["compass3d.js"] and "init.defaults.shots" in src["compass3d.js"]
    assert "${init.challenge_rounds} rounds" in src["figures.js"]
    assert "challengeView(state, init)" in src["main.js"] and "twinView(info, init)" in src["main.js"]


def test_minute_select_shows_short_labels_and_describes_the_minute():
    """The circuit-run 'Minute' options are the time and the field step only, so they fit the select;
    the line under it (its description) says what happens in that minute."""
    src = VIEWS["tracker.js"]
    assert "${p.minute.replace('T', ' ')} (${fmt.signed(p.step_nt, 1)} nT)" in src
    assert "field('Minute (UTC)', preset, presetHint)" in src
    assert "id: 'ec-minute-hint'" in src
    assert "control.setAttribute('aria-describedby', note.id)" in src
    assert "preset.addEventListener('change', syncPreset)" in src
    assert "Field step in this minute: ${fmt.signed(p.step_nt, 1)} nT." in src


def test_twin_minute_select_shows_short_labels_and_describes_the_minute():
    """The Two observatories 'Minute' options are the time only, so they fit the select at phone
    widths; the line under it (its description) gives the note for that minute."""
    src = VIEWS["twin.js"]
    assert "'Minute (UTC)'), minute, minuteHint)" in src
    assert "'aria-describedby': 'ec-twin-minute-hint'" in src and "id: 'ec-twin-minute-hint'" in src
    assert "el('option', { value: String(i) }, m.replace('T', ' '))" in src
    assert "UTC: ${note}" not in src
    assert "minute.addEventListener('change', syncMinute)" in src
    # the notes the hint shows agree with the two records
    notes = dict(re.findall(r"\['(\d{4}-\d\d-\d\dT\d\d:\d\d)', '([^']+)'\]", src))
    times, f_a, f_b = data.load_pair()
    step = {m: (f_a[i] - f_a[i - 1], f_b[i] - f_b[i - 1]) for m in notes for i in [times.index(m)]}
    assert notes["2024-05-10T17:06"].startswith("storm onset: both sites jump")
    assert step["2024-05-10T17:06"][0] > 10 and step["2024-05-10T17:06"][1] > 10
    assert notes["2024-05-11T02:07"].startswith("largest step at Boulder: Tucson barely moves")
    assert abs(step["2024-05-11T02:07"][1]) < 1
    assert round(float(step["2024-05-11T02:07"][0]), 1) == round(float(max(abs(f_a[1:] - f_a[:-1]))), 1)
