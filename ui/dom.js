// Small DOM helpers: element builders, a live region, number formats.
const SVG_NS = 'http://www.w3.org/2000/svg';
let counter = 0;

function apply(el, attrs) {
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'on') for (const [ev, fn] of Object.entries(v)) el.addEventListener(ev, fn);
    else if (k === 'text') el.textContent = v;
    else el.setAttribute(k, v === true ? '' : String(v));
  }
  return el;
}

function append(el, children) {
  for (const c of children.flat(Infinity)) {
    if (c === null || c === undefined || c === false || c === '') continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

export function el(tag, attrs, ...children) {
  return append(apply(document.createElement(tag), attrs), children);
}

export function svg(tag, attrs, ...children) {
  return append(apply(document.createElementNS(SVG_NS, tag), attrs), children);
}

export function uid(prefix) {
  counter += 1;
  return `${prefix}-${counter}`;
}

const live = el('div', { class: 'sr-only', 'aria-live': 'polite', role: 'status' });
document.body.append(live);

/** Tell screen-reader users about a change that happened away from their focus. */
export function announce(text) {
  live.textContent = '';
  setTimeout(() => { live.textContent = text; }, 30);
}

/** Let the browser paint (status text, busy state) before a long synchronous Python call. */
export function nextPaint() {
  return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
}

export const fmt = {
  n: (x, d = 2) => (x === null || x === undefined || !Number.isFinite(x) ? '–' : x.toFixed(d)),
  pm: (o, d = 2) => (o && o.mean !== null ? `${o.mean.toFixed(d)} ± ${o.two_se.toFixed(d)}` : '–'),
  int: (x) => (x === null || x === undefined ? '–' : Math.round(x).toLocaleString('en-US')),
  signed: (x, d = 2) => (x === null || x === undefined ? '–' : `${x >= 0 ? '+' : '−'}${Math.abs(x).toFixed(d)}`),
};
