// The explanatory figures: the model loop (Overview), one sensor register as a circuit with the
// one-job qubit map (Method), where each number comes from (Method) and the two-observatory
// what-if (Two observatories). Every number shown comes from Python (init or the circuit data).
// What is real, a model choice, simulated or classical is said by an outline AND a tag in words.
import { svg } from './dom.js';
import { arrow, box, cx, figure, frame, gate, meter, text, wires } from './schematic.js';

const REAL = { tone: 'var(--text)' };
const MODEL = { tone: 'var(--muted)', dash: '7 4' };
const SIM = { tone: 'var(--accent)', inner: true };
const CLASSICAL = { tone: 'var(--muted)', dash: '2 3' };
const INTERFACE = { tone: 'var(--muted)' };
const PLATFORM = { tone: 'var(--s4)', dash: '12 3 2 3' };
const WHATIF = { tone: 'var(--s5)', dash: '14 6', fill: 'none' };
const LINK = { tone: 'var(--text)', width: 1.8 };

/** A box in one of the styles above, with its tag word above the top-right corner. */
function node(x, y, w, h, title, lines, style, tag) {
  const g = box(x, y, w, h, title, lines, style);
  if (style.inner) g.append(svg('rect', { x: x + 4, y: y + 4, width: w - 8, height: h - 8, rx: 7, style: `fill:none;stroke:${style.tone};stroke-width:1.2` }));
  if (tag) g.append(text(x + w, y - 7, tag, { cls: 'sk-label', anchor: 'end' }));
  return g;
}

const nt = (v) => Number(v).toFixed(1);

