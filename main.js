// Entangled Compass - entry point. Qollab injects `backend` (the simulator chosen in the Run
// dialog) and resolves the Python import below. All numbers come from Python (compass/);
// this file only builds the interface.
import * as compassApi from 'compass.api';
import { challengeView } from './ui/challenge.js';
import { compass3dView } from './ui/compass3d.js';
import { el, nextPaint } from './ui/dom.js';
import { methodView } from './ui/method.js';
import { overviewView } from './ui/overview.js';
import { connect, py } from './ui/py.js';
import { loadTex } from './ui/tex.js';
import { trackerView } from './ui/tracker.js';
import { twinView } from './ui/twin.js';

const main = document.getElementById('ec-main');
const tablist = document.getElementById('ec-tablist');

function tabs(items) {
  const buttons = items.map((it, i) => el('button', {
    type: 'button', role: 'tab', id: `ec-tab-${it.id}`, 'aria-controls': `ec-panel-${it.id}`,
    'aria-selected': i === 0 ? 'true' : 'false', tabindex: i === 0 ? '0' : '-1',
  }, it.title));
  const panels = items.map((it, i) => el('div', {
    role: 'tabpanel', id: `ec-panel-${it.id}`, 'aria-labelledby': `ec-tab-${it.id}`, tabindex: '0', hidden: i !== 0,
  }, it.element));
  function select(i, focus) {
    buttons.forEach((b, k) => {
      b.setAttribute('aria-selected', String(k === i));
      b.tabIndex = k === i ? 0 : -1;
      panels[k].hidden = k !== i;
    });
    if (focus) buttons[i].focus();
    if (items[i].onShow) items[i].onShow();
  }
  buttons.forEach((b, i) => {
    b.addEventListener('click', () => select(i, false));
    b.addEventListener('keydown', (e) => {
      const last = buttons.length - 1;
      const next = { ArrowRight: i === last ? 0 : i + 1, ArrowLeft: i === 0 ? last : i - 1, Home: 0, End: last }[e.key];
      if (next !== undefined) {
        e.preventDefault();
        select(next, true);
      }
    });
  });
  tablist.replaceChildren(...buttons);
  main.replaceChildren(...panels);
  return { select };
}

async function start() {
  connect(compassApi, backend);
  const texReady = loadTex(); // formulas: Temml from jsDelivr, or plain text if it cannot load
  const [init, info] = [await py.init(), await py.backendInfo()];
  await texReady;
  document.getElementById('ec-backend').textContent = `Simulator for this session: ${info.name}${info.noise_model ? ` (noise model ${info.noise_model})` : ''}. Choose another in Qollab’s Run dialog.`;
  const state = { lastRun: null, measuredVis: null };
  let tabCtl = null;
  const overview = overviewView(init, () => tabCtl.select(2, true), () => tabCtl.select(1, true));
  const tracker = trackerView(init, info, state);
  const method = methodView(init);
  const compass3d = compass3dView(init);
  tabCtl = tabs([
    { id: 'overview', title: 'Overview', element: overview.element },
    { id: 'challenge', title: 'Storm challenge', element: challengeView(state, init) },
    { id: 'tracker', title: 'Field tracker', element: tracker },
    { id: 'compass3d', title: '3D compass', element: compass3d.element, onShow: compass3d.onShow },
    { id: 'twin', title: 'Two observatories', element: twinView(info, init) },
    { id: 'method', title: 'Method & sources', element: method.element, onShow: method.onShow },
  ]);
  // The skip link moves focus without changing the URL (the frame's hash belongs to Qollab).
  document.querySelector('.skip-link').addEventListener('click', (e) => {
    e.preventDefault();
    main.focus();
  });
  await nextPaint(); // show the tabs before the first (blocking) replay
  try {
    overview.fill(await py.overview());
  } catch (err) {
    overview.fail(err.message);
  }
}

try {
  await start();
} catch (err) {
  const box = document.getElementById('ec-loading') || main;
  box.textContent = `The app could not start: ${err && err.message ? err.message : err}`;
  box.setAttribute('role', 'alert');
}

// Keep main.js running: the injected backend (and so the circuit runs) stays available only while it does.
await new Promise(() => {});
