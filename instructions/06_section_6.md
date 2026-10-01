# instructions/06_section_6.md — Session 6: Section 6 (trade generator and CLI)

Section 5 is approved (through `4e886f1`). The reviewer ran the suite on Linux (226 passed) and checked 3 things independently:

- **Levered funds.** It recomputed the levered risk parity and HRP funds with its own loop from `weights_long.parquet`. The mean leverage matches exactly. Sharpe agrees to 1e-5 (0.62965 against 0.62964), and the gap is consistent with the cash-drift detail, so it is immaterial.
- **Turnover grid.** It reran the grid through the engine and reproduced `realised_net_vs_none_bp_pa` (125.9 bp at τ = 0.05).
- **Bootstrap on that column.** None of the τ rows is distinguishable from 0. τ = 0.05: 90% interval (−88.6, +329.2) bp a year, fraction ≤ 0 0.16. τ = 0.10: (−104.2, +163.2). The write-up must not claim that tight turnover limits paid off; step 6.0 adds these intervals to the tables.

This session runs step 6.0, then Section 6 of `PLAN.md` (steps 6.1 to 6.5), every step. Do not pause between steps. Stop only under rule 4. Nothing from Section 7. Where this file and `PLAN.md` or the kickoff differ, this file wins. This file is already committed; do not edit it. Stage files by explicit path; never stage `CLAUDE.md` or `PLAN.md`.

---

## Step 6.0 — reviewer decisions for Section 5 (commit: `section 6: reviewer decisions for section 5`)

### a. `decisions/section_6_review.md`

1. **Open decision 7: option 1** (Σ_lw_cc for the 3 references).
2. **Open decision 8: option 1.** The supremum √(A − B²/C) = 1.7175, flagged `supremum_not_attained`. It is the correct statement, because the budget-1 frontier never reaches it. Option 2 depends on where a plot stops.
3. **Open decision 9: option 2.** A τ with `n_binding = 0` lies on the line, not below it. The answer becomes NaN, read as "no limit in the grid was worth it ex ante". Option 1 reports solver noise of 5e-8 bp as a result.
4. **Open decision 10: option 1,** the kickoff 4.6 form, for consistency with every other net return in the repo.
5. **Review Deviations 1 to 9 of Section 5:** accepted, except item 7's "the 2 Q3 ratios at the last date only", which is replaced by item 6 below.
6. **Q3 at all 3 dates.** At 2012-12-31, Black-Litterman's mean_abs_change (1.23) is larger than `mv_constrained`'s (0.94). Its ratio is 1.31 there, against 0.50 at 2020-02-28 and 0.22 at 2026-07-31. Reporting the last date only would overstate how reliably Black-Litterman calms weights. `answers.csv` carries both ratios at each of the 3 dates, 6 rows in place of 2.
7. Clear `decisions/OPEN.md`.

### b. Bootstrap intervals on the turnover frontier

- Add `realised_net_vs_none_p05`, `realised_net_vs_none_p95` and `realised_net_vs_none_frac_le_0` to `turnover_frontier.csv`.
- Paired monthly differences ret_net(τ) − ret_net(none), over months 2 to 196 (195 months, matching the point estimate). Mean × 12 × 1e4 per replication, from `stationary_bootstrap_indices(195, 6, 10000, run.bootstrap_seed)`. Quantiles as in decision 3 of Section 2.
- The `none` row gets NaN.
- In `answers.csv`, Q2 gains the τ = 0.05 and τ = 0.30 realised differences with these intervals.

### c. Regenerate

Regenerate `turnover_frontier.csv`, Chart 4 (unchanged apart from any annotation of the new columns; adding none is fine) and `answers.csv`. The evidence prints the old and new versions of both CSVs. Tests from Section 5 that assert the answer row count or the Q2 τ answer are updated to the decisions above. That is a change of spec, not of tolerance; list each in review Deviations.

---

## Amendments to steps 6.1 to 6.5

### 6.1 Trade core

- **Holdings and weights.**
  - `current_weights` returns w_before = holdings value / NAV for every universe ticker (0 where not held), plus NAV.
  - Cash is not part of w_before, so w_before sums to 1 − cash/NAV.
  - The allocator's budget constraint fully invests the cash.
- **Rounding, fixed.**
  - target_qty = w_target × NAV / price.
  - raw = target_qty − current_qty.
  - trade = sign(raw) × floor(|raw| / lot) × lot.
  - So a buy never buys past target, and a sell never sells past target or below 0.
