# Section 4 review decisions (session 4)

From `instructions/04b_section_4_completion.md`, step 4.2 completion.

1. **Open decision 5: option 2.** Part (b) of `test_no_look_ahead` checks the information set directly, not the wealth path. The engine-level comparison stays in part (a).
   - Reason: the ruin rule makes the wealth path at t depend on the previous decision's holding return, whose period ends at exec_date(t), 1 trading day after t. That is realised P&L, not information used to choose weights.
   - Part (b) compares, with `==`, for the perturbed and unperturbed prices: every Σ (all 4 estimators) and `mu_sample` from `DateInputs` at t; μ_BS; Black-Litterman's Π, P, Q, μ_BL and Σ_BL for `lw_cc`; and the allocator outputs at t for the 5 specs that do not use w_prev, called with w_prev = None.
   - The count is 5, not 6. The reviewer's "6" was a miscount.
   - The item is moved out of `decisions/OPEN.md`, which is now empty.
2. **First-period `weights_long`:** confirmed. `w_prev_drifted` and `trade` are NaN, and `cost_i` is 0.
3. **Post-ruin months:** confirmed. They are kept in `periods` with NaN fields, `ruined = True` and `status = "not_solved"`, and have no `weights_long` rows.
4. **3 of 4 set A strategies ruined:** a result, not a defect. In session 4's run:

   | strategy | ruin month |
   |---|---|
   | `mv_unconstrained|sample|sample|A` | 2026-02-27 |
   | `mv_unconstrained|ewma|sample|A` | 2013-04-30 |
   | `mv_unconstrained|pca3|sample|A` | 2026-02-27 |

   `mv_unconstrained|sample|sample|A` gross leverage ranges from 26.7 to 129.2. `mv_unconstrained|lw_cc|sample|A` is not ruined.
5. **`rp_converged = False` months:** the flag is kept. A column `rp_max_rc_dev` is added to `periods.parquet`: max |pct RC − 1/N| for risk parity rows, NaN for the others.
6. **SCS retries:** the policy is unchanged. The reviewer instrumented all 267 SCS retries in `mv_constrained|lw_cc|bayes_stein|C` and `black_litterman|ewma|bl|C`. In each one, CLARABEL returned `optimal_inaccurate` both at the 1e-12 tolerance and at its own defaults. Against CLARABEL's inaccurate solution, the SCS weights differ by 8.7e-8 at worst (median 6e-11) and the objectives by 8e-9.
