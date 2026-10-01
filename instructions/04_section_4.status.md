# Status: session 4 (instructions/04_section_4.md)

## Outcome

Stopped under rule 4 at step 4.2. Step 4.0 (a, b, c) and step 4.1 are complete. Step 4.2's engine is built, and the full 26-strategy, 196-date run completes in 81.8 s. But `test_no_look_ahead` part (b), as specified in amendment 4.2.9, fails, and rule 5 forbids rewriting it. Steps 4.3 to 4.6 were not started. The suite gives 210 passed and 1 failed, both in the repo and in the fresh clone at `%TEMP%\pcs4`.

## Last step reached

Step 4.2 (`d72f7c5`), then open decision 5 (`29170e1`) and the review file (`ad5cc43`).

## Reason for the stop

Part (b) perturbs every price dated after t = 2010-06-30. The previous decision's holding period (2010-06-01 to 2010-07-01) ends after t, so the perturbation changes that realised return. `mv_unconstrained|sample|sample|A`, at 39.9 gross leverage, goes from +4.7% to −458.4% and is ruined. Under amendment 4.2.8 it is then not solved at t, so it has no weights at t to compare. No input used at t changed, so this is not look-ahead. Part (a) passes in full. The evidence is in `review/section_4.md` under "Rule 4 stop".

## Questions and blockers for the reviewer

1. **Open decision 5 (`decisions/OPEN.md`).** How part (b) of `test_no_look_ahead` should treat a spec that the perturbation ruins before t. Two options are given:
   - Compare only specs solved at t in both runs, and assert that any dropped spec was ruined by a holding period ending after t.
   - Check the information set directly through `DateInputs` and the allocator at t.
2. **The amendment says "the 6 specs" for part (b).** Excluding the 2 `mv_constrained` specs and `black_litterman` from 8 leaves 5. The test asserts 5.
3. **Step 4.2 choices to confirm** (review Deviations 1):
   - First period `weights_long`: `w_prev_drifted` and `trade` are NaN and `cost_i` is 0.
   - Post-ruin months are kept in `periods` with NaN fields, `ruined = True` and `status = "not_solved"`, and have no `weights_long` rows.
4. **Three of the four set A strategies are ruined on real data.** They are `sample` at 2026-02-27, `ewma` at 2013-04-30 and `pca3` at 2026-02-27, with `mv_unconstrained|sample|sample|A` gross leverage between 26.7 and 129.2. Nothing is truncated: amendment 4.2.8 applies as written.
5. **Risk parity did not converge in 1 month each for `ewma` and `pca3`** (`rp_converged = False`). There are 0 fallbacks and 0 ridged months in all 26 strategies. SCS retries number 53 to 148 per set C strategy.
6. **`outputs/results/*.parquet` are not committed**, because step 4.2 is incomplete.
7. `CLAUDE.md` and `PLAN.md` were not staged or committed, as instructed.

## git log origin/main --oneline -3

```
ad5cc43 section 4: review file (stopped under rule 4 at step 4.2)
29170e1 section 4: open decision 5 (look-ahead part b and the ruin rule)
d72f7c5 step 4.2: walk-forward engine (stopped under rule 4: test_no_look_ahead part b)
```
