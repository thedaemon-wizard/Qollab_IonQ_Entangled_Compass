// The compass dials: one per sensor in the run. The needle angle is the phase the sensor
// measured, atan2(<Y>, <X>) = m * delta (mod 360°); the needle length is the measured
// visibility (the dashed circle is 1). A thin tick marks where an ideal needle would point.
// Past half a turn the needle still points the right way, but reading it back gives the wrong
// field: that is the GHZ fringe problem, drawn.
import { el, fmt, svg, uid } from './dom.js';

const COLORS = { 1: 'var(--s1)', 2: 'var(--s3)', 4: 'var(--s2)' };

function polar(r, deg) {
  const a = (deg * Math.PI) / 180;
  return [r * Math.cos(a), -r * Math.sin(a)];
}

function dial(d, readNt, trueNt, halfNt) {
  const R = 54;
  const tId = uid('dt');
  const dId = uid('dd');
  const color = d.label.includes('passes') ? 'var(--s5)' : COLORS[d.m];
  const [nx, ny] = polar(R * Math.min(1, Math.max(0, d.length)), d.angle_deg);
  const [tx0, ty0] = polar(R - 8, d.true_deg);
  const [tx1, ty1] = polar(R + 6, d.true_deg);
  const verdict = Math.abs(readNt - trueNt) < halfNt ? 'right fringe' : 'wrong fringe';
  const s = svg('svg', { viewBox: '-70 -70 140 140', role: 'img', 'aria-labelledby': `${tId} ${dId}`, class: 'dial-svg' },
    svg('title', { id: tId, text: `${d.label} dial` }),
    svg('desc', { id: dId, text: `Needle at ${fmt.n(d.angle_deg, 0)} degrees (ideal ${fmt.n(d.true_deg, 0)}), length ${fmt.n(d.length, 2)}. Read back as a field step of ${fmt.signed(readNt, 1)} nT; the true step is ${fmt.signed(trueNt, 1)} nT: ${verdict}.` }),
    svg('circle', { r: R, class: 'dial-ring' }),
    svg('line', { x1: -R, x2: R, y1: 0, y2: 0, class: 'dial-axis' }),
    svg('line', { x1: 0, x2: 0, y1: -R, y2: R, class: 'dial-axis' }),
    svg('text', { x: R + 3, y: 4, class: 'dial-tick', text: 'X' }),
    svg('text', { x: -3, y: -R - 4, class: 'dial-tick', text: 'Y', 'text-anchor': 'middle' }),
    svg('line', { x1: tx0, y1: ty0, x2: tx1, y2: ty1, class: 'dial-true' }),
    svg('line', { x1: 0, y1: 0, x2: nx, y2: ny, style: `stroke:${color};stroke-width:4;stroke-linecap:round` }),
    svg('circle', { r: 4, style: `fill:${color}` }));
  return el('figure', { class: 'dial' }, s,
    el('figcaption', null, el('strong', null, d.label), el('br'),
      `phase ×${d.m}: ${fmt.n(d.angle_deg, 0)}° (ideal ${fmt.n(d.true_deg, 0)}°)`, el('br'),
      `reads ${fmt.signed(readNt, 1)} nT: `, el('span', { class: verdict === 'right fringe' ? 'ok' : 'bad' }, verdict)));
}

/** r: the run report. */
export function dialsPanel(r) {
  const readNt = (d) => (d.angle_deg * Math.PI) / 180 / d.m / r.scale;
  const row = el('div', { class: 'dials' }, r.dials.map((d) => dial(d, readNt(d), r.dF_nT, Math.PI / (d.m * r.scale))));
  return el('section', { class: 'dials-panel', 'aria-label': 'Compass dials' },
    el('h3', null, 'The dials: entanglement turns the needle faster'),
    row,
    el('p', { class: 'small muted' }, `A GHZ register of m qubits turns its needle m times as far for the same field step, so the needle is m times as sensitive, but it can only be read back unambiguously within ±${fmt.n(r.fringes.half_range_nT['4'], 1)} nT per minute for GHZ-4 (±${fmt.n(r.fringes.half_range_nT['1'], 1)} nT for one qubit). The cascade reads the 1-qubit and GHZ-2 dials first to know which turn GHZ-4 is on.`));
}
