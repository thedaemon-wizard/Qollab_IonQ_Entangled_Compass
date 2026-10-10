// Field tracker: replay a field record with every sensor arm (numpy, in Python) and run the
// packed sensor circuit for one minute on the backend Qollab injected (one job).
import { dataTable, timeChart } from './chart.js';
import { dialsPanel } from './dials.js';
import { announce, el, fmt, nextPaint } from './dom.js';
import { py } from './py.js';

const ARM_STYLE = {
  IND8: { color: 'var(--s1)', dash: null, name: '8 independent qubits (matched, unentangled)' },
  GHZ4: { color: 'var(--s2)', dash: null, name: 'GHZ-4 (entangled)' },
  CASC: { color: 'var(--s3)', dash: '7 4', name: 'Cascade 1-2-4 (entangled)' },
  IND14: { color: 'var(--s4)', dash: '2 3', name: '14 independent qubits' },
  MP4: { color: 'var(--s5)', dash: '9 3 2 3', name: '1 qubit, 4 passes (4× interrogation)' },
};
const SHOWN = ['IND8', 'GHZ4', 'CASC', 'MP4'];

function field(label, control, hint) {
  const id = control.id;
  return el('div', { class: 'field' }, el('label', { for: id }, label), control, hint ? el('p', { class: 'hint small muted', id: `${id}-hint` }, hint) : null);
}

function select(id, options, value) {
  const s = el('select', { id }, options.map(([v, text]) => el('option', { value: v }, text)));
  s.value = String(value);
  return s;
}

