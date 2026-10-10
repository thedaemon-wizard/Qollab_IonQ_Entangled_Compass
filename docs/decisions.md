# Decisions

All recorded on 2026-10-10, during the build window. Each states the decision, the evidence
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
- **Evidence.** The matched sensor is √2 above the SQL because its X quadrature carries little
  information near δ = 0; beating it by 2 would overstate the advantage. Against the SQL the
  ideal gain is √2, 1.36 under IonQ's documented Aria 1 gate noise, and it vanishes at
  γ = ln 2 / 6 ≈ 0.116 (tests check all three).

## E3 — Phase per nT fixed at 0.02 rad

- **Decision.** No selector for s.
- **Evidence.** The slip counts depend on s: at 0.05 rad/nT even the cascade and the independent
  qubits jump fringes in the storm, so each headline would need its own conditions. 0.02 rad/nT
  is an electron spin with a 113.6 µs Ramsey time and is printed next to every number.

## E4 — One packed circuit, one job, everywhere

- **Decision.** Every run submits exactly one circuit (17 qubits, 21 with dephasing, 13 for the
  twin sensors) as one job; a module-level counter refuses a second IonQ job in the same Run, and
  both run functions share it. Names containing "qpu" are refused.
- **Evidence.** IonQ allows one job per Run on Qollab; another team reported that the IonQ proxy
  rejects a list of circuits. A canary qubit checks the bit order of the returned keys.

## E5 — Replays are a model of the circuits, checked against them

- **Decision.** Field tracking, the challenge and the twin replay use binomial shot noise with
  each register's visibility instead of thousands of circuit runs.
- **Evidence.** One replay of the storm is 2,880 minutes × 5 sensors × 32 repetitions; as
  circuits that would be over 450,000 jobs. Tests check the model against exact circuit
  parities (Statevector) and against simulator runs.

## E6 — Dephasing by one ancilla per register

- **Decision.** Independent dephasing γ is added with one ancilla per register (CX·Rz(b)·CX, ancilla
  in |+⟩, cos b = e^{−mγ}) rather than one per qubit.
- **Evidence.** On a GHZ register, independent dephasing of the m qubits only matters through the
  parity of the flips, so its coherence decays as e^{−mγ} (Huelga et al. 1997); one ancilla
  reproduces that exactly (tests compare with the closed form) and keeps the circuit at 21 qubits.

## E7 — No common-mode noise layout

- **Decision.** The designed common-mode ("same kick for every sensor") layout was left out.
- **Evidence.** In a magnetometer, a field change shared by all sensors is the signal, so the
  layout would need a different physical story (for example reference-oscillator phase noise).

## E8 — Two observatories as a labelled what-if

- **Decision.** The twin-sensor view entangles a qubit at Boulder with one at Tucson and is
  labelled as a what-if.
- **Evidence.** Sharing entanglement between observatories needs a quantum network that does not
  exist. The data show the storm is not common across the about 1,000 km between them (one-minute
  changes correlate r = 0.33), so the cancelling trick does not apply; the √2 gain for measuring
  a difference directly does.

## E9 — Data as served, from one source

- **Decision.** USGS geomagnetism web service, element F, one-minute values, as served (storm:
  quasi-definitive; quiet day: adjusted), downloaded by `scripts/fetch_usgs.py`. Data types are
  never mixed within one comparison, and every comparison uses changes from a start value.
- **Evidence.** Adjusted and quasi-definitive values of the same storm day differed by about 11 nT
  on average in an earlier fetch.
