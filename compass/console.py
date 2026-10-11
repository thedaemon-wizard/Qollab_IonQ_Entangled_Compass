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


def _gain(d: dict, n: int) -> str:
    """A ratio with its spread, e.g. '2.01× (± 0.02, 2 SE over 16 replays)'."""
    return f"{d['mean']:.2f}× (± {d['two_se']:.2f}, 2 SE over {n} replays)"


def started(info: dict) -> str:
    noise = f", noise model {info['noise_model']}" if info.get("noise_model") else ""
    return say(
        f"running on {info['name']} ({info['kind']}{noise}). Printed here: the Overview numbers, each "
        "replay, each challenge round, the 3D compass and every circuit run."
    )


def overview(o: dict) -> str:
    st = o["storm"]
    return say(
        "Overview (model replay, 1000 shots per register per minute): on the quiet day GHZ-4 is "
        f"{_gain(o['ideal'], 16)} as precise as 8 independent qubits (ideal {o['ideal']['theory']:.2f}); "
        f"with IonQ Aria 1 gate noise {_gain(o['aria1'], 16)}; with dephasing 0.2 "
        f"{_gain(o['dephasing_0_2'], 16)}. Storm of May 2024 (quick estimate, 8 replays): GHZ-4 alone "
        f"changes fringe {st['ghz4_slips']['mean']:.0f} times, the cascade "
        f"{st['cascade_slips']['mean']:.0f} times."
    )


def replay(params: dict, r: dict) -> str:
    g, s, a = r["gain_ghz4"], r["sql"]["gain_ghz4"], r["arms"]
    n = int(params.get("replicates", 32))
    return say(
        f"Replay of the {params.get('dataset', 'quiet')} record ({params.get('shots', 1000)} shots, "
        f"gate noise {params.get('gate_model', 'none')}, added dephasing "
        f"{params.get('gamma', 0) if params.get('noise') == 'indep' else 0}). On the minutes GHZ-4 stays on "
        f"the right fringe it is {_gain(g, n)} as precise as 8 independent qubits (model at zero field step "
        f"{g['theory']:.2f}) and {s['mean']:.2f}× (± {s['two_se']:.2f}) the standard quantum limit. "
        f"Over the whole record the RMS error is {a['GHZ4']['rmse']['mean']:.2f} nT for GHZ-4 alone, "
        f"{a['IND8']['rmse']['mean']:.2f} nT for 8 independent qubits and {a['CASC']['rmse']['mean']:.2f} nT "
        f"for the cascade; GHZ-4 is on a wrong fringe for {a['GHZ4']['wrong_minutes']['mean']:.0f} minutes, "
        f"the cascade for {a['CASC']['wrong_minutes']['mean']:.0f}."
    )


def run(r: dict) -> str:
    a = r["arms"]
    return say(
        f"One-minute circuit on {r['backend']['name']} ({r['n_qubits']} qubits, {r['shots']} shots, "
        f"{r['wall_s']} s): canary {100 * r['canary']:.1f}%, field step {r['dF_nT']:+.2f} nT; "
        f"cascade error {a['CASC']['error_nT']:+.2f} nT, GHZ-4 alone {a['GHZ4']['error_nT']:+.2f} nT, "
        f"2 independent qubits {a['IND2']['error_nT']:+.2f} nT."
    )


def twin_run(r: dict) -> str:
    d, s = r["reads"]["difference"], r["reads"]["sum"]
    return say(
        f"Twin circuit on {r['backend']['name']} ({r['n_qubits']} qubits, {r['shots']} shots): canary "
        f"{100 * r['canary']:.1f}%; difference pair read {d['estimate_nT']:+.1f} nT "
        f"(true {d['true_nT']:+.1f}), sum pair {s['estimate_nT']:+.1f} nT (true {s['true_nT']:+.1f})."
    )


def challenge_round(r: dict) -> str:
    mine, others = r["result"], r["others"]
    label = r["choices"][r["choice"]]["label"]
    rest = "; ".join(
        f"{r['choices'][c]['label']} {o['score']:.2f}" for c, o in others.items() if c != r["choice"]
    )
    return say(
        f"Storm challenge round {r['round'] + 1} of {r['rounds']} ({r['start'].replace('T', ' ')} to "
        f"{r['end'].replace('T', ' ')} UTC): "
        f"{label} scores {mine['score']:.2f} (RMS error {mine['rmse_nt']:.2f} nT × √(q/8), lower is better), "
        f"{mine['slips']} fringe changes; from the same start the others score: {rest}."
    )


def twin_replay(r: dict, n: int) -> str:
    g, st = r["gain"], r["steps"]
    return say(
        f"Two observatories, Boulder − Tucson replay ({r['shots']} shots): the entangled pair is "
        f"{_gain(g, n)} as precise for the difference as one qubit per site (ideal √2 = "
        f"{g['theory']:.2f}); correlation of one-minute changes r = {st['corr_one_minute_changes']:.2f}."
    )


def storm3d(r: dict) -> str:
    t, rp = r["totals"], r["replay"]
    return say(
        f"3D compass, replay {rp['shown']} of {rp['of']} of the {r['dataset']} record ({r['shots']} shots), "
        f"the one closest to their average: GHZ-4 alone changes fringe {t['GHZ4']['slips']} times and is "
        f"wrong for {t['GHZ4']['wrong_minutes']} minutes (averages {rp['mean_slips']:.1f} and "
        f"{rp['mean_wrong']:.0f}); the cascade changes fringe {t['CASC']['slips']} times, 8 independent "
        f"qubits {t['IND8']['slips']} times."
    )
