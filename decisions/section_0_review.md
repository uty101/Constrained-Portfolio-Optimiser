# Section 0 review decisions

From `instructions/01b_section_1_completion.md`. Answers to the questions left open in `instructions/00_kickoff.status.md`.

- **3b, step 2.2, the 50 random windows.** Seed `run.seed_master`; `default_rng(seed).choice(196, size=50, replace=False)` over the calendar's decision dates in order; each window is `window_daily(returns_d, t, 36)`.
- **3c, step 3.5, the 5 dates.** 2010-04-30, 2012-12-31, 2016-06-30, 2020-02-28, 2026-07-31, each with all 4 estimators through `estimate_cov`. The test runs 20 cases.
- **3d, step 3.6, the hand-worked 4-asset HRP example.** Tickers A, B, C, D with monthly vols 0.04, 0.05, 0.02, 0.03 and correlations ρ_AB = 0.8, ρ_CD = 0.6, ρ_AC = 0.1, ρ_AD = 0.2, ρ_BC = 0.15, ρ_BD = 0.1. Single linkage orders them A, B, C, D, and the first bisection splits {A, B} from {C, D}. The docstring writes out the derivation: the 2 inverse-variance cluster variances, α, then each pair split by inverse variance. The reviewer's independent values, which the test asserts to 1e-12:
  - V₁ = 0.0017370612730517548, V₂ = 0.0004302958579881656, α = 0.198534820046803
  - w_A = 0.12105781710170915, w_B = 0.07747700294509384, w_C = 0.5548605091983672, w_D = 0.24660467075482986
- **3e, step 4.2, the no-look-ahead factor.** Seed `run.seed_master`, one factor per ticker per date after t, drawn from Uniform(0.5, 1.5).
- **4, names introduced by `PLAN.md`.** All confirmed. `black_litterman(mu, Sigma, w_prev, cons) -> AllocResult` in `pc/allocators.py` is a thin wrapper that calls `mv_constrained` unchanged. The backtest computes μ_BL and Σ_BL in its return-model stage and passes them in as `mu` and `Sigma` (convention 21 in `docs/CONVENTIONS_RESOLVED.md`).
- **5, `stationary_bootstrap_indices` built at step 2.6.** Accepted.
- **6, setuptools backend and removing the placeholder test at 7.5.** Accepted.
- **1, 2, 7.** Accepted as done in session 0.
