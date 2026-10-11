// The only place that calls Python. Every call passes and returns JSON strings, and calls are
// queued so that two never overlap (an IonQ job suspends Python while it waits).
let mod = null;
let sensorBackend = null; // the backend Qollab injected (named apart from Qollab's `backend`)
let chain = Promise.resolve();

export function connect(pythonModule, injected) {
  mod = pythonModule;
  sensorBackend = injected;
}

function lastLine(err) {
  const text = String((err && err.message) || err || 'unknown error').trim();
  const lines = text.split('\n').filter((l) => l.trim());
  return lines[lines.length - 1] || text;
}

function call(name, ...args) {
  const job = chain.then(async () => {
    try {
      const out = JSON.parse(await mod[name].callPromising(...args));
      // Qollab shows console.log in its run console, the first place judges look for results.
      if (out && typeof out.console_line === 'string') console.log(out.console_line);
      return out;
    } catch (err) {
      throw new Error(lastLine(err));
    }
  });
  chain = job.catch(() => {});
  return job;
}

export const py = {
  init: () => call('init_json'),
  backendInfo: () => call('backend_info_json', sensorBackend),
  overview: () => call('overview_json'),
  series: (dataset) => call('series_json', dataset),
  replay: (params) => call('replay_json', JSON.stringify(params)),
  run: (params) => call('run_json', sensorBackend, JSON.stringify(params)),
  circuitText: (layout) => call('circuit_text_json', layout),
  challengeSetup: (params) => call('challenge_setup_json', JSON.stringify(params)),
  challenge: (params) => call('challenge_json', JSON.stringify(params)),
  twinReplay: (params) => call('twin_replay_json', JSON.stringify(params)),
  twinRun: (params) => call('twin_run_json', sensorBackend, JSON.stringify(params)),
  storm3d: (params) => call('storm3d_json', JSON.stringify(params)),
};
