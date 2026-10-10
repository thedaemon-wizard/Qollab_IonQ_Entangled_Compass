# Review (2026-10-10, evening)

An independent review of the code and the texts was run with AI assistants in three parts
(correctness, Qollab runtime and rules, documentation and claims); every finding was then
checked separately, by reproducing it or reading the source. 35 findings were checked, 32
confirmed; the author checked each before it was fixed. Severity: HIGH = wrong result or claim,
MEDIUM = misleading or fragile, LOW = polish.

| # | Severity | Finding | Fix |
|---|---|---|---|
| 1 | HIGH | Replay with "measured in the last run" ignored the dephasing $`\gamma`$ | Measured gate-only visibilities are multiplied by $`e^{-m\gamma}`$; test added |
| 2 | HIGH | Storm challenge: after a two-fringe GHZ-4 slip (157 nT), switching to a single-qubit-range sensor could lock the estimate 314 nT off | New rule: keeping a sensor keeps its estimate; switching starts the new sensor from a fresh absolute fix. Verdict text names the chosen sensor and the end offset; test added |
| 3 | HIGH | main.js returned at once; the injected backend is only available while it runs | main.js now awaits a promise that never resolves, as on Qollab's working projects |
| 4 | MEDIUM | SQL described without its condition (one interrogation of the same length per qubit); "below 1, entanglement no longer pays" overstated it | Condition stated everywhere; "this X/Y readout"; note on optimal readout (gain 2, crossover 0.231) and on the 4-pass qubit |
| 5 | MEDIUM | Twin run did not stop on a wrong bit order | Canary check as in the main run; test added |
| 6 | MEDIUM | Backend detection by name only; unknown or Braket cloud backends escaped the one-job guard | Allow-list of known simulators; IonQ non-simulator and Braket cloud refused; unknown backends get one guarded job |
| 7 | MEDIUM | Twin $`\sqrt{2}`$ gain shown only against the matched baseline | SQL for a difference (1.58 nT) added: the X/Y pair matches it, an optimally read pair would beat it by $`\sqrt{2}`$ |
| 8 | MEDIUM | Challenge benchmarks could use a different visibility model than a game in progress | Settings frozen at the start of a game |
| 9 | MEDIUM | "Same random draws" was not true | Now "same random seed" |
| 10 | MEDIUM | Higgins 2007 cited as theory; Finkelstein 2024 overstated | Higgins = experiment without entanglement; Finkelstein = a GHZ cascade was prepared |
| 11 | MEDIUM | Japanese "要確認" in the English UI; Aria visibility stated without its assumption | English text; model counts abstract gates, IonQ compiles to native gates first |
| 12 | LOW | Non-finite numbers could break JSON.parse | Sent as null |
| 13 | LOW | IBM noise models in the browser could block for minutes | Capped at 200 shots |
| 14 | LOW | "29% of their variance is shared" was a non-standard statistic | $`r^2 = 0.11`$, and "29% of the summed variance cancels in the difference" |
| 15 | LOW | 17:06 values in the README were the true values, not readings | "ideally reads", with one local run's readings |
| 16 | LOW | Charts other than the field chart had no data table; two series differed by colour only | Tables on every chart; distinct dashes |
| 17 | LOW | Status messages were announced twice | Duplicate announcements removed |
| 18 | LOW | The skip link changed the frame's URL hash | Focus moves without a hash change |
| 19 | LOW | CSV files were parsed again on every call | Parsed once per file |
| 20 | LOW | First paint waited for the overview computation | One paint before it |
| 21 | LOW | Fringe-jump wording, Leibfried and Ruster details | "fringe changes"; "a perfect experiment with three unentangled ions"; "up to 6.2 mm apart" |

Not yet done at the time of writing: runs on Qollab's built-in and IonQ simulators ("Where it
ran" in the README).
