// Method & sources: the model in words and formulas, the circuit, the noise models, credits.
import { el } from './dom.js';
import { py } from './py.js';

const REFS = [
  ['Bollinger, Itano, Wineland, Heinzen 1996', 'Optimal frequency measurements with maximally correlated states. Phys. Rev. A 54, R4649.'],
  ['Huelga et al. 1997', 'Improvement of frequency standards with quantum entanglement. Phys. Rev. Lett. 79, 3865 (local dephasing removes the Heisenberg scaling).'],
  ['Leibfried et al. 2004', 'Toward Heisenberg-limited spectroscopy with multiparticle entangled states. Science 304, 1476.'],
  ['Higgins et al. 2007', 'Entanglement-free Heisenberg-limited phase estimation. Nature 450, 393 (multiple passes instead of entanglement).'],
  ['Monz et al. 2011', '14-qubit entanglement: creation and coherence. Phys. Rev. Lett. 106, 130506 (correlated dephasing: coherence of up to 8 ions decays with N²).'],
  ['Demkowicz-Dobrzański, Kołodyński, Guţă 2012', 'The elusive Heisenberg limit in quantum-enhanced metrology. Nat. Commun. 3, 1063 (with uncorrelated noise, only a constant-factor gain asymptotically).'],
  ['Kimmel, Low, Yoder 2015', 'Robust calibration of a universal single-qubit gate set via robust phase estimation. Phys. Rev. A 92, 062315; erratum Phys. Rev. A 104, 069901 (2021).'],
  ['IonQ', 'Simulation with noise models, docs.ionq.com/features/simulation-with-noise-models (read 2026-10-10).'],
  ['USGS', 'Geomagnetism Program web service, geomag.usgs.gov/ws/ (Boulder, BOU; read 2026-10-10).'],
];

export function methodView() {
  const circuitBox = el('div', null, el('p', { class: 'muted' }, 'Loading the circuit…'));
  const view = el('div', { class: 'view' },
    el('section', { class: 'card' }, el('h2', null, 'The model'),
      el('ul', null,
        el('li', null, 'Field to phase: δ = s·(F_t − estimate), with s = 0.01, 0.02 or 0.05 rad per nT. For an electron spin (28.025 Hz per nT) s = 0.02 is a Ramsey time of 113.6 µs; this mapping is a model choice.'),
        el('li', null, 'A GHZ register of m qubits picks up m·δ: its X parity is V·cos(mδ), its Y parity V·sin(mδ). The angle atan2(Y, X)/m estimates δ, but only modulo 2π/m: GHZ-4 cannot tell a step of +44.6 nT from −34.0 nT at s = 0.02.'),
        el('li', null, 'Fair comparison: GHZ-4 read in X and in Y uses 8 qubits per shot, the same as 8 independent qubits (4 read X, 4 read Y). With ideal qubits the standard deviation is 1/(4√S) against 1/(2√S): a factor 2 = √4.'),
        el('li', null, 'Cascade 1-2-4 (Kimmel et al.): the single qubit fixes the coarse value, GHZ-2 and GHZ-4 refine it; 14 qubits per shot, compared with 14 independent qubits (ideal gain 2·√(8/14) ≈ 1.51).'),
        el('li', null, 'Independent dephasing with coherence e^(−γ) per qubit multiplies a GHZ-m visibility by e^(−mγ), so the gain is √N·e^(−(N−1)γ); for N = 4 it falls below 1 at γ = ln 4 / 6 ≈ 0.231 (Huelga et al. 1997).'),
        el('li', null, 'Hybrid loop: a classical predictor (the last estimate) sets the working point, the quantum readout measures the residual, the estimate is updated; nothing else is fitted.'))),
    el('section', { class: 'card' }, el('h2', null, 'The circuit (layout A, δ = 0.3 rad)'), circuitBox),
    el('section', { class: 'card' }, el('h2', null, 'What the IonQ noise models can and cannot show'),
      el('ul', null,
        el('li', null, 'IonQ documents its Aria models (and Forte jobs before mid-September 2025) as depolarizing after each one- and two-qubit gate; the current Forte models are described as more complex and not yet documented, so this app reports what it measures and assumes nothing about their contents.'),
        el('li', null, 'Gate depolarizing costs a GHZ register little (Aria 1: visibility 0.958 for GHZ-4), so it barely dents √N. Dephasing during the interrogation and correlated noise, which do, are not separate channels in the documented model; the knob in this app adds independent dephasing, clearly labelled.'),
        el('li', null, 'IonQ recompiles circuits; Rz and Sdg are taken as noise-free here (要確認 for the cloud simulator). A measured visibility that differs from the model is reported as measured.'))),
    el('section', { class: 'card' }, el('h2', null, 'What this app does not claim'),
      el('ul', null,
        el('li', null, 'It does not compare quantum sensors with the observatory’s magnetometers (resolution 0.1 nT, scalar accuracy 1 nT per INTERMAGNET); the field data are the truth here, not an opponent.'),
        el('li', null, 'Nothing ran on a magnetometer or on quantum hardware; the results are simulations of a stated model.'),
        el('li', null, 'Curves beyond GHZ-4 are model formulas, not circuits.'))),
    el('section', { class: 'card' }, el('h2', null, 'Sources'), el('ul', { class: 'refs' }, REFS.map(([a, b]) => el('li', null, el('strong', null, `${a}. `), b)))),
    el('section', { class: 'card' }, el('h2', null, 'Disclosure and credits'),
      el('p', null, 'Built during the hackathon window (10–12 October 2026) as a second entry next to the author’s Bell-Test Lab; no code is shared between them. Generative-AI coding assistance was used for code, documents and research drafts; the author checked the results.'),
      el('p', null, 'Geomagnetic data: USGS Geomagnetism Program, Boulder (BOU) observatory, courtesy of the U.S. Geological Survey; thanks to INTERMAGNET (www.intermagnet.org). Code: MIT licence. This effort is supported by Qollab & IonQ.')));
  let loaded = false;
  return {
    element: view,
    async onShow() {
      if (loaded) return;
      loaded = true;
      try {
        const c = await py.circuitText('A');
        const pre = el('pre', { class: 'circuit', tabindex: '0', role: 'region', 'aria-label': `Qiskit text drawing of the ${c.n_qubits}-qubit circuit` }, c.text);
        circuitBox.replaceChildren(
          el('p', null, `${c.n_qubits} qubits: q0 is the canary; ${c.registers.map((r) => `${r.name} on q${r.qubits.join(',q')}`).join('; ')}. Gate counts: ${Object.entries(c.ops).map(([k, v]) => `${k} ${v}`).join(', ')}.`),
          pre);
      } catch (err) {
        circuitBox.replaceChildren(el('p', null, `Could not draw the circuit: ${err.message}`));
      }
    },
  };
}
