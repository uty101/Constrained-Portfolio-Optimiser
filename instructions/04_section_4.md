# instructions/04_section_4.md — Session 4: Section 4 (walk-forward and headline results)

Section 3 is approved (through `d7472bd`). The reviewer ran the suite on Linux (204 passed). It then recomputed all 6 optimised allocators at 2016-06-30 with its own code (cvxpy, scipy, PyPortfolioOpt and a hand-written Black-Litterman). Every weight matches the review table to its 8 printed decimals, and P, Q and μ_BL match at 2010-04-30, 2016-06-30 and 2020-02-28.

The reviewer's first Black-Litterman attempt did not match, and the cause is worth knowing. It used `pd.DateOffset(months=1)` for "t − 1 month", which from 2016-06-30 lands on 2016-05-30 and drops May. Your `trailing_months` works on calendar month periods and checks the row count, which is the correct reading. The same flaw exists in `window_daily`, from the reviewer's own amendment 2.1; step 4.0.c fixes it.

This session runs step 4.0, then Section 4 of `PLAN.md` (steps 4.1 to 4.6), every step. Do not pause between steps. Stop only under rule 4. Nothing from Section 5. Where this file and `PLAN.md` or the kickoff differ, this file wins. This file is already committed; do not edit it. Stage files by explicit path; never stage `CLAUDE.md` or `PLAN.md`.

---

## Step 4.0 — reviewer decisions and one correction

### a. `decisions/section_3_review.md` (one commit with b: `section 4: reviewer decisions for section 3`)

1. **Open decision 4: option 1 confirmed.** One ranking, highest first, ties by config order, so on a bottom tie the later ticker is short. It is the plain reading of "the 6 lowest" in a single ranking. `decisions/OPEN.md` is then empty.
2. **`pc.solver.solver_config()` reading `config.toml` via a path relative to the package:** accepted. It does not depend on the working directory, which the Section 6 CLI needs.
3. **Solver strings joined by "+" and SCS retries counted with `count("SCS")`:** accepted, and carried into `periods.parquet`.
4. **risk_parity when L-BFGS-B fails:** keep scipy's message as the status and `fallback = False`, but add a boolean column `rp_converged` to `periods.parquet` (True for every non risk parity row). Section 4 evidence counts the False rows per strategy.
5. **`mu_sample` built at 3.3, the test inputs and tolerances in review Deviations 7 and 8, and the 24-minute first fresh-clone run:** accepted. The run was environmental, most likely a virus scan of a new venv.

### b. Convention 23 in `docs/CONVENTIONS_RESOLVED.md`

> **Monthly windows are calendar-month periods.** Any window stated in months covers whole calendar months by period: the 36-month estimation window, the 12-1 momentum window and the mean of monthly returns. A 36-month window ending at t covers the months p − 35 through p, where p is the month of t. Row counts are checked. `pd.DateOffset` arithmetic on trading dates is never used for a month window.

### c. Correct `window_daily` (separate commit: `step 4.0: window_daily on calendar-month periods`)

- **Reason.** With `t − DateOffset(months=36)` measured from a last trading day such as the 28th or 29th, the window starts before month end. 59 of the 196 windows therefore include 1 to 3 trading days from the month before the 36. Counts by extra days: 1 day in 28 windows, 2 in 27, 3 in 4; 137 are exact. The effect on a covariance built from about 756 rows is small, but the window should match its definition before the backtest is built on it.
- **New rule.** `window_daily(returns_d, t, months)` returns the daily rows whose calendar month is in [p − months + 1, p], p the month of t, and whose date is ≤ t. Signature unchanged.
- **Tests.**
  - Update `test_window_boundaries` to assert this rule on a synthetic index where a decision date falls on the 28th, so the old rule would have included the 29th to 31st of the earlier month.
  - Add `test_window_matches_calendar_months_real` to assert, at all 196 decision dates, that every window's first date is the first trading day of month p − 35.
- **Rerun** `write_cov_eval` and commit the 4 regenerated CSVs in the same commit.
- **Evidence.** Old and new values of `cov_eval.csv` and `cov_eval_qlike_diff.csv` side by side, with the max abs change per column. If any sign in `diff_vs_lw_cc` flips, or `p05` and `p95` move to the other side of zero, list those rows. Tests that read real-data windows (steps 2.2, 3.5, 3.6) must still pass unchanged. If one fails, stop under rule 4.

---

## Amendments to steps 4.1 to 4.6

### 4.2 Engine, fixed details

1. **Caching.** Compute each (decision date, estimator) Σ once and reuse it across strategies. Compute `mu_sample` once per date.
2. **μ passed to each allocator.**
   - `sample`: `mu_sample(monthly_excess, t, 36)`.
   - `bayes_stein`: `mu_bayes_stein(mu_sample, Σ_lw_cc, 36)`.
   - `bl`: Π = δ Σ_cov w_mkt, the views at t, and `bl_posterior` with the strategy's own Σ_cov. μ_BL goes in as `mu` and Σ_BL as `Sigma` (convention 21).
   - Allocators that do not read μ receive `mu_sample`.
