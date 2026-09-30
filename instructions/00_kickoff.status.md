# Status: session 0 (instructions/00_kickoff.md)

## Outcome

Completed. Plan and scaffolding only. No estimator code, no allocator code, no data pulled, no packages installed into the repo.

## Last step reached

Step 0.0, plan and scaffolding. Files written: `PLAN.md`, `CLAUDE.md` (kickoff Sections 0, 4 and 6 verbatim), `config.toml`, `review/TEMPLATE.md`, `decisions/OPEN.md` (empty), `decisions/{universe,timing,costs,bl_prior_and_views,covariance_frequency}.md`, `docs/CONVENTIONS_RESOLVED.md` (items 1 to 20), `pyproject.toml`, `.gitignore` (replaced entirely), `README.md`, `pc/__init__.py`, `tests/test_placeholder.py`, and `.gitkeep` in `data/raw`, `data/processed`, `outputs/results`, `outputs/tables`, `outputs/figures`, `review`, `examples`. `CLAUDE_LOG.md` has its final entry and is retired. `Project Outline/03_Portfolio_Optimiser.docx` is unchanged.

Checks run: `config.toml` parses with `tomllib`; 18 tickers; |Σ w_mkt − 1| < 1e-12; `one_way_bp` has 18 entries. Placeholder test, run in a throwaway uv environment (Python is not on PATH on this machine, so `uv run --no-project --python 3.11 --with pytest -- python -m pytest -q`):

```
.                                                                        [100%]
1 passed in 0.02s
```

## Reason for any stop

None.

## Questions and blockers for the reviewer

1. **Two step 0.0 commits.** The `.gitignore` specified in item 7 contains `data/processed/**`, which also ignores the `data/processed/.gitkeep` item 7 requires. The first commit (`59a7469`) therefore missed it. Rather than amend, I force-added it in a second commit, `33bf7c3 step 0.0: track data/processed/.gitkeep past its ignore rule`. The ignore rule is unchanged.
2. **Where the gaps below were recorded.** Item 5 says `decisions/OPEN.md` is created empty, and rule 1 says unspecified points go there. I kept it empty and listed the gaps here and inline in `PLAN.md` as **[open: ...]**. If they should be in `OPEN.md`, say so and the next session will move them there, 2 options each.
3. **Unspecified points in the kickoff** (none blocks Section 1 except 3a, which blocks only step 1.6):
   - a. Step 1.6 `data_summary.csv`: annualisation for ann_return and ann_vol. Option 1: geometric, 252 days, (Π(1+r))^(252/n) − 1 and std×√252. Option 2: arithmetic, mean×252 and std×√252.
   - b. Step 2.2, "50 random windows from the real data": which seed key and how the window end dates are drawn. Option 1: `seed_master`, 50 decision dates drawn without replacement from the 196. Option 2: `seed_master`, 50 end dates drawn from all trading days with a full 36-month window.
   - c. Step 3.5, "real Σ at 5 dates": which dates and which estimator. Option 1: `lw_cc` at the 3 sensitivity dates plus the first and last decision dates. Option 2: `sample` at 5 evenly spaced decision dates.
   - d. Step 3.6, the hand-worked 4-asset HRP example: the input covariance is not given. Option 1: the reviewer supplies a 4×4 Σ in the Section 3 instruction file. Option 2: the session chooses one and writes the hand calculation in the docstring for review.
   - e. Step 4.2 no-look-ahead test: seed key for the random price factor. Option 1: `seed_master`. Option 2: a new `[run]` key (would change `config.toml`, so needs your approval).
4. **Names `PLAN.md` fixes that the kickoff does not.** Please confirm or change these: modules `pc/charts.py` (4.6 and the Chart 3 and 4 code), `pc/sensitivity.py` (5.1), `pc/experiments.py` (5.2 to 5.5); a `StrategySpec` dataclass in `pc/backtest.py` with fields allocator, cov, mu_model, cons_set, id; the `black_litterman` allocator function in `pc/allocators.py` (it is in Section 5.3's allocator list but not in the Section 6 signatures); the data summary function in `pc/data.py`; every test file and test name.
5. **Order dependency.** Step 2.6 needs the stationary block bootstrap of kickoff 5.8 for QLIKE difference intervals. `PLAN.md` builds `stationary_bootstrap_indices` in `pc/stats.py` at step 2.6, and step 4.4 reuses it. Confirm that is acceptable, since it puts a Section 4 file into Section 2.
6. **Additions to confirm.** `pyproject.toml` uses the setuptools build backend with `packages = ["pc"]` (the kickoff names no backend). Step 7.5 in `PLAN.md` removes `tests/test_placeholder.py` as part of the tidy.
7. **Push count.** Rule 11 needs the `origin/main` log in this file, so the step commits were pushed first and this file is a second push.

## git log origin/main --oneline -3

```
33bf7c3 step 0.0: track data/processed/.gitkeep past its ignore rule
59a7469 step 0.0: plan and scaffolding
d26dd00 00: instructions
```