/** Figure 1: one minute of the model, as a loop of five steps. */
export function modelFigure(init) {
  const { value: s, ramsey_us: ramsey, range_nt: range } = init.scale;
  const r4 = nt(range['4']);
  const r1 = nt(range['1']);
  const desc = [
    'One minute of the model, as a loop of five steps.',
    '1. Real data: the total magnetic field F(t) at the USGS Boulder observatory, one value per minute, on a quiet day (1 October 2026) and through the G5 storm of 10–11 May 2024.',
    `2. A model choice: the qubits see only what is left after the current estimate, as a phase δ = s·ΔF, with ΔF = F(t) − estimate and s = ${s} rad per nT (an electron spin with a ${ramsey} µs Ramsey time).`,
    '3. Simulated in a Qiskit circuit: a GHZ register of m qubits gets Rz(δ) on each qubit and so picks up m·δ. It is read in X, or in Y with S† first.',
    '4. Classical: the counts give the mean parities X = V·cos(mδ) and Y = V·sin(mδ). The needle angle θ = atan2(Y, X) gives δ as θ/m, but only modulo 2π/m.',
    `5. Classical: the estimate moves by θ/(m·s). This is right only while |m·δ| < π, which is ±${r4} nT per minute for GHZ-4 and ±${r1} nT for one qubit. The 1-2-4 cascade reads the ×1 and ×2 needles first and keeps the ±${r1} nT range.`,
    'A dashed arrow returns to step 2: the new estimate is the next minute’s working point.',
    'The loop runs in two ways. For one minute it runs as one packed Qiskit circuit, sent as one job to the simulator chosen in Qollab’s Run dialog. For a whole record it runs as a model of the same readout (binomial shot noise times the visibility V), checked against the circuit.',
    'Nothing ran on a magnetometer or on quantum hardware.',
  ].join(' ');
  const glyph = [140, 172].flatMap((y) => [
    svg('line', { x1: 532, x2: 732, y1: y, y2: y, class: 'sk-wire' }),
    gate(632, y, '$R_z(δ)$', { w: 50, tone: 'var(--accent)' }),
    gate(680, y, '$H$', { w: 26, tone: 'var(--text)' }),
    meter(716, y),
  ]);
  // the needle of the dial: 58° from the X axis, length 23 (SVG y grows downwards)
  const a = (58 * Math.PI) / 180;
  const dial = svg('g', null,
    svg('circle', { cx: 566, cy: 384, r: 26, class: 'dial-ring' }),
    svg('line', { x1: 540, x2: 592, y1: 384, y2: 384, class: 'dial-axis' }),
    svg('line', { x1: 566, x2: 566, y1: 358, y2: 410, class: 'dial-axis' }),
    text(600, 388, '$X$', { anchor: 'middle' }),
    text(566, 352, '$Y$', { anchor: 'middle' }),
    svg('line', { x1: 566, y1: 384, x2: (566 + 23 * Math.cos(a)).toFixed(1), y2: (384 - 23 * Math.sin(a)).toFixed(1), style: 'stroke:var(--text);stroke-width:3.5;stroke-linecap:round' }),
    svg('circle', { cx: 566, cy: 384, r: 3, style: 'fill:var(--text)' }));
  return figure({
    w: 760, h: 440, min: 600, title: 'One minute of the model', desc,
    caption: 'Figure 1. One minute of the model. Outlines and tags in words mark what is real (solid), a model choice (dashed), simulated (double outline) and classical arithmetic (dotted). Box 3 shows one register with m = 2, read in X; the whole circuit is in Method & sources. In the one-minute circuit run, the estimate is the field one minute earlier. Nothing ran on a magnetometer or on quantum hardware.',
  },
  node(16, 40, 228, 160, 'Real field (USGS)', ['Boulder observatory: total', 'magnetic field, one value', 'per minute: a quiet day', '(1 Oct 2026) and the G5', 'storm of 10–11 May 2024'], REAL, 'REAL DATA'),
  text(130, 184, '$F(t)$', { cls: 'sk-key', anchor: 'middle' }),
  node(266, 40, 228, 160, 'Field → phase', ['the qubits see only the rest:', '$ΔF = F(t) −$ estimate', `$s$ = ${s} rad per nT (electron`, `spin, ${ramsey} µs Ramsey time)`], MODEL, 'MODEL CHOICE'),
  text(380, 184, '$δ = s·ΔF$', { cls: 'sk-key', anchor: 'middle' }),
  node(516, 40, 228, 160, 'Qubit sensor (Qiskit)', ['GHZ register of $m$ qubits;', '$R_z(δ)$ on each: it picks up $m·δ$', 'read in $X$, or in $Y$ ($S^†$ first)'], SIM, 'SIMULATED'),
  glyph, gate(552, 140, '$H$', { w: 26, tone: 'var(--text)' }), cx(588, 140, 172),
  node(516, 262, 228, 160, 'Readout', ['counts → $X = V·cos(mδ)$,', '$Y = V·sin(mδ)$; needle at', '$θ = atan2(Y, X)$, length $V$'], CLASSICAL, 'CLASSICAL'),
  dial, text(616, 380, 'estimate of $δ$: $θ/m$'), text(616, 398, 'only mod $2π/m$'),
  node(266, 262, 228, 160, 'Update', ['estimate += $θ/(m·s)$', 'right only while $|mδ| < π$:', `±${r4} nT per minute for GHZ-4,`, `±${r1} nT for one qubit.`, 'The cascade 1-2-4 reads the', '×1 and ×2 needles first, so', `it keeps the ±${r1} nT range.`], CLASSICAL, 'CLASSICAL'),
  frame(16, 262, 228, 160, 'THE LOOP RUNS TWO WAYS'),
  ['One minute: one packed', 'Qiskit circuit, one job, on', 'the simulator chosen in', 'Qollab’s Run dialog.', 'Whole record: a model of the', 'same readout (shot noise × $V$),', 'checked against the circuit.']
    .map((line, i) => text(28, 300 + 16 * i, line)),
  arrow([[244, 120], [264, 120]], LINK),
  arrow([[494, 120], [514, 120]], LINK),
  arrow([[630, 200], [630, 260]], { ...LINK, label: 'counts', at: [662, 234] }),
  arrow([[516, 342], [496, 342]], LINK),
  arrow([[380, 262], [380, 202]], { ...LINK, dash: '5 4', label: 'next minute: new working point', at: [490, 236] }));
}

