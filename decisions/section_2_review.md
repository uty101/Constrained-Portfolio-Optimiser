# Section 2 review decisions

From `instructions/03_section_3.md`, step 3.0.

1. **Open decision 3: option 1 confirmed.** A bootstrap percentile is `np.quantile(boot, ci)` with numpy's default linear interpolation (Hyndman-Fan type 7), in step 2.6 and in step 4.4. The 2 rules differ by at most 1e-4 on the 9 rows of `cov_eval_qlike_diff.csv`. The item is moved out of `decisions/OPEN.md`, which is now empty.
2. **`BAND_Z = 1.645` literal: accepted.** It is part of the kickoff 5.6 formula, not a tunable parameter. Recorded as convention 22 in `docs/CONVENTIONS_RESOLVED.md`.
3. **No ridge fired on real data** (max cond 82,458): noted. Section 5.4 is where conditioning is expected to bite, on 36 monthly returns.
4. **Test tolerances set where `PLAN.md` gave none, and helpers not in kickoff Section 6:** accepted as listed in `review/section_2.md` Deviations 1, 3, 5, 6.

## Config added

`[solver] clarabel_tol = 1e-12`, with the matching field in `SolverConfig`. Every CLARABEL call passes `tol_gap_abs`, `tol_gap_rel` and `tol_feas` all equal to it. Reason, measured by the reviewer: at CLARABEL's defaults, set B solved with and without the zero-cost |w − w_prev| term differs by up to 4.3e-6 on the real Σ at the 5 dates of step 3.5, well past the 1e-7 in step 3.4. At 1e-10 it is still 3.2e-6. At 1e-12 it is 3.3e-8 with every status `optimal`.
