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
        body = readme.split("\n", 1)[1]  # the title line is dropped (Qollab shows the project title)
        assert not out.startswith("# ")
        assert len(re.findall(r"(?<!\$)\$(?!\$)[^$\n]+?\$", out)) == len(INLINE.findall(body))
    with pytest.raises(ValueError):
        mw.convert(readme + "\nbroken $`x\n", "main", False)


# GitHub's math renderer rejects \operatorname ("The following macros are not allowed"); the
# others define macros, load extensions, or emit links, classes or HTML attributes, which
# GitHub's and Qollab's renderers may refuse or strip. \html matches \htmlClass, \htmlId, ...
UNSAFE_MACROS = re.compile(
    r"\\(?:(?:operatorname|require|def|newcommand|href|class|cssId)(?![A-Za-z])|html[A-Za-z]*)"
)


def test_unsafe_macro_pattern():
    for bad in (
        r"\operatorname{atan2}",
        r"\require{x}",
        r"\def\a{b}",
        r"\newcommand{\a}{b}",
        r"\href{u}{t}",
        r"\htmlClass{c}{x}",
        r"\html",
        r"\class{c}{x}",
        r"\cssId{i}{x}",
    ):
        assert UNSAFE_MACROS.search(bad), bad
    for ok in (r"\mathrm{atan2}", r"\delta", r"\hat{F}", r"\default", r"\classic", r"\sqrt{N}"):
        assert not UNSAFE_MACROS.search(ok), ok


def test_markdown_math_uses_github_safe_macros():
    skip = {".venv", ".git", ".pytest_cache", "dist", "node_modules"}
    paths = [p for p in ROOT.rglob("*.md") if not skip & set(p.relative_to(ROOT).parts)]
    assert {"README.md", "decisions.md", "review.md"} <= {p.name for p in paths}
    spec = importlib.util.spec_from_file_location("make_writeup", ROOT / "scripts" / "make_writeup.py")
    mw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mw)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    texts = {p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8") for p in paths}
    texts["write-up"] = mw.convert(readme, "v1.0-submission", False)
    for name, text in texts.items():
        found = UNSAFE_MACROS.findall(text)
        assert not found, f"{name}: {found}"


def test_decision_e11_states_the_final_writeup_counts():
    spec = importlib.util.spec_from_file_location("make_writeup", ROOT / "scripts" / "make_writeup.py")
    mw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mw)
    out = mw.convert((ROOT / "README.md").read_text(encoding="utf-8"), "v1.0-submission", False)
    inline = len(re.findall(r"(?<!\$)\$(?!\$)[^$\n]+?\$", out))
    assert "$$" not in out
    e11 = " ".join((ROOT / "docs" / "decisions.md").read_text(encoding="utf-8").split())
    assert f"has {len(out):,} characters (Qollab's limit is {mw.LIMIT:,}) and {inline} formulas" in e11
