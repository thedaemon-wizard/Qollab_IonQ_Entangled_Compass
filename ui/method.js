// Method & sources: the model in words and formulas, the circuit, the noise models, credits.
import { el } from './dom.js';
import { architectureFigure, circuitFigure } from './figures.js';
import { rich } from './tex.js';
import { py } from './py.js';

const REFS = [
  ['Bollinger, Itano, Wineland, Heinzen 1996', 'Optimal frequency measurements with maximally correlated states. Phys. Rev. A 54, R4649.'],
  ['Huelga et al. 1997', 'Improvement of frequency standards with quantum entanglement. Phys. Rev. Lett. 79, 3865 (local dephasing removes the Heisenberg scaling).'],
  ['Leibfried et al. 2004', 'Toward Heisenberg-limited spectroscopy with multiparticle entangled states. Science 304, 1476.'],
  ['Higgins et al. 2007', 'Entanglement-free Heisenberg-limited phase estimation. Nature 450, 393 (an experiment: multiple passes instead of entanglement).'],
  ['Monz et al. 2011', '14-qubit entanglement: creation and coherence. Phys. Rev. Lett. 106, 130506 (correlated dephasing: coherence of up to 8 ions decays with $N^2$).'],
  ['Demkowicz-Dobrzański, Kołodyński, Guţă 2012', 'The elusive Heisenberg limit in quantum-enhanced metrology. Nat. Commun. 3, 1063 (with uncorrelated noise, only a constant-factor gain asymptotically).'],
  ['Nusran, Momeen, Dutt 2012', 'High-dynamic-range magnetometry with a single electronic spin in diamond. Nat. Nanotechnol. 7, 109; doi:10.1038/nnano.2011.225.'],
  ['Waldherr et al. 2012', 'High-dynamic-range magnetometry with a single nuclear spin in diamond. Nat. Nanotechnol. 7, 105; doi:10.1038/nnano.2011.224.'],
  ['Kessler et al. 2014', 'Heisenberg-limited atom clocks based on entangled qubits. Phys. Rev. Lett. 112, 190403; doi:10.1103/PhysRevLett.112.190403 (theory of GHZ cascades for clocks).'],
  ['Cao et al. 2024', 'Multi-qubit gates and Schrödinger cat states in an optical clock. Nature 634, 315; doi:10.1038/s41586-024-07913-z (GHZ states of up to 4 qubits beat the standard quantum limit at short dark times, but their reduced dynamic range keeps a single GHZ size from improving the clock at the optimal dark time; a GHZ cascade extends the range and still stayed about 2 dB above the standard quantum limit).'],
  ['Finkelstein et al. 2024', 'Universal quantum operations and ancilla-based read-out for tweezer clocks. Nature 634, 321; doi:10.1038/s41586-024-08005-8 (a cascade of GHZ states of different sizes, and GHZ phases read in two quadratures, as this app does with X and Y).'],
  ['Slepnev, Gubaydullin, Vinokur 2026', 'Quantum entanglement for magnetometry. EPJ Quantum Technol. 13, 76; doi:10.1140/epjqt/s40507-026-00524-9 (entangled, parallel and partitioned GHZ magnetometry on IQM Garnet and Rigetti Ankaa-3: smaller GHZ subsets run in parallel came close to the best sensitivity; the paper notes that the range of measurable fields falls linearly with the number of entangled qubits).'],
  ['Direkci, Endres, Gefen 2026', 'Extending the dynamic range in quantum frequency estimation with sequential weak measurements. Phys. Rev. Research 8, L022046; doi:10.1103/2hyn-cqlq (phase slips, the clock literature\'s name for what this app calls fringe changes).'],
  ['Kimmel, Low, Yoder 2015', 'Robust calibration of a universal single-qubit gate set via robust phase estimation. Phys. Rev. A 92, 062315; erratum Phys. Rev. A 104, 069901 (2021).'],
  ['Ruster et al. 2017', 'Entanglement-based dc magnetometry with separated ions. Phys. Rev. X 7, 031050 (a Bell pair of two ions up to 6.2 mm apart measures a field difference and rejects common magnetic noise).'],
  ['Yin et al. 2017', 'Satellite-based entanglement distribution over 1200 kilometers. Science 356, 1140; doi:10.1126/science.aan3211 (entangled photons, not sensor qubits, shared between ground stations).'],
  ['IonQ', 'Simulation with noise models, docs.ionq.com/features/simulation-with-noise-models (read 2026-10-10).'],
  ['Qollab docs', 'Compute backends and Runtime environment, qollab.xyz/learn/docs (read 2026-10-11): IonQ backends accept one job per run; the Aria 1 and Aria 2 hardware is retired and their noise models are still offered.'],
  ['USGS', 'Geomagnetism Program web service, geomag.usgs.gov/ws/ (Boulder BOU and Tucson TUC; read 2026-10-10).'],
];

