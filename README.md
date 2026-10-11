# Entangled Compass: is a GHZ sensor really $`\sqrt{N}`$ better?

> **Theme: Quantum Playground** · Qollab × IonQ Global Quantum Hackathon 2026 · team Quantum Daemons
> Repository: https://github.com/thedaemon-wizard/Qollab_IonQ_Entangled_Compass

**Demo video (2:54):** https://youtu.be/IomHduFJqyc

*One continuous take on Qollab's free built-in simulator; synthetic narration, English captions.
The gains it narrates are over 8 independent qubits read the same X/Y way (the matched sensor):
2.00 with ideal gates, 1.92 with IonQ Aria 1's documented gate noise and 1.05 with that noise plus
dephasing $`\gamma = 0.2`$. Against the standard quantum limit (SQL) the same settings give
$`\sqrt{2} \approx 1.41`$, 1.36 and 0.74 (a loss). The twin pair's 1.42 is over one qubit per site, and
for a difference it only matches the SQL. All of these are model replays (see Results).*

Qollab's own example project [*Scaled Entanglement*](https://qollab.xyz/u/qollab/scaled-entanglement)
says that an $`N`$-qubit GHZ sensor is $`\sqrt{N}`$ times
more precise than $`N`$ independent sensors. That is true in the ideal case: the same qubits, the
same interrogation time, no noise, and a field already known to within a narrow range. This
playground puts simulated qubit sensors on a **real record**, the total magnetic field measured
at the USGS Boulder observatory, on a quiet day and through the G5 storm of 10–11 May 2024, and
lets you find out where the $`\sqrt{N}`$ survives and where it breaks.