3. **Σ passed.**
   - Each strategy's own estimator, conditioned.
   - Black-Litterman gets Σ_BL.
   - `equal_weight` has cov `none`, so its Σ is `lw_cc`, used only for `forecast_vol_ann`.
4. **Constraint sets.**
   - A: `Constraints(lower=None, upper=None, gamma=mv.gamma)`.
   - B: lower `mv.lower`, upper `mv.upper`.
   - C: B plus `max_turnover = mv.max_turnover` and cost c_i = `costs.one_way_bp[i]` / 1e4 × cost scale (scale 1 here).
   - `none`: `Constraints()` with defaults.
   - The cost actually charged in every strategy, equal weight included, uses the same c_i.
5. **Recorded fields.**
   - `mu_exante` = (the μ passed)′w.
   - `forecast_vol_ann` = √(12 w′Σw), with the strategy's conditioned Σ_cov. For Black-Litterman this is Σ_cov, not Σ_BL, so every strategy's forecast vol is on the same basis.
   - `gross_leverage` = Σ|w|.
6. **First period.** cost 0 and turnover NaN. Mean turnover excludes it.
7. **Drift.** w_prev,i = w_i(1 + r_i) / Σ_j w_j(1 + r_j) over (exec_t−1, exec_t]. If the denominator is ≤ 0, the fund has lost everything, and the ruin rule below applies.
8. **Ruin.** This deliberately overrides kickoff 4.10.
   - The month whose `ret_net` ≤ −1 is kept, with ret_net floored at −1, and `ruined = True` from that month on.
   - Later months have NaN returns and are not solved.
   - Metrics include the ruin month, so wealth ends at 0, ann. return is −100% and max DD is −100%.
   - Reason: reporting "the months before ruin" alone would print a Sharpe ratio for a strategy that lost everything.
   - A ruined strategy gets NaN Sharpe intervals in 4.4, and shows `ruined` in every table.
9. **`test_no_look_ahead`.** Clarified, because w_prev legitimately uses prices up to the execution close (kickoff 4.3), which is after t.
   - It runs one spec per allocator, 8 specs: `mv_unconstrained|sample|sample|A`, `mv_constrained|lw_cc|sample|C`, `mv_constrained|lw_cc|bayes_stein|C`, `min_variance|ewma|none|B`, `risk_parity|pca3|none|none`, `black_litterman|lw_cc|bl|C`, `hrp|sample|none|none`, `equal_weight|none|none|none`.
   - It covers the first 6 decision dates, with t the 3rd.
   - (a) Multiply every price dated after `exec_date(t)` by the factors: every weight at decision dates ≤ t is unchanged, compared with `==`.
   - (b) Multiply every price dated after t: the weights at t of the 6 specs that do not use w_prev (the 2 `mv_constrained` and `black_litterman` excluded) are unchanged, compared with `==`.

### 4.3 Metrics

Add `n_months` (months in the wealth path), `ruined`, `scs_retries`, `fallbacks` and `rp_not_converged` as columns of `metrics_all.csv`.

### 4.5 Primary table

`results_primary.csv` also carries `forecast_vol_ann` (mean) and `realised_vol_ann`, so the forecast/realised ratio can be checked from its parts.

### 4.6 Charts, fixed

**Chart 1** is drawn in excess-return space, so the frontier and the points are comparable.

- **Frontier inputs.** μ = the mean of the 196 holding-period excess returns × 12, Σ = their sample covariance × 12.
- **Set A frontier.** The closed-form hyperbola, plotted from the GMV return up to 3 times the largest single-asset excess return.
- **Set B frontier.** 50 target returns evenly spaced from the set B minimum variance fund's return to the largest return feasible under 0 ≤ w ≤ 0.30. Each point is a CLARABEL solve.
- **Strategy points.** x = std(excess_net) × √12, y = mean(excess_net) × 12.
- **Axes.** x runs from 0 to 30%. Any primary strategy outside the axes is listed in a text box with its coordinates, not dropped.
- **Labels.** One label per point, with the short allocator name.

**Chart 2** has its y-axis from 0 to 1. Both strategies are long-only.

---

## Review file evidence (in addition to `PLAN.md`)

1. Step 4.0.c: the side-by-side old and new tables and the max changes.
2. The 26 strategies, one row each: n_months, ruined, solver strings seen with counts, scs_retries, fallbacks, tau_relaxed months, rp_not_converged, ridged months.
3. `metrics_all.csv`, `sharpe_intervals.csv` and `results_primary.csv` in full.
4. For `mv_unconstrained|sample|sample|A`: gross leverage by date (min, median, max), the 5 worst months by `ret_net`, and the ruin month if there is one.
5. For `mv_constrained|lw_cc|sample|C`: mean `turnover_dual` in bp per 1% over binding months, and the number of binding months.
6. A reconciliation for `min_variance|lw_cc|none|B` at the 3rd decision date: w_target, w_prev_drifted, trade, cost_i, the gross holding return as w′r, and net from the formula. Every figure is printed, so the reviewer can recompute it.
7. Runtime per step. Step 4.2 in total, and per strategy.
8. Fresh-clone output under the standing rule.

Status file: `instructions/04_section_4.status.md`, per rule 11. Then push and stop.
