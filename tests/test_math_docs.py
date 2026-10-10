"""Formulas in the README and docs are GitHub math ($`...`$ inline, ```math display) and
convert cleanly into the $...$ / $$...$$ that Qollab's write-up renders with KaTeX."""

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
INLINE = re.compile(r"\$`([^`\n]+?)`\$")


@pytest.mark.parametrize("path", DOCS, ids=lambda p: p.name)
def test_inline_math_is_well_formed(path):
    text = path.read_text(encoding="utf-8")
    for n, line in enumerate(text.split("\n"), 1):
        assert line.count("$`") == line.count("`$"), f"{path.name}:{n} formula not closed on its line"
        for tex in INLINE.findall(line):
            # a literal | splits a table cell; use \lvert, \rvert or \mid
            assert "|" not in tex, f"{path.name}:{n} {tex}"
            # GitHub's sanitizer drops '<' directly followed by a letter
            assert not re.search(r"<\S|\S<|>\S|\S>", tex.replace("\\langle", "").replace("\\rangle", "")), tex
    assert not re.search(r"^[ \t]+```math", text, re.M), "indented math fence"


@pytest.mark.parametrize("path", DOCS, ids=lambda p: p.name)
def test_no_tex_notation_left_as_plain_text(path):
    text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
    text = INLINE.sub("", text)
    text = re.sub(r"`[^`\n]*`", "", text)
    for bad in ("e^{", "e^(", "^{", "_{", "√(", "δ̂"):
        assert bad not in text, f"{path.name}: {bad}"


def test_writeup_has_only_qollab_math():
    spec = importlib.util.spec_from_file_location("make_writeup", ROOT / "scripts" / "make_writeup.py")
    mw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mw)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for out in (mw.convert(readme, "v1.0-submission", False), mw.convert(readme, "main", True)):
        assert "$`" not in out and "`$" not in out and "```math" not in out
        assert len(re.findall(r"(?<!\$)\$(?!\$)[^$\n]+?\$", out)) == len(INLINE.findall(readme))
    with pytest.raises(ValueError):
        mw.convert(readme + "\nbroken $`x\n", "main", False)
