"""The build scripts and the documents: what the Qollab bundle carries, that --check and --help
write nothing, the write-up's embedded video, and that the README quotes the recomputed numbers."""

import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
HEADLINE = json.loads((ROOT / "results" / "headline_numbers.json").read_text(encoding="utf-8"))
VIDEO = "https://youtu.be/IomHduFJqyc"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _stamp(path: Path):
    return path.stat().st_mtime_ns if path.exists() else None


def test_bundle_ships_saved_runs_and_headline_numbers_within_limits(tmp_path):
    bu = _load("build_upload")
    shipped = {p.relative_to(ROOT).as_posix() for p in bu.files()}
    runs = {p.relative_to(ROOT).as_posix() for p in (ROOT / "results" / "qollab").glob("*.json")}
    assert runs and runs <= shipped
    assert "results/headline_numbers.json" in shipped
    # tests, scripts, docs and the accessibility records stay in the repository only
    assert not any(s.split("/")[0] in ("tests", "scripts", "docs", "tools") for s in shipped)
    assert not any(s.startswith("results/a11y/") for s in shipped)
    for s in shipped:
        if s.endswith(".json"):
            json.loads((ROOT / s).read_text(encoding="utf-8"))
    card = tmp_path / "writeup.md"
    card.write_text(_load("make_writeup").convert(README, "v1.0-submission", False), encoding="utf-8")
    paths = bu.files()
    assert bu.check_limits(paths, card) == []
    assert len(paths) <= bu.MAX_FILES


def test_build_upload_check_and_help_write_nothing(capsys):
    bu = _load("build_upload")
    zip_path = ROOT / "dist" / "qollab_upload.zip"
    before = _stamp(zip_path)
    assert bu.main(["--check"]) == 0
    out = capsys.readouterr().out
    assert "results/headline_numbers.json" in out and "nothing written" in out
    with pytest.raises(SystemExit) as e:
        bu.main(["--help"])
    assert e.value.code == 0
    with pytest.raises(SystemExit) as e:
        bu.main(["--chek"])
    assert e.value.code == 2
    assert _stamp(zip_path) == before


def test_make_writeup_check_and_help_write_nothing(capsys):
    mw = _load("make_writeup")
    dest = ROOT / "dist" / "writeup.md"
    before = _stamp(dest)
    assert mw.main(["--check"]) == 0
    assert "nothing written" in capsys.readouterr().out
    with pytest.raises(SystemExit) as e:
        mw.main(["--help"])
    assert e.value.code == 0
    assert _stamp(dest) == before


def test_writeup_embeds_the_video_and_the_readme_links_it():
    mw = _load("make_writeup")
    assert f"**Demo video (2:54):** {VIDEO}\n" in README
    assert "![Demo video" not in README
    final = mw.convert(README, "v1.0-submission", False)
    assert final.count(f"![Demo video (2:54)]({VIDEO})") == 1
    assert f"**Demo video (2:54):** {VIDEO}" not in final
    # generic: plain or bold label, youtu.be or youtube.com/watch
    sample = "Demo video (1:05): https://www.youtube.com/watch?v=abc_D-1\ntext Demo video (1:05): x\n"
    assert mw.embed_video(sample).startswith(
        "![Demo video (1:05)](https://www.youtube.com/watch?v=abc_D-1)\n"
    )
    assert mw.embed_video(sample).endswith("text Demo video (1:05): x\n")


def test_readme_and_writeup_fit_qollab_limit():
    mw = _load("make_writeup")
    assert len(README) < mw.LIMIT
    for out in (mw.convert(README, "v1.0-submission", False), mw.convert(README, "main", True)):
        assert len(out) < mw.LIMIT


def test_readme_quotes_the_recomputed_numbers():
    q = HEADLINE["quiet_day_gain_ghz4_vs_8_independent"]
    both = q["ionq_aria1_documented_plus_dephasing_0.20"]
    assert f"{both['mean']:.2f} ± {both['two_se']:.2f} / {both['theory']:.3f}" in README
    sql = both["gain_over_sql"]
    assert f"{sql['mean']:.3f} ± {sql['two_se']:.3f} / {sql['theory']:.3f}" in README
    s3d = HEADLINE["storm_3d_compass_replays"]
    common = max(s3d["ghz4_outcomes"], key=lambda o: o["replays"])
    assert f"{common['replays']} of the {s3d['replays']}" in README
    assert f"{s3d['mean_ghz4_wrong_minutes']:.0f}" in README
    ch = HEADLINE["challenge_strategies"]
    assert f"{ch['ghz4_rounds_1_2_then_cascade_by_seed']['7']:.2f}" in README
    assert f"{ch['hindsight_cascade_in_stormy_rounds_by_seed']['7']:.2f}" in README
    assert f"{ch['reactive_cascade_after_a_step_beyond_range_seed_7']:.1f}" in README
    # the switch-once plan beats always-cascade for every seed listed
    for s in ch["seeds"]:
        assert ch["ghz4_rounds_1_2_then_cascade_by_seed"][str(s)] < ch["always_by_seed"][str(s)]["CASC"]
    onset = HEADLINE["two_observatories_onset_1706"]
    assert f"{onset['difference_nt']:+.1f}".replace("-", "−") in README
    se = HEADLINE["recorded_ionq_aria1_visibility_se"]
    lo = min(se[k]["se"] for k in ("GHZ-1", "GHZ-2", "GHZ-4"))
    hi = max(se[k]["se"] for k in ("GHZ-1", "GHZ-2", "GHZ-4"))
    assert f"about {lo:.2f}\N{EN DASH}{hi:.2f}" in README


