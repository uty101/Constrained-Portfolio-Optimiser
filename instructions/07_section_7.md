# instructions/07_section_7.md — Session 7: Section 7 (write-up and reproducibility)

Section 6 is approved (through `5889d5a`). The reviewer ran the suite on Linux (259 passed, including `test_demo_reproduces_trades_demo`, so the byte comparison holds across platforms). It also checked the demo 2 ways:

- **The allocator target.** It solved the demo's target with its own cvxpy problem from the book's weights. XLK 0.175040, TLT 0.075033, GLD 0.300000, with the rest unchanged, and a turnover dual of 0.946883 bp per 1%, all exact.
- **The cash repair.** By hand: floor(9993.94) = 9993 XLK shares leave cash at −970.67, and 6 lots cut reach 9987 shares and +80.52.

The reviewer's τ intervals in `06_section_6.md` were drawn over 196 months with the first month included; yours follow the spec (195 months) and stand.

This is the last section. It runs step 7.0, then Section 7 of `PLAN.md` (steps 7.1 to 7.5), every step. Do not pause between steps. Stop only under rule 4. Where this file and `PLAN.md` or the kickoff differ, this file wins. This file is already committed; do not edit it. Stage files by explicit path; never stage `CLAUDE.md` or `PLAN.md`.

---

## Step 7.0 — reviewer decisions (commit: `section 7: reviewer decisions for section 6`)

Write `decisions/section_7_review.md`:

1. **Open decision 11: option 1.** A missing ticker is held at 0 and priced at the panel close on `--asof`. It is the price the CLI already uses for its warnings. The `--help` text already says the CLI runs on the pinned snapshot. Clear `decisions/OPEN.md`.
2. **Review Deviations 6 to 9 of Section 6:** accepted. That covers the signed notional, the extra exit 2 cases, negative `--cash` with a warning, and `current_weights(…, tickers=None)`.
3. **`test_demo_reproduces_trades_demo` stays as a byte comparison.** It passed on Linux.

---

## Amendments to steps 7.1 to 7.5

### 7.1 `scripts/run_all.py`

- **Order.** It calls the writers in section order:
  1. data issues and data summary;
  2. covariance evaluation;
  3. the walk forward;
  4. metrics, intervals and the primary table;
  5. Charts 1 and 2;
  6. every Section 5 writer and Charts 3 and 4;
  7. the README tables in 7.2 below;
  8. the CLI demo, through `pc.cli.main` with the 6.5 command.
- **Runtime.** It prints the time taken by each writer.
- **Determinism.** Run it twice. After the second run, `git status --porcelain` is empty. If a PNG or parquet differs between runs, stop under rule 4 and report which.
- **Test.** `test_run_all_is_importable_and_offline` as in `PLAN.md`.

### 7.2 README

**Tables come from code, not from typing.** Add `pc/report.py::write_readme_tables(cfg)`, which writes 5 Markdown snippets to `outputs/tables/`:

- `readme_primary.md`, from `results_primary.csv`. Columns: Strategy, Ann. return, Vol, Sharpe (90% interval), Max DD, Monthly turnover, Avg positions. Percentages to 1 dp, Sharpe to 2 dp. A ruined row shows "ruined (YYYY-MM)" in the Sharpe cell.
- `readme_qlike.md`, from `cov_eval.csv` and `cov_eval_qlike_diff.csv`. One row per estimator. Per portfolio set: mean QLIKE, the difference against `lw_cc` with its interval, and the bias ratio.
- `readme_turnover.md`, from `turnover_frontier.csv`. Columns: τ, months binding, return given up (bp pa), cost saved (bp pa), realised net vs no limit (bp pa, with interval).
- `readme_levered.md`, from `levered_risk_based.csv`.
- `readme_robustness.md`, from `cost_sensitivity.csv` (Sharpe at cost scales 0, 1, 3 for the 7 primary strategies) and `monthly_cov_strategies.csv`.

The README embeds each snippet verbatim, between marker comments `<!-- readme_primary.md -->` and `<!-- /readme_primary.md -->`. The test `test_readme_tables_match_snippets` asserts that the text between the markers equals the snippet file.

**Outline, in this order.** Section titles may be reworded; the order and content may not.

1. **Title, and 2 sentences** on what the project is.
2. **What it found.** 4 short paragraphs, one per research question, carrying the figures and intervals from `answers.csv`. This is the only place in the README where prose may repeat a figure that also appears in a table or chart.
3. **Setup.** Universe, sample, timing (decision at month end, trade at the next close, 196 holding periods), the cost model, and the 7 primary strategies with their constraint sets. Under 200 words, linking to `docs/METHODS.md`.
4. **Results.** A 1-paragraph callout, then the primary table. A callout, then Chart 1. A callout, then Chart 2.
5. **Estimation error and weight stability.** A callout, then Chart 3, then the Bayes-Stein and Black-Litterman ratios at all 3 dates.
6. **Turnover limits.** A callout, then Chart 4, then the turnover table.
7. **Risk forecasts.** A callout, then the QLIKE table.
8. **Robustness.** Cost scales, the 36-monthly-return covariance, and the levered risk-based funds. A callout and a table for each.
9. **Trade generator.** Install with the lock file, the demo command, and a link to `docs/cli_demo.md`. What the demo shows: the 0.30 turnover limit binding, GLD traded down to its cap, and the cash deployed.
10. **Reproduce.** The exact commands, from a fresh clone to `run_all` and `pytest`.
11. **Limitations.** One sentence each:
    - 196 monthly observations, so intervals are wide;
    - a universe chosen in 2026 from ETFs that survived since 2007 (hindsight in the universe);
    - flat bp costs with no market impact;
    - no financing cost on set A shorts;
    - a sample dominated first by zero rates, then by rate rises;
    - one snapshot of yfinance adjusted prices;
    - Black-Litterman views that are mechanical, not researched.
