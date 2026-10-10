# Entangled Compass: is a GHZ sensor really √N better?

> **Theme: Quantum Playground** · Qollab × IonQ Global Quantum Hackathon 2026 · team Quantum Daemons
> Repository: https://github.com/thedaemon-wizard/Qollab_IonQ_Entangled_Compass

Qollab's own example project *Scaled Entanglement* says that an N-qubit GHZ sensor is √N times
more precise than N independent sensors. That is true in the ideal case: the same qubits, the
same interrogation time, no noise, and a field already known to within a narrow range. This
playground puts simulated qubit sensors on a **real record**, the total magnetic field measured
at the USGS Boulder observatory, on a quiet day and through the G5 storm of 10–11 May 2024, and
lets you find out where the √N survives and where it breaks.

Everything quantum here is a Qiskit circuit or the exact model of one; the field data are real;
nothing ran on a magnetometer or on quantum hardware.

## What it does

- **Storm challenge** (the game). Twelve two-hour rounds through the storm. Before each round
  you see only the past and pick a sensor: 8 independent qubits, a GHZ-4 pair of registers
  (twice as precise, but it loses its place if the field jumps more than ±39.3 nT in one
  minute), or a 1-2-4 cascade that costs 14 qubits. The round is replayed with your pick and
  compared with what the other two would have done from the same starting point and the same
  random draws. A GHZ-4 that jumps a fringe stays wrong until you switch to a wider-range
  sensor.
- **Field tracker.** Replays a whole record with every sensor arm (32 replays) and shows the
  field, each arm's estimate and its error, with a table of RMS error, minutes on a wrong
  fringe and fringe jumps. Settings: record (quiet day or storm), shots, added dephasing γ, and
  the gate noise used in the replay (ideal, IonQ Aria 1 as documented, or the visibilities
  measured in your last circuit run).
- **One minute on the quantum simulator.** One packed circuit holds every sensor (GHZ-1,
  GHZ-2, GHZ-4 read in X and in Y, a single qubit that passes the field four times, and a
  canary qubit) and is run as **one job** on the backend chosen in Qollab's Run dialog. The
  result is shown as **compass dials**: the needle angle is the phase the sensor measured,
  atan2(⟨Y⟩, ⟨X⟩); its length is the measured visibility. A GHZ-4 needle turns four times as
  far as a single qubit's; past half a turn it still points the right way, but reading it back
  gives the wrong field. Next to the dials, the fringes cos(m·s·ΔF) show why.
- **Overview.** The claim, four answers computed when the page opens, and what is real and
  what is simulated.

## Run it

**On Qollab:** open the project and press **Run** (the free built-in simulator is fine). Start
with the Storm challenge, then open the Field tracker and press **Run the sensor circuit (one
job)**. To use IonQ's noise-model simulator, pick it in the Run dialog: the app submits exactly
one job per Run and refuses a second one.

**Locally** (Python 3.14):

```
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q                                   # 43 tests
.venv/bin/python tools/devserver/server.py            # http://127.0.0.1:8770/tools/devserver/dev.html
PYTHONPATH=. .venv/bin/python scripts/headline_numbers.py   # every number in this README
```

## How it works

- **Field to phase.** Each minute the residual field step becomes a qubit phase δ = s·(F − F̂),
  with s = 0.02 rad per nT (an electron spin with a 113.6 µs Ramsey time; this mapping is a
  model choice and is fixed, because the slip counts below depend on it). F̂ is the sensor's
  previous estimate: a classical predictor sets the working point, the quantum readout measures
  what is left, and the estimate moves by δ̂/s. Nothing else is fitted.
- **Sensors.** A GHZ register of m qubits after Rz(δ) on every qubit is
  (|0…0⟩ + e^{imδ}|1…1⟩)/√2. Read with H on every qubit, its parity has mean V·cos(mδ); with
  Sdg on the first qubit first, V·sin(mδ). The angle atan2(Y, X)/m estimates δ, but only
  modulo 2π/m. V is the visibility.
- **Fair comparison.** GHZ-4 read in X and in Y uses 8 qubits per shot; the baseline is a
  *matched unentangled sensor* with the same 8 qubits (4 read X, 4 read Y) and the same shots.
  Ideal standard deviations: 1/(4s√S) against 1/(2s√S) per minute, a factor 2 = √4. (This
  baseline is √2 above the standard quantum limit because its X quadrature carries little
  information near δ = 0; GHZ-4 loses the same factor, so the ratio is still 2.)
