# instructions/02_section_2.md — Session 2: Section 2 (covariance estimators and forecast evaluation)

Section 1 is approved (sessions 1 and 1b, through `ec91ac8`). The reviewer installed from `requirements-lock.txt` on Linux, ran the suite with sockets disabled (21 passed) and recomputed `data_summary.csv` and `corr_full_sample.csv` from the raw prices without calling `pc`. They agree to 5e-11, which is the `%.10g` rounding, and every worst and best date matches. `git ls-files --eol` shows LF throughout.

Build Section 2 of `PLAN.md` (steps 2.1 to 2.6), every step, in this session. Do not pause between steps. Stop only under rule 4. Nothing from Section 3. Where this file and `PLAN.md` or the kickoff differ, this file wins. This file is already committed; do not edit it.

## Before step 2.1

- `CLAUDE.md` and the 2 remaining `PLAN.md` edits from 1.0b are handled outside this session. Never stage or commit `CLAUDE.md` or `PLAN.md` in this session. Stage files by explicit path, never with `git add -A` or `git add .`.
- The standing rules in the 1.0b `## Amendments` text apply whether or not that text is committed yet: instruction precedence, the `.venv` built from the lock file, the fresh-clone check at `%TEMP%\pcs2` with `--disable-socket` and no `-p socket`, and status naming.
- If a package needed here is missing from `requirements-lock.txt`, stop under rule 4. Do not install it unpinned.

## Amendments to steps 2.1 to 2.6

**2.1** `window_daily` uses `t - pd.DateOffset(months=months)` as the exclusive start. `condition_cov` computes eigenvalues with `np.linalg.eigvalsh` on the symmetrised matrix ½(S + S′), and cond = λ_max/λ_min. If λ_min ≤ 0, cond_before is recorded as `inf` and the same ridge formula applies, which makes λ_min + r > 0. cond_after is recomputed from the ridged matrix, not assumed. The returned matrix is symmetrised.

**2.2** The ddof rule, fixed, so the PyPortfolioOpt cross-check is achievable:

- `ddof` changes S only: S = Xm′Xm/(T − ddof).
- Everything built from S follows it (the variances, r̄, F, and every term that multiplies S).
- The raw sample moments inside π̂ and θ̂ always divide by T: Xm′Xm/T, (Xm²)′(Xm²)/T and (Xm³)′Xm/T.
- This is what PyPortfolioOpt 1.6.0 (locked) does with pandas' ddof = 1 S, and what the authors' covCor.m does with ddof 0.

Test data for both cross-checks: the real daily window at 2010-04-30, plus one synthetic Gaussian panel (T = 100, N = 18, seed `run.seed_master`, a random positive definite covariance). Tolerances:

- Matrices: `np.allclose(ours, ref, rtol=1e-10, atol=0)`.
- Shrinkage constants: absolute 1e-10.

`cov_lw_identity` uses the ddof 0 empirical covariance, as sklearn does. Call PyPortfolioOpt as `CovarianceShrinkage(X, returns_data=True, frequency=1).ledoit_wolf("constant_correlation")` and read `.delta`.

**2.3** k = 0 is the most recent row, the row dated t. The λ = 1e-12 test compares against the outer product of that row.

**2.4** No change.

**2.5** `test_monthly_is_daily_times_21_exactly` compares the matrix before `condition_cov` with 21 × the daily estimator output using `==` on every entry. `estimate_cov` returns the conditioned matrix, and its log dict also carries `lw_delta` (NaN for the other estimators).

**2.6** Fixed details:

- Holding-period daily returns are the rows with date in (exec_date, next_exec_date], with fixed weights and no drift.
- σ̂²_h = w′Σw × n_hold_days/21, using the conditioned Σ.
- For the `random` set, QLIKE and r_h/σ̂_h are computed per portfolio. The date-level QLIKE is the mean over the 100 portfolios. The bias ratio for `random` is the mean of the 100 per-portfolio bias ratios.
- The QLIKE difference is per date: QLIKE_est − QLIKE_lw_cc on the same portfolio set. The bootstrap mean difference comes from `stationary_bootstrap_indices(196, 6, 10000, run.bootstrap_seed)`. `cov_eval_qlike_diff.csv` has 9 rows (3 estimators × 3 sets). `lw_cc` is the base and is not listed.
- `stationary_bootstrap_indices` algorithm, fixed: `rng = default_rng(seed)`. For each replication, in order, index 0 is `rng.integers(n)`. For j ≥ 1, draw `u = rng.random()`. If u < 1/mean_block, the index is `rng.integers(n)`; otherwise it is (previous + 1) mod n. The output is an int64 array, reps × n.
- Two extra outputs, so the reviewer can recompute from raw rows:
  - `outputs/tables/cov_eval_by_date.csv`: decision_date, estimator, portfolio_set, sigma2_hat, sigma2_realised, r_h, qlike. The `random` set appears only as date-level means.
  - `outputs/tables/cov_diagnostics.csv`: decision_date, estimator, cond_before, cond_after, ridge, lw_delta. 784 rows.

All CSVs use `float_format="%.10g"`, `index=False` and `lineterminator="\n"`.

## Review file evidence (in addition to `PLAN.md`)

1. Max abs and max relative differences against PyPortfolioOpt and sklearn, for both test panels.
2. The 50 δ values with their dates, and δ summarised over all 196 dates (min, median, max).
3. From `cov_diagnostics.csv`: per estimator, the count of ridged dates and the max `cond_before`, plus every ridged row in full.
4. `cov_eval.csv` (12 rows) and `cov_eval_qlike_diff.csv` (9 rows) in full.
5. For `ew` × `lw_cc`: the first and last 5 rows of `cov_eval_by_date.csv`, and for 2020-03-31 the forecast and realised variance worked by hand from the raw daily returns.
6. The first 3 replications × first 20 indices of `stationary_bootstrap_indices(196, 6, 10000, run.bootstrap_seed)`.
7. Runtime of step 2.6.
8. Fresh-clone output under the standing rule.

Status file: `instructions/02_section_2.status.md`, per rule 11. Then push and stop.
