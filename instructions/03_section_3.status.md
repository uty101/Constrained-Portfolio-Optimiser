# Status: session 3 (instructions/03_section_3.md)

## Outcome

Completed. Step 3.0 and every step of Section 3, 3.1 to 3.7, are built and committed. 204 tests pass in the repo and in the fresh clone at `%TEMP%\pcs3`. The HRP cross-check against PyPortfolioOpt matches to 1.1e-16 at 2010-04-30 and 2020-02-28, with identical quasi-diagonal orders. Across the 220 solves on real data in the suite there are 0 SCS retries and 0 fallbacks.

## Last step reached

Step 3.7 (`bb7defa`), then open decision 4 (`5aa4f29`) and the review file (`80863ec`).

## Reason for any stop

None. No rule 4 stop.

## Questions and blockers for the reviewer

1. **Open decision 4 (`decisions/OPEN.md`): which ticker is short when two tie at the bottom boundary of the momentum view.** Implemented as option 1: one ranking, highest first, ties by config order, so the later ticker is short. Option 2: the earlier ticker is short. The two readings agree at the top boundary. No tie occurs on the real data, so this changes only `test_momentum_views_ties_by_config_order`.
2. **Allocators read `[solver]` from the repo's `config.toml`** through `pc.solver.solver_config()`, because the fixed allocator signature carries no Config (review Deviations 2). Please confirm.
3. **Solver bookkeeping** (review Deviations 3). `AllocResult.solver` lists every solver called in the allocator call, joined by "+": for example `CLARABEL+CLARABEL` for the LP and then the QP. The SCS retry count is `solver.count("SCS")`. Section 4's `periods.parquet` `solver` column will carry these strings. Please confirm the format.
4. **risk_parity when L-BFGS-B reports failure** (review Deviations 4). The status is scipy's message and `fallback` stays False. It never happened on the 20 test cases.
5. **`mu_sample` was built at step 3.3, not 3.7,** because the 3.3 and 3.4 tests need it (review Deviations 1).
6. **Test inputs and tolerances I set** where the instruction file and `PLAN.md` give none are in review Deviations 7 and 8. Among them: w_prev = 1/N in the zero-cost-term test, which gives a max difference of 1.2e-10 where the reviewer measured 3.3e-8, and all 4 estimators in the KKT test.
7. **The first fresh-clone pytest run took 24 minutes** (204 passed). A rerun in the same clone took 12.5 s, and no test takes more than 0.7 s. The cause looks environmental (a new venv on its first run) and was not investigated further.
8. `CLAUDE.md` and `PLAN.md` were not staged or committed, as instructed.

## git log origin/main --oneline -3

```
80863ec section 3: review file
5aa4f29 section 3: open decision 4 (momentum tie at the short boundary)
bb7defa step 3.7: Bayes-Stein, Black-Litterman views and posterior, equal weight
```
