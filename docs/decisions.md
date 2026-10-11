# Decisions

E1–E9 recorded on 2026-10-10 and E10–E13 on 2026-10-11, during the build window. Each states the decision, the evidence
behind it, and what would make us revisit it.

## E1 — Quantum Playground, not Quantum Impact

- **Decision.** The entry is declared in the Quantum Playground theme.
- **Evidence.** Quantum Impact asks for a strong classical baseline and a measurable gain on a
  real problem. Here the simulated sensors are compared with other *quantum* sensors (matched
  unentangled qubits, the standard quantum limit); against the observatory's own instruments the
  app makes no claim. The GHZ parity readout is interference and entanglement at work, which is
  what Playground asks to be essential.
- **Revisit if** the app ever compares with a classical instrument model on equal terms.

## E2 — The strongest honest baseline is the standard quantum limit

- **Decision.** Besides the matched unentangled sensor (same 8 qubits, same X/Y split), every
  replay reports GHZ-4 against the standard quantum limit for the same qubits and shots.
- **Evidence.** The matched sensor is $`\sqrt{2}`$ above the SQL because its X quadrature carries little
  information near $`\delta = 0`$; beating it by 2 would overstate the advantage. Against the SQL (one
  interrogation of the same length per qubit) the X/Y GHZ-4 readout gains $`\sqrt{2}`$ ideally, 1.36
  under IonQ's documented Aria 1 gate noise, and nothing from $`\gamma = (\ln 2)/6 \approx 0.116`$ on (tests
  check all three). The twin view applies the same baseline to the difference (1.58 nT).

## E3 — Phase per nT fixed at 0.02 rad

- **Decision.** No selector for $`s`$.
- **Evidence.** The slip counts depend on $`s`$: at 0.05 rad/nT even the cascade and the independent
  qubits jump fringes in the storm, so each headline would need its own conditions. 0.02 rad/nT
  is an electron spin with a 113.6 µs Ramsey time and is printed next to every number.

## E4 — One packed circuit, one job, everywhere

- **Decision.** Every run submits exactly one circuit (17 qubits, 21 with dephasing, 13 for the
  twin sensors) as one job; a module-level counter refuses a second IonQ job in the same Run, and
  both run functions share it. Names containing "qpu" are refused.
- **Evidence.** Qollab's hackathon FAQ (qollab.xyz/programs/hackathon/how-it-works#faq, read
  2026-10-11): "IonQ backends accept one per run, so put everything an IonQ run measures into one
  circuit." Qollab's docs (*Runtime environment*, read 2026-10-11) say the same for the remote
  simulators and the quantum computers. A canary qubit checks the bit order of the returned keys.

## E5 — Replays are a model of the circuits, checked against them

- **Decision.** Field tracking, the challenge and the twin replay use binomial shot noise with
  each register's visibility instead of thousands of circuit runs.
- **Evidence.** One replay of the storm is 2,880 minutes × 32 repetitions; even with every
  sensor packed into one circuit per minute, that would be 92,160 jobs, and the estimate of each
  minute depends on the previous one, so they could not be batched. Tests check the model against exact circuit
  parities (Statevector) and against simulator runs.

## E6 — Dephasing by one ancilla per register

- **Decision.** Independent dephasing $`\gamma`$ is added with one ancilla per register ($`\mathrm{CX}\cdot R_z(b)\cdot\mathrm{CX}`$, ancilla
  in $`\lvert +\rangle`$, $`\cos b = e^{-m\gamma}`$) rather than one per qubit.
- **Evidence.** On a GHZ register, independent dephasing of the $`m`$ qubits only matters through the
  parity of the flips, so its coherence decays as $`e^{-m\gamma}`$ (Huelga et al. 1997); one ancilla
  reproduces that exactly (tests compare with the closed form) and keeps the circuit at 21 qubits.

## E7 — No common-mode noise layout

- **Decision.** The designed common-mode ("same kick for every sensor") layout was left out.
- **Evidence.** In a magnetometer, a field change shared by all sensors is the signal, so the
  layout would need a different physical story (for example reference-oscillator phase noise).

## E8 — Two observatories as a labelled what-if

- **Decision.** The twin-sensor view entangles a qubit at Boulder with one at Tucson and is
  labelled as a what-if.
- **Evidence.** Sharing entangled sensor qubits between observatories would need a quantum network
  that does not exist yet; entangled photons, not sensor qubits, have been shared between ground
  stations over 1,200 km apart by satellite (Yin et al., Science 356, 1140 (2017),
  doi:10.1126/science.aan3211). The data show the storm is not common across the about 1,000 km between them (one-minute
  changes correlate $`r = 0.33`$), so the cancelling trick does not apply; the $`\sqrt{2}`$ gain for measuring
  a difference directly does.

## E9 — Data as served, from one source

- **Decision.** USGS geomagnetism web service, element F, one-minute values, as served (storm:
  quasi-definitive; quiet day: adjusted), downloaded by `scripts/fetch_usgs.py`. Data types are
  never mixed within one comparison, and every comparison uses changes from a start value.
- **Evidence.** Adjusted and quasi-definitive values of the same storm day differed by about 11 nT
  on average in an earlier fetch.

## E10 — Figures drawn by the app from its own numbers

