// Two observatories: a what-if in which one qubit at Boulder and one at Tucson share an
// entangled pair. (|01> + |10>)/sqrt(2) reads only the DIFFERENCE of the two fields, so a change
// both sites share cancels; (|00> + |11>)/sqrt(2) reads the SUM. The field records are real.
import { dataTable, timeChart } from './chart.js';
import { el, fmt, nextPaint } from './dom.js';
import { twinFigure } from './figures.js';
import { py } from './py.js';

const MINUTES = [
  ['2024-05-10T17:06', 'storm onset: both sites jump together'],
  ['2024-05-11T02:07', 'largest step at Boulder: Tucson barely moves'],
  ['2024-05-10T21:47', 'first minute where GHZ-4 alone jumps a fringe at Boulder'],
];

export function twinView(info) {
  const status = el('p', { role: 'status', class: 'status' }, 'Press “Replay the storm at both sites”.');
  const replayBtn = el('button', { type: 'button', class: 'primary' }, 'Replay the storm at both sites');
  const out = el('div');
  const minute = el('select', { id: 'ec-twin-minute' }, MINUTES.map(([m, note], i) => el('option', { value: String(i) }, `${m.replace('T', ' ')} UTC: ${note}`)));
  const runBtn = el('button', { type: 'button', class: 'primary', id: 'ec-twin-run' }, 'Run the twin circuit (one job)');
  const runStatus = el('p', { role: 'status', class: 'status', id: 'ec-twin-status' }, `Backend: ${info.name}. One circuit, 13 qubits. On IonQ this uses the run’s only job.`);
  const runOut = el('div');

  replayBtn.addEventListener('click', async () => {
    replayBtn.disabled = true;
    status.textContent = 'Replaying both records with both sensor pairs…';
    out.setAttribute('aria-busy', 'true');
    await nextPaint();
    try {
      const r = await py.twinReplay({ shots: 1000 });
      const st = r.steps;
      const maxAbs = Math.max(...r.boulder.map(Math.abs), ...r.tucson.map(Math.abs), ...r.gradient.map(Math.abs));
      out.replaceChildren(
        el('p', null, `One-minute changes at the two sites are only weakly correlated during the storm (r = ${fmt.n(st.corr_one_minute_changes)}); only ${fmt.n(100 * st.corr_one_minute_changes ** 2, 0)}% of the variance of one is explained by the other (r²), and only ${fmt.n(100 * st.common_fraction, 0)}% of the summed variance cancels in the difference. So the Boulder − Tucson difference jumps almost as much as Boulder itself (standard deviation of one-minute steps ${fmt.n(st.std_step_gradient_nt, 1)} nT against ${fmt.n(st.std_step_a_nt, 1)} nT; largest ${fmt.n(st.largest_step_gradient_nt, 1)} nT). Across 1,000 km the storm is not common noise; the cancelling trick needs sensors close enough to share it.`),
        timeChart({
          title: 'The storm at Boulder and Tucson, and their difference',
          desc: `Change of the total field since ${r.times[0]} UTC at Boulder and at Tucson (USGS), and Boulder minus Tucson. The difference is nearly as stormy as Boulder alone.`,
          xLabels: r.times, xLabel: 'Time (UTC)', yLabel: 'Change (nT)', yMin: -maxAbs * 1.05, yMax: maxAbs * 1.05,
          series: [
            { name: 'Boulder', values: r.boulder, color: 'var(--s1)' },
            { name: 'Tucson', values: r.tucson, color: 'var(--s3)', dash: '7 4' },
            { name: 'Boulder − Tucson', values: r.gradient, color: 'var(--s2)', width: 2.2, dash: '9 3' },
          ],
          table: { caption: 'Change every 60 min (nT)', columns: ['Time (UTC)', 'Boulder', 'Tucson', 'Boulder − Tucson'],
            rows: r.times.map((tt, i) => [tt, fmt.n(r.boulder[i]), fmt.n(r.tucson[i]), fmt.n(r.gradient[i])]).filter((_, i) => i % 60 === 0) },
        }),
        dataTable({
          caption: `Tracking the difference with 4 qubits per shot, ${r.shots} shots per minute, ${r.scale} rad/nT (32 replays, mean ± 2 standard errors)`,
          columns: ['Sensor', 'RMS error of the difference (nT)'],
          rows: [['Entangled pair (|01⟩+|10⟩), read in X and Y', fmt.pm(r.rmse.DIFF)], ['One qubit per site, read in X and Y', fmt.pm(r.rmse.IND)],
            ['Standard quantum limit for a difference, 4 qubits (best single-pass unentangled sensor)', fmt.n(r.sql_difference_nt)]],
        }),
        el('p', null, `The entangled pair is ${fmt.pm(r.gain)}× as precise for the difference as one qubit per site (ideal √2 = ${fmt.n(r.gain.theory)}): it measures the difference directly instead of subtracting two noisy readings. Read in X and Y it only matches the standard quantum limit for a difference; an optimally read pair would beat that limit by √2. None of this needs shared noise.`));
      status.textContent = `Done. Correlation of one-minute changes r = ${fmt.n(st.corr_one_minute_changes)}; the pair is ${fmt.n(r.gain.mean)}× as precise for the difference.`;
    } catch (err) {
      status.textContent = `The replay failed: ${err.message}`;
    } finally {
      replayBtn.disabled = false;
      out.removeAttribute('aria-busy');
    }
  });

  runBtn.addEventListener('click', async () => {
    const [m] = MINUTES[Number(minute.value)];
    runBtn.disabled = true;
    runStatus.textContent = `Submitting one job to ${info.name}…`;
    await nextPaint();
    try {
      const r = await py.twinRun({ minute: m, shots: info.default_shots });
      if (r.error) {
        runStatus.textContent = r.message;
        return;
      }
      const label = { difference: 'Entangled pair |01⟩+|10⟩ (difference)', sum: 'Entangled pair |00⟩+|11⟩ (sum)', boulder: 'Single qubit at Boulder', tucson: 'Single qubit at Tucson' };
      runOut.replaceChildren(
        dataTable({ caption: `What each sensor read at ${r.minute.replace('T', ' ')} UTC (nT, change in one minute)`, columns: ['Sensor', 'Reads', 'True', 'Error'],
          rows: Object.entries(r.reads).map(([k, v]) => [label[k], fmt.signed(v.estimate_nT, 1), fmt.signed(v.true_nT, 1), fmt.signed(v.error_nT, 1)]) }),
        el('p', { class: 'small' }, `Difference from the two single qubits: ${fmt.signed(r.independent_difference_nT, 1)} nT. Canary read correctly in ${fmt.n(100 * r.canary, 1)}% of ${r.shots} shots; ${r.wall_s} s; gates ${Object.entries(r.ops).map(([k, v]) => `${k} ${v}`).join(', ')}.`));
      runStatus.textContent = `Done: ${r.backend.name}. The difference pair read ${fmt.signed(r.reads.difference.estimate_nT, 1)} nT (true ${fmt.signed(r.reads.difference.true_nT, 1)}).`;
    } catch (err) {
      runStatus.textContent = `The run failed: ${err.message}`;
    } finally {
      runBtn.disabled = info.kind === 'ionq';
    }
  });

  return el('div', { class: 'view' },
    el('section', { class: 'card' }, el('h2', null, 'Two observatories: can entanglement cancel the storm?'),
      el('p', null, 'Put one qubit at Boulder and one at Tucson, about 1,000 km apart, and entangle them as (|01⟩ + |10⟩)/√2. The pair then picks up only the difference of the two fields: anything both sites feel cancels. Trapped-ion experiments use exactly this to ignore magnetic noise shared by two ions a few millimetres apart (Ruster et al. 2017). Does it cancel a geomagnetic storm across a continent?'),
      el('p', { class: 'small muted' }, 'A what-if: sharing entanglement between observatories needs a quantum network that does not exist. The field records are real (USGS, quasi-definitive); the sensors are simulated.'),
      twinFigure(),
      el('div', { class: 'row' }, replayBtn), status, out),
    el('section', { class: 'card', 'aria-labelledby': 'ec-twin-run-h' }, el('h2', { id: 'ec-twin-run-h' }, 'One minute with the twin circuit'),
      el('p', { class: 'small muted' }, 'One circuit holds both entangled pairs (difference and sum, each read in X and Y), a single qubit per site, and a canary qubit.'),
      el('div', { class: 'field' }, el('label', { for: 'ec-twin-minute' }, 'Minute'), minute),
      el('div', { class: 'row' }, runBtn), runStatus, runOut));
}
