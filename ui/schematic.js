// Small SVG kit for the explanatory figures: boxes, arrows, circuit wires and gates.
// Everything is drawn with the theme's CSS variables, and each figure carries a title and a
// description in words (role="img"), so nothing depends on seeing the picture.
// Text may contain formulas between $…$: they are set in the math font, with italic variables,
// upright functions and digits, and _x / ^x (or _{…} / ^{…}) as sub- and superscripts.
import { el, svg, uid } from './dom.js';

const FUNCTIONS = ['atan2', 'cos', 'sin', 'exp', 'ln', 'mod'];
const VARIABLE = /^[A-Za-zα-ωϑϕ]$/u;

/** Split a formula into runs: italic variables, upright everything else, and scripts. */
function formulaRuns(src) {
  const runs = [];
  const push = (t, italic, shift = 0) => {
    const last = runs[runs.length - 1];
    if (last && last.italic === italic && last.shift === shift) last.t += t;
    else runs.push({ t, italic, shift });
  };
  const chars = [...src];
  for (let i = 0; i < chars.length; i += 1) {
    const rest = chars.slice(i).join('');
    const fn = FUNCTIONS.find((f) => rest.startsWith(f) && !VARIABLE.test(chars[i + f.length] || ''));
    if (fn) {
      push(fn, false);
      i += fn.length - 1;
    } else if ((chars[i] === '_' || chars[i] === '^') && i + 1 < chars.length) {
      const shift = chars[i] === '_' ? 1 : -1;
      let body;
      if (chars[i + 1] === '{') {
        const end = chars.indexOf('}', i + 2);
        body = chars.slice(i + 2, end).join('');
        i = end;
      } else {
        body = chars[i + 1];
        i += 1;
      }
      for (const r of formulaRuns(body)) push(r.t, r.italic, shift);
    } else {
      push(chars[i], VARIABLE.test(chars[i]));
    }
  }
  return runs;
}

/** Fill an SVG <text> with plain text and $…$ formulas. */
export function setRich(node, content) {
  const parts = String(content).split('$');
  if (parts.length === 1) {
    node.textContent = content;
    return node;
  }
  let pos = 0; // baseline offset of the last run: subscripts sit 4 units lower, superscripts 6 higher
  const run = (t, cls, shift) => {
    const target = shift > 0 ? 4 : shift < 0 ? -6 : 0;
    node.append(svg('tspan', { class: cls, dy: target === pos ? null : target - pos, text: t }));
    pos = target;
  };
  parts.forEach((part, k) => {
    if (!part) return;
    if (k % 2 === 0) run(part, null, 0);
    else for (const r of formulaRuns(part)) run(r.t, `sk-math${r.italic ? ' sk-mi' : ''}${r.shift ? ' sk-script' : ''}`, r.shift);
  });
  return node;
}

