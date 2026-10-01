# instructions/05_section_5.md — Session 5: Section 5 (estimation error, turnover and robustness)

Section 4 is approved (through `afbe686`). The reviewer ran the suite on Linux (217 passed). From `periods.parquet`, it then recomputed every strategy's annualised return, vol, Sharpe, max drawdown and mean turnover with its own code: max differences 5e-12, 5e-10, 3e-10, 5e-11 and 3e-8. It replayed the stationary bootstrap and reproduced 3 results exactly:

- equal weight's interval (0.387, 1.110);
- Bayes-Stein against equal weight (−0.306, 0.316, fraction ≤ 0 0.4863);
- HRP against equal weight (−1.023, −0.013).

This session runs step 5.0, then Section 5 of `PLAN.md` (steps 5.1 to 5.6, where 5.6 is new), every step. Do not pause between steps. Stop only under rule 4. Nothing from Section 6. Where this file and `PLAN.md` or the kickoff differ, this file wins. This file is already committed; do not edit it. Stage files by explicit path; never stage `CLAUDE.md` or `PLAN.md`.

---

## Step 5.0 — reviewer decisions and 2 corrections (commit: `section 5: reviewer decisions for section 4`)

### a. `decisions/section_5_review.md`

1. **Open decision 6: option 1, ddof 1,** the same as annualised vol. Clear `decisions/OPEN.md`.
2. **Ruined strategies get a NaN point Sharpe as well as NaN intervals,** in `metrics_all.csv`, `sharpe_intervals.csv` and `results_primary.csv`.
   - Reason: `mv_unconstrained|ewma|sample|A` lost everything in month 37 and currently shows a Sharpe of 1.15. A mean over standard deviation of monthly returns says nothing about a path that ends at 0.
   - `ann_return` −1 and `max_dd` −1 stay, as they are the truthful figures.
   - Add `ruin_month` to `metrics_all.csv`.
3. **Review Deviations 9 to 15:** accepted.
4. **Risk parity convergence differing across platforms:** accepted. `rp_max_rc_dev` is about 6e-9 in every flagged month, so it is noise, and results may differ across operating systems at that level.

### b. Chart 1 corrections

- **Overlapping labels.** `risk_parity` sits on `min_variance`, and `mv_constrained` sits on `black_litterman`. Give each label a fixed offset in points, chosen so no 2 labels overlap. Keep the offsets in a dict in `pc/charts.py`, keyed by allocator.
- **Text box entry for a ruined strategy.** Show it as `mv_unconstrained (…): ruined 2026-02, wealth 0` instead of its mean and vol. A positive mean excess return for a fund that went to 0 misleads.
- Regenerate Chart 1, `metrics_all.csv`, `sharpe_intervals.csv` and `results_primary.csv` in the same commit. Nothing else may change, and the evidence shows the diff of those 3 CSVs.

---

## Amendments to steps 5.1 to 5.5

### 5.1 Sensitivity, fixed details

- **Draws.** One generator per date: `default_rng(run.sensitivity_seed + k)`, k the 0-based index of the date in `sensitivity.dates`. Draw Z (1000 × 18) first, then Z_Q (1000 × 2).
  - ε = Z Lᵀ, with L the Cholesky factor of Σ_lw_cc/36.
  - ε_Q = Z_Q L_Qᵀ, with L_Q the Cholesky factor of PΣ_lw_ccPᵀ/11. The divisor is 11, not 12, because the momentum window holds 11 months (convention 23).
  - Every μ-based strategy at a date uses the same ε draws.
- **Strategies and inputs.**
  - `mv_unconstrained|sample` uses the sample Σ.
  - The 3 set B strategies use Σ_lw_cc.
  - Bayes-Stein applies the shrinkage to μ̂ + ε.
  - Black-Litterman perturbs Q only.
  - All are re-optimised with w_prev = None.
- **Definitions.**
  - mean_abs_change = mean over draws of Σ_i |w̃_i − w_base,i|.
  - frac_top_asset_changes = the share of draws whose argmax ticker differs from the base argmax.
  - iqr = p75 − p25.
- **Chart 3.**
  - 7 panels, one per strategy (4 μ-based and the 3 references), at the last date.
  - Boxes are p25 to p75, whiskers p05 to p95, no fliers.
  - Each panel has its own y-axis, and the panel title gives mean_abs_change.
- **Evidence.**
  - `sensitivity_summary.csv` in full, and the last date's rows of `sensitivity.csv`.
  - A small table at each date: mean_abs_change of Bayes-Stein and of Black-Litterman, each divided by that of `mv_constrained|lw_cc` set B. This is question 3.

### 5.2 Turnover frontier, fixed details

- **Runs.** 8 runs of `mv_constrained|lw_cc|sample|C`: τ in the grid, plus `none`, which keeps the cost term and drops the turnover constraint.
- **Monthly means** exclude the first period.
- **Column definitions.**
  - `exante_return_given_up_bp_pa` = (mean μ′w at none − mean μ′w at τ) × 12 × 1e4.
  - `cost_saved_bp_pa` = (mean cost at none − mean cost at τ) × 12 × 1e4.
  - n_binding counts months with turnover ≥ τ_eff − 1e-6.