/** Figure 2: one sensor register (GHZ-4 read in Y) as a circuit, and every sensor in one job. */
export function circuitFigure(a, b) {
  const reg = a.registers.find((r) => r.name === 'G4Y');
  const anc = b.registers.find((r) => r.name === 'G4Y').ancilla;
  const q = reg.qubits;
  const ancillas = b.registers.map((r) => r.ancilla).filter((v) => v !== null);
  const ancRange = `q${Math.min(...ancillas)}–q${Math.max(...ancillas)}`;
  const ys = [52, 92, 132, 172];
  const owner = new Map();
  for (const r of a.registers) for (const k of r.qubits) owner.set(k, r);
  const strokeOf = (r) => {
    if (!r) return 'stroke:var(--text);stroke-width:2.4';
    if (r.kind === 'mp') return 'stroke:var(--s5);stroke-width:1.6;stroke-dasharray:2 2';
    return { 1: 'stroke:var(--s1);stroke-width:1.6', 2: 'stroke:var(--s3);stroke-width:1.6;stroke-dasharray:6 3', 4: 'stroke:var(--s2);stroke-width:2' }[r.m];
  };
  const cellX = (i) => 20 + 42 * i;
  const cells = Array.from({ length: a.n_qubits }, (_, i) => svg('g', null,
    svg('rect', { x: cellX(i), y: 328, width: 38, height: 34, rx: 4, style: `fill:${owner.get(i)?.name === 'G4Y' ? 'var(--band)' : 'var(--bg)'};${strokeOf(owner.get(i))}` }),
    text(cellX(i) + 19, 350, `$q_{${i}}$`, { cls: 'sk-note', anchor: 'middle' })));
  const span = (first, last, y, label, cls = 'sk-small') => {
    const x0 = cellX(first) + 3;
    const x1 = cellX(last) + 35;
    return svg('g', null,
      svg('line', { x1: x0, x2: x1, y1: y, y2: y, style: 'stroke:var(--muted);stroke-width:1.2' }),
      text((x0 + x1) / 2, y + 12, label, { cls, anchor: 'middle' }));
  };
  const regSpans = [span(0, 0, 368, 'canary'), ...a.registers.map((r) => span(r.qubits[0], r.qubits[r.qubits.length - 1], 368, r.name))];
  const group = (kind, m) => a.registers.filter((r) => r.kind === kind && r.m === m).flatMap((r) => r.qubits);
  const groups = [[group('ghz', 1), '1 qubit'], [group('ghz', 2), 'GHZ-2'], [group('ghz', 4), 'GHZ-4'], [group('mp', 4), '1 qubit, 4 passes']]
    .map(([qs, label]) => text((cellX(Math.min(...qs)) + cellX(Math.max(...qs)) + 38) / 2, 398, label, { cls: 'sk-note', anchor: 'middle' }));
  const desc = [
    `Top: one of the eight sensor registers of the packed circuit, GHZ-4 read in Y on qubits q${q[0]} to q${q[3]}, in the order compass/circuits.py builds it.`,
    `H on q${q[0]} and a ladder of three CNOTs (q${q[0]} to q${q[1]}, q${q[1]} to q${q[2]}, q${q[2]} to q${q[3]}) prepare a GHZ state.`,
    'Rz(δ) on every qubit stands for the field acting on the qubit, giving (|0000⟩ + e^(i·4δ)|1111⟩)/√2. This is a simulation, not a magnetometer.',
    `In layout B only (the grey dashed box and the dashed ancilla wire), an ancilla q${anc} gets H, then a CNOT from q${anc} to q${q[0]}, Rz(b) on q${q[0]} and the CNOT again. So q${q[0]} sees Rz(+b) or Rz(−b) with equal odds; with cos b = e^(−4γ) this equals independent dephasing γ of each of the four qubits.`,
    `S† on q${q[0]} selects the Y reading, then H on all four qubits and measurement; the ancilla is measured and ignored.`,
    'The parity of the four bits has mean V·sin 4δ (V·cos 4δ for register G4X, read in X).',
    `Bottom: the ${a.n_qubits} qubits of layout A, run as one job. q0 is the canary. ${a.registers.map((r) => `${r.name} on q${r.qubits.join(', q')}`).join('; ')}.`,
    `The canary gets X and must read 1; if it reads 1 in fewer than 90% of shots, the bit order is wrong and the app stops. Layout B drops the 4-pass qubit and adds one ancilla per register on ${ancRange}: ${b.n_qubits} qubits.`,
  ].join(' ');
  return figure({
    w: 760, h: 452, min: 600, title: 'One sensor register as a circuit, and every sensor in one job', desc,
    caption: `Figure 2. Top: one of the eight sensor registers (GHZ-4 read in Y, q${q[0]}–q${q[3]}) as compass/circuits.py builds it; the grey dashed box (and the dashed ancilla wire) is added only in layout B, and the construction is ours. Bottom: all ${a.n_qubits} qubits of the packed circuit that runs as one job. Qiskit’s own drawing of the whole circuit is below.`,
  },
  text(165, 24, 'prepare GHZ-4', { anchor: 'middle' }), text(310, 24, 'field acts (simulated)', { anchor: 'middle' }),
  text(530, 24, '$Y$ only', { anchor: 'middle' }), text(583, 24, 'read', { anchor: 'middle' }),
  wires(q.map((k) => `$q_{${k}}$ $|0⟩$`), 78, 616, 52, 40),
  svg('line', { x1: 78, x2: 616, y1: 222, y2: 222, class: 'sk-anc' }),
  text(70, 226, `$q_{${anc}}$ $|0⟩$`, { anchor: 'end' }), text(70, 244, 'layout B', { anchor: 'end' }),
  gate(105, 52, '$H$', { w: 28, tone: 'var(--text)' }),
  cx(145, 52, 92), cx(185, 92, 132), cx(225, 132, 172),
  svg('rect', { x: 262, y: 34, width: 96, height: 156, rx: 6, style: 'fill:var(--band);stroke:var(--accent);stroke-width:1.4', 'stroke-dasharray': '6 4' }),
  ys.map((y) => gate(310, y, '$R_z(δ)$', { w: 56, tone: 'var(--accent)' })),
  svg('rect', { x: 380, y: 34, width: 132, height: 204, rx: 6, style: 'fill:none;stroke:var(--muted);stroke-width:1.4', 'stroke-dasharray': '4 3' }),
  gate(398, 222, '$H$', { w: 26, tone: 'var(--muted)' }),
  cx(428, 222, 52),
  gate(462, 52, '$R_z(b)$', { w: 48, tone: 'var(--muted)' }),
  cx(496, 222, 52),
  gate(530, 52, '$S^†$', { w: 30, tone: 'var(--text)' }),
  ys.map((y) => gate(565, y, '$H$', { w: 26, tone: 'var(--text)' })),
  [...ys, 222].map((y) => meter(600, y)),
  text(622, 226, 'read and ignored'),
  text(372, 207, '$(|0000⟩ + e^{i·4δ}|1111⟩)/√2$', { cls: 'sk-note', anchor: 'end' }),
  svg('path', { d: 'M618,42 L628,42 L628,182 L618,182 M628,112 L636,112', style: 'fill:none;stroke:var(--muted);stroke-width:1.4' }),
  text(642, 98, '4-bit parity', { cls: 'sk-title' }),
  text(642, 117, '$Y$: $V·sin 4δ$', { cls: 'sk-note' }),
  text(642, 134, 'G4X: $V·cos 4δ$'),
  text(78, 258, `Layout B only: the ancilla, prepared in $|+⟩$, makes q${q[0]} see $R_z(+b)$ or $R_z(−b)$ with equal odds;`),
  text(78, 279, 'with $cos b = e^{−4γ}$ this equals independent dephasing $γ$ of each of the 4 qubits (Huelga et al. 1997).'),
  svg('line', { x1: 20, x2: 740, y1: 292, y2: 292, style: 'stroke:var(--border);stroke-width:1' }),
  text(20, 316, `Every sensor in one circuit, run as one job (layout A, ${a.n_qubits} qubits)`, { cls: 'sk-title' }),
  cells, regSpans, groups,
  text(20, 422, 'Canary q0 gets $X$ and must read 1; below 90% of shots the bit order is wrong and the app stops.'),
  text(20, 438, `Layout B (with dephasing) drops the 4-pass qubit and adds one ancilla per register on ${ancRange}: ${b.n_qubits} qubits.`));
}

