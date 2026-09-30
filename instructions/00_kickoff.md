# instructions/00_kickoff.md — Session 0 instructions for Claude Code

Repo: https://github.com/uty101/Constrained-Portfolio-Optimiser (at commit 7678a9b: `Project Outline/03_Portfolio_Optimiser.docx`, `.gitignore`, `CLAUDE_LOG.md`)
Project: Constrained Portfolio Optimiser and Trade Generator (quant project 3 of the home-built series)

This document is the specification. Nothing in it is yours to redesign. Where it corrects or tightens the source project doc (03_Portfolio_Optimiser.docx), this document wins.

---

## 0. How this repo is run

Session 0 (this session) writes the plan and scaffolding only: no estimator code, no allocator code, no data pulls. After session 0, session number equals section number: Session N builds all of Section N of `PLAN.md`, every step in it, in one session, and nothing from any other section. A reviewer (Claude in chat) reads the repo once per section and either approves it or returns fixes. You never start the next section until a new session tells you to.

Rules that hold for every session:

1. **No design choices.** Every parameter, definition, signature, schema, convention and file path is fixed in this document or in `PLAN.md`. If something is genuinely unspecified, append it to `decisions/OPEN.md` with 2 concrete options, finish every other step in the section that does not depend on it, and report it in the review file. Do not pick an option yourself.
2. **Commits.** One commit per step, message `step X.Y: <one line>`, on `main`. Push once at the end of the section. Never force push, never rewrite history, never amend a pushed commit.
3. **One review file per section**: `review/section_N.md`, following `review/TEMPLATE.md` exactly.
4. **Stop conditions.** Stop the section, write the review and status files, and push if any of these happen: a data pull fails; a test from an earlier section fails; a cross-check against a reference library fails its stated tolerance; a result can only be produced by making a design choice; a step would need a file or function outside that section's scope. Do not work around any of them.
5. **Tests are fixed.** Never loosen a tolerance, skip, xfail, or rewrite a test so that it passes. If a test in this document is wrong, stop under rule 4 and say why.
6. **Config is fixed.** Every parameter lives in `config.toml`. No numeric parameter is hard-coded in `pc/`. Do not change a value set in this document.
7. **Tests build what they read.** No test may depend on `outputs/` or `data/processed/` already existing. Tests read only `data/raw/` (committed) or synthetic data they generate. The full suite runs offline: `pytest -p socket --disable-socket` must pass.
8. **No network outside `scripts/pull_data.py`.** Nothing in `pc/` or `tests/` touches the network.
9. **Determinism.** Every random draw uses `numpy.random.default_rng(seed)` with a seed from `config.toml`. Running the same section twice produces byte-identical CSV outputs.
10. **Evidence, not summaries.** Every numeric claim in a review file is backed by raw rows printed with `DataFrame.to_string()`, never by a description of them.
11. **Instructions and status live in the repo.** Every session's instructions are a file committed to `instructions/` before the session starts: `instructions/00_kickoff.md` (this document), then `instructions/NN_<name>.md` for each later session. The session prompt only names the file. Read that file from the repo and follow it; never edit an instruction file. Reviewer comments on a finished section arrive the same way, inside the next instruction file. Every session ends by writing `instructions/NN_<name>.status.md` with: outcome (completed or stopped), the last step reached, the reason for any stop, every question or blocker for the reviewer, and the output of `git log origin/main --oneline -3`; then commit and push it and stop. Then wait: do not start any further work until a new session names a new instruction file. This applies to sessions that stop early or hit rule 4: the status file is always written and always pushed. Nothing is relayed by chat.
12. **Fresh-clone check at the end of every section from Section 1 on.** Clone the pushed repo into a temp folder, `pip install -e ".[dev]"`, run `pytest -p socket --disable-socket -q`, and paste the full output into the review file.

---

## 1. What the project answers

1. How much of the in-sample gap between allocators survives out of sample once estimation error is included?
2. What does a turnover limit cost in ex-ante expected return, and what does it save in realised trading cost, as a function of the limit?
3. How sensitive are mean-variance weights to sampling noise in expected returns, and do Bayes-Stein shrinkage of the mean or Black-Litterman reduce that sensitivity in practice?
4. Which covariance estimator (sample, Ledoit-Wolf constant correlation, EWMA, 3-factor PCA) gives the best out-of-sample risk forecast, scored by QLIKE and bias ratio?

The expected answer is the textbook one: estimation error in means dominates; minimum variance and risk parity beat unconstrained mean-variance out of sample most of the time; constraints act as shrinkage. The project quantifies it with intervals, and ships a trade-generation CLI on top.

---

## 2. Corrections to the source doc (already applied below)

1. The doc says 5 allocators and lists 6. There are 6 allocators plus equal weight as the benchmark.
2. The doc never defines expected returns. Fixed: trailing 36-month mean of monthly excess returns (Section 5.1 below), with Bayes-Stein and Black-Litterman as the two alternatives.
3. sklearn's `LedoitWolf` shrinks to a scaled identity, not to constant correlation. The constant-correlation estimator is implemented by hand and cross-checked against PyPortfolioOpt.
4. λ = 0.97 is the RiskMetrics monthly decay. Covariances here are estimated on daily returns, so λ = 0.97 is applied to daily data (half-life about 23 trading days) and stated as such. The monthly-data version, where N = 18 against T = 36 makes the sample covariance close to singular, is run as a robustness test in Section 5.
5. ETF AUM from issuer pages is not point-in-time. Black-Litterman uses a fixed strategic prior (Section 5.4).
6. Execution at the same close as the decision uses the close twice. Trades execute at the close of the next trading day.
7. The turnover constraint and cost are measured against drifted weights, not last month's targets.
8. A turnover cap plus a position cap can be infeasible when a drifted weight sits above its cap. A fixed feasibility rule is added.
9. The universe is chosen so every ETF trades from the first day of the sample. No missing-asset handling is needed.

