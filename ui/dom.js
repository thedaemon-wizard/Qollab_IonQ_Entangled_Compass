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

/**
 * After an action that disabled its own control: if focus fell back to <body>, put it on the
 * control again, or, when the control stays disabled, on `fallback` (made focusable for this).
 */
export function keepFocus(control, fallback) {
  const lost = !document.activeElement || document.activeElement === document.body;
  if (!lost) return;
  if (control && !control.disabled && control.isConnected) control.focus();
  else if (fallback && fallback.isConnected) {
    if (!fallback.hasAttribute('tabindex')) fallback.setAttribute('tabindex', '-1');
    fallback.focus();
  }
}

/**
 * A sideways scroller for a picture with a minimum width. While the picture is wider than the
 * space it has, the scroller is a focusable, named region (so keyboard users can scroll it) and a
 * hint under it says so; otherwise neither is there.
 */
export function scroller(picture, label, what = 'chart') {
  const hint = el('p', { class: 'scroll-hint small muted', hidden: true }, `Scroll sideways to see the whole ${what}.`);
  const wrap = el('div', { class: 'scroll-wrap' }, picture);
  const check = () => {
    const scrolls = wrap.clientWidth > 0 && wrap.scrollWidth > wrap.clientWidth + 1;
    hint.hidden = !scrolls;
    if (scrolls) {
      wrap.setAttribute('tabindex', '0');
      wrap.setAttribute('role', 'region');
      wrap.setAttribute('aria-label', label);
    } else if (wrap.hasAttribute('tabindex')) {
      if (document.activeElement === wrap) return; // keep a focused scroller until focus moves on
      wrap.removeAttribute('tabindex');
      wrap.removeAttribute('role');
      wrap.removeAttribute('aria-label');
    }
  };
  if (typeof ResizeObserver === 'function') new ResizeObserver(check).observe(wrap);
  return el('div', { class: 'scroll-box' }, wrap, hint);
}

/** A typographic minus (U+2212) for a leading hyphen-minus, as in fmt.signed. */
export const minus = (s) => String(s).replace(/^-/, '\u2212');

export const fmt = {
  n: (x, d = 2) => (x === null || x === undefined || !Number.isFinite(x) ? '–' : minus(x.toFixed(d))),
  pm: (o, d = 2) => (o && o.mean !== null ? `${minus(o.mean.toFixed(d))} ± ${o.two_se.toFixed(d)}` : '–'),
  int: (x) => (x === null || x === undefined ? '–' : Math.round(x).toLocaleString('en-US')),
  signed: (x, d = 2) => (x === null || x === undefined ? '–' : `${x >= 0 ? '+' : '−'}${Math.abs(x).toFixed(d)}`),
};
