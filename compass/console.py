"""One-line summaries for Qollab's run console, where judges look for a project's results.

Each function takes the dictionary that an API call already returns and gives one line;
nothing is recomputed here. Python's print does not reach that console from a function the
page calls, so api.py returns the line as ``console_line`` and ui/py.js logs it with
``console.log``, which Qollab routes to the console.
"""

from __future__ import annotations

PREFIX = "[Entangled Compass]"


def say(text: str) -> str:
    return f"{PREFIX} {text}"


def _pm(d: dict, digits: int = 2) -> str:
    return f"{d['mean']:.{digits}f} ± {d['two_se']:.{digits}f}"


def started(info: dict) -> str:
    noise = f", noise model {info['noise_model']}" if info.get("noise_model") else ""
    return say(f"running on {info['name']} ({info['kind']}{noise}); each result is also printed here.")


def overview(o: dict) -> str:
    st = o["storm"]
    return say(
        "Overview (model replay, 1000 shots per register per minute): GHZ-4 is "
        f"{_pm(o['ideal'])}x as precise as 8 independent qubits on the quiet day "
        f"(ideal {o['ideal']['theory']:.2f}); with IonQ Aria 1 gate noise {_pm(o['aria1'])}x; "
        f"with dephasing 0.2 {_pm(o['dephasing_0_2'])}x. Storm of May 2024: GHZ-4 alone slips a fringe "
        f"{st['ghz4_slips']['mean']:.0f} times, the cascade {st['cascade_slips']['mean']:.0f} times."
    )


def replay(params: dict, r: dict) -> str:
    g, s = r["gain_ghz4"], r["sql"]["gain_ghz4"]
    return say(
        f"Replay of the {params.get('dataset', 'quiet')} record ({params.get('shots', 1000)} shots, "
        f"gate noise {params.get('gate_model', 'none')}, added dephasing "
        f"{params.get('gamma', 0) if params.get('noise') == 'indep' else 0}): GHZ-4 gain over 8 independent "
        f"qubits {_pm(g)} (model {g['theory']:.2f}), over the standard quantum limit {_pm(s)}; "
        f"GHZ-4 on a wrong fringe for {r['arms']['GHZ4']['wrong_minutes']['mean']:.0f} minutes, "
        f"the cascade for {r['arms']['CASC']['wrong_minutes']['mean']:.0f}."
    )


def run(r: dict) -> str:
    a = r["arms"]
    return say(
        f"One-minute circuit on {r['backend']['name']} ({r['n_qubits']} qubits, {r['shots']} shots, "
        f"{r['wall_s']} s): canary {100 * r['canary']:.1f}%, field step {r['dF_nT']:+.2f} nT; "
        f"cascade error {a['CASC']['error_nT']:+.2f} nT, GHZ-4 alone {a['GHZ4']['error_nT']:+.2f} nT, "
        f"one qubit {a['IND2']['error_nT']:+.2f} nT."
    )


def twin_run(r: dict) -> str:
    d, s = r["reads"]["difference"], r["reads"]["sum"]
    return say(
        f"Twin circuit on {r['backend']['name']} ({r['n_qubits']} qubits, {r['shots']} shots): canary "
        f"{100 * r['canary']:.1f}%; difference pair read {d['estimate_nT']:+.1f} nT "
        f"(true {d['true_nT']:+.1f}), sum pair {s['estimate_nT']:+.1f} nT (true {s['true_nT']:+.1f})."
    )


def storm3d(r: dict) -> str:
    t, rp = r["totals"], r["replay"]
    return say(
        f"3D compass, replay {rp['shown']} of {rp['of']} of the {r['dataset']} record ({r['shots']} shots), "
        f"the one closest to their average: GHZ-4 alone slips a fringe {t['GHZ4']['slips']} times and is "
        f"wrong for {t['GHZ4']['wrong_minutes']} minutes (average {rp['mean_slips']:.1f} and "
        f"{rp['mean_wrong']:.0f}); the cascade slips {t['CASC']['slips']} times, 8 independent qubits "
        f"{t['IND8']['slips']} times."
    )
