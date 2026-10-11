// The storm in 3D: a compass whose three needles follow a model replay of the real field record
// minute by minute (every number comes from Python, compass/api.py storm3d_json). A needle shows
// the angle its register reads back; the arc beneath it shows how far the field step really
// turned that register. Past half a turn the reading lands on the wrong fringe: the arc turns red
// and the slip counter goes up. three.js comes from Qollab's import map (three@0.186.1); without
// WebGL the controls and the text panel below still show every number.
import { announce, el, fmt, uid } from './dom.js';
import { py } from './py.js';
import { rich } from './tex.js';

const ARMS = [
  { key: 'IND8', name: '8 independent qubits', short: '1 qubit', colorVar: '--s1', y: 0.08, radius: 1.05 },
  { key: 'GHZ4', name: 'GHZ-4 alone', short: 'GHZ-4', colorVar: '--s2', y: 0.3, radius: 1.25 },
  { key: 'CASC', name: 'Cascade 1-2-4 (its GHZ-4 needle)', short: 'cascade', colorVar: '--s3', y: 0.52, radius: 1.45 },
];
const SPEEDS = [[30, '30 minutes per second'], [120, '2 hours per second'], [480, '8 hours per second']];
const DEG = 180 / Math.PI;
const DIAL_R = 1.6;

// The theme's colours live on the app root (.ec-root), so read them from the element drawn into.
const cssVar = (node, name) => getComputedStyle(node).getPropertyValue(name).trim() || '#888888';
const deg = (rad) => `${rad >= 0 ? '+' : '−'}${Math.abs(rad * DEG).toFixed(0)}°`;
const utc = (iso) => `${iso.replace('T', ' ')} UTC`;

/** A point on the dial at angle a (rad, counter-clockwise from +X seen from above) and height y. */
function onDial(THREE, r, a, y) {
  return new THREE.Vector3(r * Math.cos(a), y, -r * Math.sin(a));
}

