// Storm challenge: twelve two-hour rounds of the May 2024 storm. Before each round, pick the
// sensor; the round is replayed with it (in Python) and compared with what the other two would
// have done from the same starting point. Turn-based: nothing moves until you choose.
import { dataTable, timeChart } from './chart.js';
import { announce, el, fmt, keepFocus, nextPaint } from './dom.js';
import { py } from './py.js';
import { rich } from './tex.js';

const ORDER = ['IND8', 'GHZ4', 'CASC'];
const STYLE = { IND8: 'var(--s1)', GHZ4: 'var(--s2)', CASC: 'var(--s3)' };

export function challengeView(state, init) {
  let setup = null;
  let k = 0;
  let offset = 0;
  let history = [];
  let lastStep = null;
  let previous = null;
  let frozen = null; // settings fixed at the start of a game, so the benchmarks stay comparable
  const status = el('p', { role: 'status', class: 'status' }, 'Press “Start the challenge”.');
  const roundBox = el('div');
  const result = el('div');
  const summary = el('div');
  const startBtn = el('button', { type: 'button', class: 'primary' }, 'Start the challenge');

  const settings = () => ({ shots: init.defaults.shots, gate_model: state.measuredVis ? 'measured' : 'none', measured: state.measuredVis, seed: init.defaults.challenge_seed });

  async function start() {
    startBtn.disabled = true;
    status.textContent = 'Preparing the storm and the three fixed strategies…';
    await nextPaint();
    try {
      frozen = settings();
      setup = await py.challengeSetup(frozen);
      k = 0;
      offset = 0;
      history = [];
      lastStep = null;
      previous = null;
      result.replaceChildren();
      summary.replaceChildren();
      showRound();
      status.textContent = `Round 1 of ${setup.rounds.length}. ${frozen.measured ? 'Visibilities from your last circuit run are used for the whole game.' : 'Ideal visibilities for the whole game (run the circuit in the Field tracker first to use measured ones).'}`;
    } catch (err) {
      status.textContent = `Could not start: ${err.message}`;
    } finally {
      startBtn.disabled = false;
      startBtn.textContent = 'Restart';
      keepFocus(startBtn, status); // after a start that worked, focus is already on the round heading
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
        : `Last round, the largest one-minute jump was ${fmt.n(lastStep, 1)} nT. Your estimate is ${fmt.signed(offset, 1)} nT from the true field. Keep the same sensor and it keeps that estimate; switch, and the new sensor starts from a fresh absolute fix.`),
      runningScore(),
      el('p', { class: 'small muted' }, 'Which sensor tracks the next two hours?'),
      el('div', { class: 'choices', role: 'group', 'aria-label': 'Choose a sensor' }, buttons)));
    roundBox.querySelector('h3').focus();
  }

  // your mean so far against each fixed strategy over the same rounds (same seed as the final card)
  function runningScore() {
    if (!history.length) return null;
    const mean = (xs) => xs.reduce((t, x) => t + x, 0) / xs.length;
    const n = history.length;
    const fixed = ORDER.map((c) => `always ${setup.choices[c].label} ${fmt.n(mean(setup.always[c].scores.slice(0, n)))}`).join(', ');
    return el('p', { class: 'small' }, `Your mean score so far: ${fmt.n(mean(history.map((h) => h.score)))}. Over the same ${n === 1 ? 'round' : `${n} rounds`}: ${fixed} (lower is better).`);
  }

  async function play(choice) {
    roundBox.querySelectorAll('button').forEach((b) => { b.disabled = true; });
    status.textContent = 'Replaying two hours…';
    await nextPaint();
    try {
      const out = await py.challenge({ ...frozen, round: k, choice, offset_nt: offset, previous_choice: previous });
      previous = choice;
      const mine = out.result;
      history.push({ round: k, choice, score: mine.score, slips: mine.slips, best: ORDER.reduce((b, c) => (out.others[c].score < out.others[b].score ? c : b), ORDER[0]) });
      offset = mine.end_offset_nt;
      lastStep = out.largest_step_nt;
      const label = out.choices[choice].label;
      const off = Math.abs(offset) > 5 ? ` The estimate ends ${fmt.signed(offset, 1)} nT off.` : '';
      const fresh = out.reanchored ? 'Switching sensors started it from a fresh absolute fix. ' : '';
      const verdict = `${fresh}${mine.slips > 0 ? `${label} changed fringe ${mine.slips} time(s).` : 'No fringe changes.'}${off}`;
      result.replaceChildren(el('section', { class: 'card' },
        el('h3', null, `Round ${k + 1}: you chose ${out.choices[choice].label}`),
        el('p', null, rich(String.raw`Score ${fmt.n(mine.score)} (RMS error ${fmt.n(mine.rmse_nt)} nT $\times \sqrt{q/8}$ for a sensor of $q$ qubits; lower is better). ${verdict} The largest jump in this round was ${fmt.n(out.largest_step_nt, 1)} nT.`)),
        timeChart({
          title: `Round ${k + 1}: your estimation error`,
          desc: `Error of ${out.choices[choice].label} from ${out.start} to ${out.end} UTC. RMS ${fmt.n(mine.rmse_nt)} nT, ${mine.wrong_minutes} minutes on a wrong fringe.`,
          width: 640, height: 200, xLabels: mine.times, xEvery: 30, xLabel: 'Time (UTC)', yLabel: 'Error (nT)',
          yMin: Math.min(-3, ...mine.error_nt) * 1.1, yMax: Math.max(3, ...mine.error_nt) * 1.1,
          series: [{ name: out.choices[choice].label, values: mine.error_nt, color: STYLE[choice] }],
          table: { caption: 'Error every 10 minutes (nT)', columns: ['Time (UTC)', 'Error (nT)'],
            rows: mine.times.map((tt, i) => [tt, fmt.n(mine.error_nt[i])]).filter((_, i) => i % 10 === 0) },
        }),
        dataTable({ caption: 'The three sensors from the same start (a switch starts from a fresh fix) and the same random seed', columns: ['Sensor', 'Score', 'RMS error (nT)', 'Fringe changes'],
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
      keepFocus(roundBox.querySelector('button'), status);
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
      dataTable({ caption: 'Your rounds', columns: ['Round', 'Your pick', 'Score', 'Fringe changes', 'Best pick this round'],
        rows: history.map((h) => [String(h.round + 1), setup.choices[h.choice].label, fmt.n(h.score), String(h.slips), setup.choices[h.best].label]) }),
      dataTable({ caption: `Fixed strategies over all ${setup.rounds.length} rounds (same random seed)`, columns: ['Strategy', 'Mean score'], rows: always.map(([l, s]) => [`always ${l}`, fmt.n(s)]) })));
    summary.querySelector('h3').focus();
    status.textContent = 'Challenge complete.';
    announce(`Challenge complete. Mean score ${fmt.n(mean)}.`);
  }

  startBtn.addEventListener('click', start);
  return el('div', { class: 'view' },
    el('section', { class: 'card' }, el('h2', null, 'Storm challenge'),
      el('p', null, 'Track the 10–11 May 2024 G5 storm at the Boulder observatory, two hours at a time. Before each round you see only the past. Pick the sensor for the next two hours: the steady 8 independent qubits, the twice-as-precise but short-ranged GHZ-4, or the 1-2-4 cascade that costs 14 qubits.'),
      el('p', { class: 'small muted' }, `Rules: keeping a sensor keeps its estimate (a GHZ-4 that jumped a fringe stays off until another jump brings it back); switching starts the new sensor from a fresh absolute fix. Sensors are simulated (model replay of the same parity measurement the circuit makes); the field is the measured USGS record. ${init.defaults.shots} shots per register per minute, ${init.scale.value} rad per nT.`),
      el('div', { class: 'row' }, startBtn), status),
    result, roundBox, summary);
}
