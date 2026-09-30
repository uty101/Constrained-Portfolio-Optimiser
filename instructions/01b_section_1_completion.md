# instructions/01b_section_1_completion.md — Session 1b: finish Section 1

Section 1 steps 1.1 to 1.5 are approved as built (`cd30b4f` to `dc80e08`). The reviewer cloned the repo on Linux, ran the suite with sockets disabled (18 passed) and recomputed the rf series, the calendar, all 232 monthly excess returns and all 196 holding returns from the raw CSVs without calling `pc`. Every value matched exactly (holding rf to 1.1e-15).

This session does 3 things, in order: step 1.0b (decisions and housekeeping, text and config only), step 1.6, then the review, fresh-clone and status files. Nothing from Section 2. Where this file and `PLAN.md` or the kickoff differ, this file wins. This file is already committed; do not edit it.

---

## Step 1.0b — one commit: `section 1: reviewer decisions and housekeeping`

### a. `decisions/OPEN.md` → resolved

Move both open items to a new file `decisions/section_1_review.md` with the decision and reason below, then leave `OPEN.md` empty.

1. **Annualisation in step 1.6: option 1, geometric.** ann_return = (Π(1 + r_d))^(D/n) − 1, ann_vol = std(r_d, ddof=1) × √D, D = 12 × `sample.days_per_month` (252), n the number of daily returns. This matches the geometric annual return in kickoff 5.8, so the data summary and the backtest tables use the same convention.
2. **"d − 1" in the rf rule: option 1 confirmed, as built.** rf accrues from one trading close to the next, and the rate that applies over that period is the one known at its start, the previous trading day. A Good Friday or Hurricane Sandy print falls inside an accrual period rather than starting one. The difference is 4 days of 4,888 at 1 to 4 bp.

Also record the reviewer's acceptance of these session 1 additions: `.gitattributes`, `tests/conftest.py`, `pc.data.write_data_issues`, 252 computed as 12 × `sample.days_per_month` (no new config key), and every implicit behaviour in review Deviations item 7. rf is NaN only on 2007-04-11, the panel start. No monthly excess return, holding return or holding rf uses that day, and `monthly_excess_returns` has 0 NaN over 232 rows. It stays NaN and the FRED pull is not rerun.

### b. `decisions/section_0_review.md` (new)

Answers to the session 0 questions still open (`instructions/00_kickoff.status.md`):

- **3b, step 2.2, the 50 random windows:** seed `run.seed_master`; `default_rng(seed).choice(196, size=50, replace=False)` over the calendar's decision dates in order; each window is `window_daily(returns_d, t, 36)`.
- **3c, step 3.5, the 5 dates:** 2010-04-30, 2012-12-31, 2016-06-30, 2020-02-28, 2026-07-31, each with all 4 estimators through `estimate_cov`. The test runs 20 cases.
- **3d, step 3.6, the hand-worked 4-asset HRP example:** tickers A, B, C, D with monthly vols 0.04, 0.05, 0.02, 0.03 and correlations ρ_AB = 0.8, ρ_CD = 0.6, ρ_AC = 0.1, ρ_AD = 0.2, ρ_BC = 0.15, ρ_BD = 0.1. Single linkage orders them A, B, C, D, and the first bisection splits {A, B} from {C, D}. The docstring writes out the derivation: the 2 inverse-variance cluster variances, α, then each pair split by inverse variance. The reviewer's independent values, which the test asserts to 1e-12, are:
  - V₁ = 0.0017370612730517548, V₂ = 0.0004302958579881656, α = 0.198534820046803
  - w_A = 0.12105781710170915, w_B = 0.07747700294509384, w_C = 0.5548605091983672, w_D = 0.24660467075482986
