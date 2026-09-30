# instructions/03_section_3.md — Session 3: Section 3 (allocators)

Section 2 is approved (through `fa3962c`). The reviewer ran the suite on Linux (43 passed). It then recomputed from the raw prices, without calling `pc`, using its own covCor.m-style Ledoit-Wolf:

- the `ew` rows of `cov_eval_by_date.csv` for `sample`, `lw_cc` and `ewma` at all 196 dates;
- the `lw_cc` δ at all 196 dates;
- the first 3 bootstrap index paths.

δ matches to 5e-12, the forecast variances to 5e-10 relative (the `%.10g` rounding), the bias ratios and mean QLIKE to every printed digit, and the bootstrap paths exactly.

Build Section 3 of `PLAN.md` (steps 3.1 to 3.7) after step 3.0 below, every step, in this session. Do not pause between steps. Stop only under rule 4. Nothing from Section 4. Where this file and `PLAN.md` or the kickoff differ, this file wins. This file is already committed; do not edit it. Stage files by explicit path; never stage `CLAUDE.md` or `PLAN.md`.

---

## Step 3.0 — one commit: `section 3: reviewer decisions for section 2`

Text and config only.

**a.** Create `decisions/section_2_review.md` and record:

1. **Open decision 3: option 1 confirmed.** `np.quantile(boot, ci)` with the default linear interpolation (type 7), here and in step 4.4. The 2 rules differ by at most 1e-4 on the 9 rows. Move the item out of `decisions/OPEN.md`, which is then empty.
2. **`BAND_Z = 1.645` literal: accepted.** It is part of the kickoff 5.6 formula, not a tunable parameter. Add convention 22 to `docs/CONVENTIONS_RESOLVED.md`: *"Constants written inside a formula in the kickoff or an instruction file (1.645 in 5.6, the 1e-6 in the τ relaxation, the 1e-12 lower bound in risk parity, Uniform(0.5, 1.5) in the look-ahead test) may be literals, each with a comment citing where the formula is written. Every other number comes from `config.toml`."*
3. **No ridge fired on real data** (max cond 82,458): noted. Section 5.4 is where conditioning is expected to bite, on 36 monthly returns.
4. **Test tolerances set where `PLAN.md` gave none**, and helpers not in kickoff Section 6: accepted as listed in `review/section_2.md` Deviations 1, 3, 5, 6.

**b.** `config.toml`, `[solver]`: add `clarabel_tol = 1e-12`, and the matching field in `SolverConfig`. Every CLARABEL call passes `tol_gap_abs`, `tol_gap_rel` and `tol_feas` all equal to it. The reason is measured: at CLARABEL's defaults, set B solved with and without the zero-cost |w − w_prev| term differs by up to 4.3e-6 on the real Σ at the 5 dates of step 3.5, well past the 1e-7 in step 3.4. At 1e-10 it is still 3.2e-6. At 1e-12 it is 3.3e-8 with every status `optimal`.

---

## Amendments to steps 3.1 to 3.7

**General, all allocators.**

- `mu`, `w_prev` and `Sigma` must share the ticker index in config order. On a mismatch, raise `ValueError`; never reorder silently.
- `w_prev = None` means the first period (kickoff 4.4): no turnover constraint and no cost term.
- If the solver fails and `w_prev` is None, the allocator returns 1/N with `fallback = True` and the status string.
- `AllocResult.objective` is the objective value in monthly units, including the cost term where there is one. For allocators with no objective (risk parity, HRP, equal weight) it is NaN.

**3.1**

- The feasibility LP runs through `pc/solver.py` with the same solver policy.
- `test_fallback_returns_w_prev_on_solver_failure` forces failure by monkeypatching the cvxpy solve to report a non-optimal status. It covers both branches: w_prev given, and w_prev None.
- CLARABEL `optimal_inaccurate` counts as not optimal, as the kickoff says. Every fallback and every SCS retry is counted in the result fields, so Section 4 can report them.

**3.3** Formulations are fixed:

- `min_variance` minimises `cp.quad_form(w, Sigma)` with Σ symmetrised.
- The budget-only closed-form test calls `min_variance` with `Constraints(lower=None, upper=None)`.
- The set A mean-variance cvxpy reference in `test_mv_unconstrained_matches_cvxpy_budget_only` lives in the test file only, not in `pc/`.

**3.4**

- Formulation: maximise `mu @ w - gamma/2 * cp.quad_form(w, Sigma) - cost @ cp.abs(w - w_prev)`. The turnover constraint is `cp.norm1(w - w_prev) <= tau_eff`, and `turnover_dual` is that constraint's `dual_value`.
- With `cost` None and `max_turnover` None, the |w − w_prev| term and the constraint are still built with cost 0 when `w_prev` is given, so `test_mv_constrained_no_tau_no_cost_equals_set_b` compares 2 different formulations. It uses the real Σ at the 5 dates of 3.5 with `sample`, and μ = `mu_sample` at each date, to 1e-7.
- `test_mv_constrained_kkt_stationarity` is on the smooth set B problem (cost 0, no turnover): μ − γΣw − ν1 + λ_lo − λ_hi = 0 from cvxpy's duals of the budget and bound constraints, max abs residual < 1e-6, on the real Σ at 2016-06-30. The kinked problem is covered by the binding and slack tests, not by a KKT test.
- Evidence reports `turnover_dual` × 100 as bp of monthly return per 1% of turnover.

**3.5** No change. The reviewer checked that L-BFGS-B at the configured tolerances reaches 1.5e-8 on all 20 cases, so 1e-6 has room.

**3.6** `test_hrp_matches_pypfopt` runs on the real daily window at 2010-04-30 and at 2020-02-28. Our `hrp` receives `X.cov()` only and derives ρ from it; PyPortfolioOpt receives `returns=X`. If the 2 quasi-diagonal orders differ at any date, that is a rule 4 stop, reported with both orders. Do not change the tolerance or the dates.

**3.7**

- **Momentum window, fixed** (the kickoff's "t−12 to t−1" is read as the standard 12-1): the 11 monthly returns with month-end dates in (t − 12 months, t − 1 month]. The ranking uses the compounded total return over those 11 months. Q uses the mean monthly excess return over the same 11 months. `test_momentum_window_is_11_months_skipping_t` asserts the exact 11 month-ends at 2010-04-30 (2009-05-29 to 2010-03-31).
- Ω uses τΣ with Σ the conditioned monthly covariance passed in.
- Evidence adds `bl_posterior` at 2020-02-28, and φ at the 5 dates of 3.5.

---

## Review file evidence (in addition to `PLAN.md`)

1. The `clarabel_tol` effect: the max abs difference in `test_mv_constrained_no_tau_no_cost_equals_set_b` across its 5 dates.
2. The count of SCS retries and fallbacks across every test that solves on real data (expected 0).
3. Every allocator's weights at 2016-06-30 with `lw_cc` (μ = `mu_sample`), side by side in one table, each column's weight sum on the last row. For `mv_unconstrained`, also the gross leverage Σ|w|.
4. Pct risk contributions at 2016-06-30 for the same allocators.
5. Fresh-clone output under the standing rule.

Status file: `instructions/03_section_3.status.md`, per rule 11. Then push and stop.
