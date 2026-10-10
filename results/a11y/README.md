# Accessibility checks (2026-10-10, figures added 2026-10-11)

Run on the local harness (`tools/devserver/`), which serves the same `index.html`, `main.js`,
`main.css` and `ui/` as the Qollab project.

| Check | Result |
|---|---|
| axe-core 4.14.0, tags wcag2a, wcag2aa, wcag21a, wcag21aa, wcag22aa, best-practice; all 5 views (the challenge after one round, the tracker and the two-observatories view after a replay and a circuit run), dark and light | 0 violations in all 10 combinations (`axe_20261010.json`). The first pass found two (the tab list outside a landmark; a skipped heading level in the tracker), both fixed. |
| Colour tokens (WCAG 2.2 contrast against both background tokens) | Dark: text 14.8, muted 8.8, series 7.2–9.9, control borders 4.7. Light: text 16.4, muted 7.1, series 4.9–7.1, control borders 4.3. Series also differ by dash. |
| 320 px wide viewport | No horizontal page scroll on any view (long URLs wrap; tables and the circuit drawing scroll inside focusable boxes). |
| Keyboard | Skip link; tabs with arrow keys, Home and End; native buttons, selects and sliders with labels; focus moves to each new challenge round and to the final result; visible focus ring. |
| Text alternatives | Every chart and dial is an SVG with a title and a description that states the numbers; charts have a data table. |
| Figures (2026-10-11) | The four explanatory figures (model loop, circuit and qubit map, architecture, two-observatory what-if) are SVGs with role img, a title and a description in words; what is real, a model, simulated or classical is shown by outline style and a tag word, not by colour alone. In both schemes: no two text boxes overlap, every text sits inside its box and the view box, and the page does not scroll sideways at 320 px (the figures scroll inside focusable regions) (`figure_checks_20261011.json`). axe-core 4.14.0 again finds 0 violations in all 10 combinations (`axe_20261011_figures.json`). |
| Formulas (2026-10-11) | Formulas in the app are native MathML (Temml 0.14.0, Latin Modern Math): 54 on the five views after a replay and a circuit run, 0 Temml errors, no TeX left visible; with cdn.jsdelivr.net blocked the same strings appear as Unicode text and nothing else changes (`math_checks_20261011.json`). axe-core 4.14.0: 0 violations in all 10 view and scheme combinations (`axe_20261011_math.json`). The Field tracker scrolled sideways at 320 px before this round (the settings fieldset kept its min-content width); fixed, now no view scrolls sideways. |
| Motion | Nothing moves on its own; the challenge is turn-based. |