12. **Repo map.** Folders and what is in each.

**Claims the README must not make** (each is contradicted by the outputs):

- that any allocator beat equal weight. No Sharpe difference against equal weight has an interval above 0;
- that tight turnover limits paid off. Every realised interval contains 0;
- that Black-Litterman reliably steadies weights. Its ratio is 1.31 at 2012-12-31;
- that Bayes-Stein steadies weights. Its ratios are 0.98, 0.95 and 1.02;
- that unconstrained mean-variance with Ledoit-Wolf "survived" in any useful sense. It had a −98% drawdown.

**Statements that must appear:**

- HRP, under all 4 covariance estimators, is the only allocator whose Sharpe is reliably below equal weight's (primary row: interval −1.02 to −0.01).
- 3 of the 4 unconstrained mean-variance funds went to 0.
- The turnover result. Each limit gives up more expected return than it saves in cost, and the realised effect cannot be told apart from 0.
- Risk parity levered to equal weight's vol keeps a Sharpe within noise of equal weight's. HRP levered to the same vol does not.

**Writing rules** (from the kickoff, made specific):

- Plain English, conversational but technical. Concrete figures over adjectives.
- Numerals for every number.
- No dash or hyphen joining 2 clauses: no "—", no " – ", no " - " between clauses. Hyphens inside compound terms (mean-variance, Ledoit-Wolf, out-of-sample) are fine.
- None of the words robust, resilient, rigorous, leveraging, grounded. No "delve", "crucial", "landscape", "notably" or "it's worth noting".
- No lists of 3 adjectives, and no filler openers.
- The vehicle is "the fund". Strategy names stay as they are.
- Each chart and table gets its callout in the prose immediately before it. The callout says what to look at and why it matters. Outside section 2 of the outline, it does not restate numbers the chart or table shows.
- Causal language only where the outputs support the mechanism. For example, HRP's weak Sharpe follows from its SHY weight in a zero-rate sample (shown by HRP's SHY weights in `weights_long.parquet` and by `levered_risk_based.csv`). Otherwise use "is associated with" or state the figure.
- A light touch of humour is welcome in at most 2 places. It must never replace a figure.
- Total length 1,500 to 2,500 words, excluding tables.

### 7.3 `docs/DESIGN_NOTE.md`

Write 1 paragraph per constraint or rule, each saying why a portfolio implementation desk has it and what this repo's outputs showed about it:

- the 30% position cap;
- long only;
- the full-investment budget;
- the turnover limit;
- flat bp costs in the objective;
- the feasibility relaxation when a drifted weight breaches its cap. A mandate breach outranks a turnover budget, and the demo shows it;
- lot rounding and minimum notional;
- the cash repair;
- the solver fallback and hold rule;
- blocking set A in the CLI.

Follow the same writing rules, and keep it under 900 words.

### 7.4 `docs/METHODS.md`

- **Content.** The maths of kickoff Section 5, as finally built. That includes:
  - the 11-month momentum window and calendar-month windows (convention 23);
  - the ddof rule for Ledoit-Wolf;
  - Ω with τΣ;
  - Σ_BL in the optimiser;
  - the ruin rule as overridden in 4.2.8, and NaN Sharpe for ruined funds;
  - the levered variant of 5.6;
  - the bootstrap algorithm.
- **Format.** Formulas in LaTeX math blocks.
- **Pointers.** It refers to `docs/CONVENTIONS_RESOLVED.md` for the 23 conventions rather than repeating them, and to each `decisions/section_*_review.md` where a choice was made.

### 7.5 Final check and tidy

- **Fresh clone,** per standing amendments 2 and 3 (the lock file, a short temp path). Run `scripts/run_all.py`, then `.venv\Scripts\python -m pytest --disable-socket -q`. After `run_all`, `git status --porcelain` in the clone is empty.
- **Unused functions.** Add `scripts/find_unused.py`. It parses every module in `pc/` with `ast` and lists each top-level function and class whose name appears in no other file under `pc/`, `scripts/` or `tests/`. Run it. For each hit, remove it or state in the review why it stays (for example, `pctrade` entry points).
- **Grep.** `git grep -n -E "TODO|FIXME|XXX"` returns nothing.
- **Remove** `tests/test_placeholder.py`.
- **Update** `README.md` is done in 7.2. Nothing else in the repo may still say "results pending".

---

## Review file evidence

1. `run_all` output from both runs, with per-writer runtime, and `git status --porcelain` after each.
2. A trace table for every figure in README section 2 and every figure in prose elsewhere: the figure as written, the source CSV, its row and column, and the value there.
3. Output of `grep -n -E " — | – | - |robust|resilient|rigorous|leverag|grounded|delve|crucial|landscape|notably" README.md docs/DESIGN_NOTE.md docs/METHODS.md`, with each hit justified or fixed. Markdown list markers at the start of a line do not count.
4. Word counts of the README (excluding tables), DESIGN_NOTE and METHODS.
5. `find_unused.py` output and the disposition of each hit.
6. Fresh-clone output (`run_all`, `pytest`, `git status`).

Status file: `instructions/07_section_7.status.md`, per rule 11. Then push and stop.
