// Storm challenge: twelve two-hour rounds of the May 2024 storm. Before each round, pick the
// sensor; the round is replayed with it (in Python) and compared with what the other two would
// have done from the same starting point. Turn-based: nothing moves until you choose.
import { dataTable, timeChart } from './chart.js';
import { announce, el, fmt, nextPaint } from './dom.js';
import { py } from './py.js';

const ORDER = ['IND8', 'GHZ4', 'CASC'];
const STYLE = { IND8: 'var(--s1)', GHZ4: 'var(--s2)', CASC: 'var(--s3)' };

export function challengeView(state) {
  let setup = null;
  let k = 0;
  let offset = 0;
  let history = [];
  let lastStep = null;
  const status = el('p', { role: 'status', class: 'status' }, 'Press “Start the challenge”.');
  const roundBox = el('div');
  const result = el('div');
  const summary = el('div');
  const startBtn = el('button', { type: 'button', class: 'primary' }, 'Start the challenge');

  const settings = () => ({ shots: 1000, gate_model: state.measuredVis ? 'measured' : 'none', measured: state.measuredVis, seed: 7 });

  async function start() {
    startBtn.disabled = true;
    status.textContent = 'Preparing the storm and the three fixed strategies…';
    await nextPaint();
    try {
      setup = await py.challengeSetup(settings());
      k = 0;
      offset = 0;
      history = [];
      lastStep = null;
      result.replaceChildren();
      summary.replaceChildren();
      showRound();
      status.textContent = `Round 1 of ${setup.rounds.length}. ${state.measuredVis ? 'Visibilities from your last circuit run are used.' : 'Ideal visibilities (run the circuit in the Field tracker to use measured ones).'}`;
    } catch (err) {
      status.textContent = `Could not start: ${err.message}`;
    } finally {
      startBtn.disabled = false;
      startBtn.textContent = 'Restart';
    }
  }

  function showRound() {
    const r = setup.rounds[k];
    const buttons = ORDER.map((c) => el('button', { type: 'button', class: 'choice', on: { click: () => play(c) } },
      el('strong', null, setup.choices[c].label), el('br'), el('span', { class: 'small' }, `${setup.choices[c].qubits} qubits per shot`)));
    roundBox.replaceChildren(el('section', { class: 'card', 'aria-labelledby': 'ec-round-h' },
      el('h3', { id: 'ec-round-h', tabindex: '-1' }, `Round ${k + 1} of ${setup.rounds.length}: ${r.start.replace('T', ' ')} to ${r.end.slice(11)} UTC`),
      el('p', null, lastStep === null
        ? `The storm begins this afternoon. GHZ-4 reads the field four times as finely, but loses its place if the field jumps more than ±${fmt.n(setup.ghz4_range_nt, 1)} nT in one minute.`
        : `Last round, the largest one-minute jump was ${fmt.n(lastStep, 1)} nT. Your estimate starts ${fmt.signed(offset, 1)} nT from the true field.`),
      el('p', { class: 'small muted' }, 'Which sensor tracks the next two hours?'),
      el('div', { class: 'choices', role: 'group', 'aria-label': 'Choose a sensor' }, buttons)));
    roundBox.querySelector('h3').focus();
  }

  async function play(choice) {
    roundBox.querySelectorAll('button').forEach((b) => { b.disabled = true; });
    status.textContent = 'Replaying two hours…';
    await nextPaint();
    try {
      const out = await py.challenge({ ...settings(), round: k, choice, offset_nt: offset });
      const mine = out.result;
      history.push({ round: k, choice, score: mine.score, slips: mine.slips, best: ORDER.reduce((b, c) => (out.others[c].score < out.others[b].score ? c : b), ORDER[0]) });
      offset = mine.end_offset_nt;
      lastStep = out.largest_step_nt;
      const verdict = mine.slips > 0 ? `GHZ-4 jumped a fringe ${mine.slips} time(s): the estimate is now ${fmt.signed(offset, 1)} nT off.` : 'No fringe jumps.';
      result.replaceChildren(el('section', { class: 'card' },
        el('h3', null, `Round ${k + 1}: you chose ${out.choices[choice].label}`),
        el('p', null, `Score ${fmt.n(mine.score)} (RMS error ${fmt.n(mine.rmse_nt)} nT × √(qubits/8); lower is better). ${verdict} The largest jump in this round was ${fmt.n(out.largest_step_nt, 1)} nT.`),
        timeChart({
          title: `Round ${k + 1}: your estimation error`,
          desc: `Error of ${out.choices[choice].label} from ${out.start} to ${out.end} UTC. RMS ${fmt.n(mine.rmse_nt)} nT, ${mine.wrong_minutes} minutes on a wrong fringe.`,
          width: 640, height: 200, xLabels: mine.times, xEvery: 30, xLabel: 'Time (UTC)', yLabel: 'Error (nT)',
          yMin: Math.min(-3, ...mine.error_nt) * 1.1, yMax: Math.max(3, ...mine.error_nt) * 1.1,
          series: [{ name: out.choices[choice].label, values: mine.error_nt, color: STYLE[choice] }],
        }),
        dataTable({ caption: 'From the same starting point and the same random draws', columns: ['Sensor', 'Score', 'RMS error (nT)', 'Fringe jumps'],
          rows: ORDER.map((c) => [`${out.choices[c].label}${c === choice ? ' (your pick)' : ''}`, fmt.n(out.others[c].score), fmt.n(out.others[c].rmse_nt), String(out.others[c].slips)]) })));
      announce(`Round ${k + 1}: score ${fmt.n(mine.score)}. ${verdict}`);
      k += 1;
      if (k < setup.rounds.length) {
        roundBox.replaceChildren(el('button', { type: 'button', class: 'primary', on: { click: showRound } }, `Next: round ${k + 1}`));
        roundBox.querySelector('button').focus();
        status.textContent = `Round ${k} done.`;
      } else {
        finish();
      }
    } catch (err) {
      status.textContent = `The round failed: ${err.message}`;
      roundBox.querySelectorAll('button').forEach((b) => { b.disabled = false; });
    }
  }

  function finish() {
    const mean = history.reduce((s, h) => s + h.score, 0) / history.length;
    const always = ORDER.map((c) => [setup.choices[c].label, setup.always[c].mean_score]);
    const bestFixed = always.reduce((b, x) => (x[1] < b[1] ? x : b));
    roundBox.replaceChildren();
    summary.replaceChildren(el('section', { class: 'card', 'aria-labelledby': 'ec-final-h' },
      el('h3', { id: 'ec-final-h', tabindex: '-1' }, `Your mean score: ${fmt.n(mean)}`),
      el('p', null, mean < bestFixed[1]
        ? `You beat every fixed strategy: the best of them, “always ${bestFixed[0]}”, scores ${fmt.n(bestFixed[1])}. Entanglement pays when you also know when not to trust it.`
        : `The best fixed strategy, “always ${bestFixed[0]}”, scores ${fmt.n(bestFixed[1])}. GHZ-4 is the finest sensor in calm hours, but one big jump costs more than it gains.`),
      dataTable({ caption: 'Your rounds', columns: ['Round', 'Your pick', 'Score', 'Fringe jumps', 'Best pick this round'],
        rows: history.map((h) => [String(h.round + 1), setup.choices[h.choice].label, fmt.n(h.score), String(h.slips), setup.choices[h.best].label]) }),
      dataTable({ caption: 'Fixed strategies over all 12 rounds (same random draws)', columns: ['Strategy', 'Mean score'], rows: always.map(([l, s]) => [`always ${l}`, fmt.n(s)]) })));
    summary.querySelector('h3').focus();
    status.textContent = 'Challenge complete.';
    announce(`Challenge complete. Mean score ${fmt.n(mean)}.`);
  }

  startBtn.addEventListener('click', start);
  return el('div', { class: 'view' },
    el('section', { class: 'card' }, el('h2', null, 'Storm challenge'),
      el('p', null, 'Track the 10–11 May 2024 G5 storm at the Boulder observatory, two hours at a time. Before each round you see only the past. Pick the sensor for the next two hours: the steady 8 independent qubits, the twice-as-precise but short-ranged GHZ-4, or the 1-2-4 cascade that costs 14 qubits.'),
      el('p', { class: 'small muted' }, 'Sensors are simulated (model replay of the same parity measurement the circuit makes); the field is the measured USGS record. 1000 shots per register per minute, 0.02 rad per nT.'),
      el('div', { class: 'row' }, startBtn), status),
    result, roundBox, summary);
}