---

## 3. Universe and sample

18 US-listed ETFs, all trading before 2007-04-30:

| Class | Tickers |
|---|---|
| US equity | SPY, IWM |
| International equity | EFA, EEM |
| US sectors | XLE, XLF, XLK, XLU, XLV |
| Treasuries | SHY, IEF, TLT |
| Inflation linked | TIP |
| Credit | LQD, HYG |
| Real assets | GLD, DBC, VNQ |

Ticker order everywhere (columns, indexes, CSVs) is the order above, read from `config.toml`.

- Daily prices: yfinance, `auto_adjust=True` (dividend and split adjusted close), from 2007-04-11 to 2026-09-15 inclusive.
- Risk-free: FRED DGS3MO via `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS3MO` (no API key needed), same date range.
- Panel start: first trading day on which all 18 have a price (expected 2007-04-11, HYG's first day). Rows before it are dropped.
- Decision dates: last trading day of each month from 2010-04-30 to 2026-07-31 inclusive (196 dates). The first estimation window is the 36 months ending 2010-04-30.
- Execution date: the next trading day after each decision date.
- Holding period: from execution close to the next execution close. The last holding period ends at the first trading day of September 2026. 196 holding periods.

---

## 4. Timing, returns and costs (conventions)

1. **Information set.** Everything used at decision date `t` (means, covariances, views, momentum) uses prices with date ≤ `t` only.
2. **Execution.** Target weights are traded at the close of `exec_date = t + 1 trading day`. Cost is charged at execution, before the holding return.
3. **Drift.** `w_prev` at an execution date is the previous target drifted by each asset's gross return from the previous execution close to this execution close, renormalised to sum to 1. Turnover, cost and the turnover constraint all use `w_prev` drifted.
4. **First period.** At the first decision date there is no `w_prev`: the target is solved with no turnover constraint and no cost term, and no cost or turnover is recorded for it.
5. **Turnover.** `turnover = sum_i |w_i − w_prev_i|` (two-way, fraction of fund). The limit τ applies to this quantity.
6. **Cost.** `cost = sum_i c_i |w_i − w_prev_i|`, with `c_i` the one-way cost in decimals from `config.toml`: 3 bp for SPY, IWM, EFA, XLE, XLF, XLK, XLU, XLV, SHY, IEF, TLT, LQD, GLD; 6 bp for EEM, TIP, HYG, DBC, VNQ. Net holding return = `(1 − cost) × (1 + gross) − 1`.
7. **Units.** All optimisation inputs are monthly decimals: μ is a monthly mean excess return, Σ is a monthly covariance. Daily covariances are scaled by 21. Cost is a per-rebalance decimal, which is consistent with monthly units.
8. **Risk-free.** DGS3MO is an annualised percent yield. Daily rf on trading day d = `DGS3MO(d−1)/100/252`, forward filled across FRED gaps (FRED publishes blanks on bond holidays). Monthly rf for estimation = compounded daily rf over the month. Holding-period rf = compounded daily rf over the holding days.
9. **Excess returns.** Estimation uses calendar-month simple returns (month-end close to month-end close) minus monthly rf. The fund is fully invested; rf is used only for excess returns and the Sharpe ratio. Short positions in unconstrained mean-variance carry no financing cost; this is stated in the write-up.
10. **Ruin rule.** If any strategy's net monthly return is ≤ −100%, its wealth path stops at that month, the strategy is flagged `ruined = True`, and its metrics are reported over the months before ruin with the flag shown.
11. **Positions count.** A position is held if `|w_i| ≥ 0.005`.

---

## 5. Methods (fixed)

### 5.1 Expected return models (`pc/returns_model.py`)

- `sample`: μ̂ = mean of the 36 trailing monthly excess returns ending at `t`.
- `bayes_stein` (Jorion 1986): μ_BS = (1 − φ) μ̂ + φ μ₀ 1, where μ₀ = (1′Σ⁻¹μ̂)/(1′Σ⁻¹1), φ = (N + 2) / [(N + 2) + T (μ̂ − μ₀1)′ Σ⁻¹ (μ̂ − μ₀1)], T = 36, Σ the monthly Ledoit-Wolf covariance at `t`.
- `black_litterman`: Section 5.4.

### 5.2 Covariance estimators (`pc/cov.py`)

All four take the daily simple returns in the window `(t − 36 months, t]` and return a monthly covariance (daily × 21).

- `sample`: `np.cov(X, rowvar=False, ddof=1)`.
- `lw_cc`: Ledoit-Wolf 2004 shrinkage to constant correlation. S = Xm′Xm / T (ddof 0, as in the authors' covCor.m). F has F_ii = S_ii, F_ij = r̄ √(S_ii S_jj), r̄ the average off-diagonal sample correlation. δ* = max(0, min(1, (π̂ − ρ̂)/(γ̂ T))). π̂, ρ̂, γ̂ as in LW 2004 (π̂ = Σ_ij AsyVar of S_ij, ρ̂ = Σ_i π̂_ii + r̄ Σ_{i≠j} ½(√(S_jj/S_ii) θ̂_ii,ij + √(S_ii/S_jj) θ̂_jj,ij), γ̂ = ‖F − S‖²_F). Signature carries `ddof: int = 0`; `ddof = 1` exists only for the PyPortfolioOpt cross-check test.
- `lw_identity`: Ledoit-Wolf shrinkage to scaled identity, implemented by hand. Used only in a test against `sklearn.covariance.LedoitWolf`, not in the backtest.
- `ewma`: Σ = Σ_k w_k r_{t−k} r_{t−k}′ over the window, w_k = (1 − λ) λ^k / (1 − λ^n), λ = 0.97, n = rows in window, no demeaning.
- `pca3`: R = sample correlation; eigendecompose; R_f = V₃Λ₃V₃′ + diag(1 − diag(V₃Λ₃V₃′)); Σ = D R_f D with D = diag of sample vols. The factor count is 3.

Conditioning (`condition_cov`): if cond(Σ) > 1e6, add ridge r·I with r = max(0, (λ_max − 1e6·λ_min)/(1e6 − 1)), which sets cond to exactly 1e6. Log condition number before and after, and r, for every call. Applied to every Σ before any allocator sees it.

### 5.3 Allocators (`pc/allocators.py`, `pc/hrp.py`)

Uniform signature: `allocate(mu, Sigma, w_prev, cons) -> AllocResult`. Allocators that ignore μ accept it and do not read it.

Constraint sets (`Constraints` dataclass):

- **A** (budget only): 1′w = 1. Shorts and leverage allowed.
- **B** (long-only capped): 1′w = 1, 0 ≤ w ≤ 0.30.
- **C** (B plus trading): B, plus ‖w − w_prev‖₁ ≤ τ with τ = 0.30, plus cost term c′|w − w_prev| in the objective.

Allocators:

1. `mv_unconstrained` (set A): max μ′w − (γ/2) w′Σw s.t. 1′w = 1, γ = 2.5. Closed form: w = (1/γ) Σ⁻¹(μ − η1), η = (1′Σ⁻¹μ − γ)/(1′Σ⁻¹1). No solver.
2. `mv_constrained` (set C, or B when τ and costs are switched off): max μ′w − (γ/2) w′Σw − c′|w − w_prev|, γ = 2.5, via cvxpy. Report the dual value of the turnover constraint as `turnover_dual` (monthly return per unit of turnover; zero when the constraint is slack). Report it in the review as basis points of monthly return per 1% of turnover.
3. `min_variance` (set B): min w′Σw. Budget-only closed form Σ⁻¹1/(1′Σ⁻¹1) lives in `pc/risk.py` and is used by tests and by the covariance evaluation.
4. `risk_parity` (long-only, no caps): Spinu: minimise ½ x′Σx − Σ_i b_i log x_i over x > 0, b_i = 1/N, then w = x / 1′x. Solve with `scipy.optimize.minimize(method="L-BFGS-B")`, analytic gradient Σx − b/x, bounds (1e-12, None), start x₀ = 1/√diag(Σ), `ftol=1e-15, gtol=1e-12, maxiter=10000`.
5. `black_litterman` (set C): mean-variance on μ_BL with Σ_BL, same objective and constraints as `mv_constrained`.
6. `hrp` (long-only, no caps): López de Prado HRP written by hand. d_ij = √(clip((1 − ρ_ij)/2, 0, 1)); `scipy.cluster.hierarchy.linkage(squareform(d), "single")`; quasi-diagonal order from `to_tree(link).pre_order()`; recursive bisection splitting the ordered list in halves, inverse-variance weights within each half, α = 1 − V₁/(V₁ + V₂). Linkage is applied to d directly (the PyPortfolioOpt convention), not to the Euclidean distance between columns of d; this is written into `docs/CONVENTIONS_RESOLVED.md`.
7. `equal_weight`: 1/N every month, rebalanced back to 1/N, costs charged.

Solver policy (`pc/solver.py`): cvxpy with CLARABEL. On any status other than `optimal`, retry once with SCS (`eps=1e-9`). If SCS is not `optimal`, the allocator returns `w_prev` (drifted) with `fallback = True` and the status string. Every call records solver, status, fallback.

Feasibility rule for set C: before solving, compute τ_min = min ‖w − w_prev‖₁ s.t. 1′w = 1, 0 ≤ w ≤ 0.30 (a linear program). If τ_min > τ, solve with τ_eff = τ_min + 1e-6 and record `tau_relaxed = True` and τ_eff.

### 5.4 Black-Litterman (`pc/bl.py`)

- Strategic prior w_mkt (fixed, sums to exactly 1): SPY 0.19, IWM 0.04, EFA 0.12, EEM 0.05, XLE 0.02, XLF 0.02, XLK 0.02, XLU 0.02, XLV 0.02, SHY 0.05, IEF 0.09, TLT 0.08, TIP 0.04, LQD 0.08, HYG 0.04, GLD 0.04, DBC 0.03, VNQ 0.05. Equities 0.50, bonds 0.38, real assets 0.12.
- Π = δ Σ w_mkt, δ = 2.5.
- τ = 1/36.
- Views (mechanical, 12-1 momentum computed from monthly total returns over months t−12 to t−1, skipping month t):
  - View 1 (cross-sectional momentum): P row = +1/6 on the 6 highest-momentum tickers, −1/6 on the 6 lowest. Ties broken by ticker order in config. Q₁ = mean monthly excess return of the long 6 minus the short 6 over months t−12 to t−1.
  - View 2 (stocks against bonds): P row = +1/4 on SPY, IWM, EFA, EEM; −1/3 on SHY, IEF, TLT. Q₂ = the same basket difference in mean monthly excess return over months t−12 to t−1.
- Ω = diag(P τΣ P′).
- μ_BL = [(τΣ)⁻¹ + P′Ω⁻¹P]⁻¹ [(τΣ)⁻¹ Π + P′Ω⁻¹ Q]; Σ_BL = Σ + [(τΣ)⁻¹ + P′Ω⁻¹P]⁻¹. Computed with `np.linalg.solve`, never an explicit inverse of a matrix that is then multiplied.

### 5.5 Risk decomposition (`pc/risk.py`)

`risk_contributions(w, Sigma)` returns RC_i = w_i (Σw)_i / √(w′Σw) (sums to fund vol). `pct_risk_contributions` returns RC_i / √(w′Σw). These are the functions project 4 will import; keep them pure numpy/pandas with no dependency on the rest of `pc/`.

### 5.6 Covariance forecast evaluation (`pc/cov_eval.py`)

For every decision date and every estimator, on 3 portfolio sets held fixed over the holding period (no drift):

- `ew`: 1/N.
- `gmv`: budget-only closed-form minimum variance from that estimator (this portfolio exposes optimiser bias: it will under-forecast).
- `random`: 100 long-only portfolios drawn once from Dirichlet(1,…,1) with seed `cov_eval_seed`, the same 100 at every date.

Forecast variance for the holding period = w′Σw × (n_days / 21), n_days = trading days in the holding period. Realised variance = Σ_d (w′r_d)² over the holding days (no demeaning). Holding return r_h = Σ_d w′r_d.

- QLIKE = log σ̂² + σ²_realised / σ̂², averaged over dates (and over the 100 portfolios for `random`).
- Bias ratio = std(r_h / σ̂_h, ddof=1) over dates. Report the 90% band for a well-calibrated forecast, 1 ± 1.645 √(1/(2n)).
- QLIKE differences against `lw_cc`: stationary block bootstrap over dates (Section 5.8), 90% interval.

### 5.7 Walk-forward engine (`pc/backtest.py`)

Strategy id format: `<allocator>|<cov>|<mu_model>|<cons_set>`. Registry (26 strategies):

- `mv_unconstrained|{sample,lw_cc,ewma,pca3}|sample|A`
- `mv_constrained|{sample,lw_cc,ewma,pca3}|sample|C`
- `mv_constrained|lw_cc|bayes_stein|C`
- `min_variance|{sample,lw_cc,ewma,pca3}|none|B`
- `risk_parity|{sample,lw_cc,ewma,pca3}|none|none`
- `black_litterman|{sample,lw_cc,ewma,pca3}|bl|C`
- `hrp|{sample,lw_cc,ewma,pca3}|none|none`
- `equal_weight|none|none|none`

Primary table rows (from the source doc, fixed): `mv_unconstrained|sample|sample|A`, `mv_constrained|lw_cc|sample|C`, `min_variance|lw_cc|none|B`, `risk_parity|ewma|none|none`, `black_litterman|lw_cc|bl|C`, `hrp|sample|none|none`, `equal_weight|none|none|none`.

### 5.8 Statistics (`pc/stats.py`)

- Annualised return = (Π(1 + r_net))^(12/n) − 1. Annualised vol = std(r_net, ddof=1) × √12. Sharpe = mean(excess_net)/std(excess_net) × √12. Max drawdown on the net wealth path. Forecast/realised vol = mean ex-ante annualised vol ÷ realised annualised vol.
- Stationary block bootstrap (Politis-Romano), mean block length 6 months, 10,000 replications, seed `bootstrap_seed`. The same resampled index paths are used for every strategy so differences are paired. Report Sharpe 90% intervals per strategy and the Sharpe difference against `equal_weight` and against `min_variance|lw_cc|none|B`, with the fraction of replications at or below zero.

---

## 6. Signatures and schemas (fixed)

All DataFrames use a `DatetimeIndex` named `date` unless stated. All returns are simple decimals. Tickers are columns in config order.

```python
# pc/config.py
@dataclass(frozen=True)
class Config: ...                              # one field per config.toml key, nested dataclasses per table
def load_config(path: str | Path = "config.toml") -> Config

# pc/data.py
def load_prices(cfg: Config) -> pd.DataFrame           # daily adj close, trading days, 18 cols, no NaN from panel start
def load_rf_daily(cfg: Config, index: pd.DatetimeIndex) -> pd.Series   # name "rf", daily decimal, aligned to index
def validate_prices(prices: pd.DataFrame, cfg: Config) -> pd.DataFrame  # returns issues table: date, ticker, issue, value

# pc/calendar.py
def build_calendar(prices_index: pd.DatetimeIndex, cfg: Config) -> pd.DataFrame
#   columns: decision_date, exec_date, next_exec_date, n_hold_days; RangeIndex; 196 rows

# pc/returns.py
def daily_returns(prices: pd.DataFrame) -> pd.DataFrame
def monthly_excess_returns(prices: pd.DataFrame, rf_daily: pd.Series) -> pd.DataFrame   # month-end index
def holding_returns(prices: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame            # index decision_date, gross asset returns exec→next_exec
def holding_rf(rf_daily: pd.Series, cal: pd.DataFrame) -> pd.Series

# pc/cov.py
def window_daily(returns_d: pd.DataFrame, t: pd.Timestamp, months: int) -> pd.DataFrame
def cov_sample(X: pd.DataFrame) -> pd.DataFrame
def cov_lw_cc(X: pd.DataFrame, ddof: int = 0) -> tuple[pd.DataFrame, float]            # (Sigma daily, delta)
def cov_lw_identity(X: pd.DataFrame) -> tuple[pd.DataFrame, float]
def cov_ewma(X: pd.DataFrame, lam: float) -> pd.DataFrame
def cov_pca(X: pd.DataFrame, k: int) -> pd.DataFrame
def condition_cov(S: pd.DataFrame, max_cond: float) -> tuple[pd.DataFrame, dict]       # dict: cond_before, cond_after, ridge
def estimate_cov(returns_d: pd.DataFrame, t: pd.Timestamp, name: str, cfg: Config) -> tuple[pd.DataFrame, dict]  # monthly, conditioned

# pc/risk.py
def risk_contributions(w: pd.Series, Sigma: pd.DataFrame) -> pd.Series
def pct_risk_contributions(w: pd.Series, Sigma: pd.DataFrame) -> pd.Series
def gmv_closed_form(Sigma: pd.DataFrame) -> pd.Series

# pc/returns_model.py
def mu_sample(monthly_excess: pd.DataFrame, t: pd.Timestamp, months: int) -> pd.Series
def mu_bayes_stein(mu_hat: pd.Series, Sigma: pd.DataFrame, T: int) -> tuple[pd.Series, float]   # (mu, phi)

# pc/bl.py
def implied_returns(Sigma: pd.DataFrame, w_mkt: pd.Series, delta: float) -> pd.Series
def momentum_views(monthly_total: pd.DataFrame, monthly_excess: pd.DataFrame, t: pd.Timestamp, cfg: Config) -> tuple[pd.DataFrame, pd.Series]  # (P: views x tickers, Q)
def bl_posterior(Sigma, Pi, P, Q, tau) -> tuple[pd.Series, pd.DataFrame]              # (mu_BL, Sigma_BL)

# pc/allocators.py
@dataclass(frozen=True)
class Constraints:
    budget: float = 1.0
    lower: float | None = None        # None = unbounded
    upper: float | None = None
    max_turnover: float | None = None
    cost: pd.Series | None = None     # one-way decimal per ticker
    gamma: float = 2.5
@dataclass
class AllocResult:
    weights: pd.Series
    solver: str
    status: str
    fallback: bool
    objective: float
    turnover_dual: float              # NaN when no turnover constraint
    tau_relaxed: bool
    tau_eff: float                    # NaN when no turnover constraint
def mv_unconstrained(mu, Sigma, w_prev, cons) -> AllocResult
def mv_constrained(mu, Sigma, w_prev, cons) -> AllocResult
def min_variance(mu, Sigma, w_prev, cons) -> AllocResult
def risk_parity(mu, Sigma, w_prev, cons) -> AllocResult
def equal_weight(mu, Sigma, w_prev, cons) -> AllocResult
# pc/hrp.py
def hrp(mu, Sigma, w_prev, cons) -> AllocResult

# pc/backtest.py
def build_registry(cfg: Config) -> list[StrategySpec]                                  # 26 specs, ids as in 5.7
def run_walk_forward(specs, prices, rf_daily, cfg) -> tuple[pd.DataFrame, pd.DataFrame]  # (weights_long, periods)

# pc/stats.py
def strategy_metrics(periods: pd.DataFrame) -> pd.DataFrame
def stationary_bootstrap_indices(n: int, mean_block: float, reps: int, seed: int) -> np.ndarray   # reps x n
def sharpe_intervals(periods: pd.DataFrame, idx: np.ndarray, benchmarks: list[str]) -> pd.DataFrame

# pc/trades.py
def current_weights(positions: pd.DataFrame, cash: float) -> tuple[pd.Series, float]   # (weights incl. universe zeros, NAV)
def generate_trades(positions, cash, target_w, cfg, lot_size, min_notional) -> tuple[pd.DataFrame, dict]
```

Output schemas:

- `outputs/results/weights_long.parquet`: strategy_id, decision_date, exec_date, ticker, w_target, w_prev_drifted, trade, cost_i.
- `outputs/results/periods.parquet`: strategy_id, decision_date, exec_date, next_exec_date, ret_gross, cost, ret_net, rf_hold, excess_net, forecast_vol_ann, mu_exante (μ′w, monthly), turnover, n_positions, gross_leverage (Σ|w|), solver, status, fallback, turnover_dual, tau_relaxed, tau_eff, cond_before, cond_after, ridge, ruined.
- `outputs/tables/*.csv`: named per step in Section 8, written with `float_format="%.10g"`, index=False.
- `outputs/figures/*.png`: matplotlib, 150 dpi, one chart per file.

The source doc asked for one long DataFrame. Two tables keyed by (strategy_id, decision_date) replace it because per-asset and per-period fields do not share a grain. Record this in `docs/CONVENTIONS_RESOLVED.md`.

---

## 7. config.toml contents

Tables and keys (session 0 writes every one with the values stated in this document):

- `[run]` seed_master = 20260930, bootstrap_seed = 20260930, cov_eval_seed = 20260931, sensitivity_seed = 20260932
- `[universe]` tickers (ordered list of 18), asset_class (table ticker → class)
- `[sample]` price_start = "2007-04-11", price_end = "2026-09-15", first_decision = "2010-04-30", last_decision = "2026-07-31", window_months = 36, days_per_month = 21, expected_n_decisions = 196
- `[data]` prices_csv = "data/raw/prices_adjclose.csv", rf_csv = "data/raw/rf_dgs3mo.csv", manifest = "data/raw/MANIFEST.json", max_abs_daily_return_flag = 0.25, max_gap_days_flag = 4
- `[cov]` estimators = ["sample","lw_cc","ewma","pca3"], ewma_lambda = 0.97, pca_k = 3, max_cond = 1e6
- `[mv]` gamma = 2.5, upper = 0.30, lower = 0.0, max_turnover = 0.30
- `[costs]` one_way_bp (table ticker → 3 or 6), cost_scales = [0.0, 1.0, 3.0]
- `[bl]` delta = 2.5, tau = 0.0277777777777778 (1/36), w_mkt (table), mom_lookback = 12, mom_skip = 1, n_long_short = 6, equity_basket, bond_basket
- `[solver]` primary = "CLARABEL", fallback = "SCS", scs_eps = 1e-9, rp_ftol = 1e-15, rp_gtol = 1e-12, rp_maxiter = 10000
- `[cov_eval]` n_random = 100
- `[bootstrap]` mean_block = 6, reps = 10000, ci = [0.05, 0.95]
- `[sensitivity]` dates = ["2012-12-31","2020-02-28","2026-07-31"], draws = 1000
- `[turnover_grid]` taus = [0.05,0.10,0.20,0.30,0.50,0.75,1.00], include_none = true
- `[positions]` threshold = 0.005
- `[cli]` default_lot_size = 1, default_min_notional = 1000.0, price_warn_pct = 0.05
- `[outputs]` results_dir, tables_dir, figures_dir

A Section 1 test asserts every key in `config.toml` is a field of `Config` and every field of `Config` is a key in `config.toml`.

---

## 8. Section list (PLAN.md expands exactly these; add or remove nothing)

### Section 1 — Data, calendar and returns
- 1.1 `pc/config.py`: `Config` and `load_config`. Test: key set equality both ways; w_mkt sums to 1 within 1e-12; one_way_bp has exactly the 18 tickers.
- 1.2 `scripts/pull_data.py`: the only network code. Pulls the 18 tickers and DGS3MO for the configured range, writes `data/raw/prices_adjclose.csv` and `data/raw/rf_dgs3mo.csv`, and `data/raw/MANIFEST.json` (pull timestamp UTC, yfinance version, row counts, first and last date per ticker, sha256 per file). Run it once; commit the files. If yfinance or FRED fails, stop under rule 4; do not switch source. Test: manifest hashes match the committed files.
- 1.3 `pc/data.py`: loaders and `validate_prices`. Issues reported, never fixed: any |daily return| > 25%, any gap between trading days > 4 calendar days, any non-positive price, any duplicate date. Write `outputs/tables/data_issues.csv`.
- 1.4 `pc/calendar.py`. Tests: 196 rows; first decision 2010-04-30; last 2026-07-31; exec_date is always the next trading day; no decision date is a non-trading day.
- 1.5 `pc/returns.py`. Tests: compounding daily returns over a holding period equals the holding return to 1e-12; rf conversion on a synthetic constant 5% yield gives 0.05/252 per day; monthly excess return at a hand-picked month (2020-03) matches a manual calculation printed in the review.
- 1.6 `outputs/tables/data_summary.csv` (ticker, first_date, last_date, n_days, ann_return, ann_vol, worst_day, best_day) and `outputs/tables/corr_full_sample.csv`.

### Section 2 — Covariance estimators and forecast evaluation
- 2.1 `window_daily`, `cov_sample`, `condition_cov`. Tests: window boundaries (exclusive start, inclusive end) on a synthetic index; ridge brings a synthetic cond 1e9 matrix to 1e6 within 1e-6 relative.
- 2.2 `cov_lw_cc` and `cov_lw_identity`. Tests: `cov_lw_cc(X, ddof=1)` matches PyPortfolioOpt `CovarianceShrinkage(X, returns_data=True, frequency=1).ledoit_wolf("constant_correlation")` and its `delta` to 1e-10; `cov_lw_identity` matches `sklearn.covariance.LedoitWolf(assume_centered=False)` covariance and shrinkage to 1e-10; δ in [0,1] on 50 random windows from the real data.
- 2.3 `cov_ewma`. Tests: weights sum to 1; with λ → 0 limit (λ = 1e-12) equals the outer product of the last row.
- 2.4 `cov_pca`. Tests: unit diagonal of R_f; positive definite; with k = N equals the sample covariance to 1e-10.
- 2.5 `estimate_cov` and `gmv_closed_form` (in `pc/risk.py`). Test: monthly = daily × 21 exactly; conditioning log fields always present.
- 2.6 `pc/cov_eval.py` over all 196 dates. Writes `outputs/tables/cov_eval.csv` (estimator, portfolio_set, n, qlike_mean, bias_ratio, band_lo, band_hi, mean_cond_before, n_ridged) and `outputs/tables/cov_eval_qlike_diff.csv` (estimator, portfolio_set, diff_vs_lw_cc, p05, p95, frac_le_0). Review evidence: the 12 rows of cov_eval.csv and the first and last 5 dates of per-date QLIKE for `ew`.

### Section 3 — Allocators
- 3.1 `pc/solver.py`, `Constraints`, `AllocResult`, feasibility LP. Test: a synthetic case with a drifted weight of 0.45 against a 0.30 cap and τ = 0.05 sets `tau_relaxed = True` and τ_eff = 0.30 + 1e-6 within 1e-8.
- 3.2 `pc/risk.py` risk contributions. Tests: RC sums to fund vol to 1e-12; Euler identity w′∂σ/∂w = σ.
- 3.3 `mv_unconstrained`, `min_variance`. Tests: closed form matches cvxpy budget-only solution to 1e-7; budget-only min variance equals Σ⁻¹1/1′Σ⁻¹1 to 1e-7; set B solution respects bounds to 1e-9.
- 3.4 `mv_constrained`. Tests: with τ = None and cost = 0 it equals the set B solution to 1e-7; KKT stationarity residual < 1e-6 on a synthetic case; turnover_dual ≥ 0, and equal to 0 within 1e-8 when the constraint is slack; turnover never exceeds τ_eff + 1e-7.
- 3.5 `risk_parity`. Tests: pct risk contributions all within 1e-6 of 1/N on the real Σ at 5 dates; weights positive and sum to 1.
- 3.6 `hrp`. Tests: matches PyPortfolioOpt `HRPOpt(returns=X).optimize("single")` to 1e-10 when fed `X.cov()` and `X.corr()`; a hand-worked 4-asset example (written out in the test docstring) matches to 1e-12.
- 3.7 `pc/returns_model.py`, `pc/bl.py`, `equal_weight`. Tests: BL with no views returns Π exactly; set A mean-variance on (Π, Σ) with γ = δ returns w_mkt to 1e-8 (uses Σ, not Σ_BL); with Ω scaled by 1e-10 the posterior satisfies Pμ_BL = Q to 1e-6; Bayes-Stein φ in [0,1]; with μ̂ = constant vector φ-shrinkage leaves it unchanged.

### Section 4 — Walk-forward and headline results
- 4.1 `build_registry`. Test: 26 ids, exact strings.
- 4.2 `run_walk_forward`. Tests: a synthetic 3-asset, 5-period path with hand-computed wealth matches to 1e-12; drift test; **no look-ahead test**: multiplying every price after decision date t by a random factor leaves every weight at t unchanged.
- 4.3 `strategy_metrics` → `outputs/tables/metrics_all.csv` (26 rows).
- 4.4 Bootstrap → `outputs/tables/sharpe_intervals.csv`.
- 4.5 `outputs/tables/results_primary.csv`: the 7 primary rows with the source doc's columns (allocator, covariance, OOS ann. return, OOS vol, Sharpe with 90% interval, forecast/realised vol, monthly turnover, max DD, avg positions), plus solver fallbacks and ridged months.
- 4.6 Chart 1 `frontier_vs_oos.png`: in-sample frontiers (set A and set B) from the mean and sample covariance of the 196 holding-period excess returns of the 18 assets, with each primary strategy's realised (ann vol, ann return) plotted on the same axes. Chart 2 `weights_stacked.png`: two panels, `mv_constrained|lw_cc|sample|C` and `risk_parity|ewma|none|none`.

### Section 5 — Estimation error, turnover and robustness experiments
- 5.1 Sensitivity at the 3 configured dates: μ̃ = μ̂ + ε, ε ~ N(0, Σ_monthly/36) with Σ the LW monthly covariance, 1,000 draws, seed `sensitivity_seed`. Re-optimise `mv_unconstrained|sample` (set A), `mv_constrained|lw_cc` (set B, no turnover), `mv_constrained|lw_cc|bayes_stein` (set B), `black_litterman|lw_cc` (set B) with Q perturbed instead of μ̂: Q̃ = Q + ε_Q, ε_Q ~ N(0, P Σ P′/12), the sampling covariance of a 12-month mean. Min variance, risk parity and HRP shown as zero-dispersion references. Writes `outputs/tables/sensitivity.csv` (date, strategy, ticker, w_base, p05, p25, p50, p75, p95, iqr) and `sensitivity_summary.csv` (date, strategy, mean_abs_change, frac_top_asset_changes). Chart 3 `sensitivity_boxplots.png`, one panel per strategy, last date.
- 5.2 Turnover grid: rerun `mv_constrained|lw_cc|sample|C` for each τ in the grid plus no limit. Writes `outputs/tables/turnover_frontier.csv` (tau, mean_mu_exante, exante_return_given_up_bp_pa, mean_cost, cost_saved_bp_pa, realised_net_ann_return, mean_turnover, mean_dual_bp_per_pct, n_binding, n_relaxed). Chart 4 `turnover_frontier.png`: ex-ante return given up against cost saved, points labelled by τ.
- 5.3 Cost sensitivity: the 7 primary strategies at cost scales 0, 1, 3. `outputs/tables/cost_sensitivity.csv`.
- 5.4 N close to T: rebuild the sample covariance from 36 monthly returns at every date; report condition numbers and ridge counts against the daily version, and rerun `mv_unconstrained|sample` and `min_variance|sample` on it. `outputs/tables/monthly_cov_robustness.csv`.
- 5.5 `outputs/tables/answers.csv`: one row per research question (Section 1) holding the specific figures and interval that answer it, each with the source table and row it came from.

### Section 6 — Trade generator and CLI
- 6.1 `pc/trades.py` core. Positions file columns: ticker, quantity, price. Cash via `--cash` (default 0). NAV = Σ qty × price + cash. Target shares = target weight × NAV / price. Trade = target − current, rounded toward zero to the lot size (never overshoots). Trades with |notional| < min_notional are dropped. If post-trade cash < 0, reduce the largest buy by one lot at a time until cash ≥ 0. Errors (exit code 2): unknown ticker, negative quantity, non-positive price, duplicate ticker.
- 6.2 Trade list and summary. `trades.csv` columns: ticker, side (BUY/SELL), quantity, price, notional, est_cost, weight_before, weight_target, weight_after. Printed summary: NAV, turnover before and after rounding, total estimated cost in $ and bp of NAV, turnover shadow price (bp of monthly return per 1% turnover) when the allocator has a turnover constraint, residual cash, max |weight_after − weight_target|, and a warning line for every price that differs from the data store's last close by more than 5%.
- 6.3 `pc/cli.py`, console script `pctrade`. Flags: `--positions`, `--cash`, `--strategy` (a registry id, default `mv_constrained|lw_cc|sample|C`), `--asof` (decision date, default the last in the calendar), `--max-turnover`, `--lot-size`, `--min-notional`, `--out` (default `trades.csv`), `--dry-run` (print only, write nothing). `w_prev` is the current weights from the positions file, not the backtest's drifted weights.
- 6.4 Tests: round-trip on a synthetic book; rounding never overshoots; min notional filter; negative cash repair; every error path and exit code; `--dry-run` writes no file; `--max-turnover 0.05` yields turnover ≤ 0.05 + rounding slack reported.
- 6.5 `examples/positions_demo.csv` (a $10m book deliberately off target, with GLD at 0.40 so the cap binds), `examples/trades_demo.csv`, and `docs/cli_demo.md` with the exact command and full printed output.

### Section 7 — Write-up and reproducibility
- 7.1 `scripts/run_all.py`: regenerates every table and figure from `data/raw/`. Running it twice leaves `git status` clean.
- 7.2 `README.md`: what it is, the 4 answers with figures and intervals from `answers.csv`, the primary results table, the 4 charts with one callout each placed in the prose before the chart, the QLIKE table, how to run the CLI, and limitations. Figures shown in a table or chart are not restated in prose.
- 7.3 `docs/DESIGN_NOTE.md`: why each constraint exists on a portfolio implementation desk (mandate limits, liquidity, cost budgets, turnover budgets, lot sizes), 1 short paragraph each.
- 7.4 `docs/METHODS.md`: the maths in Section 5 of this document, with the corrections in Section 2.
- 7.5 Final fresh-clone run of `scripts/run_all.py` and the test suite with sockets disabled; tidy (no stray files, no TODOs, no unused functions).

Writing rules for README and docs: plain English, conversational but technical; numerals, not words, for numbers; no hyphens joining sentences; none of the words robust, resilient, rigorous, leveraging, grounded; no filler; the vehicle is called "the fund".

---

## 9. What session 0 must produce

This document is already committed as `instructions/00_kickoff.md`. If it is not, stop and say so in your reply; do not recreate it.

Existing files from commit 7678a9b: keep `Project Outline/03_Portfolio_Optimiser.docx` unchanged; it is the source doc, and this document overrides it where they differ. `CLAUDE_LOG.md` is retired: append one final entry dated today saying that from session 0 onward status lives in `instructions/NN_<name>.status.md` and review files in `review/`, and never write to it again. The existing `.gitignore` ignores `data/raw/`, which conflicts with rule 7 (raw snapshots are committed); replace it entirely with the `.gitignore` specified in item 7 below.

Write these files, commit as `step 0.0: plan and scaffolding`, then the status file, push, stop. No other files.

1. `PLAN.md`: Sections 1 to 7 from Section 8 above. For each step, one paragraph stating what is built, the file it lives in, the signatures from Section 6 it implements, the tests that prove it (file and test name), the output files it writes, and the review evidence to attach. Expand, do not summarise, and add or remove no step.
2. `CLAUDE.md`: Sections 0, 4 and 6 of this document verbatim.
3. `config.toml`: every key in Section 7 with the values in this document.
4. `review/TEMPLATE.md`, headings in this order: Section; Steps completed (one line each with commit hash); Evidence (one subsection per numeric claim, each with raw rows via `to_string()`); Tests run (exact command and full output); Fresh-clone check (full output); Runtime per step; Deviations from PLAN.md; Not verified; Open questions; Files changed; Reviewer reads (ordered, shortest sufficient set).
5. `decisions/OPEN.md` (empty). `decisions/universe.md`, `decisions/timing.md`, `decisions/costs.md`, `decisions/bl_prior_and_views.md`, `decisions/covariance_frequency.md`, each restating the decision in 5 lines or fewer.
6. `docs/CONVENTIONS_RESOLVED.md`, numbered: 1 information set ≤ t; 2 execution at t+1 close; 3 drifted w_prev; 4 first-period rule; 5 two-way turnover definition; 6 cost model; 7 monthly units and ×21 scaling; 8 rf conversion and forward fill; 9 no financing on shorts; 10 ruin rule; 11 position threshold 0.005; 12 λ = 0.97 on daily data; 13 LW ddof 0 in production, ddof 1 only for the cross-check; 14 HRP linkage on d directly; 15 ridge rule; 16 solver fallback and hold rule; 17 τ feasibility relaxation; 18 BL uses Σ_BL in the optimiser and Σ in the round-trip test; 19 two output tables instead of one long frame; 20 package name `pc`, CLI in `pc/cli.py` not a top-level `cli.py`.
7. `pyproject.toml` (Python ≥ 3.11; runtime: numpy, pandas, scipy, cvxpy with clarabel, matplotlib, pyarrow, yfinance; dev extra: pytest, pytest-socket, PyPortfolioOpt, scikit-learn; console script `pctrade = pc.cli:main`), `.gitignore` (`data/processed/**`, `.env`, `__pycache__/`, `*.py[cod]`, `.venv/`, `venv/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.ipynb_checkpoints/`, `*.egg-info/`, `.DS_Store`, `Thumbs.db`, `~$*`, `.vscode/`; `data/raw/` is not ignored), `README.md` with a 5-line description and "results pending", `pc/__init__.py`, `tests/test_placeholder.py` that passes, `.gitkeep` in `data/raw`, `data/processed`, `outputs/results`, `outputs/tables`, `outputs/figures`, `review`, `examples`.
8. `instructions/00_kickoff.status.md` per rule 11.

Do not install packages beyond what is needed to run the placeholder test. Do not pull data.