- **Extra column.** Add `realised_net_vs_none_bp_pa` = (mean ret_net at τ − mean ret_net at none) × 12 × 1e4. It measures whether the limit paid off after the fact, which is the other half of question 2.
- **Chart 4** adds the 45° line, where cost saved equals expected return given up. Points below it are limits that were worth it ex ante.

### 5.3 Cost sensitivity

- The cost scale multiplies the costs in both the optimiser and the charge.
- Columns: strategy_id, cost_scale, ruined, ann_return, ann_vol, sharpe, mean_turnover, mean_cost_bp_pa.
- Ruined rows follow 5.0.a item 2.

### 5.4 N close to T

- **Monthly Σ.** `np.cov` (ddof 1) of the 36 monthly excess returns in `trailing_months` for the decision month, then `condition_cov`.
- **`monthly_cov_robustness.csv`.** One row per decision date: decision_date, cond_daily, cond_monthly_before, cond_monthly_after, ridge_monthly.
- **`monthly_cov_strategies.csv`.** `mv_unconstrained|sample|sample|A` and `min_variance|sample|none|B` walk-forwards on the monthly Σ, with the same columns as `metrics_all.csv`, next to their daily-Σ rows.
- **Evidence.** The ridge count, the median and max cond_monthly_before, and both strategy tables.

### 5.5 Answers table, fixed content

Columns: question, figure, value, p05, p95, source_table, source_row.

- **Q1.**
  - The in-sample max Sharpe of the set A and set B frontiers, from the Chart 1 inputs.
  - The out-of-sample Sharpe, with interval, of `mv_constrained|lw_cc|sample|C`, `equal_weight` and `min_variance|lw_cc`.
  - The count of ruined set A strategies.
- **Q2.**
  - The τ = 0.30 row of the turnover frontier: return given up, cost saved, realised net vs none.
  - The largest τ in the grid whose point lies below the 45° line.
- **Q3.**
  - At the last date: mean_abs_change for each of the 4 μ-based strategies.
  - The 2 ratios from 5.1.
- **Q4.**
  - QLIKE difference against `lw_cc`, with interval, for `ewma` on `ew` and on `gmv`.
  - The bias ratio of `ewma` on `gmv`, and that of `lw_cc` on `gmv`.

Every value is read from its source CSV, never retyped.

---

## Step 5.6 — new: leveraged risk-based funds

**Why.** Risk parity, min variance and HRP hold 30% to 92% in SHY, and run at 2% to 4% vol against equal weight's 10%. Their unlevered returns mostly measure that vol gap. In practice, risk parity is run with leverage. This step asks whether their Sharpe ratios survive when they run at equal weight's risk.

**Config.** Add to `config.toml` a table `[levered]` with:

- `strategies = ["risk_parity|lw_cc|none|none", "min_variance|lw_cc|none|B", "hrp|lw_cc|none|none"]`
- `financing_spread_bp_pa = 50`

**Method** (`pc/experiments.py::levered_variants`).

- At each decision date, k_t = forecast_vol_ann(equal weight) / forecast_vol_ann(strategy), both from `periods.parquet`, both on Σ_lw_cc. No cap; report k.
- Target holdings are k_t·w_t in the risky assets and 1 − k_t in cash.
- Drift uses the risky assets and cash at rf. Turnover and cost apply to the risky weights only.
- Net holding return = k_t·(w′r) + (1 − k_t)·rf_hold − max(k_t − 1, 0)·spread·n_hold_days/(12 × `sample.days_per_month`) − cost.
- The ruin rule applies.

**Outputs.**

- `outputs/tables/levered_risk_based.csv`: strategy_id, mean_k, max_k, ann_return, ann_vol, sharpe, sharpe_p05, sharpe_p95, diff_vs_ew, diff_p05, diff_p95, frac_le_0, max_dd. The same bootstrap paths as step 4.4.
- One row per strategy, plus `equal_weight` for reference.

**Tests** in `tests/test_experiments.py`:

- `test_levered_k1_equals_unlevered`: forcing k = 1 reproduces the strategy's `ret_net` to 1e-12.
- `test_levered_zero_spread_cash_leg`: on a synthetic path with spread 0, the cash leg earns exactly rf.

**Evidence.** The table in full, and k by date (min, median, max) per strategy.

---

## Review file evidence (in addition to `PLAN.md` and the items above)

1. The 5.0 diff of the 3 CSVs, and Chart 1 and Chart 2 embedded.
2. Charts 3 and 4 embedded.
3. `answers.csv` in full, with each source row printed from its source table.
4. Runtime per step.
5. Fresh-clone output under the standing rule.

Status file: `instructions/05_section_5.status.md`, per rule 11. Then push and stop.