/** Figure 3: where each number comes from (architecture and the main components). */
export function architectureFigure(init) {
  const { A, B, twin } = init.qubits;
  const desc = [
    'Data flow from left to right.',
    'Real data: the USGS records of the total magnetic field, one value per minute: Boulder on a quiet day (1 October 2026) and in the G5 storm of 10–11 May 2024, and Tucson in the same storm for the what-if. They were fetched once on 2026-10-10 and the values are used as served.',
    'Python (compass/), run by Qollab in the browser, does every calculation along two paths.',
    'Whole record: a replay model (replay.py) of the same X/Y parity readout runs every minute without a circuit. It uses binomial shot noise times the visibility V, which is ideal, IonQ’s documented Aria 1 rates, or the value measured in a run.',
    `One minute: one packed Qiskit circuit (circuits.py) holds every sensor and a canary qubit q0. It has ${A} qubits, ${B} with dephasing, and the what-if circuit has ${twin}. It is sent as one job to the backend chosen in Qollab’s Run dialog, the built-in or an IonQ noise-model simulator; hardware is refused. The counts come back and decode.py turns them into parities.`,
    'Estimators (estimators.py) turn parities into needle angles θ = atan2(Y, X). The 1-2-4 cascade unwraps GHZ-4. They give the estimates, RMS errors, minutes on a wrong fringe and the dials.',
    'The JavaScript views (main.js, ui/*.js) reach Python only through ui/py.js, as JSON strings. The Overview and the Storm challenge use the replay; the Field tracker and the Two observatories what-if use both paths; Method shows the circuit.',
    'Nothing ran on a magnetometer or on quantum hardware.',
  ].join(' ');
  return figure({
    w: 800, h: 452, min: 640, title: 'Where each number comes from', desc,
    caption: 'Figure 3. Where each number comes from. Real: the USGS records. Model: the replay of the same parity readout, used for whole records. Simulated: one packed Qiskit circuit, sent as one job to the simulator chosen in Qollab’s Run dialog. Classical: the estimators. The two-observatory view is a what-if. Nothing ran on a magnetometer or on quantum hardware.',
  },
  frame(184, 20, 412, 330, 'Python (compass/), run by Qollab in the browser'),
  node(12, 40, 156, 310, 'USGS records', ['total field $F$, one', 'value per minute', '', 'Boulder: quiet day', '1 Oct 2026', 'Boulder: G5 storm', '10–11 May 2024', 'Tucson: same storm,', 'for the what-if', '', 'fetched 2026-10-10,', 'values as served'], REAL, 'REAL'),
  text(196, 58, 'WHOLE RECORD', { cls: 'sk-label' }),
  node(196, 64, 224, 120, 'Replay model (replay.py)', ['the same $X$/$Y$ parity readout,', 'binomial shot noise × $V$,', 'every minute; no circuit.', '$V$: ideal, IonQ Aria 1 rates,', 'or as measured in a run'], MODEL, 'MODEL'),
  text(196, 214, 'ONE MINUTE', { cls: 'sk-label' }),
  node(196, 220, 224, 110, 'Packed Qiskit circuit', ['every sensor + canary q0:', `${A} qubits, ${B} with $γ$; the`, `what-if circuit: ${twin} qubits`, 'circuits.py · decode.py'], SIM, 'SIMULATED'),
  node(436, 64, 148, 266, 'Estimators', ['parities → needle', '$θ = atan2(Y, X)$;', 'cascade 1-2-4', 'unwraps GHZ-4', '', '→ estimates, RMS', 'error, minutes on a', 'wrong fringe, dials', '', 'estimators.py'], CLASSICAL, 'CLASSICAL'),
  node(640, 40, 148, 310, 'Views (JS)', ['main.js, ui/*.js', 'draw what Python', 'returns as JSON', '', 'Overview: replay', 'Storm challenge:', `replay, ${init.challenge_rounds} rounds`, 'Field tracker:', 'replay + one run', '', 'Two observatories', '(what-if): both', '', 'Method: circuit'], INTERFACE, 'INTERFACE'),
  node(644, 227, 140, 36, '', [], WHATIF, null),
  node(196, 380, 388, 60, 'Backend chosen in Qollab’s Run dialog', ['built-in or IonQ noise-model simulator; hardware refused'], PLATFORM, 'QOLLAB'),
  arrow([[168, 124], [194, 124]], LINK),
  arrow([[168, 275], [194, 275]], LINK),
  arrow([[420, 124], [434, 124]], LINK),
  arrow([[300, 330], [300, 378]], { ...LINK, label: 'one job', at: [338, 366] }),
  arrow([[520, 380], [520, 332]], { ...LINK, label: 'counts', at: [488, 366] }),
  arrow([[584, 300], [638, 300]], LINK),
  svg('text', { x: 612, y: 180, transform: 'rotate(-90 612 180)', 'text-anchor': 'middle', class: 'sk-label', text: 'ui/py.js · JSON strings' }));
}