async function makeScene(host, onChange) {
  const THREE = await import('three');
  const { OrbitControls } = await import('three/addons/controls/OrbitControls.js');
  const { CSS2DRenderer, CSS2DObject } = await import('three/addons/renderers/CSS2DRenderer.js');
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  host.append(renderer.domElement);
  renderer.domElement.setAttribute('aria-hidden', 'true');
  const labels = new CSS2DRenderer();
  labels.domElement.className = 'c3d-labels';
  labels.domElement.setAttribute('aria-hidden', 'true');
  host.append(labels.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 16 / 9, 0.1, 50);
  const view = { radius: 4.6, theta: -0.5, phi: 1.02 };
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
  controls.minDistance = 2.6;
  controls.maxDistance = 8;
  controls.addEventListener('change', onChange);

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

  function resize() {
    const w = host.clientWidth || 640;
    const h = Math.round(Math.min(Math.max(w * 0.56, 260), 520));
    renderer.setSize(w, h, true);
    labels.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    onChange();
  }
  new ResizeObserver(resize).observe(host);
  resize();

  /** Draw minute t: needle angles are the readings, arcs the true (unwrapped) turns. */
  function show(arms, t) {
    for (const arm of ARMS) {
      const a = arms[arm.key];
      const p = parts[arm.key];
      p.needle.rotation.y = a.reading[t];
      const turn = a.true_phase[t];
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
      p.arc.geometry = Math.abs(turn) < 1e-3 ? new THREE.BufferGeometry()
        : new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), n * 2, 0.022, 8, false);
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
    },
    turn: (dTheta, dPhi) => {
      const off = camera.position.clone();
      view.radius = off.length();
      view.theta = Math.atan2(off.x, off.z) + dTheta;
      view.phi = Math.min(1.45, Math.max(0.15, Math.acos(off.y / view.radius) + dPhi));
      placeCamera();
    },
    reset: () => {
      Object.assign(view, { radius: 4.6, theta: -0.5, phi: 1.02 });
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
  const slider = el('input', { type: 'range', id: 'ec3-minute', min: '0', max: '0', step: '1', value: '0' });
  const sliderLabel = el('label', { for: 'ec3-minute' }, 'Minute');
  const status = el('p', { role: 'status', class: 'status', id: 'ec3-status' }, 'Open this tab to load the replay.');
  const stage = el('div', { class: 'c3d', role: 'img', id: 'ec3-stage', 'aria-label': 'The 3D compass (loading).' });
  // the same time and slip counts as the text panel, over the picture (hidden from screen readers)
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
  const readout = el('dl', { class: 'c3d-readout', id: 'ec3-readout' });
  const summary = el('p', { class: 'small' });
  const descId = uid('c3d');

  let data = null;
  let scene = null;
  let t = 1;
  let playing = false;
  let last = 0;
  let pending = false;

  function describe(minute) {
    if (!data) return '';
    const parts = ARMS.map((arm) => {
      const a = data.arms[arm.key];
      const wrong = a.fringe[minute] !== 0;
      return `${arm.name} reads ${deg(a.reading[minute])}; the field turned it ${deg(a.true_phase[minute])}: ${wrong ? 'wrong fringe' : 'right fringe'}, ${a.slips_so_far[minute]} slip${a.slips_so_far[minute] === 1 ? '' : 's'} so far.`;
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
        el('dd', null, `reads ${deg(a.reading[minute])}, turned ${deg(a.true_phase[minute])}: `,
          el('span', { class: wrong ? 'bad' : 'ok' }, wrong ? 'wrong fringe' : 'right fringe'),
          `; slips so far ${a.slips_so_far[minute]}`));
    }
    readout.replaceChildren(...rows);
  }

  function draw() {
    if (!data) return;
    const minute = Math.round(t);
    slider.value = String(minute);
    slider.setAttribute('aria-valuetext', `${utc(data.times[minute])}, minute ${minute} of ${data.times.length - 1}`);
    fillReadout(minute);
    hud.replaceChildren(el('div', null, utc(data.times[minute])),
      el('div', null, `field step ${fmt.signed(data.dF_nT[minute], 1)} nT`),
      ...ARMS.map((arm) => {
        const a = data.arms[arm.key];
        return el('div', { class: a.fringe[minute] !== 0 ? 'bad' : '' },
          el('span', { class: 'swatch', style: `background:var(${arm.colorVar})` }),
          `${arm.short}: ${a.slips_so_far[minute]} slip${a.slips_so_far[minute] === 1 ? '' : 's'}${a.fringe[minute] !== 0 ? ', wrong fringe' : ''}`);
      }));
    if (scene) {
      scene.show(data.arms, minute);
      scene.render();
    }
  }

  function settle(minute) {
    stage.setAttribute('aria-label', `3D compass. ${describe(minute)}`);
  }

  function frame(now) {
    pending = false;
    if (playing) {
      const dt = last ? Math.min(0.1, (now - last) / 1000) : 0;
      last = now;
      t = Math.min(data.times.length - 1, t + dt * Number(speed.value));
      if (t >= data.times.length - 1) stop();
    }
    draw();
    if (playing) request();
  }
  function request() {
    if (!pending) {
      pending = true;
      requestAnimationFrame(frame);
    }
  }
  function stop() {
    playing = false;
    last = 0;
    play.textContent = 'Play';
    settle(Math.round(t));
    announce(`Paused at ${utc(data.times[Math.round(t)])}.`);
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
  slider.addEventListener('input', () => {
    if (playing) stop();
    t = Math.max(1, Number(slider.value));
    draw();
    settle(Math.round(t));
  });
  resetView.addEventListener('click', () => { if (scene) { scene.reset(); draw(); } });

  async function load() {
    if (playing) stop();
    status.textContent = 'Replaying the record (32 replays, 1000 shots per register per minute)…';
    try {
      data = await py.storm3d({ dataset: dataset.value });
    } catch (err) {
      status.textContent = `The replay failed: ${err.message}`;
      return;
    }
    const n = data.times.length - 1;
    slider.max = String(n);
    const first = data.arms.GHZ4.fringe.findIndex((x) => x !== 0);
    t = 1;
    const tot = data.totals;
    status.textContent = `Replay ${data.replay.shown} of ${data.replay.of}, the one closest to their average: GHZ-4 alone slips ${tot.GHZ4.slips} times and is on a wrong fringe for ${tot.GHZ4.wrong_minutes} minutes; the cascade slips ${tot.CASC.slips} times and 8 independent qubits ${tot.IND8.slips}.`;
    summary.replaceChildren(rich(first > 0
      ? `First GHZ-4 slip: ${utc(data.times[first])}, when the field stepped ${fmt.signed(data.dF_nT[first], 1)} nT and turned the GHZ-4 register ${deg(data.arms.GHZ4.true_phase[first])}, more than half a turn. Use “+ 1 minute” around it to watch the reading land on the wrong fringe.`
      : 'GHZ-4 never leaves its fringe in this record: every minute’s step turns it less than half a turn.'));
    draw();
    settle(1);
  }

  async function start() {
    if (!scene) {
      try {
        scene = await makeScene(stage, () => { if (!playing) request(); });
      } catch (err) {
        hud.style.position = 'static'; // no picture to lay it over
        stage.replaceChildren(el('p', { class: 'note' }, `The 3D view is not available here (${err && err.message ? err.message : 'no WebGL'}). The panel below shows the same numbers minute by minute.`), hud);
      }
    }
    if (!data) await load();
  }
  dataset.addEventListener('change', load);

  const element = el('section', { class: 'card', 'aria-labelledby': 'ec3-h', 'aria-describedby': descId },
    el('h2', { id: 'ec3-h' }, 'The storm on a 3D compass'),
    el('p', { id: descId }, rich(String.raw`Three needles follow the real field record minute by minute in one model replay: 8 independent qubits, GHZ-4 alone, and the cascade’s GHZ-4 register. Each needle points where its register reads back; the arc under it shows how far that minute’s field step really turned it ($m\,s\,\Delta F$, with $s = 0.02$ rad per nT). Past half a turn (the red line) GHZ-4 alone reads back the wrong fringe: its arc and hub turn red and its slip counter goes up. The cascade’s GHZ-4 register turns just as far, but its 1-qubit and GHZ-2 registers tell it which turn it is on, so it stays right. Drag to turn the view, or use the buttons.`)),
    el('div', { class: 'controls c3d-controls' },
      el('div', { class: 'field' }, dataLabel, dataset),
      el('div', { class: 'field' }, speedLabel, speed),
      el('div', { class: 'toolbar' }, play, back, fwd)),
    el('div', { class: 'field' }, sliderLabel, slider),
    status,
    stage,
    el('div', { class: 'toolbar', role: 'group', 'aria-label': 'Turn the 3D view' }, ...camButtons, resetView),
    readout,
    summary,
    el('p', { class: 'small muted' }, 'Simulated sensors, real field data (USGS). The needles are drawn from one replay of the model in compass/replay.py, chosen as the replay closest to the average of 32; the tables in the Field tracker give the averages. Nothing ran on a magnetometer or on quantum hardware.'));

  return { element, onShow: start };
}