- **Decision** (2026-10-11). Four explanatory figures: the model loop (Overview), one sensor
  register as a circuit with the map of all qubits in the one job (Method), where each number
  comes from (Method) and the two-observatory what-if (Two observatories). They are SVGs drawn by
  `ui/figures.js` from what Python returns (the scale, the ranges, the qubit counts, the register
  layout), and the README shows screenshots of the first three.
- **Evidence.** Before this, the model was only bullet text and Qiskit's 17-wire text drawing,
  and the dials appeared only after a circuit run. A full gate-by-gate drawing of all 17 qubits
  was left out: it reads no better than Qiskit's own drawing, which stays available under a
  disclosure. Tests check that the drawn register matches the circuit `compass/circuits.py`
  builds, that the figures use only theme colours and that no physics number is typed into them.
- **Revisit if** the circuit layout changes (the tests will fail first).

## E11 — Formulas typeset as math everywhere a judge reads them

- **Decision** (2026-10-11). README and docs use GitHub math (`` $`…`$ `` inline, which keeps
  backslashes and `*` intact; ```` ```math ```` for display). The Qollab write-up is generated
  from the README with `$…$`, which Qollab renders with KaTeX. In the app, `ui/tex.js` turns
  TeX strings into native MathML with Temml 0.14.0, loaded at run time from jsDelivr, in the
  Latin Modern Math font. SVG text, `<option>`, ARIA labels and live messages stay plain
  Unicode.
- **Evidence.** Plain `$…$` on GitHub drops backslashes before punctuation (`\,`, `\%`), which
  changes formulas. Qollab's write-up renderer understands only `$…$` and `$$…$$`. The project
  frame's CSP allows scripts and fonts from cdn.jsdelivr.net but blocks `data:` fonts. MathML is
  exposed to screen readers; if the import fails, the same strings appear as Unicode text
  (tested with jsDelivr blocked). On Qollab (2026-10-11), the in-app formulas rendered with the
  built-in simulator, and the pasted write-up (20,453 characters) showed 59 KaTeX formulas in
  Qollab's write-up preview with no KaTeX error; after the review fixes the pasted write-up
  (22,843 characters, 2026-10-11 evening) shows 60, again with no KaTeX error.
- **Revisit if** the app must work offline (vendor Temml and the font with their licences).

## E12 — The storm on a 3D compass, drawn from one typical replay

- **Decision** (2026-10-11). A "3D compass" tab plays the storm minute by minute on three
  stacked needles (8 independent qubits, GHZ-4 alone, the cascade's GHZ-4 register), drawn
  with three.js from Qollab's import map. A needle shows the angle its register reads back; a
  tube shows the turn that minute's field step gave it, $`m\,s\,\Delta F`$, so the first slip is
  visible as a tube past half a turn. While a sensor sits on a wrong fringe its tube is red and
  thicker; the counter counts fringe changes, onto a wrong fringe and back. `compass/api.py`
  `storm3d_json` computes every angle, fringe index and count; the page only draws. The needles
  come from the one replay (of 32) closest to the average fringe-change count and wrong-minute
  count of GHZ-4, and the page gives both averages. The outcome is close to two-valued (seed 0:
  26 replays with 20 changes and 1,115 wrong minutes, 6 with 21 and 436), so the replay shown is
  the most common outcome and the averages (20.2, 988) describe no single replay; both are in
  `results/headline_numbers.json`.
- **Correction** (2026-10-11, review round 3). The first version drew the phase against the
  tracker's prediction, $`m\,s\,(F_t - \hat{F}_{t-1})`$, while the text said $`m\,s\,\Delta F`$. On
  a wrong fringe that phase carries the whole turns the estimate is off by, so a 2 nT step showed
  as an almost full red ring. The tube now draws $`m\,s\,\Delta F`$ (tests pin both quantities), the
  counter is called "fringe changes" (it also counts the step back), the wheel scrolls the page
  instead of zooming, playback pauses when the tab is left and moves in one-second steps under
  reduced motion, and the three.js import gives up after 8 s.
- **Evidence.** The fringe slip was shown only as a jump in an error chart and as a static dial
  for one minute. Lines in WebGL are one pixel wide, so the turns are tubes. The colours are read
  from the theme on the app root, and the text panel and the canvas label give the same numbers
  for screen readers and when WebGL is missing (the canvas itself is hidden from them).
- **Revisit if** the replay model changes (tests compare the tab's numbers with
  `replay.metrics`).

## E13 — Qollab is the live demo; the 3D compass uses WebGL

- **Decision** (2026-10-11). The judged artefact is the Qollab project; no copy is hosted
  elsewhere during the window, as in the first entry (*Bell-Test Lab*, its decision D1). The 3D
  compass uses three.js's `WebGLRenderer` from Qollab's import map; there is no WebGPU path.
- **Evidence.** The first entry probed Qollab's project frame on 2026-10-10 and found
  `navigator.gpu` undefined there (its decision D10), so a WebGPU renderer could not start on
  Qollab. Three needles and their tubes need no more than WebGL, and without WebGL the view falls
  back to the text panel with the same numbers.
- **Revisit if** Qollab's project frame exposes WebGPU, or the view needs far more geometry.