export function methodView(init) {
  const circuitBox = el('div', null, el('p', { class: 'muted' }, 'Loading the circuit…'));
  const view = el('div', { class: 'view' },
    el('section', { class: 'card' }, el('h2', null, 'How the app is built'), architectureFigure(init)),
    el('section', { class: 'card' }, el('h2', null, 'The model'),
      el('ul', null,
        el('li', null, rich(String.raw`Field to phase: $\delta = s\,(F_t - \text{estimate})$, with $s = 0.02$ rad per nT. For an electron spin (28.025 Hz per nT) this is a Ramsey time of 113.6 µs; the mapping is a model choice, fixed because the slip counts depend on it.`)),
        el('li', null, rich(String.raw`A GHZ register of $m$ qubits picks up $m\delta$: its X parity is $V\cos(m\delta)$, its Y parity $V\sin(m\delta)$. The angle $\operatorname{atan2}(Y, X)/m$ estimates $\delta$, but only modulo $2\pi/m$: GHZ-4 cannot tell a step of +44.6 nT from −33.9 nT at $s = 0.02$.`)),
        el('li', null, rich(String.raw`Fair comparison: GHZ-4 read in X and in Y uses 8 qubits per shot, the same as 8 independent qubits (4 read X, 4 read Y). With ideal qubits and $S$ shots the standard deviation of the phase is $1/(4\sqrt{S})$ against $1/(2\sqrt{S})$ rad: a factor $2 = \sqrt{4}$.`)),
        el('li', null, rich(String.raw`Cascade 1-2-4: the single qubit fixes the coarse value, GHZ-2 and GHZ-4 refine it; 14 qubits per shot, compared with 14 independent qubits (ideal gain $2\sqrt{8/14} \approx 1.51$). Cascades extend the unambiguous range (theory: Kessler et al. 2014 and Kimmel et al. 2015; experiment without entanglement: Higgins et al. 2007; with GHZ states: Cao et al. 2024, whose cascade still stayed about 2 dB above the standard quantum limit, and Finkelstein et al. 2024).`)),
        el('li', null, rich(String.raw`Independent dephasing with coherence $e^{-\gamma}$ per qubit multiplies a GHZ-$m$ visibility by $e^{-m\gamma}$, so at a fixed interrogation time the gain is $\sqrt{N}\,e^{-(N-1)\gamma}$; for $N = 4$ it falls below 1 at $\gamma = (\ln 4)/6 \approx 0.231$. If the interrogation time is re-optimised, GHZ and independent qubits reach the same best precision (Huelga et al. 1997); for uncorrelated (Markovian) noise any gain is asymptotically a constant factor (Demkowicz-Dobrzański et al. 2012).`)),
        el('li', null, 'Hybrid loop: a classical predictor (the last estimate) sets the working point, the quantum readout measures the residual, the estimate is updated; nothing else is fitted.'))),
    el('section', { class: 'card' }, el('h2', null, 'The circuit'), circuitBox),
    el('section', { class: 'card' }, el('h2', null, 'What the IonQ noise models can and cannot show'),
      el('ul', null,
        el('li', null, 'IonQ documents its Aria models (and Forte jobs before mid-September 2025) as depolarizing after each one- and two-qubit gate; the current Forte models are described as more complex and not yet documented, so this app reports what it measures and assumes nothing about their contents.'),
        el('li', null, rich(String.raw`Gate depolarizing costs a GHZ register little (Aria 1: visibility 0.958 for GHZ-4), so it barely dents $\sqrt{N}$. Dephasing during the interrogation and correlated noise, which do, are not separate channels in the documented model; the knob in this app adds independent dephasing, clearly labelled.`)),
        el('li', null, 'The model counts the abstract gates of our circuit (H, X and CX), with Rz and Sdg as noise-free virtual Z rotations. IonQ compiles circuits to its native gates before the noise is applied, so the model is an estimate; the visibility measured in a run is reported as measured.'))),
    el('section', { class: 'card' }, el('h2', null, 'What this app does not claim'),
      el('ul', null,
        el('li', null, 'It does not compare the simulated sensors with the observatory’s own instruments; the USGS data are the truth here, not an opponent.'),
        el('li', null, 'Nothing ran on a magnetometer or on quantum hardware; the results are simulations of a stated model.'),
        el('li', null, 'Only GHZ-1, GHZ-2, GHZ-4 and the 4-pass qubit are circuits; the replays and the challenge are a model of the same parity measurement (binomial shot noise with the register’s visibility), checked against the circuits by tests.'))),
    el('section', { class: 'card' }, el('h2', null, 'Sources'), el('ul', { class: 'refs' }, REFS.map(([a, b]) => el('li', null, el('strong', null, `${a}. `), rich(b))))),
    el('section', { class: 'card' }, el('h2', null, 'Disclosure and credits'),
      el('p', null, 'Built during the hackathon window (9 October 19:00 ET to 11 October 19:00 ET 2026, that is 10 October 08:00 to 12 October 08:00 in Japan; first commit 2026-10-10 12:28 UTC) as a second entry next to the author’s Bell-Test Lab. The two share no app code; each has its own Temml formula helper. The √N sentence on the Overview is quoted from Qollab’s example project Scaled Entanglement; no other part of it is used. A few small pieces were written for both during the window and are alike: the math font declaration, the local harness’s response shim, and the link and math conversion in scripts/make_writeup.py. Generative-AI coding assistants drafted most of the code, documentation and research notes under the author’s direction; the author set the design, reviewed the changes, ran the tests and checked the cited sources.'),
      el('p', null, 'Geomagnetic data: USGS Geomagnetism Program, Boulder (BOU) and Tucson (TUC) observatories, courtesy of the U.S. Geological Survey; thanks to INTERMAGNET (www.intermagnet.org). Code: MIT licence. This effort is supported by Qollab & IonQ.')));
  let loaded = false;
  return {
    element: view,
    async onShow() {
      if (loaded) return;
      loaded = true;
      try {
        const c = await py.circuitText('A');
        const b = await py.circuitText('B');
        const pre = el('pre', { class: 'circuit', tabindex: '0', role: 'region', 'aria-label': `Qiskit text drawing of the ${c.n_qubits}-qubit circuit` }, c.text);
        circuitBox.replaceChildren(
          circuitFigure(c, b),
          el('p', null, `${c.n_qubits} qubits: q0 is the canary; ${c.registers.map((r) => `${r.name} on q${r.qubits.join(',q')}`).join('; ')}. Gate counts: ${Object.entries(c.ops).map(([k, v]) => `${k} ${v}`).join(', ')}.`),
          el('details', null, el('summary', null, rich(String.raw`Qiskit’s own drawing of all ${c.n_qubits} qubits (layout A, $\delta = 0.3$ rad)`)), pre));
      } catch (err) {
        circuitBox.replaceChildren(el('p', null, `Could not draw the circuit: ${err.message}`));
      }
    },
  };
}