/** A figure: viewBox w x h, scaled to its container; `min` keeps it legible on narrow screens. */
export function figure({ w, h, title, desc, caption, min = 560 }, ...children) {
  const tId = uid('ft');
  const dId = uid('fd');
  const markerId = uid('arrowhead');
  const root = svg('svg', { viewBox: `0 0 ${w} ${h}`, role: 'img', 'aria-labelledby': `${tId} ${dId}`, class: 'schematic', style: `min-width:${min}px;max-width:${Math.round(w * 1.15)}px` },
    svg('title', { id: tId, text: title }), svg('desc', { id: dId, text: desc }),
    svg('defs', null, svg('marker', { id: markerId, viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse' },
      svg('path', { d: 'M0,0 L10,5 L0,10 z', class: 'sk-head' }))));
  for (const c of children.flat()) if (c) root.append(typeof c === 'function' ? c(markerId) : c);
  const box = el('div', { class: 'schematic-wrap', tabindex: '0', role: 'region', 'aria-label': title }, root);
  // shown only while the figure is wider than the space it has (phones)
  const hint = el('p', { class: 'scroll-hint small muted', hidden: true }, 'Scroll sideways to see the whole figure.');
  if (typeof ResizeObserver === 'function') {
    new ResizeObserver(() => { hint.hidden = !(box.clientWidth > 0 && box.scrollWidth > box.clientWidth + 1); }).observe(box);
  }
  return el('figure', { class: 'schematic-fig' }, box, hint, caption ? el('figcaption', { class: 'small muted' }, caption) : null);
}

/** A rounded box with a bold title and lines of small text (16 units apart, 18 with scripts). */
export function box(x, y, w, h, title, lines = [], { tone = 'var(--border)', dash = null, fill = 'var(--bg)' } = {}) {
  const g = svg('g', null,
    svg('rect', { x, y, width: w, height: h, rx: 10, style: `fill:${fill};stroke:${tone};stroke-width:2`, 'stroke-dasharray': dash }));
  if (title) g.append(text(x + 10, y + 22, title, { cls: 'sk-title' }));
  // 18 units between lines when a formula has a sub- or superscript, so scripts do not crowd the next line
  const step = lines.some((l) => /\$[^$]*[_^]/.test(l || '')) ? 18 : 16;
  lines.forEach((line, i) => { if (line) g.append(text(x + 10, y + 40 + i * step, line)); });
  return g;
}

/** A labelled group frame (dashed). */
export function frame(x, y, w, h, label) {
  return svg('g', null,
    svg('rect', { x, y, width: w, height: h, rx: 12, class: 'sk-frame' }),
    svg('text', { x: x + 10, y: y + 16, class: 'sk-label', text: label }));
}

/** An arrow along a polyline [[x,y], ...]; returns a function so it can use the figure's marker. */
export function arrow(points, { tone = 'var(--muted)', dash = null, width = 1.8, label = null, at = null } = {}) {
  return (markerId) => {
    const d = points.map(([x, y], i) => `${i ? 'L' : 'M'}${x},${y}`).join(' ');
    const g = svg('g', null, svg('path', { d, fill: 'none', style: `stroke:${tone};stroke-width:${width}`, 'stroke-dasharray': dash, 'marker-end': `url(#${markerId})` }));
    if (label) g.append(text(at[0], at[1], label, { anchor: 'middle' }));
    return g;
  };
}

/** Text at (x, y); $…$ parts are set as formulas. */
export function text(x, y, content, { cls = 'sk-small', anchor = 'start' } = {}) {
  return setRich(svg('text', { x, y, class: cls, 'text-anchor': anchor }), content);
}

/** Circuit wires: one horizontal line per qubit label, from x0 to x1, spaced by dy. */
export function wires(labels, x0, x1, y0, dy) {
  return svg('g', null, labels.map((lab, i) => svg('g', null,
    text(x0 - 8, y0 + i * dy + 4, lab, { anchor: 'end' }),
    svg('line', { x1: x0, x2: x1, y1: y0 + i * dy, y2: y0 + i * dy, class: 'sk-wire' }))));
}

/** A single-qubit gate box centred on (x, y). */
export function gate(x, y, label, { w = 34, tone = 'var(--accent)' } = {}) {
  return svg('g', null,
    svg('rect', { x: x - w / 2, y: y - 13, width: w, height: 26, rx: 4, style: `fill:var(--surface);stroke:${tone};stroke-width:1.6` }),
    text(x, y + 5, label, { cls: 'sk-gate', anchor: 'middle' }));
}

/** A controlled-X from (x, yc) to (x, yt). */
export function cx(x, yc, yt) {
  return svg('g', null,
    svg('line', { x1: x, x2: x, y1: yc, y2: yt, class: 'sk-wire-strong' }),
    svg('circle', { cx: x, cy: yc, r: 4, class: 'sk-dot' }),
    svg('circle', { cx: x, cy: yt, r: 9, class: 'sk-target' }),
    svg('line', { x1: x - 9, x2: x + 9, y1: yt, y2: yt, class: 'sk-wire-strong' }),
    svg('line', { x1: x, x2: x, y1: yt - 9, y2: yt + 9, class: 'sk-wire-strong' }));
}

/** A measurement box on (x, y). */
export function meter(x, y) {
  return svg('g', null,
    svg('rect', { x: x - 14, y: y - 13, width: 28, height: 26, rx: 4, style: 'fill:var(--surface);stroke:var(--text);stroke-width:1.4' }),
    svg('path', { d: `M${x - 9},${y + 6} A10,10 0 0 1 ${x + 9},${y + 6}`, fill: 'none', style: 'stroke:var(--text);stroke-width:1.4' }),
    svg('line', { x1: x, y1: y + 6, x2: x + 7, y2: y - 7, style: 'stroke:var(--text);stroke-width:1.4' }));
}
