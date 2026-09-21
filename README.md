# PR #6713 follow-up evidence

Baseline: `6ce559969683bfbb1e3c54c4f19736cbacff23e7`
Candidate: `4631ef1d887f1845c101a1d34ab03336ca721e9a`

Chromium 153.0.8010.0; the production `_showProjectPicker` function and `static/style.css` in an isolated DOM fixture with synthetic session/project labels. This is focused browser geometry evidence, not an end-to-end mobile-device certification.

- Desktop 900x700 and narrow 390x844: scroll the session list 100px. Baseline trigger gap changes from 4px to 104px; candidate remains 4px.
- Removing the anchor row without a viewport event leaves an orphan in the baseline and closes the candidate.
- Constrained 390x500 with 24 projects: candidate stays in view, scrolls internally, and reaches `+ New project`.
- Injected visual viewport 220x500 at offsets (180,100): candidate respects all four bounds.
- Native Chromium page scale 1.25: visual viewport becomes 312x675.2 while layout remains 390x844; candidate stays in view.
- No uncaught exceptions in these focused scenarios.

`browser-results.json` contains the measured rectangles. Desktop/narrow before and after images show the state after the same 100px list scroll.

## Verification limits

The unmodified whole-page smoke routes `/`, `/#settings`, `/#sessions` loaded the local application but could not pass the zero-console-error gate: seven existing jsDelivr Prism/xterm assets per page failed with `net::ERR_EMPTY_RESPONSE` in this environment. `smoke-results.json` records those failures. No physical Android/iOS keyboard test or full pytest suite was run for this follow-up.