export function trackerView(init, info, state) {
  const dataset = select('ec-dataset', Object.entries(init.datasets).map(([k, d]) => [k, `${d.label}: ${d.minutes} min`]), 'quiet');
  const shots = select('ec-shots', init.shots.map((s) => [s, String(s)]), info.default_shots);
  const noise = select('ec-noise', [['off', 'Off (only the backend’s own gate noise)'], ['indep', 'Independent dephasing γ, added by this app']], 'off');
  const gamma = el('input', { type: 'range', id: 'ec-gamma', min: '0', max: String(init.gamma_max), step: '0.01', value: '0.05', 'aria-describedby': 'ec-gamma-out' });
  const gammaOut = el('output', { id: 'ec-gamma-out', for: 'ec-gamma' }, 'γ = 0.05 per qubit per shot');
  const gateModel = select('ec-gate', [['none', 'None (ideal gates)'], ...Object.entries(init.documented_models), ['measured', 'Measured in the last run']], 'none');
  gateModel.querySelector('option[value="measured"]').disabled = true;
  const status = el('p', { role: 'status', class: 'status', id: 'ec-replay-status' }, 'Press “Update replay” to track the record.');
  const replayBtn = el('button', { type: 'button', class: 'primary' }, 'Update replay');
  const charts = el('div', { class: 'charts' });
  const metrics = el('div');

  const syncGamma = () => {
    gamma.disabled = noise.value !== 'indep';
    gammaOut.textContent = `γ = ${Number(gamma.value).toFixed(2)} per qubit per shot${gamma.disabled ? ' (off)' : ''}`;
    gamma.setAttribute('aria-valuetext', gammaOut.textContent);
  };
  noise.addEventListener('change', syncGamma);
  gamma.addEventListener('input', syncGamma);
  syncGamma();

  const params = () => ({
    dataset: dataset.value, shots: Number(shots.value), noise: noise.value,
    gamma: Number(gamma.value), gate_model: gateModel.value, measured: state.measuredVis, replicates: 32, seed: 0,
  });

  let lastReplay = null;
  async function doReplay() {
    replayBtn.disabled = true;
    status.textContent = 'Replaying 32 times with every sensor arm…';
    charts.setAttribute('aria-busy', 'true');
    await nextPaint();
    try {
      lastReplay = await py.replay(params());
      draw(lastReplay);
      const g = lastReplay.gain_ghz4;
      status.textContent = `Done in ${lastReplay.seconds} s. GHZ-4 is ${fmt.pm(g)}× as precise as 8 independent qubits on the minutes where it stays on the right fringe (model at zero field step: ${fmt.n(g.theory)}).`;
      announce(status.textContent);
    } catch (err) {
      status.textContent = `The replay failed: ${err.message}`;
    } finally {
      replayBtn.disabled = false;
      charts.removeAttribute('aria-busy');
    }
  }
  replayBtn.addEventListener('click', doReplay);

  function draw(r) {
    const f0 = r.F[0];
    const truth = r.F.map((v) => v - f0);
    const runIndex = state.lastRun && state.lastRun.dataset === dataset.value ? r.times.indexOf(state.lastRun.minute) : null;
    const marker = runIndex !== null && runIndex >= 0 ? { index: runIndex, label: 'circuit run' } : null;
    const series = SHOWN.map((a) => ({ ...ARM_STYLE[a], values: r.arms[a].trace.map((v) => v - f0) }));
    const yMin = Math.min(...truth, ...series.flatMap((s) => s.values));
    const yMax = Math.max(...truth, ...series.flatMap((s) => s.values));
    const pad = (yMax - yMin) * 0.06 || 1;
    const label = init.datasets[dataset.value].label;
    const summary = SHOWN.map((a) => `${ARM_STYLE[a].name}: RMS error ${fmt.n(r.arms[a].rmse.mean)} nT, ${fmt.n(r.arms[a].wrong_minutes.mean, 0)} minutes on a wrong fringe`).join('; ');
    const step = Math.max(1, Math.round(r.times.length / 60));
    const sampled = r.times.map((t, i) => i).filter((i) => i % step === 0);
    const fieldChart = timeChart({
      title: `Field change and the sensors' estimates, ${label}`,
      desc: `Change of the total field since ${r.times[0]} UTC (USGS, Boulder) and the estimate of each sensor arm in one replay. ${summary}.`,
      xLabels: r.times, xLabel: 'Time (UTC)', yLabel: 'F − F₀ (nT)', yMin: yMin - pad, yMax: yMax + pad,
      series: [{ name: 'Measured field (USGS)', values: truth, color: 'var(--text)', width: 2.6 }, ...series],
      marker,
      table: { caption: `Field and estimates every ${step} min (nT, relative to the first minute)`, columns: ['Time (UTC)', 'Field', ...SHOWN.map((a) => ARM_STYLE[a].name)],
        rows: sampled.map((i) => [r.times[i], fmt.n(truth[i]), ...SHOWN.map((a) => fmt.n(r.arms[a].trace[i] - f0))]) },
    });
    const errs = SHOWN.map((a) => ({ ...ARM_STYLE[a], values: r.arms[a].trace.map((v, i) => v - r.F[i]) }));
    const bandG = r.band_nt.GHZ4;
    const bandI = r.band_nt.IND8;
    const half = r.fringe_nt.GHZ4 / 2;
    const maxErr = Math.max(4 * bandI, ...errs.flatMap((s) => s.values.map(Math.abs)));
    const errChart = timeChart({
      title: `Estimation error, ${label}`,
      desc: `Error of each arm (estimate minus measured field). Shot noise alone gives about ±${fmt.n(bandI)} nT for 8 independent qubits and ±${fmt.n(bandG)} nT for GHZ-4. An error near ±${fmt.n(2 * half)} nT means GHZ-4 has jumped to a neighbouring fringe.`,
      xLabels: r.times, xLabel: 'Time (UTC)', yLabel: 'Error (nT)', yMin: -maxErr * 1.1, yMax: maxErr * 1.1,
      series: errs,
      bands: [{ y0: -bandI, y1: bandI, fill: 'var(--band)', name: `±1σ shot noise, 8 independent qubits (${fmt.n(bandI)} nT)` }],
      hlines: maxErr > half ? [{ y: half, label: `GHZ-4 fringe edge +${fmt.n(half)} nT` }, { y: -half, label: `−${fmt.n(half)} nT` }] : [],
      marker,
    });
    charts.replaceChildren(fieldChart, errChart);
    metrics.replaceChildren(dataTable({
      caption: `32 replays (mean ± 2 standard errors), ${shots.value} shots per register per minute, ${init.scale.value} rad/nT`,
      columns: ['Sensor arm', 'Qubits per shot', 'RMS error (nT)', 'RMS error on the right fringe (nT)', 'Minutes on a wrong fringe', 'Fringe jumps'],
      rows: Object.entries(r.arms).map(([a, x]) => [ARM_STYLE[a].name, String(x.qubits), fmt.pm(x.rmse), fmt.pm(x.rmse_ok), fmt.pm(x.wrong_minutes, 1), fmt.pm(x.slips, 1)]),
    }), el('p', { class: 'small' },
      `Gain of GHZ-4 over 8 independent qubits (same 8 qubits per shot): ${fmt.pm(r.gain_ghz4)}; model at zero field step ${fmt.n(r.gain_ghz4.theory)}. `,
      `Gain of the cascade over 14 independent qubits: ${fmt.pm(r.gain_cascade)}; ideal ${fmt.n(r.gain_cascade.theory_ideal)}.`));
  }

  // ---------- one circuit run ----------
  const preset = select('ec-minute', init.presets.map((p, i) => [i, `${p.minute.replace('T', ' ')} UTC: ${p.note}`]), 2);
  const runBtn = el('button', { type: 'button', class: 'primary', id: 'ec-run' }, 'Run the sensor circuit (one job)');
  const runStatus = el('p', { role: 'status', class: 'status', id: 'ec-run-status' }, `Backend: ${info.name}. One packed circuit: 17 qubits, or 21 with dephasing.`);
  const runOut = el('div');
  runBtn.addEventListener('click', async () => {
    const p = init.presets[Number(preset.value)];
    runBtn.disabled = true;
    runStatus.textContent = `Submitting one job to ${info.name}…`;
    runOut.setAttribute('aria-busy', 'true');
    await nextPaint();
    try {
      const r = await py.run({ ...params(), dataset: p.dataset, minute: p.minute });
      if (r.error) {
        runStatus.textContent = r.message;
        return;
      }
      state.lastRun = r;
      state.measuredVis = Object.fromEntries(Object.entries(r.visibility).map(([k, v]) => [k, Math.min(1, v.gate_only)]));
      gateModel.querySelector('option[value="measured"]').disabled = false;
      runOut.replaceChildren(runCard(r));
      runStatus.textContent = `Done: ${r.backend.name}, ${r.shots} shots, ${r.n_qubits} qubits, ${r.wall_s} s. Cascade error ${fmt.signed(r.arms.CASC.error_nT)} nT, GHZ-4 alone ${fmt.signed(r.arms.GHZ4.error_nT)} nT.`;
      announce(runStatus.textContent);
      if (lastReplay) draw(lastReplay);
    } catch (err) {
      runStatus.textContent = `The run failed: ${err.message}`;
    } finally {
      runBtn.disabled = ionqUsed(info, state);
      runOut.removeAttribute('aria-busy');
    }
  });

  const controls = el('fieldset', { class: 'card controls' }, el('legend', null, 'Replay settings'),
    field('Field record', dataset),
    el('p', { class: 'small muted' }, `Phase per nT: ${init.scale.value} rad (a model choice: an electron spin with a ${init.scale.ramsey_us} µs Ramsey time). GHZ-4 can then follow at most ±${init.scale.ghz4_range_nt} nT per minute.`),
    field('Shots per register per minute', shots), field('Added noise', noise),
    el('div', { class: 'field' }, el('label', { for: 'ec-gamma' }, 'Dephasing strength'), gamma, gammaOut),
    field('Gate noise in the replay', gateModel, 'IonQ’s documented depolarizing rates for Aria 1 (now retired), or the visibilities measured in your last circuit run.'),
    el('div', { class: 'row' }, replayBtn), status);
  const runCardEl = el('section', { class: 'card', 'aria-labelledby': 'ec-run-h' }, el('h3', { id: 'ec-run-h' }, 'One minute on the quantum simulator'),
    el('p', { class: 'small muted' }, 'Every sensor below is in ONE circuit and sees the same field step: GHZ-1, GHZ-2 and GHZ-4 registers read in X and Y, a single qubit that passes the field four times, and a canary qubit that checks the bit order.'),
    field('Minute', preset), el('div', { class: 'row' }, runBtn), runStatus, runOut);
  return el('div', { class: 'view' }, el('div', { class: 'grid' }, controls, runCardEl), charts, metrics);
}

