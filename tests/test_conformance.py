"""Static checks of the Qollab-specific rules."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
JS = sorted([ROOT / "main.js", *(ROOT / "ui").glob("*.js")])
PY = sorted((ROOT / "compass").glob("*.py"))


def test_python_called_only_from_py_js():
    callers = [p.name for p in JS if ".callPromising(" in p.read_text(encoding="utf-8")]
    assert callers == ["py.js"]


@pytest.mark.parametrize("path", JS, ids=lambda p: p.name)
def test_js_rules(path):
    src = path.read_text(encoding="utf-8")
    for bad in ("localStorage", "sessionStorage", "indexedDB", "location.hash", "eval("):
        assert bad not in src, bad
    # Qollab bundles main.js into one function that receives `backend` and `sendFile`
    assert not re.search(r"^(?:export\s+)?(?:let|const|var|function|class)\s+(backend|sendFile)\b", src, re.M)


def test_index_html_is_body_only_without_scripts():
    html = (ROOT / "index.html").read_text(encoding="utf-8").lower()
    assert not re.search(r"<(script|html|head|body)\b", html)


def test_backend_used_only_in_the_two_run_functions():
    """One job per run: only api.run_json and api.twin_run_json call backend.run, and both check
    the shared one-IonQ-job counter before they do."""
    hits = [
        (p.name, m.start()) for p in PY for m in re.finditer(r"backend\.run\(", p.read_text(encoding="utf-8"))
    ]
    assert [h[0] for h in hits] == ["api.py", "api.py"]
    api = (ROOT / "compass" / "api.py").read_text(encoding="utf-8")
    for fn, (_, pos) in zip(("def run_json(", "def twin_run_json("), hits, strict=True):
        start = api.index(fn)
        end = api.find("\ndef ", start + 1)
        end = end if end > 0 else len(api)
        assert start < pos < end
        body = api[start:end]
        assert body.index('_jobs["ionq"] >= 1') < body.index("backend.run(")


def test_no_sampler_no_measure_all_no_dynamic_circuits():
    for p in PY:
        src = p.read_text(encoding="utf-8")
        for bad in ("Sampler", "Estimator", "measure_all", "c_if", "if_test", "input("):
            assert bad not in src, f"{p.name}: {bad}"


def test_data_paths_are_literal_strings():
    src = (ROOT / "compass" / "data.py").read_text(encoding="utf-8")
    for csv in (ROOT / "data").glob("*.csv"):
        assert f'"data/{csv.name}"' in src


def test_readme_attribution_and_licence():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "This effort is supported by Qollab & IonQ" in readme
    assert "MIT" in readme and (ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
@pytest.mark.parametrize("path", JS, ids=lambda p: p.name)
def test_js_parses(path, tmp_path):
    copy = tmp_path / "m.mjs"
    copy.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    out = subprocess.run(["node", "--check", str(copy)], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