- **Cascade.** The single qubit fixes the coarse value; GHZ-2 and GHZ-4 refine it, so the
  estimate is never on a wrong fringe while one-minute steps stay below ±157 nT. Cascades extend
  the unambiguous range (theory: Higgins et al. 2007; Kimmel et al. 2015 with its 2021
  erratum; demonstrated with GHZ states by Cao et al. 2024, whose cascade still stayed about
  2 dB above the standard quantum limit, and by Finkelstein et al. 2024). It costs 14 qubits, so it is
  compared with 14 independent qubits (ideal gain 2·√(8/14) ≈ 1.51).
- **Noise.** *Gate noise*: IonQ documents its Aria models (and Forte jobs before mid-September
  2025) as depolarizing after each gate; for our gate counts this leaves GHZ-4 a visibility of
  0.958 on Aria 1. *Independent dephasing* γ is added by this app (layout B): one extra qubit
  per register, prepared in |+⟩ and coupled by CX·Rz(b)·CX, makes the register see Rz(+b) or
  Rz(−b) with equal odds. With cos b = e^{−mγ} this equals independent dephasing of each of the
  m qubits as seen by the GHZ coherence, which decays as e^{−mγ} (Huelga et al. 1997); the
  construction is ours.
- **One job.** The canary qubit (X, then measure) must read 1 on every shot; if it does not, the
  bit order of the returned keys is wrong and the app stops instead of guessing. Counts are read
  with `backend.run` and `get_counts()`; no Sampler.

## Results

Model replay of the same parity measurement, s = 0.02 rad/nT, 1000 shots per register per
minute, mean ± 2 standard errors over 32 replays (quiet day) unless stated; all values are in
`results/headline_numbers.json` and are recomputed by `scripts/headline_numbers.py`.

| Quiet day, gain of GHZ-4 over the matched unentangled sensor | Replay | Model at δ = 0 |
|---|---|---|
| Ideal gates | 2.00 ± 0.02 | 2 |
| IonQ Aria 1 gate noise (documented rates) | 1.92 ± 0.02 | 1.918 |
| Dephasing γ = 0.05 per qubit | 1.72 ± 0.02 | 2e^{−3γ} = 1.721 |
| Dephasing γ = 0.10 | 1.48 ± 0.01 | 1.482 |
| Dephasing γ = 0.20 | 1.10 ± 0.01 | 1.098 |

- At fixed interrogation time, GHZ-4 stops beating 4 independent qubits at γ = ln 4 / 6 ≈ 0.231
  (0.347 for N = 2, 0.149 for N = 8). If the interrogation time may be re-optimised, Huelga et
  al. show that the GHZ state and independent qubits then reach the same best precision; for uncorrelated (Markovian) noise any
  entanglement gain is asymptotically a constant factor (Demkowicz-Dobrzański et al. 2012).
- **The storm.** With exact means (no shot noise), GHZ-4 alone jumps a fringe 20 times, first
  at 21:47 UTC on 10 May (+44.6 nT in one minute), and is on a wrong fringe for 1,115 of the
  2,879 minutes (by 78.5 or 157.1 nT); the cascade and the independent qubits never are. With
  shot noise (200 replays): 20 jumps in 152 replays, 21 in 48; wrong-fringe minutes median
  1,115, range 436–1,268; cascade and independent qubits 0 jumps in every replay.
- **The challenge.** Mean scores of the fixed strategies (lower is better):
  always 8 independent qubits 0.77, always GHZ-4 49.6, always cascade 0.47. Five of the twelve
  rounds (3, 4, 6, 8, 9) contain a one-minute step beyond GHZ-4's range, so a player who uses
  GHZ-4 in the calm rounds and the cascade in the stormy ones beats every fixed strategy (for
  example 0.42 in our test game).
- **Circuit runs** (one job each): see "Where it ran".

## Where it ran

| Backend | What | Result |
|---|---|---|
| Local Qiskit BasicSimulator (tests and harness) | layout A, 2024-05-10 21:47 UTC, 1000–2000 shots | canary 1.000; cascade within ±1 nT, GHZ-4 alone one fringe off (−78 nT), as the model says |
| Qollab built-in simulator | *to be run on the published project* | |
| Qollab IonQ noise-model simulator | *to be run (one job)* | |

## The original part

- A playable test of a sentence from Qollab's own example: the example prepares GHZ states and
  counts all-0 and all-1 outcomes in the Z basis, which cannot show phase coherence; here the
  GHZ phase is read in X and Y and turned into a field estimate.
