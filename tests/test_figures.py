"""The explanatory figures: the data they draw comes from Python, they use only theme colours,
and every figure has a title, a description and a caption."""

import importlib.util
import inspect
import json
import math
import re
from pathlib import Path

from compass import api, circuits, decode, twin

ROOT = Path(__file__).resolve().parent.parent
FIGURES = (ROOT / "ui" / "figures.js").read_text(encoding="utf-8")
SCHEMATIC = (ROOT / "ui" / "schematic.js").read_text(encoding="utf-8")
CSS = (ROOT / "main.css").read_text(encoding="utf-8")


def test_init_carries_the_numbers_the_figures_show():
    init = json.loads(api.init_json())
    assert init["scale"]["range_nt"] == {str(m): round(math.pi / (m * api.SCALE), 2) for m in (1, 2, 4)}
    assert init["scale"]["range_nt"] == {"1": 157.08, "2": 78.54, "4": 39.27}
    assert init["qubits"] == {"A": 17, "B": 21, "twin": twin.N_QUBITS}


def test_register_drawn_in_figure_2():
    a = circuits.layout("A").register("G4Y")
    b = circuits.layout("B").register("G4Y")
    assert a.qubits == (11, 12, 13, 14) and a.basis == "Y" and a.m == 4
    assert b.ancilla == 20
    assert sorted(r.ancilla for r in circuits.layout("B").registers) == list(range(15, 21))
    assert inspect.signature(decode.decode).parameters["min_canary"].default == 0.9


def test_circuit_figure_matches_the_built_circuit():
    """Figure 2 draws H, a CX ladder, Rz on every qubit, S-dagger on the first, H on all: check
    that compass/circuits.py builds G4Y in that order."""
    lay = circuits.layout("A")
    reg = lay.register("G4Y")
    qc = circuits.build(lay, 0.3, 0.0)
    ops = [
        (inst.operation.name, tuple(qc.find_bit(q).index for q in inst.qubits))
        for inst in qc.data
        if set(qc.find_bit(q).index for q in inst.qubits) <= set(reg.qubits)
        and inst.operation.name != "barrier"
    ]
    q0, q1, q2, q3 = reg.qubits
    expected = [
        ("h", (q0,)),
        ("cx", (q0, q1)),
        ("cx", (q1, q2)),
        ("cx", (q2, q3)),
        *[("rz", (q,)) for q in reg.qubits],
        ("sdg", (q0,)),
        *[("h", (q,)) for q in reg.qubits],
        *[("measure", (q,)) for q in reg.qubits],
    ]
    assert ops == expected


def _vars(block: str) -> set[str]:
    return set(re.findall(r"(--[a-z0-9-]+)\s*:", block))


def test_figures_use_only_theme_colours():
    for src in (FIGURES, SCHEMATIC):
        assert not re.search(r"#[0-9a-fA-F]{3,8}\b", src)
        assert "rgb(" not in src and "hsl(" not in src
    dark = _vars(CSS[: CSS.index("@media (prefers-color-scheme: light)")])
    light_block = CSS[CSS.index("@media (prefers-color-scheme: light)") :]
    light = _vars(light_block[: light_block.index("\n}\n")])
    used = set(re.findall(r"var\((--[a-z0-9-]+)\)", FIGURES + SCHEMATIC))
    assert used <= dark
    colours = {v for v in dark if re.search(rf"{v}\s*:\s*(#|rgba?\()", CSS)}
    assert colours <= light


def test_every_figure_has_title_desc_and_caption():
    calls = re.findall(r"return figure\(\{(.*?)\n  \},", FIGURES, re.S)
    assert len(calls) == 4
    for c in calls:
        for key in ("title:", "caption:"):
            assert key in c
        assert re.search(r"\bdesc\b", c)


def test_no_physics_numbers_hard_coded_in_figures():
    for literal in ("39.3", "157.1", "78.5", "113.6", "0.02", "17 qubits", "21 qubits"):
        assert literal not in FIGURES, literal


def _make_writeup():
    spec = importlib.util.spec_from_file_location("make_writeup", ROOT / "scripts" / "make_writeup.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_writeup_images():
    mw = _make_writeup()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    final = mw.convert(readme, "v1.0-submission", False)
    raw = f"https://raw.githubusercontent.com/{mw.REPO}/v1.0-submission/docs/figures/"
    for name in ("model", "circuit", "architecture"):
        assert f"](docs/figures/{name}.png)" in readme
        assert f"]({raw}{name}.png)" in final
    interim = mw.convert(readme, "main", True)
    assert "![" not in interim and "raw.githubusercontent.com" not in interim
    assert interim.count("*Figure (shown in the app):") == 3
    for name in ("model", "circuit", "architecture"):
        assert (ROOT / "docs" / "figures" / f"{name}.png").stat().st_size > 10_000
