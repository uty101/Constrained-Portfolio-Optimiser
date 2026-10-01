# Open decisions

## 5. Step 4.2: `test_no_look_ahead` part (b) cannot hold once a strategy is ruined by the perturbation (rule 4 stop)

Amendment 4.2.9(b) multiplies every price dated after t (t = 2010-06-30, the 3rd decision date) by Uniform(0.5, 1.5) factors, seed `run.seed_master`, and asserts that the weights at t of the specs that do not use w_prev are unchanged. The holding period of the previous decision (2010-05-28) runs from 2010-06-01 to 2010-07-01. It ends after t, so the perturbation changes that realised return. `mv_unconstrained|sample|sample|A` holds 39.9 gross leverage in that period, and its return becomes −458.4% (unperturbed: +4.7%). Amendment 4.2.8 then marks it ruined and does not solve it at t, so it has no weights at t to compare. No input used at t changed; the strategy stopped because of a realised return. Part (a) passes.

A second, smaller point: the amendment calls the compared specs "the 6 specs", but excluding the 2 `mv_constrained` specs and `black_litterman` from the 8 leaves 5. The test currently asserts 5.

- Option 1: part (b) compares only specs that are solved at t in both runs. It also asserts that every spec not solved at t in the perturbed run was ruined by a holding period whose `next_exec_date` is after t, which shows the stop came from a realised return and not from the information set.
- Option 2: part (b) checks the information set directly instead of through the wealth path. For each of the 5 specs, μ, Σ and the allocator output at t are computed with `DateInputs` from the perturbed and unperturbed prices, passing the same w_prev (None), and must be equal with `==`. The engine-level comparison stays in part (a) only.