function ionqUsed(info, state) {
  return info.kind === 'ionq' && state.lastRun !== null;
}

function runCard(r) {
  const arms = Object.entries(r.arms).map(([k, a]) => [k === 'IND2' ? '2 independent qubits' : k === 'GHZ4' ? 'GHZ-4 alone' : k === 'CASC' ? 'Cascade 1-2-4' : '1 qubit, 4 passes',
    fmt.n(a.estimate_nT), fmt.signed(a.error_nT), fmt.n(a.se_nT)]);
  return el('div', null,
    el('p', null, `Field step at ${r.minute.replace('T', ' ')} UTC: ${fmt.signed(r.dF_nT)} nT, so every register sees ${fmt.n(r.delta_rad, 4)} rad per qubit. Canary read correctly in ${fmt.n(100 * r.canary, 1)}% of shots.`),
    dialsPanel(r),
    fringeChart(r),
    dataTable({ caption: 'What each sensor reads from this one job', columns: ['Sensor', 'Estimate (nT)', 'Error (nT)', '± 1 SE (nT)'], rows: arms }),
    el('p', { class: 'small' }, `Visibility measured: GHZ-1 ${fmt.n(r.visibility['1'].hat, 3)}, GHZ-2 ${fmt.n(r.visibility['2'].hat, 3)}, GHZ-4 ${fmt.n(r.visibility['4'].hat, 3)}${r.visibility.MP4 ? `, 4-pass ${fmt.n(r.visibility.MP4.hat, 3)}` : ''}. Gain implied by them, 2·V₄/V₁ = ${fmt.n(r.gain_from_visibility)} (ideal 2).`),
    dataTable({ caption: 'Register parities (mean of ±1 over shots) against the ideal-gate model', columns: ['Register', 'Qubits', 'Measured', '± SE', 'Model', 'z'],
      rows: r.registers.map((g) => [g.name, g.qubits.join(' '), fmt.n(g.mean, 3), fmt.n(g.se, 3), fmt.n(g.ideal_model, 3), fmt.n(g.z, 1)]) }, 'Register parities'),
    el('p', { class: 'small muted' }, `Compiled circuit: ${Object.entries(r.ops).map(([k, v]) => `${k} ${v}`).join(', ')}; depth ${r.depth}. Job wall time ${r.wall_s} s (measured).`));
}

