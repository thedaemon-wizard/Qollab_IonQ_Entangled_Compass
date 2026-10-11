// The storm in 3D: a compass whose three needles follow a model replay of the real field record
// minute by minute (every number comes from Python, compass/api.py storm3d_json). A needle shows
// the angle its register reads back; the arc beneath it shows how far that minute's field step
// turned the register (m s dF). While a sensor's estimate sits on a wrong fringe its arc and hub
// are red; the counter counts its fringe changes, onto a wrong fringe and back. three.js comes
// from Qollab's import map (three@0.186.1); without WebGL the controls and the text panel below
// still show every number.
import { announce, el, fmt, fullChoice, nextPaint, uid } from './dom.js';
import { py } from './py.js';
import { rich } from './tex.js';

const ARMS = [
  { key: 'IND8', name: '8 independent qubits', short: '8 indep.', colorVar: '--s1', y: 0.08, radius: 1.05 },
  { key: 'GHZ4', name: 'GHZ-4 alone', short: 'GHZ-4', colorVar: '--s2', y: 0.3, radius: 1.25 },
  { key: 'CASC', name: 'Cascade 1-2-4 (its GHZ-4 needle)', short: 'cascade', colorVar: '--s3', y: 0.52, radius: 1.45 },
];
const SPEEDS = [[30, '30 minutes per second'], [120, '2 hours per second'], [480, '8 hours per second']];
const DEG = 180 / Math.PI;
const DIAL_R = 1.6;
const FOV = 38; // vertical field of view (degrees) on a wide stage
const FIT = 2.05; // half-width (scene units) kept in view at the home distance: the dial and its tags
const HOME = { radius: 4.6, theta: -0.5, phi: 1.02 };
const TAG_GAP = 3; // px between two needle tags, and between a tag and the HUD
const TAG_EDGE = 3; // px between a tag and the edge of the stage

// The theme's colours live on the app root (.ec-root), so read them from the element drawn into.
const cssVar = (node, name) => getComputedStyle(node).getPropertyValue(name).trim() || '#888888';
const deg = (rad) => { const d = Math.round(rad * DEG); return `${d > 0 ? '+' : d < 0 ? '−' : ''}${Math.abs(d)}°`; };
const changes = (n) => `${n} fringe change${n === 1 ? '' : 's'}`;
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const THREE_TIMEOUT_MS = 8000; // a slow CDN must not hold up the text panel
const utc = (iso) => `${iso.replace('T', ' ')} UTC`;

/** A point on the dial at angle a (rad, counter-clockwise from +X seen from above) and height y. */
function onDial(THREE, r, a, y) {
  return new THREE.Vector3(r * Math.cos(a), y, -r * Math.sin(a));
}

