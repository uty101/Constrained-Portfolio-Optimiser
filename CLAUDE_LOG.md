# Claude Code log

Running log of status, open questions and decisions, pushed with every commit so
Claude Desktop can review from GitHub. Newest entries at the top.

---

## 2026-09-30 — Repo set up

**Status:** Read `Project Outline/03_Portfolio_Optimiser.docx`. No code written yet;
waiting for instructions.

**Understanding of the project:** A constrained portfolio construction engine on
15–25 liquid multi-asset ETFs (daily prices from 2007, yfinance; risk-free from
FRED DGS3MO).

- 4 covariance estimators: sample, Ledoit-Wolf (constant-correlation target,
  implemented by hand once), EWMA λ=0.97, 3-factor PCA.
- Allocators, all `(mu, Sigma, w_prev, constraints) -> w`: unconstrained MV,
  constrained MV (bounds, L1 turnover, cost; cvxpy), min variance, risk parity
  (Spinu log-barrier), Black-Litterman (2–3 mechanical momentum views), HRP
  (by hand), plus an equal-weight benchmark.
- Walk-forward: 36-month estimation window, 1-month hold. One long DataFrame
  feeds every chart. Metrics: return, vol, Sharpe with bootstrap CIs, forecast
  vs realised vol (bias ratio, QLIKE), turnover, cost, max DD.
- Sensitivity: 1,000 perturbed μ draws at the estimate's standard error.
- CLI: `positions.csv` in, `trades.csv` out (side, qty, notional, cost), with
  round lots, a minimum trade notional, `--dry-run`, `--max-turnover`, and the
  turnover shadow price printed.
- Layout: `pc/{data,cov,allocators,backtest,trades}.py`, `cli.py`, `tests/`.
- Deliverables: results table, 4 charts plus a QLIKE table, a write-up, and a
  design note on why each constraint exists.

**Open questions:** none yet.
