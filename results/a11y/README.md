# Accessibility checks (2026-10-10)

Run on the local harness (`tools/devserver/`), which serves the same `index.html`, `main.js`,
`main.css` and `ui/` as the Qollab project.

| Check | Result |
|---|---|
| axe-core 4.14.0, tags wcag2a, wcag2aa, wcag21a, wcag21aa, wcag22aa, best-practice; all 4 views (the challenge after one round, the tracker after a replay and a circuit run), dark and light | 0 violations in all 8 combinations (`axe_20261010.json`). The first pass found two (the tab list outside a landmark; a skipped heading level in the tracker), both fixed. |
| Colour tokens (WCAG 2.2 contrast against both background tokens) | Dark: text 14.8, muted 8.8, series 7.2–9.9, control borders 4.7. Light: text 16.4, muted 7.1, series 4.9–7.1, control borders 4.3. Series also differ by dash. |
| 320 px wide viewport | No horizontal page scroll on any view (long URLs wrap; tables and the circuit drawing scroll inside focusable boxes). |
| Keyboard | Skip link; tabs with arrow keys, Home and End; native buttons, selects and sliders with labels; focus moves to each new challenge round and to the final result; visible focus ring. |
| Text alternatives | Every chart and dial is an SVG with a title and a description that states the numbers; charts have a data table. |
| Motion | Nothing moves on its own; the challenge is turn-based. |
