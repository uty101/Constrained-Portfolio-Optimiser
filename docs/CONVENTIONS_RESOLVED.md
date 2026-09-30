# Conventions resolved

Each convention below is fixed by `instructions/00_kickoff.md`. Where it differs from the source doc (`Project Outline/03_Portfolio_Optimiser.docx`), this list wins.

1. **Information set.** Everything used at decision date t (means, covariances, views, momentum) uses prices dated ≤ t only.
2. **Execution at t+1 close.** Target weights trade at the close of the next trading day after t. Executing at the decision close would use that close twice.
3. **Drifted w_prev.** At each execution date, w_prev is the previous target drifted by each asset's gross return from the previous execution close to this one, renormalised to sum to 1. Turnover, cost and the turnover constraint all use it.
4. **First period.** At the first decision date there is no w_prev: the target is solved with no turnover constraint and no cost term, and no cost or turnover is recorded.
5. **Turnover.** turnover = Σ_i |w_i − w_prev_i|, two-way, as a fraction of the fund. The limit τ applies to this quantity.
6. **Cost model.** cost = Σ_i c_i |w_i − w_prev_i|, c_i the one-way cost in decimals (3 bp or 6 bp per ticker, `config.toml`), charged at execution before the holding return. Net holding return = (1 − cost)(1 + gross) − 1.
7. **Monthly units.** All optimisation inputs are monthly decimals. Daily covariances are scaled by 21. Cost is a per-rebalance decimal, consistent with monthly units.
8. **Risk-free.** Daily rf on trading day d = DGS3MO(d−1)/100/252, forward filled across FRED gaps. Monthly and holding-period rf are compounded daily rf.
9. **No financing on shorts.** Short positions in unconstrained mean-variance carry no financing cost. The fund is fully invested; rf is used only for excess returns and the Sharpe ratio.
10. **Ruin rule.** If a strategy's net monthly return is ≤ −100%, its wealth path stops there, it is flagged `ruined = True`, and its metrics cover the months before ruin with the flag shown.
11. **Position threshold.** A position is held if |w_i| ≥ 0.005.
12. **EWMA λ on daily data.** λ = 0.97 is the RiskMetrics monthly decay, applied here to daily returns (half-life about 23 trading days).
13. **Ledoit-Wolf ddof.** `cov_lw_cc` uses ddof 0 (S = Xm′Xm/T, as in the authors' covCor.m) in production. ddof 1 exists only for the PyPortfolioOpt cross-check test.
14. **HRP linkage.** Single linkage is applied to the distance matrix d directly (the PyPortfolioOpt convention), not to the Euclidean distance between columns of d.
15. **Ridge rule.** If cond(Σ) > 1e6, add r·I with r = max(0, (λ_max − 1e6·λ_min)/(1e6 − 1)), which sets cond to exactly 1e6. Condition number before and after, and r, are logged for every call. Applied to every Σ before any allocator sees it.
16. **Solver fallback and hold rule.** cvxpy with CLARABEL; on any status other than optimal, one retry with SCS (eps 1e-9). If SCS is not optimal, the allocator returns drifted w_prev with `fallback = True` and the status string.
17. **τ feasibility relaxation.** Before solving set C, τ_min = min ‖w − w_prev‖₁ s.t. 1′w = 1, 0 ≤ w ≤ 0.30. If τ_min > τ, the solve uses τ_eff = τ_min + 1e-6 and records `tau_relaxed = True` and τ_eff.
18. **BL covariance.** The Black-Litterman allocator optimises on μ_BL with Σ_BL. The round-trip test (mean-variance on (Π, Σ) with γ = δ returns w_mkt) uses Σ, not Σ_BL.
19. **Two output tables.** The source doc asked for one long DataFrame. `weights_long.parquet` (per asset) and `periods.parquet` (per period), keyed by (strategy_id, decision_date), replace it because per-asset and per-period fields do not share a grain.
20. **Package layout.** The package is named `pc`; the CLI lives in `pc/cli.py` (console script `pctrade`), not a top-level `cli.py`.
21. **Black-Litterman allocator.** `black_litterman(mu, Sigma, w_prev, cons) -> AllocResult` in `pc/allocators.py` is a thin wrapper that calls `mv_constrained` unchanged. The backtest computes μ_BL and Σ_BL in its return-model stage and passes them in as `mu` and `Sigma`.