- **Min notional.** Trades with |trade × price| < min_notional are dropped after rounding.
- **Cash repair.**
  - post_cash = cash − Σ trade × price − Σ est_cost.
  - While post_cash < 0: take the buy with the largest notional (ties by config order) and reduce it by 1 lot. If it reaches 0 or falls below min notional, drop it. Then recompute.
- **Errors.** `TradeInputError(code=2)`, raised for:
  - an unknown ticker;
  - a negative quantity;
  - a non-positive price;
  - a duplicate ticker;
  - a missing column;
  - a non-numeric value.

### 6.2 Trade list and summary

- `est_cost` = |notional| × c_i, with c_i from `costs.one_way_bp` / 1e4.
- weight_after = (current_qty + trade) × price / NAV.
- Turnover before rounding = Σ|w_target − w_before|. After rounding = Σ|w_after − w_before|.
- The shadow price is `AllocResult.turnover_dual` × 100. When the allocator has no turnover constraint, it prints "n/a".
- The summary also prints:
  - `tau_relaxed` and τ_eff when the feasibility rule fires;
  - the solver string;
  - the decision date used.
- The price warning compares each positions price with the panel close on the decision date given by `--asof`.

### 6.3 CLI, fixed rules

- **`--asof`.** Must be a decision date in the calendar; otherwise exit 2. The allocator inputs are `DateInputs` at that date, from the committed data. State this in `--help`: the CLI runs on the pinned snapshot, and a live run needs a fresh pull.
- **`--strategy`.**
  - Must be a registry id; otherwise exit 2.
  - Set A strategies (`mv_unconstrained|…|A`) exit 2 with "set A is research only; it shorts and levers". The CLI trades long-only books.
- **`--max-turnover`.** Allowed only for set C strategies, where it replaces `mv.max_turnover`. Otherwise exit 2.
- **w_prev** is w_before from the positions file, as amendment 6.1 defines it.
- **Exit codes.** 0 on success, 2 on input errors, 1 on anything else. The exception is printed in one line and the stack trace only with `--debug`, a new flag.
- **Output.** `trades.csv` is written with `float_format="%.10g"`, `index=False` and `lineterminator="\n"`, rows in config ticker order, holding only tickers with a trade.

### 6.4 Tests

Every test in `PLAN.md`, plus:

- `test_set_a_strategy_exit_2`;
- `test_asof_not_a_decision_date_exit_2`;
- `test_max_turnover_on_non_c_strategy_exit_2`;
- `test_cash_is_fully_invested_by_budget` (a book of only cash buys into the target; post-trade cash is ≥ 0 and ≤ Σ_i (price_i × lot + min_notional));
- `test_sell_never_below_zero`.

### 6.5 Demo, fixed book

- **`examples/positions_demo.csv`.** Built from these target weights of a $10,000,000 NAV at the 2026-07-31 panel closes:
  - GLD 0.40, SPY 0.20, IEF 0.20, TLT 0.10, HYG 0.05;
  - cash 0.05 plus the rounding residual, so NAV is exactly $10,000,000.00.
  - quantity = floor(weight × NAV / close).
  - prices = the 2026-07-31 closes, rounded to 4 decimals.
- **Command:** `pctrade --positions examples/positions_demo.csv --cash <the residual> --asof 2026-07-31 --out examples/trades_demo.csv`. Everything else at defaults, so the strategy is `mv_constrained|lw_cc|sample|C` with τ = 0.30.
- **Expected behaviour.** GLD at 0.40 against the 0.30 cap means τ_min ≥ 0.20. Whether the feasibility relaxation fires depends on the rest of the target; the summary shows it either way.
- **`docs/cli_demo.md`** shows:
  - how the book was built (the formula above);
  - the exact command;
  - the full printed output;
  - the trades table.
- `test_demo_reproduces_trades_demo` reruns the command into a temp path and compares bytes.

---

## Review file evidence (in addition to `PLAN.md`)

1. Step 6.0: old and new `turnover_frontier.csv` and `answers.csv`.
2. The demo book (`positions_demo.csv`), NAV check, printed summary and `trades_demo.csv`.
3. A by-hand reconciliation of 3 demo rows (GLD, one buy, one sell): target_qty, raw, the rounded trade, notional, est_cost and weight_after.
4. The output of every error test's command line and its exit code.
5. `pctrade --help`.
6. Fresh-clone output under the standing rule, and `pctrade --help` run from the fresh clone's venv.

Status file: `instructions/06_section_6.status.md`, per rule 11. Then push and stop.
