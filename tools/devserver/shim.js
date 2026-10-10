// Stand-in for Qollab's Python bridge: each function has .callPromising(...args), which POSTs
// the call to server.py. The backend object is sent by name.
function make(name) {
  const fn = () => {
    throw new Error('call with .callPromising()');
  };
  fn.callPromising = async (...args) => {
    const payload = args.map((a) => (a && typeof a === 'object' && 'name' in a ? { __backend__: a.name } : a));
    const res = await fetch(`/call/${name}`, { method: 'POST', body: JSON.stringify({ args: payload }) });
    const out = await res.json();
    if (!out.ok) throw new Error(out.error);
    return out.value;
  };
  return fn;
}
export const init_json = make('init_json');
export const backend_info_json = make('backend_info_json');
export const overview_json = make('overview_json');
export const series_json = make('series_json');
export const replay_json = make('replay_json');
export const run_json = make('run_json');
export const circuit_text_json = make('circuit_text_json');