function fringeChart(r) {
  const fr = r.fringes;
  const idx = fr.dF.reduce((best, x, i) => (Math.abs(x - fr.this_minute_dF) < Math.abs(fr.dF[best] - fr.this_minute_dF) ? i : best), 0);
  const names = { 1: '1 qubit', 2: 'GHZ-2', 4: 'GHZ-4' };
  const colors = { 1: 'var(--s1)', 2: 'var(--s3)', 4: 'var(--s2)' };
  const dashes = { 1: null, 2: '7 4', 4: null };
  return timeChart({
    title: 'Fringes: X parity against the field step in one minute (ideal model)',
    desc: `cos(m·s·ΔF) for m = 1, 2 and 4 at s = ${r.scale} rad/nT. GHZ-4 oscillates four times as fast, so it is four times as steep, but it repeats every ${fmt.n(2 * fr.half_range_nT['4'], 1)} nT. This minute's step, ${fmt.signed(fr.this_minute_dF, 1)} nT, is marked.`,
    width: 640, height: 220,
    xLabels: fr.dF.map((x) => String(Math.round(x))), xEvery: 40, xLabel: 'Field step in one minute (nT)', yLabel: 'X parity', yMin: -1.05, yMax: 1.05,
    series: ['1', '2', '4'].map((m) => ({ name: names[m], values: fr.curves[m], color: colors[m], dash: dashes[m] })),
    marker: { index: idx, label: 'this minute' },
  });
}