async function makeScene(host, onChange, onResize) {
  const timeout = new Promise((_, reject) => { setTimeout(() => reject(new Error('three.js did not load in time')), THREE_TIMEOUT_MS); });
  const [THREE, { OrbitControls }, { CSS2DRenderer, CSS2DObject }] = await Promise.race([Promise.all([
    import('three'), import('three/addons/controls/OrbitControls.js'), import('three/addons/renderers/CSS2DRenderer.js'),
  ]), timeout]);
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  host.prepend(renderer.domElement); // before the HUD, which flows below the picture on a narrow stage
  renderer.domElement.setAttribute('aria-hidden', 'true');
  const labels = new CSS2DRenderer();
  labels.domElement.className = 'c3d-labels';
  labels.domElement.setAttribute('aria-hidden', 'true');
  host.append(labels.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(FOV, 16 / 9, 0.1, 50);
  const view = { ...HOME };
  scene.add(new THREE.AmbientLight(0xffffff, 0.75));
  const sun = new THREE.DirectionalLight(0xffffff, 0.9);
  sun.position.set(2.5, 5, 3);
  scene.add(sun);

  const mats = [];
  const mat = (colorVar, opts = {}) => {
    const m = new THREE.MeshStandardMaterial({ roughness: 0.55, metalness: 0.1, ...opts });
    m.userData.colorVar = colorVar;
    mats.push(m);
    return m;
  };
  const lineMat = (colorVar, opts = {}) => {
    const m = new THREE.LineBasicMaterial(opts);
    m.userData.colorVar = colorVar;
    mats.push(m);
    return m;
  };

  // dial face, rim, ticks every 15 degrees (long ones every 90), and the half-turn line
  const faceMat = mat('--surface', { emissiveIntensity: 0.45 }); // lit from above, so lift it to the theme's surface
  const face = new THREE.Mesh(new THREE.CylinderGeometry(DIAL_R, DIAL_R, 0.04, 96), faceMat);
  face.position.y = -0.02;
  scene.add(face);
  scene.add(new THREE.Mesh(new THREE.TorusGeometry(DIAL_R, 0.022, 12, 128).rotateX(Math.PI / 2), mat('--border')));
  const tickPts = [];
  for (let k = 0; k < 24; k += 1) {
    const a = (k * Math.PI) / 12;
    const inner = k % 6 === 0 ? DIAL_R - 0.22 : DIAL_R - 0.1;
    tickPts.push(onDial(THREE, inner, a, 0.005), onDial(THREE, DIAL_R - 0.02, a, 0.005));
  }
  scene.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(tickPts), lineMat('--muted')));
  const edge = [onDial(THREE, 0.2, Math.PI, 0.006), onDial(THREE, DIAL_R - 0.02, Math.PI, 0.006)];
  scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(edge), lineMat('--bad')));

  // needles (shaft + tip + hub) and their arcs
  const parts = {};
  const tags = [];
  for (const arm of ARMS) {
    const g = new THREE.Group();
    const m = mat(arm.colorVar);
    const shaft = new THREE.Mesh(new THREE.BoxGeometry(arm.radius - 0.14, 0.04, 0.07), m);
    shaft.position.x = (arm.radius - 0.14) / 2;
    const tip = new THREE.Mesh(new THREE.ConeGeometry(0.085, 0.2, 24).rotateZ(-Math.PI / 2), m);
    tip.position.x = arm.radius - 0.08;
    const tag = document.createElement('span');
    tag.className = 'c3d-tag';
    tag.textContent = arm.short;
    tag.style.borderColor = `var(${arm.colorVar})`;
    const label = new CSS2DObject(tag);
    label.position.set(arm.radius + 0.12, 0.06, 0);
    tags.push({ tag, label });
    g.add(shaft, tip, label);
    g.position.y = arm.y;
    scene.add(g);
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, 0.07, 24), mat(arm.colorVar, { emissiveIntensity: 0.9 }));
    hub.position.y = arm.y;
    scene.add(hub);
    // the arc is a tube (WebGL draws lines one pixel wide), rebuilt for every minute shown
    const arcMatOk = mat(arm.colorVar, { transparent: true, opacity: 0.85 });
    const arcMatBad = mat('--bad', { emissiveIntensity: 0.35 });
    const arc = new THREE.Mesh(new THREE.BufferGeometry(), arcMatOk);
    scene.add(arc);
    parts[arm.key] = { needle: g, hub, arc, arcMatOk, arcMatBad };
  }
  scene.add(new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.66, 16), mat('--muted')).translateY(0.31));

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enablePan = false;
  controls.enableZoom = false; // the wheel scrolls the page; the view only turns
  controls.addEventListener('change', onChange);
  renderer.domElement.style.touchAction = 'pan-y'; // a vertical swipe scrolls the page, a sideways drag turns

  function placeCamera() {
    camera.position.set(
      view.radius * Math.sin(view.phi) * Math.sin(view.theta),
      view.radius * Math.cos(view.phi),
      view.radius * Math.sin(view.phi) * Math.cos(view.theta),
    );
    camera.lookAt(0, 0.2, 0);
    controls.target.set(0, 0.2, 0);
    controls.update();
  }
  placeCamera();

  function recolor() {
    for (const m of mats) m.color.set(cssVar(host, m.userData.colorVar));
    for (const m of mats) if (m.userData.colorVar === '--bad' && m.emissive) m.emissive.set(cssVar(host, '--bad'));
    faceMat.emissive.set(cssVar(host, '--surface'));
    onChange();
  }
  recolor();
  const scheme = window.matchMedia('(prefers-color-scheme: light)');
  if (scheme.addEventListener) scheme.addEventListener('change', recolor);

  const size = { w: 0, h: 0, rem: 0 };
  function resize() {
    const w = host.clientWidth || 640;
    const h = Math.round(Math.min(Math.max(w * 0.56, 260), 520));
    // on a narrow stage the HUD would cover a quarter of the picture: it goes below it instead
    const rem = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
    const changed = w !== size.w || rem !== size.rem;
    host.classList.toggle('c3d-narrow', w < 36 * rem);
    Object.assign(size, { w, h, rem });
    renderer.setSize(w, h, true);
    labels.setSize(w, h);
    camera.aspect = w / h;
    // a stage narrower than about 1.3:1 would cut off the sides of the dial: widen the view to keep FIT
    camera.fov = Math.max(FOV, 2 * Math.atan(FIT / (HOME.radius * camera.aspect)) * DEG);
    camera.updateProjectionMatrix();
    if (changed) onResize();
    onChange();
  }

  // The tags are fixed-size HTML at the needle tips, which are only 0.2 apart: when needles point
  // the same way, or the stage is small, they would land on each other, on the HUD or past the
  // edge. After each render, move them apart and back into the picture, as little as needed.
  const anchor = new THREE.Vector3();
  function placeTags() {
    const { w, h } = size;
    const boxes = [];
    for (const { tag, label } of tags) {
      if (tag.style.display === 'none') continue; // behind the camera
      anchor.setFromMatrixPosition(label.matrixWorld).project(camera);
      const r = tag.getBoundingClientRect();
      boxes.push({ tag, x: ((anchor.x + 1) / 2) * w, y: ((1 - anchor.y) / 2) * h, hw: r.width / 2, hh: r.height / 2 });
    }
    const hud = host.querySelector('.c3d-hud');
    // the HUD sits at the top-left over the picture (unless it flows below it): keep tags off it
    const hudBox = hud && hud.offsetTop < h && hud.offsetWidth
      ? { x1: hud.offsetLeft + hud.offsetWidth + TAG_GAP, y1: hud.offsetTop + hud.offsetHeight + TAG_GAP } : null;
    for (let pass = 0; pass < 40; pass += 1) {
      let moved = false;
      for (let i = 0; i < boxes.length; i += 1) {
        for (let j = i + 1; j < boxes.length; j += 1) {
          const a = boxes[i];
          const b = boxes[j];
          const ox = a.hw + b.hw + TAG_GAP - Math.abs(a.x - b.x);
          const oy = a.hh + b.hh + TAG_GAP - Math.abs(a.y - b.y);
          if (ox <= 0.01 || oy <= 0.01) continue;
          moved = true;
          // split the shorter way out between the two
          if (oy <= ox) {
            const s = a.y <= b.y ? -oy / 2 : oy / 2;
            a.y += s;
            b.y -= s;
          } else {
            const s = a.x <= b.x ? -ox / 2 : ox / 2;
            a.x += s;
            b.x -= s;
          }
        }
      }
      for (const a of boxes) {
        if (hudBox) {
          const dx = hudBox.x1 - (a.x - a.hw);
          const dy = hudBox.y1 - (a.y - a.hh);
          if (dx > 0.01 && dy > 0.01) {
            if (dx < dy) a.x += dx; else a.y += dy;
            moved = true;
          }
        }
        const x = Math.min(Math.max(a.x, a.hw + TAG_EDGE), w - a.hw - TAG_EDGE);
        const y = Math.min(Math.max(a.y, a.hh + TAG_EDGE), h - a.hh - TAG_EDGE);
        if (Math.abs(x - a.x) > 0.01 || Math.abs(y - a.y) > 0.01) moved = true;
        a.x = x;
        a.y = y;
      }
      if (!moved) break;
    }
    for (const a of boxes) a.tag.style.transform = `translate(-50%, -50%) translate(${a.x.toFixed(1)}px, ${a.y.toFixed(1)}px)`;
  }
  new ResizeObserver(resize).observe(host);
  resize();

  /** Draw minute t: needle angles are the readings, arcs the true (unwrapped) turns. */
  function show(arms, t) {
    for (const arm of ARMS) {
      const a = arms[arm.key];
      const p = parts[arm.key];
      p.needle.rotation.y = a.reading[t];
      const turn = a.turn[t];
      // red only when the sensor's estimate is on a wrong fringe: the cascade's GHZ-4 register
      // also turns past half a turn, but its 1-qubit and GHZ-2 registers say which turn it is on
      const bad = a.fringe[t] !== 0;
      const n = Math.max(3, Math.min(240, Math.ceil((Math.abs(turn) / (2 * Math.PI)) * 96) + 3));
      const pts = [];
      for (let i = 0; i < n; i += 1) {
        const u = (turn * i) / (n - 1);
        pts.push(onDial(THREE, arm.radius * 0.7, u, arm.y - 0.05 + (0.06 * Math.abs(u)) / Math.PI));
      }
      const old = p.arc.geometry;
      // a wrong fringe is shown by a thicker tube as well as by colour
      p.arc.geometry = Math.abs(turn) < 1e-3 ? new THREE.BufferGeometry()
        : new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), n * 2, bad ? 0.04 : 0.022, 8, false);
      old.dispose();
      p.arc.material = bad ? p.arcMatBad : p.arcMatOk;
      p.hub.material.emissive.set(bad ? cssVar(host, '--bad') : '#000000');
    }
  }

  return {
    show,
    render: () => {
      renderer.render(scene, camera);
      labels.render(scene, camera);
      placeTags();
    },
    turn: (dTheta, dPhi) => {
      const off = camera.position.clone();
      view.radius = off.length();
      view.theta = Math.atan2(off.x, off.z) + dTheta;
      view.phi = Math.min(1.45, Math.max(0.15, Math.acos(off.y / view.radius) + dPhi));
      placeCamera();
    },
    reset: () => {
      Object.assign(view, HOME);
      placeCamera();
    },
  };
}

