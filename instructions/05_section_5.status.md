# Status: session 5 (instructions/05_section_5.md)

## Outcome

Completed. Step 5.0 and steps 5.1 to 5.6 are built and committed, one commit per step, plus 1 follow-up commit for Chart 4 (`139e653`). 226 tests pass in the repo and in the fresh clone at `%TEMP%\pcs5`. A second run of every Section 5 writer reproduced every CSV byte for byte. The only file that changed was Chart 4, whose committed PNG had been drawn from the rounded CSV and not by the writer. The writer's PNG is committed at `139e653` and is byte-identical across 2 further runs.

## Last step reached

Step 5.6 (`286544a`), then the Chart 4 follow-up (`139e653`) and the review file (`4c2c7b3`, `281d341`).

## Reason for any stop

None. No rule 4 stop. Four points needed a choice the documents do not make. Each is implemented as option 1 and listed in `decisions/OPEN.md` with both options, following the session 4b precedent for open decision 6. No other step depends on them.

## Questions and blockers for the reviewer

1. **Open decision 7 (step 5.1): the references' covariance.** Neither PLAN 5.1 nor amendment 5.1 says which Σ min variance, risk parity and HRP use as zero-dispersion references.
   - Implemented: Σ_lw_cc for all 3.
   - Alternative: their primary-table estimators (`lw_cc`, `ewma`, `sample`).
   - Their dispersion is 0 either way.
2. **Open decision 8 (step 5.5): the set A frontier has no maximum Sharpe on the Chart 1 inputs.** 1′Σ⁻¹μ = −43.4 < 0, so the budget-1 frontier's Sharpe rises towards √(A − B²/C) = 1.7175 and never reaches it. The closed-form tangency √A = 1.7536 needs a budget of −1.
   - Implemented: the supremum 1.7175, flagged `supremum_not_attained` in the new `frontier_max_sharpe.csv`.
   - Alternative: the best of the 50 plotted Chart 1 points, 1.7081.
3. **Open decision 9 (step 5.5): "the largest τ below the 45° line" is decided by solver noise.** τ = 0.05 to 0.75 all lie above the line. τ = 1.00 lies below it by 5e-8 bp a year, at a limit that never binds.
   - Implemented: the literal comparison, answer 1.00.
   - Alternative: a τ that never binds lies on the line, answer NaN.
4. **Open decision 10 (step 5.6): the levered net formula against `test_levered_k1_equals_unlevered`.** Step 5.6 subtracts cost. The engine's kickoff 4.6 form is (1 − cost)(1 + gross) − 1. At k = 1 the two forms differ by cost × w′r, up to 6.4e-5 a month, so the fixed 1e-12 test passes only with the kickoff form.
   - Implemented: the kickoff 4.6 form.
   - Effect: every levered Sharpe ratio moves by at most 2.3e-5 between the 2 forms.
5. **Two Section 4 tests changed with decision 5.0.a.2.** They had asserted a ruined strategy's point Sharpe and now assert NaN (review Deviations 1). No tolerance changed.
6. **`pc/backtest.py` gained a keyword `inputs_cls`** (default `DateInputs`) so that step 5.4 runs its monthly Σ through the same engine. The default path is unchanged: the 5.2 run at τ = 0.30 and the 5.3 run at cost scale 1 reproduce `periods.parquet` to 0.0 (review Deviations 7).
7. **Formats I set where none was given** (review Deviations 2 to 9). The main ones:
   - `ruin_month` as `YYYY-MM`.
   - `source_row` as a `DataFrame.query` string.
   - A leading `sigma_basis` column in `monthly_cov_strategies.csv`.
   - The 2 Q3 ratios at the last date only.
   - `realised_net_ann_return` over the whole wealth path.
   - `mean_dual_bp_per_pct` over all months after the first.
   - `mean_cost_bp_pa` without the first period.
   - Chart 4 with free aspect, shading and stacked labels.
8. **`test_answers_has_4_rows_with_sources` keeps its PLAN name.** Amendment 5.5 gives 20 figures, so the test checks 4 questions with 6, 4, 6 and 4 rows. It also checks that every row's source query finds its rows.
9. **Results worth a look:**
   - Every τ in the grid gives up more expected return than it saves in cost (Chart 4). τ = 0.05 still earned 126 bp a year more net than no limit.
   - Black-Litterman's weight sensitivity at 2026-07-31 is 0.22 of `mv_constrained`'s. Bayes-Stein's is 1.02.
   - On the monthly Σ, `mv_unconstrained|sample|sample|A` is ruined in 2010-12, and no monthly Σ needed a ridge (max cond 81,340).
   - Levered to equal weight's forecast vol, risk parity's Sharpe is 0.63 (0.17, 1.15) against equal weight's 0.71. HRP needs k up to 16.5 and ends at −0.15.
10. `CLAUDE.md` and `PLAN.md` were not staged or committed, as instructed.

## git log origin/main --oneline -3

```
281d341 section 5: review file, fresh-clone check
4c2c7b3 section 5: review file
139e653 step 5.2: chart 4 as written by write_turnover_frontier
```
