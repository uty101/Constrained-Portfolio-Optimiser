# instructions/04b_section_4_completion.md — Session 4b: finish Section 4

The stop was right, and it was caused by the reviewer's test spec, not by the engine. Steps 4.0, 4.1 and the engine in 4.2 are approved (through `9ce9717`). What the reviewer checked:

- **Equal weight, independently.** The reviewer re-ran `equal_weight|none|none|none` over all 196 months with its own loop on the raw prices (its own calendar, drift and costs). `ret_net` matches the engine to 2.2e-16.
- **Reconciliation at 2010-06-30.** It adds up line by line.
- **The step 4.0.c window fix.** It moved nothing by more than 5e-4, with no sign flips.
- **SCS retries.** Every set C solve that fell back to SCS in `mv_constrained|lw_cc|bayes_stein|C` and `black_litterman|ewma|bl|C` was instrumented, 267 in all. In each one, CLARABEL returned `optimal_inaccurate` at the 1e-12 tolerance and also at its own defaults. The SCS weights agree with CLARABEL's inaccurate solution to 8.7e-8 at worst (median 6e-11), and the objectives to 8e-9. The retries cost no accuracy that matters, so the solver policy stays as built.
- **Risk parity, `ewma` at 2010-08-31.** scipy reports ABNORMAL (line search) there, but the pct risk contributions sit within 4.5e-9 of 1/N. On the reviewer's Linux run, `pca3` converged in every month, so this flag can differ across platforms.

This session finishes step 4.2 and runs steps 4.3 to 4.6. Every amendment in `instructions/04_section_4.md` still applies, except where this file changes it. Do not pause between steps. Stop only under rule 4. Nothing from Section 5. Where this file differs from `04_section_4.md`, `PLAN.md` or the kickoff, this file wins. This file is already committed; do not edit it. Stage files by explicit path; never stage `CLAUDE.md` or `PLAN.md`.

---

## Step 4.2 completion

### a. `decisions/section_4_review.md` (commit: `section 4: reviewer decisions, open decision 5`)

1. **Open decision 5: option 2.** Part (b) of `test_no_look_ahead` checks the information set directly, not the wealth path. The engine-level comparison stays in part (a).
   - Reason: the ruin rule makes the wealth path at t depend on the previous decision's holding return, whose period ends at exec_date(t), 1 trading day after t. That is realised P&L, not information used to choose weights.
   - Part (b) compares, with `==`, for the perturbed and unperturbed prices: every Σ (all 4 estimators) and `mu_sample` from `DateInputs` at t; μ_BS; Black-Litterman's Π, P, Q, μ_BL and Σ_BL for `lw_cc`; and the allocator outputs at t for the 5 specs that do not use w_prev, called with w_prev = None.
   - The count is 5, not 6. The reviewer's "6" was a miscount.
   - Clear `decisions/OPEN.md`.
2. **Review Deviations 1, first-period `weights_long`:** confirmed (`w_prev_drifted` and `trade` NaN, `cost_i` 0).
3. **Review Deviations 1, post-ruin months:** confirmed (kept in `periods` with NaN fields, `ruined = True`, `status = "not_solved"`, and no `weights_long` rows).
4. **3 of 4 set A strategies ruined:** a result, not a defect. Record which strategies, the ruin months and the leverage range, as given in the status file.
5. **`rp_converged = False` months:** keep the flag. Add a column `rp_max_rc_dev` to `periods.parquet`: max |pct RC − 1/N| for risk parity rows, NaN for the others. Evidence prints it for every non-converged month.
6. **SCS retries:** policy unchanged, for the reason given above. Record the reviewer's measurement.

### b. Test and engine (commit: `step 4.2: look-ahead part (b) on the information set, rp_max_rc_dev`)

- Rewrite part (b) of `test_no_look_ahead` as in item 1.
- Add `rp_max_rc_dev`.
- Run the full 26-strategy, 196-date walk forward and commit `outputs/results/weights_long.parquet` and `outputs/results/periods.parquet`.
- The suite must pass in full before step 4.3.

## Steps 4.3 to 4.6

As in `PLAN.md`, with the amendments in `04_section_4.md` (4.3 extra columns, 4.5 vol parts, 4.6 chart rules). One commit per step.

---

## Review file

Update `review/section_4.md` in place. Add a subsection `### Session 4b` holding:

1. The rewritten part (b) and its output.
2. Evidence items 2, 3, 4, 5, 6 and 7 from `04_section_4.md` for the final run. Items already printed in session 4 may be replaced by the final run's version; say which.
3. `rp_max_rc_dev` for every `rp_converged = False` month.
4. Chart 1 and Chart 2, embedded as image links to `outputs/figures/`, with the text box contents for Chart 1 printed as text.
5. Runtime per step.
6. The fresh-clone output under the standing rule.

Status file: `instructions/04b_section_4_completion.status.md`, per rule 11. Then push and stop.