/** Figure 4: the two-observatory what-if (static; the data result stays in the computed text). */
export function twinFigure() {
  const qubit = (x, y, letter) => svg('g', null,
    svg('circle', { cx: x, cy: y, r: 16, style: 'fill:var(--bg);stroke:var(--accent);stroke-width:2.2' }),
    svg('circle', { cx: x, cy: y, r: 12, style: 'fill:none;stroke:var(--accent);stroke-width:1.2' }),
    text(x, y + 5, `$${letter}$`, { cls: 'sk-gate', anchor: 'middle' }));
  const row = (y, state, reads, note) => svg('g', null,
    svg('rect', { x: 16, y, width: 688, height: 26, rx: 4, style: 'fill:var(--bg);stroke:var(--border);stroke-width:1' }),
    text(28, y + 18, state, { cls: 'sk-title' }),
    text(222, y + 18, reads, { cls: 'sk-title' }),
    text(352, y + 18, note));
  return figure({
    w: 720, h: 256, min: 560, title: 'Two observatories, one entangled pair: a what-if',
    desc: 'A what-if. A simulated qubit at the USGS Boulder observatory picks up the phase δA from the real one-minute field step there. A simulated qubit at the Tucson observatory, about 1,000 km away, picks up δB. A dashed line marks the what-if: the two qubits share one entangled pair, which would need a quantum network that does not exist. Prepared as (|01⟩ + |10⟩)/√2, the pair reads only the difference δA − δB, so a field change both sites share cancels. Prepared as (|00⟩ + |11⟩)/√2, it reads the sum δA + δB. The field records are real; the qubits and the link are simulated.',
    caption: 'Figure 4. The two-observatory what-if. The field records at both sites are real (USGS); the qubits and the link are simulated: sharing entanglement between observatories needs a quantum network that does not exist. Two trapped ions up to 6.2 mm apart have done this (Ruster et al. 2017).',
  },
  node(16, 28, 236, 120, 'Boulder, Colorado (BOU)', ['real one-minute field steps'], REAL, 'REAL DATA'),
  node(468, 28, 236, 120, 'Tucson, Arizona (TUC)', ['real one-minute field steps'], REAL, 'REAL DATA'),
  svg('line', { x1: 242, x2: 478, y1: 116, y2: 116, style: 'stroke:var(--s5);stroke-width:2.2', 'stroke-dasharray': '14 6' }),
  qubit(226, 116, 'A'), qubit(494, 116, 'B'),
  text(204, 104, 'simulated qubit A', { anchor: 'end' }), text(204, 122, 'phase $δ_A = s·ΔF$(BOU)', { anchor: 'end' }),
  text(516, 104, 'simulated qubit B'), text(516, 122, 'phase $δ_B = s·ΔF$(TUC)'),
  text(360, 98, 'about 1,000 km', { anchor: 'middle' }),
  svg('rect', { x: 278, y: 107, width: 164, height: 18, rx: 9, style: 'fill:var(--bg);stroke:var(--s5);stroke-width:1.4' }),
  text(360, 120, 'WHAT-IF: SHARED PAIR', { cls: 'sk-label', anchor: 'middle' }),
  text(360, 166, 'would need a quantum network that does not exist', { anchor: 'middle' }),
  row(182, '$(|01⟩ + |10⟩)/√2$', 'reads $δ_A − δ_B$', 'difference: a change both sites share cancels'),
  arrow([[180, 195], [212, 195]], LINK),
  row(216, '$(|00⟩ + |11⟩)/√2$', 'reads $δ_A + δ_B$', 'sum: a change both sites share adds up'),
  arrow([[180, 229], [212, 229]], LINK));
}