def test_readme_links_point_at_files_in_the_repository():
    for target in re.findall(r"\]\((?!https?:|#)([^)]+)\)", README):
        assert (ROOT / target).exists(), target


def test_no_untranslated_marker_in_shipped_or_documented_text():
    paths = [ROOT / "README.md", *(ROOT / "docs").glob("*.md"), *(ROOT / "compass").glob("*.py")]
    paths += [*(ROOT / "ui").glob("*.js"), *(ROOT / "scripts").glob("*.py")]
    for p in paths:
        # the Japanese "to be checked" marker, written as escapes so this file stays ASCII
        assert "\u8981\u78ba\u8a8d" not in p.read_text(encoding="utf-8"), p.name


def test_csv_headers_state_the_usgs_licence_as_the_fetch_script_writes_it():
    fetch = _load("fetch_usgs")
    assert fetch.POLICY in README and fetch.POLICY in fetch.LICENCE
    flat = " ".join(README.split())
    quote = "USGS-authored or produced data and information are considered to be in the U.S. Public Domain."
    assert f'"{quote}"' in flat
    assert "not covered by this project's MIT licence" in flat
    names = {name for _, name, *_ in fetch.RECORDS}
    assert names == {p.name for p in (ROOT / "data").glob("*.csv")}
    for name in names:
        lines = (ROOT / "data" / name).read_text(encoding="utf-8").splitlines()
        header = lines[: lines.index("time_utc,F_nT")]
        assert f"# Licence: {fetch.LICENCE}" in header, name
        credit = "# Credit: Geomagnetic data: USGS Geomagnetism Program"
        assert any(ln.startswith(credit) for ln in header), name


def _flat(text: str) -> str:
    return " ".join(text.replace("\N{RIGHT SINGLE QUOTATION MARK}", "'").split())


def test_method_tab_prose_numbers_come_from_python():
    """ui/method.js explains the model in prose; its numbers must be the ones Python computes."""
    import math

    from compass import api, model

    method = _flat((ROOT / "ui" / "method.js").read_text(encoding="utf-8"))
    s = api.SCALE
    assert f"$s = {s}$ rad per nT" in method
    assert f"{model.GAMMA_E_HZ_PER_NT:.3f} Hz per nT" in method
    assert f"Ramsey time of {model.ramsey_time_us(s):.1f} µs" in method
    step = HEADLINE["storm_exact_means"]["first_step_beyond_ghz4_range"]["step_nt"]
    alias = step - model.fringe_spacing_nt(4, s)
    assert f"+{step:.1f} nT from {alias:.1f} nT".replace("-", "\N{MINUS SIGN}") in method
    assert f"2\\sqrt{{8/14}} \\approx {2 * math.sqrt(8 / 14):.2f}" in method
    assert f"(\\ln 4)/6 \\approx {model.crossover_gamma(4):.3f}" in method
    aria = model.IONQ_DOCUMENTED["aria-1"]
    assert f"visibility {model.gate_visibility(4, aria['r1'], aria['r2']):.3f} for GHZ-4" in method


def test_method_tab_and_readme_agree_on_window_sources_and_credits():
    method = _flat((ROOT / "ui" / "method.js").read_text(encoding="utf-8"))
    readme = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", _flat(README))
    for both in (
        "9 October 19:00 ET to 11 October 19:00 ET 2026",
        "2026-10-09 23:00 UTC to 2026-10-11 23:00 UTC",
        "10 October 08:00 to 12 October 08:00 in Japan",
        "2026-10-10 12:28 UTC",
        "example project Scaled Entanglement",
        "no other part of it is used",
        "Copyrights and Credits",
        "between 0 and 1.67",
        "a maximum of 9 on 10\N{EN DASH}11 May 2024",
        "doi:10.5880/Kp.0001",
    ):
        assert both in method.replace("*", "") and both in readme.replace("*", ""), both
    refs = README.split("## References", 1)[1].split("## Data and licence", 1)[0]
    firsts = re.findall(r"^- (?:[A-Z]\. )*(?:[A-Z]\. )?([A-Z][\w-]+)", refs, flags=re.M)
    assert len(firsts) >= 20
    for name in firsts:
        assert f"'{name}" in method, name