export function compass3dView(init) {
  const sel = (id, label, options, value) => {
    const s = el('select', { id }, options.map(([v, text]) => el('option', { value: String(v) }, text)));
    s.value = String(value);
    return [el('label', { for: id }, label), s];
  };
  const [dataLabel, dataset] = sel('ec3-dataset', 'Field record',
    Object.entries(init.datasets).map(([k, d]) => [k, `${d.label}: ${d.minutes} min`]), 'storm');
  const [speedLabel, speed] = sel('ec3-speed', 'Speed', SPEEDS, 120);
  const play = el('button', { type: 'button', class: 'primary', id: 'ec3-play' }, 'Play');
  const back = el('button', { type: 'button' }, '− 1 minute');
  const fwd = el('button', { type: 'button' }, '+ 1 minute');
  const toFirst = el('button', { type: 'button', id: 'ec3-first', 'aria-describedby': 'ec3-summary' }, 'Go to the first fringe change');
  const slider = el('input', { type: 'range', id: 'ec3-minute', min: '0', max: '0', step: '1', value: '0' });
  const sliderLabel = el('label', { for: 'ec3-minute' }, 'Minute');
  const status = el('p', { role: 'status', class: 'status', id: 'ec3-status' }, 'Open this tab to load the replay.');
  const stage = el('div', { class: 'c3d', role: 'img', id: 'ec3-stage', 'aria-label': 'The 3D compass (loading).' });
  // the same time and fringe-change counts as the text panel, over the picture (hidden from screen readers)
  const hud = el('div', { class: 'c3d-hud', 'aria-hidden': 'true' });
  stage.append(hud);
  const camButtons = [
    ['Turn left', -0.35, 0], ['Turn right', 0.35, 0], ['Tilt up', 0, -0.2], ['Tilt down', 0, 0.2],
  ].map(([text, dT, dP]) => {
    const b = el('button', { type: 'button' }, text);
    b.addEventListener('click', () => { if (scene) { scene.turn(dT, dP); draw(); } });
    return b;
  });
  const resetView = el('button', { type: 'button' }, 'Reset view');
  const camGroup = el('div', { class: 'toolbar', role: 'group', 'aria-label': 'Turn the 3D view' }, ...camButtons, resetView);
  const readout = el('dl', { class: 'c3d-readout', id: 'ec3-readout' });
  const summary = el('p', { class: 'small', id: 'ec3-summary' });
  const descId = uid('c3d');

  let data = null;
  let scene = null;
  let t = 1;
  let playing = false;
  let last = 0;
  let pending = false;
  let noScene = false; // WebGL is not available: text panel only, no camera, no retry

  function describe(minute) {
    if (!data) return '';
    const parts = ARMS.map((arm) => {
      const a = data.arms[arm.key];
      const wrong = a.fringe[minute] !== 0;
      return `${arm.name} reads ${deg(a.reading[minute])}; the field step turned it ${deg(a.turn[minute])}: ${wrong ? 'wrong fringe' : 'right fringe'}, ${changes(a.slips_so_far[minute])} so far.`;
    });
    return `${utc(data.times[minute])}, field step ${fmt.signed(data.dF_nT[minute], 1)} nT. ${parts.join(' ')}`;
  }

  function fillReadout(minute) {
    const rows = [el('dt', null, 'Time'), el('dd', null, utc(data.times[minute])),
      el('dt', null, 'Field step this minute'), el('dd', null, `${fmt.signed(data.dF_nT[minute], 1)} nT`)];
    for (const arm of ARMS) {
      const a = data.arms[arm.key];
      const wrong = a.fringe[minute] !== 0;
      rows.push(el('dt', null, el('span', { class: 'swatch', style: `background:var(${arm.colorVar})` }), arm.name),
        el('dd', null, `reads ${deg(a.reading[minute])}, field step turned it ${deg(a.turn[minute])}: `,
          el('span', { class: wrong ? 'bad' : 'ok' }, wrong ? 'wrong fringe' : 'right fringe'),
          `; ${changes(a.slips_so_far[minute])} so far`));
    }
    readout.replaceChildren(...rows);
  }

  function fillHud(time, step, rows) {
    hud.replaceChildren(el('div', null, utc(time)), el('div', null, `field step ${fmt.signed(step, 1)} nT`),
      ...ARMS.map((arm, i) => {
        const [slips, wrong] = rows[i];
        return el('div', { class: wrong ? 'bad' : '' },
          el('span', { class: 'swatch', style: `background:var(${arm.colorVar})` }),
          `${arm.short}: ${changes(slips)}${wrong ? ', wrong fringe' : ''}`);
      }));
  }

  // Below the picture (narrow stage) the HUD would grow by a line whenever a reading turns
  // "wrong fringe" and wraps, moving the page under it: hold the height of its longest lines.
  function reserveHud() {
    hud.style.minHeight = '';
    if (data && stage.classList.contains('c3d-narrow')) {
      const n = data.times.length - 1;
      const longest = data.dF_nT.reduce((a, v) => (fmt.signed(v, 1).length > fmt.signed(a, 1).length ? v : a), 0);
      fillHud(data.times[n], longest, ARMS.map((arm) => {
        const a = data.arms[arm.key];
        return [a.slips_so_far[n], a.fringe.some((x) => x !== 0)];
      }));
      hud.style.minHeight = `${hud.getBoundingClientRect().height}px`;
    }
    draw();
  }

  function draw() {
    if (!data) return;
    const minute = Math.round(t);
    slider.value = String(minute);
    slider.setAttribute('aria-valuetext', `${utc(data.times[minute])}, minute ${minute} of ${data.times.length - 1}`);
    fillReadout(minute);
    fillHud(data.times[minute], data.dF_nT[minute], ARMS.map((arm) => {
      const a = data.arms[arm.key];
      return [a.slips_so_far[minute], a.fringe[minute] !== 0];
    }));
    if (scene) {
      scene.show(data.arms, minute);
      scene.render();
    }
  }

  function settle(minute) {
    if (noScene) return; // the stage is plain text then, and a label on it would be ignored
    stage.setAttribute('aria-label', `3D compass. ${describe(minute)}`);
  }

  let lastDraw = 0;
  function frame(now) {
    pending = false;
    if (playing && stage.offsetParent === null) { stop(true); return; } // the tab was left: pause
    if (playing) {
      const dt = last ? Math.min(0.1, (now - last) / 1000) : 0;
      last = now;
      t = Math.min(data.times.length - 1, t + dt * Number(speed.value));
      if (t >= data.times.length - 1) stop();
    }
    // with reduced motion, playback moves in one-second steps instead of a continuous turn
    if (!playing || !reduceMotion.matches || now - lastDraw >= 1000) { lastDraw = now; draw(); }
    if (playing) request();
  }
  function request() {
    if (!pending) {
      pending = true;
      requestAnimationFrame(frame);
    }
  }
  function stop(quiet = false) {
    playing = false;
    last = 0;
    play.textContent = 'Play';
    settle(Math.round(t));
    if (!quiet) announce(`Paused at ${utc(data.times[Math.round(t)])}.`);
    draw();
  }

  play.addEventListener('click', () => {
    if (!data) return;
    if (playing) { stop(); return; }
    if (t >= data.times.length - 1) t = 1;
    playing = true;
    play.textContent = 'Pause';
    request();
  });
  const step = (d) => {
    if (!data) return;
    if (playing) stop();
    t = Math.min(data.times.length - 1, Math.max(1, Math.round(t) + d));
    draw();
    settle(Math.round(t));
    announce(describe(Math.round(t)));
  };
  back.addEventListener('click', () => step(-1));
  fwd.addEventListener('click', () => step(1));
  toFirst.addEventListener('click', () => {
    if (!data) return;
    const first = data.arms.GHZ4.fringe.findIndex((x) => x !== 0);
    if (first > 0) step(first - Math.round(t));
  });
  slider.addEventListener('input', () => {
    if (playing) stop();
    t = Math.max(1, Number(slider.value));
    draw();
    settle(Math.round(t));
  });
  resetView.addEventListener('click', () => { if (scene) { scene.reset(); draw(); } });

  // The record select is never disabled, so it keeps keyboard focus and arrow keys keep working:
  // a change during a replay is picked up when that replay ends.
  let loadingRecord = null;
  async function load() {
    if (loadingRecord !== null) return;
    if (playing) stop();
    loadingRecord = dataset.value;
    status.textContent = `Replaying the record (${init.defaults.replicates} replays, ${init.defaults.shots} shots per register per minute)…`;
    play.disabled = true;
    toFirst.disabled = true;
    await nextPaint(); // the call blocks the page on Qollab: show the status first
    let failed = false;
    try {
      data = await py.storm3d({ dataset: loadingRecord, shots: init.defaults.shots, replicates: init.defaults.replicates, seed: init.defaults.seed });
    } catch (err) {
      status.textContent = `The replay failed: ${err.message}`;
      failed = true;
    } finally {
      play.disabled = false;
      toFirst.disabled = false;
    }
    const again = dataset.value !== loadingRecord;
    loadingRecord = null;
    if (again) return load();
    if (failed) return undefined;
    const n = data.times.length - 1;
    slider.max = String(n);
    const first = data.arms.GHZ4.fringe.findIndex((x) => x !== 0);
    // nothing to go to on a record where GHZ-4 never changes fringe; the summary below says so
    toFirst.disabled = first <= 0;
    t = 1;
    const tot = data.totals;
    status.textContent = `Replay ${data.replay.shown} of ${data.replay.of}, the one closest to their average: GHZ-4 alone changes fringe ${tot.GHZ4.slips} times and is on a wrong fringe for ${tot.GHZ4.wrong_minutes} minutes (averages over all ${data.replay.of}: ${fmt.n(data.replay.mean_slips, 1)} and ${fmt.n(data.replay.mean_wrong, 0)}); the cascade changes fringe ${tot.CASC.slips} times and 8 independent qubits ${tot.IND8.slips}.`;
    summary.replaceChildren(rich(first > 0
      ? `First GHZ-4 fringe change: ${utc(data.times[first])}, when the field stepped ${fmt.signed(data.dF_nT[first], 1)} nT and turned the GHZ-4 register ${deg(data.arms.GHZ4.turn[first])}, more than half a turn. Use “Go to the first fringe change” and “− 1 minute” / “+ 1 minute” around it to watch the reading land on the wrong fringe. A later step can knock it back onto the right fringe; that counts as a change too.`
      : 'GHZ-4 never leaves its fringe in this record: every minute’s step turns it less than half a turn.'));
    reserveHud();
    settle(1);
    return undefined;
  }

  let starting = null; // one start at a time, however often the tab is shown
  async function start() {
    starting ??= (async () => {
      const loading = data ? null : load(); // the replay runs while three.js loads
      if (!scene && !noScene) {
        try {
          scene = await makeScene(stage, () => { if (!playing) request(); }, reserveHud);
        } catch (err) {
          noScene = true; // do not try again on every visit
          hud.style.position = 'static'; // no picture to lay it over
          stage.removeAttribute('role'); // the note must be read as text, not hidden inside an image
          stage.removeAttribute('aria-label');
          stage.replaceChildren(el('p', { class: 'note' }, `The 3D view is not available here (${err && err.message ? err.message : 'no WebGL'}). The panel below shows the same numbers minute by minute.`), hud);
          // with no picture there is nothing to turn: hide the camera buttons and say why
          camGroup.replaceWith(el('p', { class: 'small muted' }, 'The buttons that turn the view are hidden because there is no 3D picture here.'));
        }
      }
      await loading;
      if (data) reserveHud();
    })();
    await starting;
    if (!data) starting = null; // load the record again on the next visit
  }
  dataset.addEventListener('change', load);

  const element = el('section', { class: 'card', 'aria-labelledby': 'ec3-h', 'aria-describedby': descId },
    el('h2', { id: 'ec3-h' }, 'The storm on a 3D compass'),
    el('p', { id: descId }, rich(String.raw`Three needles follow the real field record minute by minute in one model replay: 8 independent qubits, GHZ-4 alone, and the cascade’s GHZ-4 register. Each needle points where its register reads back; the arc under it shows how far that minute’s field step turned it ($m\,s\,\Delta F$, with $s = ${init.scale.value}$ rad per nT). Past half a turn (the red line) GHZ-4 alone reads back the wrong fringe: while it is on one, its arc is red and thicker and its hub red, and its count of fringe changes goes up each time it leaves or regains the right fringe. The cascade’s GHZ-4 register turns just as far, but its 1-qubit and GHZ-2 registers tell it which turn it is on, so it stays right. Drag sideways to turn the view, or use the buttons.`)),
    el('div', { class: 'controls c3d-controls' },
      el('div', { class: 'field' }, dataLabel, dataset, fullChoice(dataset)),
      el('div', { class: 'field' }, speedLabel, speed),
      el('div', { class: 'toolbar' }, play, back, fwd, toFirst)),
    el('div', { class: 'field' }, sliderLabel, slider),
    status,
    stage,
    camGroup,
    readout,
    summary,
    el('p', { class: 'small muted' }, `Simulated sensors, real field data (USGS). The needles are drawn from one replay of the model in compass/replay.py, chosen as the replay closest to the average of ${init.defaults.replicates}; the tables in the Field tracker give the averages. Nothing ran on a magnetometer or on quantum hardware.`));

  return { element, onShow: start };
}
