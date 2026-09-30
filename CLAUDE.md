# CLAUDE.md

Sections 0, 4 and 6 of `instructions/00_kickoff.md`, verbatim. The kickoff document and `PLAN.md` are the specification.

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