Everything quantum here is a Qiskit circuit or a model of the same parity measurement (exact for
ideal gates and the added dephasing; an estimate for IonQ's gate noise); the field data are real;
nothing ran on a magnetometer or on quantum hardware.

![The 3D compass tab at 21:47 UTC on 10 May 2024, the storm's first field step beyond GHZ-4's range (+44.6 nT): three stacked needles; GHZ-4 alone is drawn red and the text panel says it reads −158° on a wrong fringe, while the cascade's GHZ-4 register reads −156° on the right fringe and 8 independent qubits read +52°.](docs/figures/screen_3d.png)

## In one minute

- **What it is.** A game and a lab on one question: does entanglement make a better magnetic
  sensor? Simulated GHZ sensors track the real field at Boulder, minute by minute, against
  unentangled sensors given the same qubits and shots. The tracking is a model replay of the
  circuits' parity measurement; one minute runs as a Qiskit circuit, one job per Run.
- **Precision (quiet day, model replay, 32 replays).** GHZ-4 is 2.00 ± 0.02 times as precise as
  8 independent qubits read the same X/Y way, and $`\sqrt{2} \approx 1.41`$ times as precise as
  the SQL for those 8 qubits. With IonQ Aria 1's documented gate-noise rates (a model replay,
  not an IonQ run) the gains are 1.92 and 1.36; adding dephasing $`\gamma = 0.2`$ per qubit
  leaves 1.05 and 0.74.
- **Range (the storm).** GHZ-4 reads a field step only up to ±39.27 nT per minute. In the storm
  it changes fringe 20 times and is on a wrong fringe for 1,115 of 2,879 minutes; the 1-2-4
  cascade (14 qubits) never is. In the game, switching to the cascade when the storm grows beats
  every fixed choice.
- **On Qollab's simulators.** One packed circuit per Run (17 qubits; 13 for the twin sensors),
  recorded on the built-in simulator, the AWS Braket local simulator, an IBM noise model (Boston)
  and IonQ's Aria 1 noise-model simulator, and the twin circuit on IonQ's Forte 1 noise-model
  simulator (see "Where it ran").
- **Run it on Qollab.** Open the **Code** tab, click **Run Project**, then **Run**; in **Select
  QPU** keep the free *Built-in simulator* (or pick another free simulator) and click **Run**
  again. The demo video above shows these steps and every tab.

## Why this matters beyond the game

Precision against dynamic range is a real design trade-off in quantum magnetometers. Single spins
in diamond have been run as high-dynamic-range magnetometers (Nusran et al. 2012; Waldherr et
al. 2012). In an optical clock, GHZ states of up to 4 qubits beat the SQL at short dark times,
but because of their reduced dynamic range a single GHZ size did not improve the clock at the
optimal dark time; a cascade of GHZ sizes extends the range (Cao et al. 2024; cascade theory:
Kessler et al. 2014). On superconducting processors, smaller GHZ subsets run in parallel came close
to the best sensitivity, and the authors note that the range of measurable fields falls as the
number of entangled qubits grows (Slepnev et al. 2026). Here a GHZ register of $`m`$ qubits loses its fringe when the field
step per update exceeds $`\pm\pi/(m\,s)`$: ±39.27 nT for GHZ-4 at $`s = 0.02`$ rad per nT. A smaller
$`s`$ (a shorter interrogation) widens that range but lowers the precision of each update, and a
faster cadence makes the field steps smaller; what carries over to a real instrument is the
trade-off, not the count. Students and teachers can test the textbook $`\sqrt{N}`$ against a real record and see
which condition breaks it. Sensor engineers can take two habits from it: quote precision together
with range, and compare against the SQL, not only against a matched sensor read the same way.

## What it does

- **Storm challenge** (the game). Twelve two-hour rounds through the storm. Before each round
  you see only the past and pick a sensor: 8 independent qubits, a GHZ-4 pair of registers
  (twice as precise, but it loses its place if the field jumps more than ±39.3 nT in one
  minute), or a 1-2-4 cascade that costs 14 qubits. The round is replayed with your pick and
  compared with what the other two would have done from the same start and the same random
  seed. Keeping a sensor keeps its estimate, so a GHZ-4 on a wrong fringe stays there until
  another jump happens to bring it back; switching starts the new sensor from a fresh absolute
  fix (we assume a slow absolute reference, such as the observatory's own instrument, is
  available when you switch). The rounds are not circuit runs: each replays the same parity
  measurement as the circuits (binomial shot noise; tests check it against Qiskit runs), with
  the visibilities measured in your last circuit run if there is one, ideal ones otherwise.
  Score per round: RMS error × $`\sqrt{q/8}`$ for a sensor of $`q`$ qubits, lower is better.

  ![The Storm challenge's final card: GHZ-4 in rounds 1 and 2, then the cascade, gives a mean score of 0.46, which beats every fixed strategy (always 8 independent qubits 0.77, always GHZ-4 49.61, always cascade 0.47); a table lists each round's pick, score, fringe changes and best pick.](docs/figures/screen_challenge.png)

- **Field tracker.** Replays a whole record with every sensor arm (32 replays) and shows the
  field, each arm's estimate and its error, with a table of RMS error, minutes on a wrong
  fringe and fringe changes. Settings: record (quiet day or storm), shots, added dephasing $`\gamma`$, and
  the gate noise used in the replay (ideal, IonQ Aria 1 as documented, or the visibilities
  measured in your last circuit run).
- **One minute on the quantum simulator.** One packed circuit holds every sensor (GHZ-1,
  GHZ-2, GHZ-4 read in X and in Y, a single qubit that passes the field four times, and a
  canary qubit) and is run as **one job** on the backend chosen in Qollab's Run dialog. The
  result is shown as **compass dials**: the needle angle is the phase the sensor measured,
  $`\operatorname{atan2}(\langle Y\rangle, \langle X\rangle)`$; its length is the measured visibility. A GHZ-4 needle turns four times as
  far as a single qubit's; past half a turn it still points the right way, but reading it back
  gives the wrong field. Next to the dials, the fringes $`\cos(m\,s\,\Delta F)`$ show why. This
  button (in the Field tracker) and the Two observatories tab are where circuits run; the other
  tabs replay the model.

  ![One circuit run in the Field tracker at 21:47 UTC on 10 May 2024 (Qiskit BasicSimulator on the local harness, 1000 shots, 17 qubits): compass dials for 1 qubit and GHZ-2 on the right fringe, GHZ-4 and the 4-pass qubit on a wrong fringe, and the X-parity fringes of 1 qubit, GHZ-2 and GHZ-4 against the field step.](docs/figures/screen_tracker.png)

- **3D compass.** The storm played back on a three-dimensional compass (three.js), minute by
  minute: three stacked needles for 8 independent qubits, GHZ-4 alone and the cascade's GHZ-4
  register. Each needle points where its register reads back; a tube under it shows how far
  that minute's field step turned it, $`m\,s\,\Delta F`$, which can be more than half a turn.
  While GHZ-4 alone sits on a wrong fringe its tube and hub are red, and its count of fringe
  changes goes up each time it leaves or regains the right one; the cascade's register turns
  just as far, but its 1-qubit and GHZ-2 registers tell it which turn it is on. Play, pause,
  step a minute, jump to the first fringe change, scrub, or turn the view with the mouse or
  buttons; a text panel gives the same numbers for every minute. The needles come from one
  replay of 32 (seed 0) and show the most common outcome: 26 of the 32 replays give 20 fringe
  changes and 1,115 minutes on a wrong fringe, the other 6 give 21 changes and 436 minutes
  (back on the right fringe sooner). The averages the tab also prints, 20.2 and 988, therefore
  describe no single replay. Every angle is computed in Python.
- **Two observatories** (a what-if). One qubit at Boulder and one at Tucson, about 1,000 km apart,
  entangled as $`(\lvert 01\rangle + \lvert 10\rangle)/\sqrt{2}`$, pick up only the *difference* of the two fields, so anything
  both sites feel cancels; as $`(\lvert 00\rangle + \lvert 11\rangle)/\sqrt{2}`$ they pick up the sum. Trapped-ion experiments use
  this to ignore magnetic noise shared by two ions millimetres apart (Ruster et al. 2017). The
  app replays the real storm at both observatories and runs one minute of the 13-qubit twin
  circuit as one job. It is a what-if: sharing entangled sensor qubits between observatories
  would need a quantum network that does not exist yet (entangled photons, not sensor qubits,
  have been shared between ground stations over 1,200 km apart by satellite: Yin et al. 2017).
- **Overview.** The claim, four answers computed when the page opens, and what is real and
  what is simulated.

## Run it

**On Qollab:** open the **Code** tab, click **Run Project**, then **Run**; in **Select QPU** keep
the free *Built-in simulator* (or pick another free simulator) and click **Run** again. Open the
Field tracker and press **Run the sensor circuit (one job)**, then play the Storm challenge,
which uses the visibilities that run measured. To use an IonQ noise-model simulator, pick it in
**Select QPU**: IonQ backends accept one job per run (Qollab docs, *Compute backends*, read
2026-10-11), and the app submits exactly one and refuses a second. The circuit run takes about
0.1 s on the built-in simulator and about 14 s on the IBM Boston noise model at 200 shots (see
"Where it ran"). Qollab's run console gets one line per result: the
Overview numbers at start-up, then each replay, each challenge round, the 3D compass and every
circuit run. For example `[Entangled Compass] One-minute circuit on basic_simulator (17 qubits,
1000 shots, …): canary 100.0%, field step +44.59 nT; cascade error +0.12 nT, GHZ-4 alone
-78.42 nT, 2 independent qubits +1.52 nT.`

**Locally** (Python 3.14):

```
python3.14 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q                         # more than 120 tests
.venv/bin/python tools/devserver/server.py            # http://127.0.0.1:8770/tools/devserver/dev.html
PYTHONPATH=. .venv/bin/python scripts/headline_numbers.py   # the model-replay numbers in Results
```

## How it works

![One minute of the model: real field, phase δ = s·ΔF, GHZ register, X/Y parity readout, update; the estimate loops back.](docs/figures/model.png)

*Figure 1. One minute of the model. Outlines and tag words mark what is real (solid), a model
choice (dashed), simulated (double outline) and classical arithmetic (dotted). Nothing ran on a
magnetometer or on quantum hardware.*

- **Field to phase.** Each minute the residual field step becomes a qubit phase $`\delta = s\,(F - \hat{F})`$,
  with $`s = 0.02`$ rad per nT (an electron spin with a 113.6 µs Ramsey time; this mapping is a
  model choice and is fixed, because the slip counts below depend on it). $`\hat{F}`$ is the sensor's
  previous estimate: a classical predictor sets the working point, the quantum readout measures
  what is left, and the estimate moves by $`\hat{\delta}/s`$. Nothing else is fitted.
- **Sensors.** A GHZ register of $`m`$ qubits after $`R_z(\delta)`$ on every qubit is
  $`(\lvert 0\dots 0\rangle + e^{im\delta}\lvert 1\dots 1\rangle)/\sqrt{2}`$. Read with H on every qubit, its parity has mean $`V\cos(m\delta)`$; with
  Sdg on the first qubit first, $`V\sin(m\delta)`$. The angle $`\operatorname{atan2}(Y, X)/m`$ estimates $`\delta`$, but only
  modulo $`2\pi/m`$. $`V`$ is the visibility.

![One sensor register (GHZ-4 read in Y) as a circuit, with the dephasing ancilla of layout B, and the 17-qubit map of the packed circuit.](docs/figures/circuit.png)

*Figure 2. Top: one of the eight sensor registers as `compass/circuits.py` builds it; the grey
dashed box (and the dashed ancilla wire) is added only in layout B. Bottom: every sensor and the canary qubit in the one circuit that
runs as one job.*

- **Fair comparison.** GHZ-4 read in X and in Y uses 8 qubits per shot; the baseline is a
  *matched unentangled sensor* with the same 8 qubits (4 read X, 4 read Y) and the same shots.
  Ideal standard deviations: $`1/(4s\sqrt{S})`$ against $`1/(2s\sqrt{S})`$ per minute, a factor $`2 = \sqrt{4}`$. (This
  baseline is $`\sqrt{2}`$ above the standard quantum limit: near $`\delta = 0`$ the $`\operatorname{atan2}(Y, X)`$ estimate draws
  its information from the Y readings only. GHZ-4 read the same way loses the same factor, so
  the ratio is still 2.)
- **Cascade.** The single qubit fixes the coarse value; GHZ-2 and GHZ-4 refine it, so the
  estimate is never on a wrong fringe while one-minute steps stay below ±157 nT. Cascades extend
  the unambiguous range (theory: Kessler et al. 2014 for GHZ cascades in clocks, and Kimmel et
  al. 2015 with its 2021 erratum; without entanglement, by passing the phase several times, in
  the experiment of Higgins et al. 2007; with GHZ states by Cao et al. 2024, whose cascade still
  stayed about 2 dB above the standard quantum limit; a GHZ cascade with readout in two
  quadratures was also shown by Finkelstein et al. 2024). It costs 14
  qubits, so it is compared with 14 independent qubits (ideal gain $`2\sqrt{8/14} \approx 1.51`$).
- **Noise.** *Gate noise*: IonQ documents its Aria models (and Forte jobs before
  mid-September 2025) as depolarizing after each gate; counting the abstract gates of our circuit (H, X, CX;
  Rz and Sdg taken as noise-free virtual rotations) this leaves GHZ-4 a visibility of 0.958 on
  Aria 1. IonQ compiles to native gates before applying the noise, so this is an estimate; the
  run reports the measured visibility. *Independent dephasing* $`\gamma`$ is added by this app (layout B): one extra qubit
  per register, prepared in $`\lvert +\rangle`$ and coupled by $`\mathrm{CX}\cdot R_z(b)\cdot\mathrm{CX}`$, makes the register see $`R_z(+b)`$ or
  $`R_z(-b)`$ with equal odds. With $`\cos b = e^{-m\gamma}`$ this equals independent dephasing of each of the
  $`m`$ qubits as seen by the GHZ coherence, which decays as $`e^{-m\gamma}`$ (Huelga et al. 1997); the
  construction is ours.
- **One job.** The canary qubit (X, then measure) must read 1; if it reads 1 in fewer than 90% of
  shots, the bit order of the returned keys is wrong and the app stops instead of guessing.
  Counts are read with `backend.run` and `get_counts()`; no Sampler.

![Architecture: USGS records feed the replay model and the packed Qiskit circuit inside the Python package; the circuit runs as one job on the backend chosen in Qollab's Run dialog; the estimators feed the JavaScript views.](docs/figures/architecture.png)

*Figure 3. Where each number comes from. The JavaScript views reach Python only through
`ui/py.js`, as JSON strings.*

## Results

Model replay of the same parity measurement, $`s = 0.02`$ rad/nT, 1000 shots per register per
minute, mean ± 2 standard errors over 32 replays (quiet day, seed 0) unless stated. The values
below are in `results/headline_numbers.json` and are recomputed by `scripts/headline_numbers.py`;
that file also ships in the Qollab project, next to the recorded runs in `results/qollab/`, so
they can be checked there. (The Overview tiles use a quicker 16 replays with seed 1 and read
2.01 and 1.94 for the first two rows, within the error bars.)

| Quiet day, gain of GHZ-4 over… | the matched unentangled sensor (replay / model) | the standard quantum limit (replay / model) |
|---|---|---|
| Ideal gates | 2.00 ± 0.02 / 2 | 1.41 ± 0.01 / $`\sqrt{2}`$ |
| IonQ Aria 1 gate noise (documented rates) | 1.92 ± 0.02 / 1.918 | 1.36 ± 0.01 / 1.356 |
| Dephasing $`\gamma = 0.05`$ per qubit | 1.72 ± 0.02 / 1.721 | 1.21 ± 0.01 / 1.217 |
| Dephasing $`\gamma = 0.10`$ | 1.48 ± 0.01 / 1.482 | 1.04 ± 0.01 / 1.048 |
| Dephasing $`\gamma = 0.20`$ | 1.10 ± 0.01 / 1.098 | 0.78 ± 0.01 / 0.776 |
| IonQ Aria 1 gate noise and dephasing $`\gamma = 0.20`$ (as narrated in the video) | 1.05 ± 0.01 / 1.053 | 0.743 ± 0.005 / 0.744 |

**The strong baseline.** The standard quantum limit (SQL) for the same 8 qubits and 1000 shots
per minute is the best precision any unentangled sensor can reach with one interrogation of the
same length per qubit, every qubit read at its most sensitive point: 0.559 nT per minute here
(for ideal gates). It is a stricter opponent than the matched sensor, which sits $`\sqrt{2}`$ above it.
The X/Y GHZ-4 readout used here beats the SQL by $`\sqrt{2}`$ ideally, by 1.36 under IonQ's documented
Aria 1 gate noise, and no longer beats it once $`\gamma \ge (\ln 2)/6 \approx 0.116`$ per qubit (at fixed
interrogation time). An optimally read GHZ-4 would beat it by 2 and keep a gain until
$`\gamma \approx 0.231`$, but it needs the working point known even more closely; the 4-pass single qubit
beats the SQL only by spending four times the interrogation time. This is the measurable
difference the app reports, with its model value, for every setting.

- At fixed interrogation time, GHZ-4 stops beating 4 independent qubits at $`\gamma = (\ln 4)/6 \approx 0.231`$
  (0.347 for $`N = 2`$, 0.149 for $`N = 8`$). If the interrogation time may be re-optimised, Huelga et
  al. show that the GHZ state and independent qubits then reach the same best precision; for uncorrelated (Markovian) noise any
  entanglement gain is asymptotically a constant factor (Demkowicz-Dobrzański et al. 2012).
- **The storm.** With exact means (no shot noise), GHZ-4 alone changes fringe 20 times, first
  at 21:47 UTC on 10 May (+44.6 nT in one minute), and is on a wrong fringe for 1,115 of the
  2,879 minutes (by 78.5 or 157.1 nT); the cascade and the independent qubits never are. A
  fringe change is what the clock literature calls a phase slip (Direkci et al. 2026). With
  shot noise (200 replays, seed 3): 20 fringe changes in 152 replays, 21 in 48; wrong-fringe
  minutes median 1,115, range 436–1,268; cascade and independent qubits never change fringe.
  The outcome is close to two-valued, so a mean misleads: the 3D compass's 32 replays (seed 0)
  give 1,115 minutes in 26 and 436 in 6 (mean 988), and the Overview's quick 8 replays (seed 2)
  give 1,115 in 7 and 436 in 1 (mean about 1,030).
- **The challenge.** Score = mean over the 12 rounds of RMS error × $`\sqrt{q/8}`$ (lower is
  better). Fixed strategies at the app's seed 7: always 8 independent qubits 0.77, always GHZ-4
  49.6 (34.4–49.6 over seeds 7–12), always cascade 0.47. Five of the twelve rounds (3, 4, 6, 8,
  9) contain a one-minute step beyond GHZ-4's range. Keeping GHZ-4 for the first two rounds and
  then the cascade for good, as in the demo video, scores 0.46, below always-cascade for each of
  seeds 7–12. That plan needs no round-by-round foresight, but its switch point was chosen
  knowing when the storm grows. With full hindsight (GHZ-4 only in the seven calm rounds) the
  score is 0.41. Switching back to GHZ-4 after every round without a big step costs far more
  (16.5): calm and stormy rounds alternate, so that rule puts GHZ-4 into the stormy rounds 3, 6
  and 8.
- **Two observatories.** The storm is *not* common noise across 1,000 km: one-minute changes at
  Boulder and Tucson correlate only $`r = 0.33`$ ($`r^2 = 0.11`$), and only 29% of their summed variance
  cancels in the difference, so the
  Boulder − Tucson difference jumps almost as much as Boulder itself (standard deviation of
  one-minute steps 7.95 nT against 8.13 nT; largest 119.6 nT). What remains is the plain
  advantage of measuring a difference directly: with the same 4 qubits per shot the entangled
  pair tracks the difference 1.42 ± 0.01 times as precisely as one qubit per site (ideal $`\sqrt{2}`$;
  1.56 against 2.21 nT). Read in X and Y, the pair only matches the SQL for a difference
  with 4 qubits (1.58 nT); an optimally read pair would beat it by $`\sqrt{2}`$. At the storm's onset
  (17:06 UTC) both sites jumped together (+12.6 and +21.5 nT): the difference pair ideally
  reads −9.0 nT of it and the sum pair +34.1 nT (the 200-shot Forte 1 noise-model run in "Where
  it ran" read −3.1 and +33.4).
- **Circuit runs** (one job each): see "Where it ran".

## Where it ran

| Backend | What | Result |
|---|---|---|
| Local Qiskit BasicSimulator (tests and harness) | layout A, 2024-05-10 21:47 UTC, 1000–2000 shots | canary 1.000; cascade within ±1 nT, GHZ-4 alone one fringe off (−78 nT), as the model says |
| Qollab built-in simulator (2026-10-10 13:52 UTC; values transcribed by hand from the run card, counts not exported) | layout A, 2024-05-10 21:47 UTC, 1000 shots, one job, 0.10 s | canary 1.000; cascade +0.29 nT, GHZ-4 alone −78.25 nT (one fringe off); visibilities GHZ-1/2/4 = 0.996 / 0.996 / 1.018 |
| Qollab IonQ Aria 1 noise-model simulator (13:57 UTC) | the same, 200 shots, one job, 12.5 s | canary 1.000; cascade +0.29 nT, GHZ-4 alone −78.25 nT; measured visibilities GHZ-1/2/4 = 1.00 / 0.97 / 0.92 (documented-rate estimate 0.999 / 0.985 / 0.958; with 200 shots the standard error of each is about 0.03–0.05, by the delta method from the recorded parities), so $`2V_4/V_1 = 1.83`$ |
| Qollab IonQ Forte 1 noise-model simulator (14:10 UTC) | twin circuit (13 qubits), 2024-05-10 17:06 UTC, 200 shots, one job, 13.0 s | canary 1.000; difference pair read −3.1 nT (true −9.0), sum pair +33.4 nT (true +34.1), single qubits +9.3 and +20.6 nT (true +12.6 and +21.5); one standard error is about 3.5 nT for a pair at 200 shots |
| Qollab IonQ Aria 1 noise-model simulator (23:21 UTC) | layout A, 2024-05-10 21:47 UTC, 200 shots, one job, 11.9 s | canary 1.000; cascade −1.99 nT, GHZ-4 alone −80.53 nT (one fringe off) |
| Qollab built-in simulator (2026-10-11 07:39 UTC, the demo video) | layout A, 2024-05-10 21:47 UTC, 1000 shots, one job, 0.105 s | canary 1.000; cascade −0.22 nT, GHZ-4 alone −78.76 nT (one fringe off) |
| Qollab IBM Boston noise-model simulator (Heron r3 architecture, 156 qubits; 2026-10-11 13:27 UTC) | layout A, 2024-05-10 21:47 UTC, 200 shots (the app caps IBM noise models at 200), one job, 14.2 s | canary 0.99; cascade +0.34 nT, GHZ-4 alone −78.20 nT (one fringe off) |
| Qollab AWS Braket local simulator (2026-10-11 13:33 UTC) | layout A, 2024-05-10 21:47 UTC, 1000 shots, one job, 3.7 s | canary 1.000; cascade +0.10 nT, GHZ-4 alone −78.44 nT (one fringe off) |

The built-in (13:52 UTC) and IonQ Aria 1 (13:57 UTC) rows show the same GHZ-4 and cascade
readings to 0.01 nT. Both readings depend only on the angle of the GHZ-4 register,
$`\theta_4 = \operatorname{atan2}(Y, X)`$ of its parities (−0.400 and −0.830 in the 13:57 run), so equal
angles give equal readings, while the other registers differ. Two independent samples agreeing
this closely is unlikely, and the 13:52 row was read off the screen with no
counts kept, so a copying error in that row cannot be ruled out; treat its GHZ-4 and cascade
values as unconfirmed. The 23:21 UTC run is a separate 200-shot sample and reads differently
(cascade −1.99 nT). IonQ has retired the Aria 1 hardware; Qollab still offers its noise model
(Qollab docs, *Compute backends*, read 2026-10-11), and IonQ documents its depolarizing rates,
which the replay uses. The values
of the three Qollab runs of 13:52–14:10 UTC are in `results/qollab/compass_runs_20261010.json`; the
23:21 UTC run was read off the screen (`results/qollab/video_runs_20261010.json`). The demo video is
one continuous take on Qollab with the built-in simulator; its circuit run and the console lines it
shows are in `results/qollab/video_take_20261011.json`. The IBM and Braket runs are in
`results/qollab/compass_runs_20261011.json` (console lines as Qollab printed them; run-card
values read off the screen, counts not exported).

## The original part

The range limit itself is known: GHZ states lose dynamic range as they gain precision, and
cascades of GHZ sizes are the published remedy (Kessler et al. 2014; Cao et al. 2024);
entangled, parallel and partitioned GHZ magnetometry has been compared on superconducting
hardware (Slepnev et al. 2026). Other entries in this hackathon also treat GHZ phase ambiguity
and quantum sensing. What this entry adds is the following; it is a simulation, not hardware.

- **A playable test of a sentence from Qollab's own example.** The example prepares GHZ states
  and counts all-0 and all-1 outcomes in the Z basis, which cannot show phase coherence; here
  the GHZ phase is read in X and Y and turned into a field estimate. Only that sentence is
  quoted: the circuits here are this repository's own (`compass/circuits.py`), and the GHZ
  preparation is the textbook H and CX ladder that the example also shows. Reading GHZ phases in
  two quadratures follows Finkelstein et al. 2024.
- **A real storm, minute by minute**: the USGS Boulder record of a G5 storm, where the range of
  the GHZ fringe matters as much as its precision, and the 1-2-4 cascade removes all 20 fringe
  changes of GHZ-4 at an ideal gain of $`2\sqrt{8/14} \approx 1.51`$ over 14 independent qubits.
- **Two baselines under IonQ's documented noise**: GHZ-4 and the cascade against matched
  unentangled sensors with the same qubits and shots and against the SQL, under IonQ's
  documented gate noise and added dephasing, with the model value next to every replay number.
- **A difference test on real data**: two observatories about 1,000 km apart, showing that the
  storm is not common noise there and that only the gain for measuring a difference remains.
- **A new way to show it**: compass dials whose needles are the measured phases, a 3D compass
  that plays the storm, and a game in which you decide when entanglement is worth the risk.

## What didn't work

- The plan to let the user choose the phase per nT (0.01–0.05 rad): at 0.05 even the cascade
  and the independent qubits change fringe in the storm, so every headline would need its own
  conditions. The scale is fixed at 0.02 and printed next to the numbers.
- A common-mode ("everyone gets the same kick") noise model was designed but left out: in a
  magnetometer a field change shared by all sensors is the signal, so it would need a different
  physical story (for example reference-oscillator phase noise).

## Limits: what this app does not claim

- It does not compare the simulated sensors with the observatory's instruments; the USGS data
  are the truth here, not an opponent.
- The sensors are simulated: $`R_z(\delta)`$ stands for a field acting on a qubit. Nothing ran on a
  magnetometer or on quantum hardware.
- Only $`N \in \{1, 2, 4\}`$ come from circuits. The replay is a model of the same parity measurement
  (binomial shot noise with the register's visibility); tests check it against the circuits.
- One update per minute with an interrogation of about 0.1 ms is a model choice; real
  magnetometers sample much faster, which would shrink the one-minute steps.
- The IonQ noise models are used as IonQ documents them. The current Forte models are not
  publicly documented; the app reports what it measures and assumes nothing about them.

## With more time

- Twin sensors at sites close enough to share the storm (the cancelling then matters), and a
  GHZ gradiometer with two qubits per site.
- Re-optimised interrogation time per noise level, to show Huelga's tie directly.
- More storms (for example October 2024) as out-of-sample challenge maps.

## Accessibility

Tested, not assumed: axe-core 4.14.0 (WCAG 2.0–2.2 A and AA, and best practice) reports 0
violations on all 6 views in dark and light, in the states listed in
[results/a11y/README.md](results/a11y/README.md). The app offers keyboard-only use (tabs with arrow keys, Home and End; every control is a native button,
select or slider with a label), visible focus, live status messages, focus moved to each new
challenge round, charts as SVG with a title, a description that states the numbers and a data
table, explanatory figures as SVG with a title and a description in words, series that differ
by dash as well as colour, formulas as native MathML (read by screen
readers; plain Unicode text if the formula library cannot load), dark and light schemes, and no
horizontal page scroll at 320 px.

## How it was verified

More than 120 pytest tests (`.venv/bin/python -m pytest -q`), by area:

- **Physics** (`tests/test_physics.py`, `tests/test_twin.py`): parities of the packed circuits,
  with and without the dephasing ancilla, against exact values; the closed forms, the documented
  gate-noise visibilities, decoding by bit position and the estimators; the twin pairs reading the
  difference and the sum, and their $`\sqrt{2}`$ for a difference.
- **Replay and runs** (`tests/test_replay_api.py`, `tests/test_storm3d.py`): the storm's exact
  means, the quiet-day gain against $`\sqrt{N}`$, the dephasing gain and the gain over the SQL
  against theory, the challenge's carry-over rule, runs on a local simulator (layouts A and B),
  one IonQ job per Run with no hardware, and the 3D compass's numbers against `replay.metrics`.
- **Qollab rules** (`tests/test_conformance.py`): Python called only through `ui/py.js`, the
  backend used only in the two run functions, no Sampler, no `measure_all`, no dynamic circuits,
  literal data paths, attribution and licence, and every JavaScript file parses.
- **Review fixes and the interface** (`tests/test_review_fixes.py`,
  `tests/test_ui_focus_and_baselines.py`, `tests/test_console.py`, `tests/test_figures.py`): each
  confirmed review finding, the run-console lines, and figures that draw only numbers from Python.
- **Documents and bundle** (`tests/test_math_docs.py`, `tests/test_scripts_docs.py`): formulas that
  convert for Qollab, the write-up and bundle under Qollab's limits with the recorded runs inside,
  and README numbers equal to `results/headline_numbers.json`.

The independent reviews and how each finding was resolved are in
[docs/review.md](docs/review.md); accessibility checks are in
[results/a11y/README.md](results/a11y/README.md).

## Extending it

- **A new sensor arm**: add it to `ARMS` in `compass/replay.py`, add its register to
  `compass/circuits.py` (the packed layouts) and a test in `tests/test_physics.py` that checks its
  parities against the closed form in `compass/model.py`.
- **Another storm or observatory**: add a line to `RECORDS` in `scripts/fetch_usgs.py`, run it,
  and add a literal path constant and a `DATASETS` entry in `compass/data.py` (Qollab needs
  literal paths; a test checks them).
- **Another noise model**: add documented rates to `IONQ_DOCUMENTED` in `compass/model.py`; the
  replay picks them up through `_visibilities` in `compass/api.py`.
- **Another view**: a module in `ui/` that asks Python through `ui/py.js` and only draws.

## Repository map

| Path | What |
|---|---|
| `main.js`, `index.html`, `main.css` | Entry point Qollab runs; builds the views |
| `compass/` | Python: circuits, decoding, estimators, replay, closed forms, the challenge, the twin sensors, the JSON interface (`api.py`) and run-console lines |
| `ui/` | JavaScript views, charts, dials, figures, the 3D compass and the formula helper |
| `data/` | USGS one-minute records (Boulder quiet day and storm, Tucson storm) |
| `results/` | Recomputed headline numbers, recorded Qollab runs (`qollab/`), accessibility checks (`a11y/`) |
| `scripts/` | Data download, headline numbers, write-up conversion, Qollab bundle |
| `tests/`, `tools/devserver/` | Tests and the local harness |
| `docs/` | Decisions, reviews and figures |

## Design decisions

The choices behind the theme, the baselines, the fixed scale, the one-job circuits, the replay
model and the two-observatory what-if are recorded with their evidence in
[docs/decisions.md](docs/decisions.md).

## Disclosure

- Built during the hackathon window: 9 October 19:00 ET to 11 October 19:00 ET 2026, that is
  2026-10-09 23:00 UTC to 2026-10-11 23:00 UTC (10 October 08:00 to 12 October 08:00 in Japan).
  The repository's first commit is 2026-10-10 12:28 UTC. It is a second entry next to the
  author's *Bell-Test Lab* (Quantum Unlocked). The two share no app code; each has its own Temml
  formula helper. A few small pieces were written for both during the window and are alike: the
  math font declaration, the local harness's response shim, and the link and math conversion in
  `scripts/make_writeup.py`.
- The sentence about $`\sqrt{N}`$ is quoted from Qollab's example project
  [*Scaled Entanglement*](https://qollab.xyz/u/qollab/scaled-entanglement); no other part of it
  is used.
- The USGS records were downloaded on 2026-10-10 by `scripts/fetch_usgs.py` (Boulder at
  12:23 UTC, Tucson at 13:05 UTC).
- Use of AI: generative-AI coding assistants drafted most of the code, documentation and research
  notes under the author's direction, and were also used for independent checks of the physics
  and the test vectors; the author set the design, reviewed the changes, ran the tests and
  checked the cited sources.

## References

- J. J. Bollinger, W. M. Itano, D. J. Wineland, D. J. Heinzen, Phys. Rev. A 54, R4649 (1996),
  doi:10.1103/PhysRevA.54.R4649.
- S. F. Huelga et al., Phys. Rev. Lett. 79, 3865 (1997), doi:10.1103/PhysRevLett.79.3865.
- D. Leibfried et al., Science 304, 1476 (2004), doi:10.1126/science.1097576: three entangled
  ions, 1.45(2) times the sensitivity of a perfect experiment with three unentangled ions (ideal
  $`\sqrt{3} \approx 1.73`$).
- B. L. Higgins et al., Nature 450, 393 (2007), doi:10.1038/nature06257: Heisenberg-limited
  phase estimation without entanglement, by passing the phase several times (an experiment).
- T. Monz et al., Phys. Rev. Lett. 106, 130506 (2011), doi:10.1103/PhysRevLett.106.130506:
  coherence of GHZ states of up to 8 ions decays with $`N^2`$ under correlated noise.
- R. Demkowicz-Dobrzański, J. Kołodyński, M. Guţă, Nat. Commun. 3, 1063 (2012),
  doi:10.1038/ncomms2067.
- N. M. Nusran, M. U. Momeen, M. V. G. Dutt, Nat. Nanotechnol. 7, 109 (2012),
  doi:10.1038/nnano.2011.225: high-dynamic-range magnetometry with a single electronic spin in
  diamond.
- G. Waldherr et al., Nat. Nanotechnol. 7, 105 (2012), doi:10.1038/nnano.2011.224:
  high-dynamic-range magnetometry with a single nuclear spin in diamond.
- E. M. Kessler et al., Phys. Rev. Lett. 112, 190403 (2014), doi:10.1103/PhysRevLett.112.190403:
  Heisenberg-limited atom clocks based on entangled qubits (theory of GHZ cascades for clocks).
- S. Kimmel, G. H. Low, T. J. Yoder, Phys. Rev. A 92, 062315 (2015),
  doi:10.1103/PhysRevA.92.062315; erratum Phys. Rev. A 104, 069901 (2021),
  doi:10.1103/PhysRevA.104.069901.
- T. Ruster et al., Phys. Rev. X 7, 031050 (2017), doi:10.1103/PhysRevX.7.031050: a Bell pair
  of two ions up to 6.2 mm apart measures a field difference and rejects common magnetic noise.
- J. Yin et al., Science 356, 1140 (2017), doi:10.1126/science.aan3211: satellite-based
  entanglement distribution over 1,200 km.
- A. Cao et al., Nature 634, 315 (2024), doi:10.1038/s41586-024-07913-z: GHZ states of up to 4
  qubits beat the SQL at short dark times, but their reduced dynamic range keeps a single GHZ
  size from improving the clock at the optimal dark time; a cascade of GHZ sizes extends the
  range (still about 2 dB above the SQL).
- R. Finkelstein et al., Nature 634, 321 (2024), doi:10.1038/s41586-024-08005-8: a cascade of
  GHZ states of different sizes, and GHZ phases read in two quadratures, as this app does with X
  and Y.
- V. Slepnev, A. Gubaydullin, V. Vinokur, EPJ Quantum Technol. 13, 76 (2026),
  doi:10.1140/epjqt/s40507-026-00524-9: entangled, parallel and partitioned GHZ magnetometry on
  IQM Garnet and Rigetti Ankaa-3; smaller GHZ subsets run in parallel came close to the best
  sensitivity, and the paper notes that the range of measurable fields falls linearly with the
  number of entangled qubits.
- S. Direkci, M. Endres, T. Gefen, Phys. Rev. Research 8, L022046 (2026), doi:10.1103/2hyn-cqlq:
  phase slips limit clock protocols; weak measurements with ancillas extend the dynamic range.
- IonQ, Simulation with noise models, docs.ionq.com (read 2026-10-10).
- Qollab docs, *Compute backends* and *Runtime environment*, qollab.xyz/learn/docs (read
  2026-10-11): one job per run on IonQ backends; the Aria 1 and Aria 2 hardware is retired and
  their noise models are still offered.
- USGS Geomagnetism Program web service, geomag.usgs.gov/ws (read 2026-10-10).

## Data and licence

Geomagnetic data: USGS Geomagnetism Program, Boulder (BOU) and Tucson (TUC) observatories,
courtesy of the U.S. Geological Survey; thanks to INTERMAGNET (www.intermagnet.org) for promoting high standards of
magnetic observatory practice. The storm records are quasi-definitive, the quiet day adjusted;
values are as served. "U.S. Government work" in the CSV headers means that the records come from
the U.S. Geological Survey, not from this project: the data in `data/` are not covered by this
project's licence, and no other licence is given for them here. The quiet day, 1 October 2026,
is called quiet from its own record: the field there spans 30.2 nT over the day with a largest
one-minute step of 0.9 nT, against 987.5 nT and 118.8 nT in the storm record; no geomagnetic
activity index was checked.

Code and documentation: MIT licence (see LICENSE). The app typesets its formulas with Temml
(MIT) in the Latin Modern Math font (GUST Font License), both loaded from jsDelivr, and draws
the 3D compass with three.js 0.186.1 (MIT), from Qollab's own import map.

This effort is supported by Qollab & IonQ.