- **New problem context**: real geomagnetic data (USGS Boulder, a G5 storm), where the range of
  the GHZ fringe matters as much as its precision.
- **Comparative benchmarking under noise**: equal-resource comparison of GHZ-4, the cascade and
  matched unentangled sensors, under IonQ's documented gate noise and added dephasing, with the
  model value next to every replay number.
- **A new way to show it**: compass dials whose needles are the measured phases, and a game in
  which you decide when entanglement is worth the risk.

## What didn't work

- The plan to let the user choose the phase per nT (0.01–0.05 rad): at 0.05 even the cascade
  and the independent qubits jump fringes in the storm, so every headline would need its own
  conditions. The scale is fixed at 0.02 and printed next to the numbers.
- A common-mode ("everyone gets the same kick") noise model was designed but left out: in a
  magnetometer a field change shared by all sensors is the signal, so it would need a different
  physical story (for example reference-oscillator phase noise).

## Limits: what this app does not claim

- It does not compare the simulated sensors with the observatory's instruments; the USGS data
  are the truth here, not an opponent.
- The sensors are simulated: Rz(δ) stands for a field acting on a qubit. Nothing ran on a
  magnetometer or on quantum hardware.
- Only N = 1, 2 and 4 come from circuits. The replay is a model of the same parity measurement
  (binomial shot noise with the register's visibility); tests check it against the circuits.
- One update per minute with an interrogation of about 0.1 ms is a model choice; real
  magnetometers sample much faster, which would shrink the one-minute steps.
- The IonQ noise models are used as IonQ documents them. The current Forte models are not
  publicly documented; the app reports what it measures and assumes nothing about them.

## With more time

- A differential (Bell-pair) gradiometer that cancels a field shared by two sites
  (Ruster et al. 2017), with a labelled synthetic gradient.
- Re-optimised interrogation time per noise level, to show Huelga's tie directly.
- More storms (for example October 2024) as out-of-sample challenge maps.

## Accessibility

Keyboard-only use (tabs with arrow keys, Home and End; every control is a native button,
select or slider with a label), visible focus, live status messages, focus moved to each new
challenge round, charts as SVG with a title, a description that states the numbers and a data
table, series that differ by dash as well as colour, dark and light schemes, and no horizontal
page scroll at 320 px.

## Disclosure

- Built during the hackathon window (10–12 October 2026). It is a second entry next to the
  author's *Bell-Test Lab* (Quantum Unlocked); no code is shared between the two.
- The USGS records were downloaded on 2026-10-10 by `scripts/fetch_usgs.py`.
- Use of AI: generative-AI coding assistance was used for code, documents and research drafts,
  including independent checks of the physics and the test vectors; the author checked the
  results.

## References

- J. J. Bollinger, W. M. Itano, D. J. Wineland, D. J. Heinzen, Phys. Rev. A 54, R4649 (1996).
- S. F. Huelga et al., Phys. Rev. Lett. 79, 3865 (1997).
- D. Leibfried et al., Science 304, 1476 (2004): three entangled ions, 1.45(2) times the
  sensitivity of three unentangled ones (ideal √3 ≈ 1.73).
- B. L. Higgins et al., Nature 450, 393 (2007).
- T. Monz et al., Phys. Rev. Lett. 106, 130506 (2011): coherence of GHZ states of up to 8 ions
  decays with N² under correlated noise.
- R. Demkowicz-Dobrzański, J. Kołodyński, M. Guţă, Nat. Commun. 3, 1063 (2012).
- S. Kimmel, G. H. Low, T. J. Yoder, Phys. Rev. A 92, 062315 (2015); erratum Phys. Rev. A 104,
  069901 (2021).
- A. Cao et al., Nature 634, 315 (2024); R. Finkelstein et al., Nature 634, 321 (2024).
- T. Ruster et al., Phys. Rev. X 7, 031050 (2017).
- IonQ, Simulation with noise models, docs.ionq.com (read 2026-10-10).
- USGS Geomagnetism Program web service, geomag.usgs.gov/ws (read 2026-10-10).

## Data and licence

Geomagnetic data: USGS Geomagnetism Program, Boulder (BOU) observatory, courtesy of the U.S.
Geological Survey; thanks to INTERMAGNET (www.intermagnet.org) for promoting high standards of
magnetic observatory practice. The storm record is quasi-definitive, the quiet day adjusted;
values are as served. The data in `data/` are not covered by this project's licence.

Code and documentation: MIT licence (see LICENSE).

This effort is supported by Qollab & IonQ.
