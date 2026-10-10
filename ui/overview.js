// Overview: the question, the claim under test, four answers computed when the page opens.
import { el, fmt } from './dom.js';

function tile(heading, value, text) {
  return el('li', { class: 'tile' }, el('h3', null, heading), el('p', { class: 'big' }, value), el('p', { class: 'small' }, text));
}

export function overviewView(answers, goTracker) {
  const tiles = el('ul', { class: 'tiles', 'aria-label': 'Four answers' });
  const status = el('p', { role: 'status', class: 'status' }, 'Computing the answers (model replay of the quiet day and the storm)…');
  function fill(a) {
    tiles.replaceChildren(
      tile('Ideal sensors', `${fmt.n(a.ideal.mean)}×`, `GHZ-4 against 8 independent qubits on the quiet day: ${fmt.pm(a.ideal)}. The textbook √4 = 2 holds.`),
      tile('IonQ Aria 1 gate noise (documented)', `${fmt.n(a.aria1.mean)}×`, `Depolarizing after every gate costs little: ${fmt.pm(a.aria1)}, model ${fmt.n(a.aria1.theory)}.`),
      tile('Dephasing γ = 0.2 per qubit', `${fmt.n(a.dephasing_0_2.mean)}×`, `Almost all of the advantage is gone: ${fmt.pm(a.dephasing_0_2)}, model 2e^(−3γ) = ${fmt.n(a.dephasing_0_2.theory)}.`),
      tile('The May 2024 storm', `${fmt.n(a.storm.ghz4_slips.mean, 0)} jumps`, `GHZ-4 alone jumps to a wrong fringe about ${fmt.n(a.storm.ghz4_slips.mean, 0)} times and is wrong for ${fmt.n(a.storm.ghz4_wrong_minutes.mean, 0)} minutes; the 1-2-4 cascade jumps ${fmt.n(a.storm.cascade_slips.mean, 0)} times (${a.storm.shots} shots, ${a.storm.scale} rad/nT).`),
    );
    status.textContent = `Computed in ${a.seconds} s from the replay model; open the Field tracker to change the settings or run the circuit.`;
  }
  const view = el('div', { class: 'view' },
    el('section', { class: 'card' },
      el('h2', null, 'The claim'),
      el('blockquote', null, '“An N-qubit GHZ sensor is √N times more precise than N independent sensors.”'),
      el('p', { class: 'small muted' }, 'From Qollab’s example project “Scaled Entanglement” (qollab.xyz/u/qollab/scaled-entanglement, version 1.0).'),
      el('p', null, 'True for ideal qubits, the same number of qubits and shots, and a field that stays inside the GHZ fringe. This playground tests it with simulated sensors on a real record: the total magnetic field at the USGS Boulder observatory, on a quiet day and during the G5 storm of 10–11 May 2024.')),
    el('section', { class: 'card' }, el('h2', null, 'Four answers'), status, tiles),
    el('section', { class: 'card' }, el('h2', null, 'Real and simulated'),
      el('ul', null,
        el('li', null, el('strong', null, 'Real: '), 'the field data (one value per minute, as served by USGS).'),
        el('li', null, el('strong', null, 'Simulated: '), 'the sensors. Each minute, a qubit phase of s·ΔF (s = 0.02 rad per nT by default) stands for the field step; GHZ registers multiply it by their size.'),
        el('li', null, el('strong', null, 'Circuits: '), 'one packed Qiskit circuit per run on the simulator chosen in Qollab’s Run dialog (one job, also on IonQ).'),
        el('li', null, el('strong', null, 'Added by this app: '), 'the dephasing knob (one extra qubit per sensor). It is not part of any IonQ noise model.'))),
    el('section', { class: 'card' }, el('h2', null, 'Try it'),
      el('ol', null,
        el('li', null, 'Open the Field tracker and press “Update replay”: the quiet day shows the √N gain.'),
        el('li', null, 'Switch to the storm: GHZ-4 alone loses track whenever the field moves more than its fringe allows in one minute.'),
        el('li', null, 'Add dephasing: above γ ≈ 0.23 per qubit the gain falls below 1. Then run one minute on the quantum simulator.')),
      el('button', { type: 'button', class: 'primary', on: { click: goTracker } }, 'Open the Field tracker')));
  return { element: view, fill, fail: (msg) => { status.textContent = `Could not compute the answers: ${msg}`; } };
}
