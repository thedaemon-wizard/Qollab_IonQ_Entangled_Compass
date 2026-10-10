// Time-series chart in SVG. Series differ by colour and by dash, the legend is text, and the
// numbers behind the picture are in a table under <details>, so nothing depends on colour or
// on seeing the plot.
import { el, svg, uid } from './dom.js';

const PAD = { l: 64, r: 14, t: 12, b: 40 };

function ticks(min, max, n = 5) {
  const span = max - min || 1;
  const raw = span / n;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((k) => k * mag).find((s) => span / s <= n + 0.5);
  const out = [];
  for (let v = Math.ceil(min / step) * step; v <= max + 1e-9; v += step) out.push(+v.toFixed(10));
  return out;
}

/**
 * spec: { title, desc, width, height, xLabels: [string], xLabel, yLabel, yMin, yMax,
 *         series: [{ name, values, color, dash }], bands: [{ y0, y1, fill, name }],
 *         hlines: [{ y, label, dash }], marker: { index, label }, table: { columns, rows } }
 */
export function timeChart(spec) {
  const W = spec.width || 760;
  const H = spec.height || 300;
  const iw = W - PAD.l - PAD.r;
  const ih = H - PAD.t - PAD.b;
  const n = spec.xLabels.length;
  const sx = (i) => PAD.l + (i / Math.max(1, n - 1)) * iw;
  const sy = (v) => PAD.t + ih - ((v - spec.yMin) / (spec.yMax - spec.yMin)) * ih;
  const clamp = (v) => Math.min(spec.yMax, Math.max(spec.yMin, v));
  const tId = uid('t');
  const dId = uid('d');
  const clip = uid('clip');
  const root = svg('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-labelledby': `${tId} ${dId}` },
    svg('title', { id: tId, text: spec.title }), svg('desc', { id: dId, text: spec.desc }),
    svg('defs', null, svg('clipPath', { id: clip }, svg('rect', { x: PAD.l, y: PAD.t, width: iw, height: ih }))));
  const grid = svg('g', { class: 'grid' });
  for (const v of ticks(spec.yMin, spec.yMax)) {
    grid.append(svg('line', { x1: PAD.l, x2: PAD.l + iw, y1: sy(v), y2: sy(v) }),
      svg('text', { x: PAD.l - 6, y: sy(v) + 4, 'text-anchor': 'end', class: 'tick', text: String(v) }));
  }
  const every = Math.max(1, Math.round(n / 6));
  for (let i = 0; i < n; i += every) {
    grid.append(svg('text', { x: sx(i), y: PAD.t + ih + 16, 'text-anchor': 'middle', class: 'tick', text: spec.xLabels[i].replace('T', ' ') }));
  }
  grid.append(svg('text', { x: PAD.l + iw / 2, y: H - 4, 'text-anchor': 'middle', class: 'axis', text: spec.xLabel }),
    svg('text', { x: 14, y: PAD.t + ih / 2, 'text-anchor': 'middle', class: 'axis', transform: `rotate(-90 14 ${PAD.t + ih / 2})`, text: spec.yLabel }));
  root.append(grid);
  const plot = svg('g', { 'clip-path': `url(#${clip})` });
  for (const b of spec.bands || []) {
    plot.append(svg('rect', { x: PAD.l, width: iw, y: sy(b.y1), height: Math.max(0, sy(b.y0) - sy(b.y1)), style: `fill:${b.fill}` }));
  }
  for (const l of spec.hlines || []) {
    plot.append(svg('line', { x1: PAD.l, x2: PAD.l + iw, y1: sy(l.y), y2: sy(l.y), class: 'hline', 'stroke-dasharray': l.dash || '6 4' }));
    if (l.label) plot.append(svg('text', { x: PAD.l + iw - 4, y: sy(l.y) - 4, 'text-anchor': 'end', class: 'tick', text: l.label }));
  }
  for (const s of spec.series) {
    const d = s.values.map((v, i) => `${i ? 'L' : 'M'}${sx(i).toFixed(1)},${sy(clamp(v)).toFixed(1)}`).join('');
    plot.append(svg('path', { d, fill: 'none', style: `stroke:${s.color};stroke-width:${s.width || 1.8}`, 'stroke-dasharray': s.dash || null }));
  }
  root.append(plot);
  if (spec.marker && spec.marker.index !== null && spec.marker.index !== undefined) {
    const x = sx(spec.marker.index);
    root.append(svg('line', { x1: x, x2: x, y1: PAD.t, y2: PAD.t + ih, class: 'marker' }),
      svg('text', { x: x + 4, y: PAD.t + 12, class: 'tick', text: spec.marker.label }));
  }
  const legend = el('ul', { class: 'legend', 'aria-hidden': 'true' },
    spec.series.map((s) => el('li', null, svgSwatch(s), s.name)),
    (spec.bands || []).filter((b) => b.name).map((b) => el('li', null, svgSwatch({ fill: b.fill }), b.name)));
  const fig = el('figure', { class: 'chart' }, root, legend);
  if (spec.table) fig.append(dataTable(spec.table, 'Data behind this chart'));
  return fig;
}

function svgSwatch(s) {
  const sw = svg('svg', { width: 28, height: 12, viewBox: '0 0 28 12', 'aria-hidden': 'true' });
  if (s.fill) sw.append(svg('rect', { x: 1, y: 1, width: 26, height: 10, style: `fill:${s.fill}` }));
  else sw.append(svg('line', { x1: 1, x2: 27, y1: 6, y2: 6, style: `stroke:${s.color};stroke-width:2.4`, 'stroke-dasharray': s.dash || null }));
  return sw;
}

/** A table inside <details>; `rows` are arrays of cells (strings or numbers). */
export function dataTable({ caption, columns, rows }, summary) {
  const table = el('table', null, el('caption', null, caption),
    el('thead', null, el('tr', null, columns.map((c) => el('th', { scope: 'col' }, c)))),
    el('tbody', null, rows.map((r) => el('tr', null, r.map((c, i) => (i === 0 ? el('th', { scope: 'row' }, c) : el('td', null, c)))))));
  const wrap = el('div', { class: 'table-wrap', tabindex: '0', role: 'region', 'aria-label': caption }, table);
  return summary ? el('details', null, el('summary', null, summary), wrap) : wrap;
}