- **3e, step 4.2, the no-look-ahead factor:** seed `run.seed_master`, one factor per ticker per date after t, drawn from Uniform(0.5, 1.5).
- **4, names introduced by `PLAN.md`:** all confirmed. `black_litterman(mu, Sigma, w_prev, cons) -> AllocResult` in `pc/allocators.py` is a thin wrapper that calls `mv_constrained` unchanged. The backtest computes μ_BL and Σ_BL in its return-model stage and passes them in as `mu` and `Sigma`. Add this as convention 21 in `docs/CONVENTIONS_RESOLVED.md`.
- **5, `stationary_bootstrap_indices` built at step 2.6:** accepted.
- **6, setuptools backend and removing the placeholder test at 7.5:** accepted.
- **1, 2, 7:** accepted as done in session 0.

Write each decision into `PLAN.md` in place of its **[open: ...]** marker, so no marker is left.

### c. `.gitattributes`: keep the existing line, and add above it

```
* text=auto eol=lf
*.png binary
*.parquet binary
```

Without the first line, CSV and Markdown outputs are stored in whatever line endings the writing machine uses, and rule 9 (byte-identical outputs) only holds on one machine.

### d. Lock file

From the working `.venv`, write `.venv\Scripts\python -m pip freeze --exclude-editable > requirements-lock.txt` and commit it. From now on every environment, fresh clones included, installs with `pip install -r requirements-lock.txt` then `pip install -e . --no-deps`. An unpinned reinstall can change numbers between sessions without any code changing.

### e. `CLAUDE.md`: append a section `## Amendments` with these standing rules, verbatim

1. **Instruction precedence.** An instruction file overrides `PLAN.md` and the kickoff where they differ. Decisions are written into `PLAN.md` when an instruction file says so.
2. **Environment.** Python is not on PATH on this machine. Build `.venv` with `uv venv --seed --python 3.11 .venv`, then `.venv\Scripts\python -m pip install -r requirements-lock.txt` and `.venv\Scripts\python -m pip install -e . --no-deps`. A dependency that fails to install is a rule 4 stop.
3. **Fresh-clone check (replaces the command in rule 12).** Clone into a short path (`%TEMP%\pcsN`, N the session number) because of the Windows 260-character path limit. Build `.venv` there as in amendment 2 and run `.venv\Scripts\python -m pytest --disable-socket -q`. `-p socket` is dropped because the plugin already loads from its entry point, and loading it twice caused the warning in session 1. Paste the full output, then delete the folder.
4. **Status file naming.** A session whose instruction file is `instructions/NN_<name>.md` writes `instructions/NN_<name>.status.md`. `instructions/01_section_1.status.md` stays under its current name as the record of session 1.

---

## Step 1.6 — as in `PLAN.md`, with the decision above

`outputs/tables/data_summary.csv` columns: ticker, first_date, last_date, n_days, ann_return, ann_vol, worst_day, worst_date, best_day, best_date. n_days is the number of daily returns. worst_day and best_day are the minimum and maximum daily simple return, and worst_date and best_date are the dates they occurred. `outputs/tables/corr_full_sample.csv` has a first column `ticker` then the 18 tickers, correlation of daily returns over the full panel. Both are written with `float_format="%.10g"`, `index=False` and `lineterminator="\n"`.

Tests in `tests/test_data.py`:

- `test_data_summary_columns_and_rows`: 18 rows, exact columns, config order.
- `test_data_summary_annualisation`: on a synthetic 3-day series with returns 0.01, −0.02, 0.03 and D = 252, assert ann_return = (1.01 × 0.98 × 1.03)^(252/3) − 1 and ann_vol = std([0.01, −0.02, 0.03], ddof=1) × √252, both to 1e-12.
- `test_corr_full_sample_symmetric_unit_diagonal`.

---

## Review file and status

Update `review/section_1.md` in place rather than writing a second file. Add a subsection `### Session 1b` holding:

- the commits
- `data_summary.csv` and `corr_full_sample.csv` in full via `to_string()`
- the full test output
- the fresh-clone output under amendment 3, installed from the lock file
- `requirements-lock.txt` lines for numpy, pandas, scipy, cvxpy, clarabel, yfinance, PyPortfolioOpt, scikit-learn and pytest
- `git ls-files --eol` output for `data/raw/*`, `outputs/tables/*` and `PLAN.md`

Status file: `instructions/01b_section_1_completion.status.md`, per rule 11. Then push and stop.
