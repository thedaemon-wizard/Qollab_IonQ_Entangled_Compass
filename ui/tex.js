// Formulas as native MathML. TeX strings become MathML through Temml 0.14.0 (MIT licence, by
// Ron Kok), loaded at run time from jsDelivr and set in the Latin Modern Math font (main.css).
// If Temml cannot be loaded, the same strings are shown as plain Unicode text instead.
// Write formulas between $…$ in a string passed to rich(); use String.raw for the backslashes.
const TEMML_URL = 'https://cdn.jsdelivr.net/npm/temml@0.14.0/dist/temml.mjs';
let temml = null;

/** Load Temml once (at most `ms` milliseconds); resolves to true when formulas can be typeset. */
export async function loadTex(ms = 4000) {
  if (temml) return true;
  const url = TEMML_URL; // a variable, so no bundler tries to resolve the URL
  try {
    const mod = await Promise.race([import(url), new Promise((_, reject) => setTimeout(() => reject(new Error('timed out')), ms))]);
    temml = mod.default;
  } catch {
    temml = null;
  }
  return Boolean(temml);
}

const WORDS = {
  alpha: 'α', gamma: 'γ', delta: 'δ', Delta: 'Δ', theta: 'θ', pi: 'π', sigma: 'σ', varphi: 'φ',
  approx: '≈', le: '≤', ge: '≥', pm: '±', times: '×', cdot: '·', in: '∈', to: '→',
  lvert: '|', rvert: '|', langle: '⟨', rangle: '⟩', dots: '…', ln: 'ln', cos: 'cos', sin: 'sin',
};

const SUB = Object.fromEntries([...'0123456789aehijklmnoprstuvx'].map((c, i) => [c, '₀₁₂₃₄₅₆₇₈₉ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ'[i]]));

/** The Unicode text shown when Temml is not available (and for tests). */
export function plain(src) {
  return src
    .replace(/\\(?:operatorname|text|mathrm)\{([^{}]*)\}/g, '$1')
    .replace(/\\hat\{([^{}]*)\}/g, '$1̂')
    .replace(/\\sqrt\{([^{}]*)\}/g, (_, x) => (x.length > 1 ? `√(${x})` : `√${x}`))
    .replace(/\^\{([^{}]*)\}/g, '^($1)')
    .replace(/_\{([^{}]*)\}/g, '_$1')
    .replace(/_([0-9a-z])/g, (m, c) => SUB[c] ?? m)
    .replace(/([A-Za-z])\\(cos|sin)/g, '$1·$2')
    .replace(/\\([,;!{}%])/g, (_, c) => ({ ',': '\u2009', ';': ' ', '!': '' }[c] ?? c))
    .replace(/\\(lvert|langle) /g, '\\$1') // TeX drops the space after these
    .replace(/\\([A-Za-z]+)/g, (_, w) => WORDS[w] ?? w)
    .replace(/[{}]/g, '')
    .replace(/-/g, '−');
}

/** One formula as a <math> element (or plain text if Temml is not loaded). */
export function tex(src, { display = false } = {}) {
  if (!temml) return document.createTextNode(plain(src));
  const host = document.createElement('span');
  temml.render(src, host, { displayMode: display, annotate: true, throwOnError: false });
  return host.firstElementChild || document.createTextNode(plain(src));
}

/** Text with $…$ formulas, as a DocumentFragment that el() can append. */
export function rich(text) {
  const frag = document.createDocumentFragment();
  String(text).split('$').forEach((part, i) => {
    if (part) frag.append(i % 2 ? tex(part) : part);
  });
  return frag;
}
