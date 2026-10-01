# Review — Section 3: Allocators

## Section

3, Allocators (`PLAN.md` Section 3), run from `instructions/03_section_3.md`. Step 3.0 and every step 3.1 to 3.7 are built. No rule 4 stop. One new open item (decision 4, the momentum tie at the short boundary) is in `decisions/OPEN.md`; it is implemented as option 1 and no tie occurs on the real data.

## Steps completed

- 3.0 `9d7976c` `decisions/section_2_review.md`; open decision 3 moved out of `decisions/OPEN.md`; convention 22 in `docs/CONVENTIONS_RESOLVED.md`; `[solver] clarabel_tol = 1e-12` in `config.toml` and `SolverConfig`.
- 3.1 `9c4ef2a` `pc/solver.py` (solver policy, `turnover_feasibility`); `Constraints`, `AllocResult` and the shared result helpers in `pc/allocators.py`; `tests/test_solver.py`.
- 3.2 `c1ec937` `pc/risk.py`: `risk_contributions`, `pct_risk_contributions`; 3 tests in `tests/test_risk.py`.
- 3.3 `9cec9f0` `pc/allocators.py`: `mv_unconstrained`, `min_variance`; `pc/returns_model.py`: `mu_sample` (Deviations 1); the session `real` fixture in `tests/conftest.py`; `tests/test_allocators.py`.
- 3.4 `f8c0273` `pc/allocators.py`: `mv_problem`, `mv_constrained`; 5 tests in `tests/test_allocators.py`.
- 3.5 `9e9fbdf` `pc/allocators.py`: `risk_parity`; 2 tests in `tests/test_allocators.py`.
- 3.6 `13dc0d0` `pc/hrp.py`; `tests/test_hrp.py`.
- 3.7 `bb7defa` `pc/returns_model.py`: `mu_bayes_stein`; `pc/bl.py`; `pc/allocators.py`: `black_litterman`, `equal_weight`; `tests/test_bl.py`, `tests/test_returns_model.py`.
- `5aa4f29` `decisions/OPEN.md`: open decision 4.

## Evidence

All real-data evidence uses the conditioned monthly Σ from `estimate_cov` and μ = `mu_sample` (the 36 months ending at t). Costs are `costs.one_way_bp` / 1e4.

### Instruction evidence 1: the `clarabel_tol` effect in `test_mv_constrained_no_tau_no_cost_equals_set_b`

Σ `sample`, μ = `mu_sample`, at the 5 dates of step 3.5. "with" is `mv_constrained` with w_prev = 1/N, cost None and no τ, so the zero-cost |w − w_prev| term is built. "without" is the same call with w_prev = None, which is pure set B. The test tolerance is 1e-7.

```
== set B with vs without zero-cost |w - w_prev| term (sample, mu_sample, w_prev = 1/N)
      date  max_abs_diff status_with status_without solver_with solver_without
2010-04-30  7.554124e-11     optimal        optimal    CLARABEL       CLARABEL
2012-12-31  1.216725e-10     optimal        optimal    CLARABEL       CLARABEL
2016-06-30  4.000605e-11     optimal        optimal    CLARABEL       CLARABEL
2020-02-28  2.300782e-11     optimal        optimal    CLARABEL       CLARABEL
2026-07-31  4.441163e-11     optimal        optimal    CLARABEL       CLARABEL
max over 5 dates: 1.216725e-10
```

For contrast, the second table reruns the same comparison with CLARABEL at its default tolerances (no options passed). Only the `clarabel_tol = 1e-12` rows are what the code does.

```
             setting       date  max_abs_diff        statuses
   CLARABEL defaults 2010-04-30  7.532437e-07 optimal/optimal
   CLARABEL defaults 2012-12-31  1.215793e-06 optimal/optimal
   CLARABEL defaults 2016-06-30  3.998178e-07 optimal/optimal
   CLARABEL defaults 2020-02-28  2.300635e-07 optimal/optimal
   CLARABEL defaults 2026-07-31  4.438876e-07 optimal/optimal
clarabel_tol = 1e-12 2010-04-30  7.554124e-11 optimal/optimal
clarabel_tol = 1e-12 2012-12-31  1.216725e-10 optimal/optimal
clarabel_tol = 1e-12 2016-06-30  4.000605e-11 optimal/optimal
clarabel_tol = 1e-12 2020-02-28  2.300782e-11 optimal/optimal
clarabel_tol = 1e-12 2026-07-31  4.441163e-11 optimal/optimal
```

The max over the 5 dates is 1.22e-10 at `clarabel_tol = 1e-12` and 1.22e-6 at CLARABEL's defaults. Every status is `optimal`. The reviewer measured 3.3e-8 at 1e-12. The gap is presumably the w_prev, which the instruction file does not fix (mine is 1/N).

### Instruction evidence 2: SCS retries and fallbacks across every test that solves

Counted by wrapping `pc.solver.solve` in a throwaway pytest plugin (not committed) and running the full suite. The count covers every `pc.solver.solve` call, per test function, summed over parametrisations. `scs_retries` counts "SCS" in each record's solver list.

```
              file                                                 test  solves  scs_retries  fallbacks
test_allocators.py    test_budget_only_min_variance_matches_closed_form      20            0          0
test_allocators.py              test_min_variance_set_b_respects_bounds      20            0          0
test_allocators.py      test_mv_constrained_no_tau_no_cost_equals_set_b      10            0          0
test_allocators.py                 test_mv_constrained_kkt_stationarity       8            0          0
test_allocators.py   test_turnover_dual_nonnegative_and_zero_when_slack      20            0          0
test_allocators.py                  test_turnover_never_exceeds_tau_eff     140            0          0
test_allocators.py test_allocator_fallback_holds_w_prev_or_equal_weight       4            4          4
        test_bl.py  test_black_litterman_is_mv_constrained_on_posterior       2            0          0
    test_solver.py       test_tau_relaxed_when_drifted_weight_above_cap       1            0          0
    test_solver.py                   test_tau_not_relaxed_when_feasible       1            0          0
    test_solver.py       test_fallback_returns_w_prev_on_solver_failure       2            2          2
```

There were 0 SCS retries and 0 fallbacks across the 220 solves on real data and the 2 synthetic feasibility LPs. The only retries and fallbacks are the 6 solves in the 2 tests that force failure by monkeypatching `cvxpy.Problem.solve`. The set A cvxpy reference in `test_mv_unconstrained_matches_cvxpy_budget_only` calls CLARABEL directly, because it lives in the test file (amendment 3.3). It asserts `optimal` on all 20 cases.

### Instruction evidence 3: every allocator's weights at 2016-06-30, `lw_cc`, μ = `mu_sample`

w_prev = None (the first-period form), so `mv_constrained` and `black_litterman` solve set B, with no turnover constraint and no cost term. `black_litterman` receives μ_BL and Σ_BL from `bl_posterior` on the `lw_cc` Σ (convention 21). The last row of the weights table is each column's weight sum. The table below it gives solver, status, objective, ex-ante annualised vol √(12 w′Σw) and μ′w (monthly).

```
== weights at 2016-06-30, Sigma lw_cc, mu = mu_sample (black_litterman: mu_BL, Sigma_BL); w_prev = None
     mv_unconstrained  mv_constrained  min_variance  risk_parity        hrp  black_litterman  equal_weight
SPY        6.62351876      0.00000000    0.00000000   0.01959516 0.00212573       0.00000000    0.05555556
IWM       -1.65226198      0.00000000    0.00000000   0.01730797 0.00042777       0.00000000    0.05555556
EFA       -1.62833718      0.00000000    0.00000000   0.01698188 0.00081299       0.00000000    0.05555556
EEM       -1.91066171      0.00000000    0.00000000   0.01304416 0.00055740       0.00000000    0.05555556
XLE        0.43897883      0.00000000    0.00000000   0.01330343 0.00047000       0.00000000    0.05555556
XLF       -1.20827909      0.00000000    0.04857422   0.02036759 0.00144034       0.00000000    0.05555556
XLK        2.73731427      0.26198291    0.00801374   0.01983570 0.00372249       0.00000000    0.05555556
XLU        0.84530288      0.30000000    0.00000000   0.01853687 0.00129558       0.00000000    0.05555556
XLV        0.85426529      0.30000000    0.00000001   0.01974385 0.00047779       0.00000000    0.05555556
SHY      -10.33799240      0.00000000    0.30000000   0.50119523 0.92492482       0.00000000    0.05555556
IEF        7.08849979      0.00000000    0.29983951   0.07156203 0.00740010       0.30000000    0.05555556
TLT        0.22582449      0.13801709    0.00000000   0.04132059 0.00149975       0.30000000    0.05555556
TIP       -8.77129203      0.00000000    0.13440569   0.06065795 0.02582575       0.09923093    0.05555556
LQD        8.12229162      0.00000000    0.00000000   0.05493935 0.01537611       0.30000000    0.05555556
HYG        2.10648747      0.00000000    0.19585710   0.04018769 0.00763708       0.00000000    0.05555556
GLD        1.28597266      0.00000000    0.00000000   0.02947807 0.00324894       0.00076907    0.05555556
DBC       -3.23094228      0.00000000    0.01330974   0.02558757 0.00152281       0.00000000    0.05555556
VNQ       -0.58868939      0.00000000    0.00000000   0.01635493 0.00123454       0.00000000    0.05555556
sum        1.00000000      1.00000000    1.00000000   1.00000000 1.00000000       1.00000000    1.00000000
mv_unconstrained gross leverage sum|w| = 59.65691214
                       solver   status fallback     objective exante_vol_ann     mu_exante
mv_unconstrained  closed_form  optimal    False   0.095333857     0.95508829    0.19035403
mv_constrained       CLARABEL  optimal    False   0.011126129     0.10469543   0.012267914
min_variance         CLARABEL  optimal    False 7.1981344e-05    0.029390069  0.0025533017
risk_parity          L-BFGS-B  optimal    False           NaN    0.030357052   0.002677736
hrp                      none  optimal    False           NaN     0.01019783 0.00089809327
black_litterman      CLARABEL  optimal    False  0.0031002884    0.074789973  0.0057679022
equal_weight             none  optimal    False           NaN    0.079907975  0.0049111017
```

### Instruction evidence 4: pct risk contributions at 2016-06-30, same allocators

Every column uses the `lw_cc` Σ, `black_litterman` included (not Σ_BL). risk_parity is 1/18 = 0.0555… on every row. mv_unconstrained and hrp have negative contributions where an asset hedges the rest.

```
== pct risk contributions at 2016-06-30 under Sigma lw_cc (all columns, including black_litterman)
     mv_unconstrained  mv_constrained  min_variance  risk_parity         hrp  black_litterman  equal_weight
SPY        0.32281200      0.00000000    0.00000000   0.05555555 -0.00203172      -0.00000000    0.08348127
IWM       -0.05602430      0.00000000    0.00000000   0.05555555 -0.00049641      -0.00000000    0.09450381
EFA       -0.01755040      0.00000000    0.00000000   0.05555555 -0.00023521      -0.00000000    0.09382527
EEM        0.00726659      0.00000000    0.00000000   0.05555556  0.00061609      -0.00000000    0.11505813
XLE       -0.00160653      0.00000000    0.00000000   0.05555555 -0.00007403      -0.00000000    0.11744308
XLF       -0.04061040      0.00000000    0.06600844   0.05555556 -0.00458955      -0.00000000    0.08950466
XLK        0.16774846      0.30729781    0.01089003   0.05555556 -0.00429480      -0.00000000    0.08410525
XLU        0.05624049      0.31842527    0.00000000   0.05555556  0.00623846       0.00000000    0.06102103
XLV        0.05823014      0.38035205    0.00000001   0.05555555 -0.00036737      -0.00000000    0.08174814
SHY       -0.01816087     -0.00000000    0.04876382   0.05555556  0.75862311       0.00000000   -0.00002415
IEF        0.15076114     -0.00000000    0.40745041   0.05555556  0.03488220       0.22881053   -0.00196350
TLT        0.01053664     -0.00607513    0.00000000   0.05555555  0.01262035       0.51608241   -0.00983378
TIP       -0.07060410      0.00000000    0.18264646   0.05555555  0.10376203       0.05956012    0.00517927
LQD        0.20342517      0.00000000    0.00000000   0.05555555  0.06075999       0.19496938    0.00729773
HYG        0.02766877      0.00000000    0.26615397   0.05555556  0.00436752      -0.00000000    0.03430498
GLD        0.01651485     -0.00000000    0.00000000   0.05555556  0.02407223       0.00057756    0.01490919
DBC        0.21783020      0.00000000    0.01808686   0.05555556  0.00151955      -0.00000000    0.05314286
VNQ       -0.03447785      0.00000000    0.00000000   0.05555556  0.00462756       0.00000000    0.07629677
sum        1.00000000      1.00000000    1.00000000   1.00000000  1.00000000       1.00000000    1.00000000
```

### 3.1 Feasibility LP, synthetic

18 tickers in config order. The drifted w_prev has 0.45 in SPY and 0.55/17 in each other ticker. Bounds are 0 and 0.30 from `mv`, and τ = 0.05.

```
                         case  tau              tau_min           tau_eff  tau_eff_minus_0_300001  tau_relaxed   solver  status  fallback
SPY drifted to 0.45, cap 0.30 0.05    0.299999999999991 0.300000999999991   -8.77076189453874e-15         True CLARABEL optimal     False
                          1/N 0.05 4.85722573273506e-16              0.05                     NaN        False CLARABEL optimal     False
```

### 3.2 Risk contributions, synthetic

Σ = 1e-3 (AA′/18 + 0.1 I), A an 18 × 18 standard normal. w is long-short and sums to 1. Both are drawn from `default_rng(run.seed_master)`. `dsigma_dw` is the analytic gradient Σw/σ.

```
                  w              RC          pct_RC       dsigma_dw
SPY  1.623726210942  0.015798865385  0.141883411222  0.009730005760
IWM  0.606063639931 -0.000185285287 -0.001663974466 -0.000305719194
EFA -1.020523216406  0.004122052441  0.037018535654 -0.004039155969
EEM -0.548419675764  0.001920053067  0.017243243250 -0.003501065246
XLE  1.549519239689  0.039250145767  0.352490159041  0.025330531407
XLF  0.510139490037  0.010095704848  0.090665564113  0.019790086918
XLK -1.411433057799  0.009449440122  0.084861714179 -0.006694926175
XLU  0.138124748770  0.002058614786  0.018487611676  0.014904025556
XLV -0.519442679643  0.002981166877  0.026772690036 -0.005739164288
SHY  0.852428509574  0.003610982048  0.032428812973  0.004236111307
IEF -1.593707338151  0.011535748692  0.103598032864 -0.007238310583
TLT  0.317950047010  0.001519521349  0.013646225040  0.004779119750
TIP  0.442886443094 -0.001941560880 -0.017436396475 -0.004383879683
LQD  0.608659484473  0.004855586454  0.043606116819  0.007977508900
HYG -0.587361275266  0.000803409088  0.007215101796 -0.001367827812
GLD  0.553585635927  0.005791566095  0.052011782735  0.010461915410
DBC  0.334908498588  0.000043268241  0.000388575097  0.000129194217
VNQ -0.857104705006 -0.000358239184 -0.003217205553  0.000417964319
    fund_vol       sum_RC  sum_RC_minus_vol  w_dot_grad_minus_vol      sum_pct
1.113510e-01 1.113510e-01      0.000000e+00          0.000000e+00 1.000000e+00
```

### 3.3 Set A closed form, budget-only and set B minimum variance, 5 dates × 4 estimators

- `setA_vs_cvxpy`: max |closed form − cvxpy set A| (test tolerance 1e-7).
- `setA_gross`: Σ|w| of the closed form.
- `gmv_vs_closed`: max |`min_variance` with `Constraints(lower=None, upper=None)` − `gmv_closed_form`| (tolerance 1e-7).
- The set B columns: `min_variance` with bounds 0 and 0.30 (tolerance 1e-9).

```
      date estimator  setA_vs_cvxpy  setA_gross  gmv_vs_closed  setB_min_w  setB_max_w_minus_cap  setB_sum_minus_1           solvers          status
2010-04-30    sample      1.809e-11   3.855e+01      7.677e-09   6.532e-13            -3.825e-13         0.000e+00 CLARABEL/CLARABEL optimal/optimal
2010-04-30     lw_cc      9.215e-12   3.138e+01      4.732e-09   1.184e-11            -7.531e-12         2.220e-16 CLARABEL/CLARABEL optimal/optimal
2010-04-30      ewma      2.155e-10   1.205e+02      6.375e-11   4.103e-12            -4.255e-12        -2.220e-16 CLARABEL/CLARABEL optimal/optimal
2010-04-30      pca3      2.244e-12   2.324e+01      1.401e-09   9.958e-12            -5.931e-12        -2.220e-16 CLARABEL/CLARABEL optimal/optimal
2012-12-31    sample      2.780e-10   1.200e+02      1.452e-10   2.870e-12            -1.627e-12         0.000e+00 CLARABEL/CLARABEL optimal/optimal
2012-12-31     lw_cc      6.762e-11   9.118e+01      1.101e-10   2.992e-12            -2.315e-12        -2.220e-16 CLARABEL/CLARABEL optimal/optimal
2012-12-31      ewma      5.862e-14   2.545e+02      1.002e-10   9.298e-11            -2.219e-11        -3.331e-16 CLARABEL/CLARABEL optimal/optimal
2012-12-31      pca3      3.715e-11   8.372e+01      6.092e-09   2.343e-12            -9.250e-13        -1.110e-16 CLARABEL/CLARABEL optimal/optimal
2016-06-30    sample      1.256e-10   6.478e+01      1.735e-11   7.732e-12            -1.659e-11        -1.110e-16 CLARABEL/CLARABEL optimal/optimal
2016-06-30     lw_cc      7.454e-11   5.966e+01      9.246e-12   3.943e-11            -1.029e-10         2.220e-16 CLARABEL/CLARABEL optimal/optimal
2016-06-30      ewma      1.883e-13   1.050e+02      2.364e-10   7.420e-13            -2.190e-12         2.220e-16 CLARABEL/CLARABEL optimal/optimal
2016-06-30      pca3      6.783e-11   7.840e+01      1.608e-10   1.261e-12            -2.916e-12         2.220e-16 CLARABEL/CLARABEL optimal/optimal
2020-02-28    sample      1.322e-13   7.759e+01      2.414e-10   1.148e-11            -1.401e-11         0.000e+00 CLARABEL/CLARABEL optimal/optimal
2020-02-28     lw_cc      6.276e-10   7.036e+01      9.016e-11   2.332e-12            -2.781e-12        -2.220e-16 CLARABEL/CLARABEL optimal/optimal
2020-02-28      ewma      2.061e-13   1.348e+02      1.329e-09   4.808e-12            -9.756e-12         2.220e-16 CLARABEL/CLARABEL optimal/optimal
2020-02-28      pca3      4.011e-10   9.642e+01      2.070e-11   5.204e-12            -7.689e-12        -1.110e-16 CLARABEL/CLARABEL optimal/optimal
2026-07-31    sample      3.882e-10   5.963e+01      4.355e-11   1.018e-12            -3.888e-12         0.000e+00 CLARABEL/CLARABEL optimal/optimal
2026-07-31     lw_cc      6.383e-11   3.718e+01      7.752e-12   4.923e-12            -2.088e-11        -2.220e-16 CLARABEL/CLARABEL optimal/optimal
2026-07-31      ewma      2.096e-13   1.423e+02      8.935e-10   4.923e-11            -1.387e-10         2.220e-16 CLARABEL/CLARABEL optimal/optimal
2026-07-31      pca3      1.203e-10   3.814e+01      5.096e-12   3.578e-11            -1.416e-10        -3.331e-16 CLARABEL/CLARABEL optimal/optimal
setA_vs_cvxpy   6.276e-10
gmv_vs_closed   7.677e-09
```

### 3.4 KKT residual on the smooth set B problem, 2016-06-30

The residual is μ − γΣw − ν1 + λ_lo − λ_hi, from cvxpy's duals of the budget and bound constraints (test: max abs < 1e-6). The test covers all 4 estimators.

```
estimator  max_abs_residual           nu  n_at_lower  n_at_upper  status
   sample      2.946266e-18 9.288756e-03          14           2 optimal
    lw_cc      3.686287e-18 9.281208e-03          14           2 optimal
     ewma      8.231110e-17 9.485855e-03          13           2 optimal
     pca3      3.252607e-18 9.207832e-03          14           2 optimal
```

### 3.4 Binding, slack and relaxed turnover cases

`lw_cc`, μ = `mu_sample`, config costs, bounds 0 and 0.30.

- binding: w_prev = 1/N, τ = 0.05.
- slack: w_prev = 1/N, τ = 2. Two long-only portfolios are at most 2 apart in L1, so this limit never binds.
- relaxed: w_prev has 0.45 in SPY and τ = 0.05, so τ_min = 0.30 and τ_eff = 0.300001.

`dual_bp_per_1pct` is `turnover_dual` × 100: basis points of monthly return per 1% of turnover. `solver` lists the LP, then the QP.

```
      date    case  tau    turnover  tau_eff  tau_relaxed   turnover_dual  dual_bp_per_1pct            cost  status            solver
2010-04-30 binding 0.05        0.05     0.05        False   0.02379868465       2.379868465         1.5e-05 optimal CLARABEL+CLARABEL
2010-04-30   slack    2 1.235766793        2        False 5.382176292e-15   5.382176292e-13 0.0004408850865 optimal CLARABEL+CLARABEL
2010-04-30 relaxed 0.05    0.300001 0.300001         True   0.02381995413       2.381995413     9.00003e-05 optimal CLARABEL+CLARABEL
2012-12-31 binding 0.05        0.05     0.05        False  0.006690493336      0.6690493336         1.5e-05 optimal CLARABEL+CLARABEL
2012-12-31   slack    2 1.511700217        2        False 2.220913294e-14   2.220913294e-12  0.000593510065 optimal CLARABEL+CLARABEL
2012-12-31 relaxed 0.05    0.300001 0.300001         True  0.006336679669      0.6336679669     9.00003e-05 optimal CLARABEL+CLARABEL
2016-06-30 binding 0.05        0.05     0.05        False   0.01208147185       1.208147185        2.25e-05 optimal CLARABEL+CLARABEL
2016-06-30   slack    2 1.444444444        2        False 1.936661015e-14   1.936661015e-12          0.0005 optimal CLARABEL+CLARABEL
2016-06-30 relaxed 0.05    0.300001 0.300001         True   0.01185442509       1.185442509    9.000045e-05 optimal CLARABEL+CLARABEL
2020-02-28 binding 0.05        0.05     0.05        False   0.01140255977       1.140255977         1.5e-05 optimal CLARABEL+CLARABEL
2020-02-28   slack    2 1.437906417        2        False 5.625681349e-15   5.625681349e-13 0.0005147052584 optimal CLARABEL+CLARABEL
2020-02-28 relaxed 0.05    0.300001 0.300001         True   0.01114183896       1.114183896     9.00003e-05 optimal CLARABEL+CLARABEL
2026-07-31 binding 0.05        0.05     0.05        False   0.01049473724       1.049473724         1.5e-05 optimal CLARABEL+CLARABEL
2026-07-31   slack    2 1.486280101        2        False  1.46338719e-14    1.46338719e-12 0.0005214418141 optimal CLARABEL+CLARABEL
2026-07-31 relaxed 0.05    0.300001 0.300001         True   0.01008512028       1.008512028     9.00003e-05 optimal CLARABEL+CLARABEL
```

The binding dual runs from 0.67 to 2.38 bp of monthly return per 1% of turnover. The slack dual is at most 2.2e-14.

### 3.5 Risk parity: pct risk contributions at the 5 dates, 4 estimators each

```
== pct risk contributions, 2010-04-30
            sample          lw_cc           ewma           pca3
SPY 0.055555555369 0.055555555712 0.055555555572 0.055555554376
IWM 0.055555555372 0.055555555733 0.055555554243 0.055555554200
EFA 0.055555556053 0.055555555792 0.055555555337 0.055555554184
EEM 0.055555557236 0.055555556309 0.055555555569 0.055555555164
XLE 0.055555557854 0.055555555917 0.055555554824 0.055555554197
XLF 0.055555551674 0.055555555853 0.055555559673 0.055555555039
XLK 0.055555555474 0.055555555788 0.055555556092 0.055555553961
XLU 0.055555555699 0.055555555532 0.055555554787 0.055555554815
XLV 0.055555556755 0.055555557084 0.055555555264 0.055555550288
SHY 0.055555549547 0.055555543938 0.055555555688 0.055555585166
IEF 0.055555550311 0.055555557431 0.055555563398 0.055555541637
TLT 0.055555559969 0.055555553424 0.055555555958 0.055555545816
TIP 0.055555554618 0.055555562383 0.055555556094 0.055555566069
LQD 0.055555557603 0.055555562579 0.055555548718 0.055555564858
HYG 0.055555558651 0.055555555447 0.055555554351 0.055555554323
GLD 0.055555556379 0.055555549856 0.055555555312 0.055555549817
DBC 0.055555557864 0.055555556407 0.055555554982 0.055555553659
VNQ 0.055555553573 0.055555554814 0.055555554138 0.055555552432
== pct risk contributions, 2012-12-31
            sample          lw_cc           ewma           pca3
SPY 0.055555555786 0.055555555051 0.055555554016 0.055555555231
IWM 0.055555556343 0.055555555424 0.055555557739 0.055555548214
EFA 0.055555555287 0.055555555229 0.055555551303 0.055555552122
EEM 0.055555555513 0.055555555458 0.055555555669 0.055555564471
XLE 0.055555554427 0.055555555606 0.055555555674 0.055555547198
XLF 0.055555555986 0.055555555445 0.055555554632 0.055555554701
XLK 0.055555555728 0.055555555021 0.055555554384 0.055555555332
XLU 0.055555553580 0.055555554441 0.055555551967 0.055555554394
XLV 0.055555554311 0.055555556393 0.055555555165 0.055555550724
SHY 0.055555545966 0.055555556917 0.055555561050 0.055555553956
IEF 0.055555568845 0.055555555942 0.055555557743 0.055555568828
TLT 0.055555561487 0.055555549408 0.055555554674 0.055555554014
TIP 0.055555551329 0.055555560024 0.055555556650 0.055555558496
LQD 0.055555554085 0.055555557604 0.055555559237 0.055555557018
HYG 0.055555553974 0.055555555124 0.055555554992 0.055555554493
GLD 0.055555555887 0.055555556650 0.055555555465 0.055555555026
DBC 0.055555555195 0.055555554935 0.055555554790 0.055555556028
VNQ 0.055555556270 0.055555555329 0.055555554849 0.055555559757
== pct risk contributions, 2016-06-30
            sample          lw_cc           ewma           pca3
SPY 0.055555555379 0.055555554983 0.055555555110 0.055555555499
IWM 0.055555554423 0.055555554502 0.055555555388 0.055555555570
EFA 0.055555556878 0.055555554987 0.055555555432 0.055555554055
EEM 0.055555556587 0.055555555598 0.055555556533 0.055555555284
XLE 0.055555554612 0.055555554814 0.055555554267 0.055555557349
XLF 0.055555555612 0.055555555118 0.055555555499 0.055555555242
XLK 0.055555555581 0.055555555010 0.055555555189 0.055555555516
XLU 0.055555556484 0.055555555709 0.055555554128 0.055555555094
XLV 0.055555555668 0.055555554922 0.055555555223 0.055555555238
SHY 0.055555553794 0.055555557895 0.055555569989 0.055555555122
IEF 0.055555557405 0.055555557509 0.055555551537 0.055555556254
TLT 0.055555560818 0.055555554434 0.055555557894 0.055555556046
TIP 0.055555554413 0.055555554267 0.055555548880 0.055555555169
LQD 0.055555552521 0.055555550058 0.055555554130 0.055555555996
HYG 0.055555555139 0.055555561014 0.055555555799 0.055555554731
GLD 0.055555554310 0.055555555473 0.055555556305 0.055555555440
DBC 0.055555556061 0.055555556954 0.055555554573 0.055555556343
VNQ 0.055555554315 0.055555556754 0.055555554124 0.055555556052
== pct risk contributions, 2020-02-28
            sample          lw_cc           ewma           pca3
SPY 0.055555555571 0.055555554676 0.055555554178 0.055555555028
IWM 0.055555555464 0.055555554863 0.055555555244 0.055555554792
EFA 0.055555555326 0.055555555097 0.055555555417 0.055555555225
EEM 0.055555555751 0.055555554025 0.055555554373 0.055555555852
XLE 0.055555555245 0.055555556337 0.055555554980 0.055555555390
XLF 0.055555555717 0.055555554978 0.055555555202 0.055555555482
XLK 0.055555556039 0.055555553772 0.055555554254 0.055555555622
XLU 0.055555555263 0.055555555767 0.055555555022 0.055555555549
XLV 0.055555555604 0.055555554780 0.055555555378 0.055555555064
SHY 0.055555555436 0.055555556991 0.055555561160 0.055555552372
IEF 0.055555554177 0.055555558840 0.055555552366 0.055555562682
TLT 0.055555556217 0.055555555982 0.055555556990 0.055555554833
TIP 0.055555555088 0.055555555950 0.055555557440 0.055555554076
LQD 0.055555555158 0.055555557265 0.055555553325 0.055555554874
HYG 0.055555555939 0.055555552302 0.055555555268 0.055555555829
GLD 0.055555556603 0.055555556509 0.055555556053 0.055555556708
DBC 0.055555555752 0.055555555235 0.055555556149 0.055555555355
VNQ 0.055555555651 0.055555556632 0.055555557200 0.055555555266
== pct risk contributions, 2026-07-31
            sample          lw_cc           ewma           pca3
SPY 0.055555556590 0.055555555519 0.055555553265 0.055555556457
IWM 0.055555555299 0.055555556078 0.055555552705 0.055555555431
EFA 0.055555556404 0.055555555069 0.055555552753 0.055555556009
EEM 0.055555556018 0.055555556037 0.055555553377 0.055555555596
XLE 0.055555556795 0.055555555050 0.055555558553 0.055555555204
XLF 0.055555556212 0.055555555405 0.055555552996 0.055555556068
XLK 0.055555555397 0.055555556414 0.055555552074 0.055555554772
XLU 0.055555556419 0.055555555140 0.055555554130 0.055555556200
XLV 0.055555555656 0.055555555336 0.055555552726 0.055555554600
SHY 0.055555546426 0.055555553781 0.055555565802 0.055555556144
IEF 0.055555560122 0.055555555973 0.055555566191 0.055555559011
TLT 0.055555556514 0.055555555501 0.055555558805 0.055555555896
TIP 0.055555556115 0.055555556237 0.055555544175 0.055555554251
LQD 0.055555557224 0.055555557092 0.055555562183 0.055555553557
HYG 0.055555555733 0.055555554013 0.055555558830 0.055555554411
GLD 0.055555556909 0.055555555538 0.055555555607 0.055555556467
DBC 0.055555550207 0.055555556400 0.055555551883 0.055555554784
VNQ 0.055555555957 0.055555555416 0.055555553947 0.055555555142
```

Summary over the 20 cases (test tolerance 1e-6; max 2.96e-8):

```
      date estimator  max_abs_dev_from_1_over_N     min_w  sum_w_minus_1  status
2010-04-30    sample                  6.009e-09 8.191e-03      0.000e+00 optimal
2010-04-30     lw_cc                  1.162e-08 8.290e-03     -2.220e-16 optimal
2010-04-30      ewma                  7.843e-09 1.196e-02      0.000e+00 optimal
2010-04-30      pca3                  2.961e-08 8.548e-03      0.000e+00 optimal
2012-12-31    sample                  1.329e-08 9.742e-03      0.000e+00 optimal
2012-12-31     lw_cc                  6.147e-09 9.761e-03      0.000e+00 optimal
2012-12-31      ewma                  5.495e-09 8.485e-03      0.000e+00 optimal
2012-12-31      pca3                  1.327e-08 1.041e-02      2.220e-16 optimal
2016-06-30    sample                  5.262e-09 1.299e-02     -1.110e-16 optimal
2016-06-30     lw_cc                  5.498e-09 1.304e-02     -2.220e-16 optimal
2016-06-30      ewma                  1.443e-08 1.168e-02      0.000e+00 optimal
2016-06-30      pca3                  1.793e-09 1.303e-02     -1.110e-16 optimal
2020-02-28    sample                  1.378e-09 1.251e-02      0.000e+00 optimal
2020-02-28     lw_cc                  3.285e-09 1.261e-02     -1.110e-16 optimal
2020-02-28      ewma                  5.604e-09 7.613e-03      0.000e+00 optimal
2020-02-28      pca3                  7.127e-09 1.248e-02      0.000e+00 optimal
2026-07-31    sample                  9.129e-09 1.760e-02     -1.110e-16 optimal
2026-07-31     lw_cc                  1.775e-09 1.797e-02      0.000e+00 optimal
2026-07-31      ewma                  1.138e-08 1.341e-02      0.000e+00 optimal
2026-07-31      pca3                  3.455e-09 1.785e-02      0.000e+00 optimal
```

### 3.6 HRP against PyPortfolioOpt 1.6.0, and the hand-worked 4-asset example

Real daily window (`window_daily`, 36 months) at each date. Ours gets `X.cov()` and derives ρ from it. PyPortfolioOpt gets `returns=X`, and its order is read from `to_tree(opt.clusters).pre_order()`. The orders are identical at both dates, so there is no rule 4 stop. Test tolerance 1e-10.

```
== 2010-04-30: rows 757; quasi-diagonal order
          0    1    2    3    4    5    6    7    8    9    10   11   12   13   14   15   16   17
ours     TIP  SHY  IEF  TLT  GLD  LQD  HYG  DBC  XLU  XLV  XLE  XLF  VNQ  IWM  XLK  EEM  SPY  EFA
pypfopt  TIP  SHY  IEF  TLT  GLD  LQD  HYG  DBC  XLU  XLV  XLE  XLF  VNQ  IWM  XLK  EEM  SPY  EFA
                    ours              pypfopt                  diff
SPY 0.000680317071154153 0.000680317071154153                     0
IWM  0.00084048936885315  0.00084048936885315                     0
EFA 0.000506029268082448 0.000506029268082448                     0
EEM 0.000465956169625962 0.000465956169625962                     0
XLE 0.000854189841966832 0.000854189841966832                     0
XLF 0.000394387012589664 0.000394387012589664                     0
XLK  0.00118502616240446  0.00118502616240446                     0
XLU  0.00347135644893868  0.00347135644893867  7.37257477290143e-18
XLV  0.00327451252279323  0.00327451252279323                     0
SHY    0.832459288718499    0.832459288718499 -1.11022302462516e-16
IEF   0.0403482494659127   0.0403482494659128 -6.93889390390723e-18
TLT   0.0120149595026014   0.0120149595026014 -1.73472347597681e-18
TIP   0.0536596789576175   0.0536596789576175 -6.93889390390723e-18
LQD   0.0289227366745348   0.0289227366745347  5.55111512312578e-17
HYG   0.0084505458811737  0.00845054588117369  1.73472347597681e-17
GLD  0.00890351471280108  0.00890351471280106  1.73472347597681e-17
DBC  0.00318542917519344  0.00318542917519343  6.50521303491303e-18
VNQ 0.000383333045257536 0.000383333045257536                     0
== 2020-02-28: rows 755; quasi-diagonal order
          0    1    2    3    4    5    6    7    8    9    10   11   12   13   14   15   16   17
ours     DBC  XLE  HYG  EEM  XLF  EFA  XLV  IWM  SPY  XLK  XLU  VNQ  GLD  LQD  SHY  TIP  IEF  TLT
pypfopt  DBC  XLE  HYG  EEM  XLF  EFA  XLV  IWM  SPY  XLK  XLU  VNQ  GLD  LQD  SHY  TIP  IEF  TLT
                    ours              pypfopt  diff
SPY 0.000827915861521161 0.000827915861521161     0
IWM 0.000601110157582587 0.000601110157582587     0
EFA   0.0021447049696259   0.0021447049696259     0
EEM  0.00174442152124877  0.00174442152124877     0
XLE   0.0011265675551911   0.0011265675551911     0
XLF  0.00109179565323178  0.00109179565323178     0
XLK  0.00315957091079327  0.00315957091079327     0
XLU  0.00704589183102696  0.00704589183102696     0
XLV  0.00140702340300256  0.00140702340300256     0
SHY    0.830777688525549    0.830777688525549     0
IEF   0.0152098827971344   0.0152098827971344     0
TLT  0.00292952141531501  0.00292952141531501     0
TIP   0.0433681433307826   0.0433681433307826     0
LQD   0.0447767959765953   0.0447767959765953     0
HYG   0.0239205500926251   0.0239205500926251     0
GLD   0.0108517601936573   0.0108517601936573     0
DBC  0.00225773939053048  0.00225773939053048     0
VNQ  0.00675891641458642  0.00675891641458642     0
      date  max_abs_diff  orders_equal
2010-04-30  1.110223e-16          True
2020-02-28  0.000000e+00          True
== hand-worked 4-asset example
                    reviewer               function                    diff
V1     0.0017370612730517548  0.0017370612730517546 -2.1684043449710089e-19
V2    0.00043029585798816562 0.00043029585798816562                       0
alpha    0.19853482004680301     0.1985348200468029 -1.1102230246251565e-16
             reviewer             function                    diff
A 0.12105781710170915  0.12105781710170908 -6.9388939039072284e-17
B 0.07747700294509384 0.077477002945093812 -2.7755575615628914e-17
C 0.55486050919836716  0.55486050919836716                       0
D 0.24660467075482986  0.24660467075482989  2.7755575615628914e-17
order: ['A', 'B', 'C', 'D']
```

### 3.7 P, Q, Π and μ_BL at the first decision date (2010-04-30) and at 2020-02-28

Σ is the `lw_cc` monthly Σ, Π = δΣw_mkt and τ = `bl.tau`. `mom_12_1` is the compounded total return over the window, which sets the ranking. `mean_excess_window` is what Q is built from.

```
2010-04-30 (Sigma = lw_cc monthly, conditioned); 12-1 window 2009-05-29 to 2010-03-31, 11 months
P:
     momentum  stocks_bonds
SPY  0.166667      0.250000
IWM  0.166667      0.250000
EFA  0.166667      0.250000
EEM  0.166667      0.250000
XLE  0.000000      0.000000
XLF  0.166667      0.000000
XLK  0.000000      0.000000
XLU  0.000000      0.000000
XLV  0.000000      0.000000
SHY -0.166667     -0.333333
IEF -0.166667     -0.333333
TLT -0.166667     -0.333333
TIP -0.166667      0.000000
LQD -0.166667      0.000000
HYG  0.000000      0.000000
GLD  0.000000      0.000000
DBC -0.166667      0.000000
VNQ  0.166667      0.000000
Q and Omega diagonal:
                         Q           Omega
momentum     0.03104221607  0.000391713409
stocks_bonds 0.03454869828 0.0003746715001
           mom_12_1  mean_excess_window  w_mkt               Pi            mu_BL   mu_BL_minus_Pi  sqrt_diag_Sigma  sqrt_diag_Sigma_BL
SPY    0.3652175725       0.02917214266   0.19    0.01154747044    0.01993576192    0.00838829148    0.08644445198       0.08692414084
IWM    0.4147780297       0.03300178973   0.04    0.01273136116    0.02239280232   0.009661441162     0.1018626022        0.1024549459
EFA    0.3761861756       0.03064529611   0.12    0.01320639908    0.02258169175   0.009375292666     0.1002316758        0.1008558137
EEM    0.4934840239       0.03935177417   0.05    0.01837417338    0.03213391224    0.01375973886     0.1448435196        0.1457110472
XLE    0.2798438715       0.02374192864   0.02    0.01470017688    0.02509066371    0.01039048683      0.124838229        0.1258199603
XLF    0.5077759459       0.03978403823   0.02     0.0189782669    0.03325637656    0.01427810966     0.1661827883        0.1673392963
XLK    0.3593415585       0.02918719058   0.02    0.01050909699    0.01829491038   0.007785813395    0.08578609708       0.08635127539
XLU    0.1969314659       0.01692898685   0.02   0.008138090297    0.01385749185   0.005719401552    0.07603825949       0.07671726824
XLV    0.3532568267       0.02825464984   0.02   0.006725330622    0.01148790419   0.004762573563     0.0637604645       0.06433037067
SHY   0.01293657529      0.001075840415   0.05 -0.0003158733919 -0.0006751162985 -0.0003592429067   0.006534701917      0.006607848305
IEF -0.009784439633    -0.0008232553824   0.09 -0.0009774733079  -0.002413902565  -0.001436429257    0.02511891467       0.02539505085
TLT  -0.05421489583     -0.004770427877   0.08  -0.001760746291   -0.00432739639  -0.002566650099    0.04603117529       0.04654399357
TIP   0.07349879337      0.006464511537   0.04  -0.000292542044  -0.001169807843 -0.0008772657989    0.02573850091       0.02606720499
LQD    0.1555365392       0.01326585215   0.08   0.001643498683   0.002064780106   0.000421281423     0.0393067239       0.03984407356
HYG    0.2660452175       0.02192402241   0.04   0.004857644057   0.008015293768   0.003157649711    0.05718684757       0.05782669094
GLD     0.248424443       0.02186795149   0.04   0.001620834946   0.002109793519  0.0004889585739    0.07084444454       0.07181580203
DBC     0.177177186       0.01660878409   0.03   0.005716743657   0.009298521463   0.003581777806    0.07937756932       0.08033288885
VNQ    0.6113459174       0.04611956044   0.05    0.01907345297    0.03339302081    0.01431956785      0.168561821        0.1697528709
P mu_BL: [0.0268194145, 0.0267331805]  P Pi: [0.0149829194, 0.014982882]
```

```
2020-02-28 (Sigma = lw_cc monthly, conditioned); 12-1 window 2019-03-29 to 2020-01-31, 11 months
P:
     momentum  stocks_bonds
SPY  0.166667      0.250000
IWM -0.166667      0.250000
EFA  0.000000      0.250000
EEM -0.166667      0.250000
XLE -0.166667      0.000000
XLF  0.000000      0.000000
XLK  0.166667      0.000000
XLU  0.166667      0.000000
XLV  0.000000      0.000000
SHY -0.166667     -0.333333
IEF  0.000000     -0.333333
TLT  0.166667     -0.333333
TIP  0.000000      0.000000
LQD  0.166667      0.000000
HYG -0.166667      0.000000
GLD  0.166667      0.000000
DBC -0.166667      0.000000
VNQ  0.000000      0.000000
Q and Omega diagonal:
                           Q           Omega
momentum       0.01961199773 1.441557337e-05
stocks_bonds -0.003806956084  5.95517617e-05
          mom_12_1  mean_excess_window  w_mkt               Pi            mu_BL  mu_BL_minus_Pi  sqrt_diag_Sigma  sqrt_diag_Sigma_BL
SPY   0.1763392168       0.01373192819   0.19   0.001745936706  -0.002188894553 -0.003934831259    0.03897935641       0.03929732179
IWM  0.03768185451      0.002580104378   0.04   0.001803444781  -0.005901787672 -0.007705232453    0.04574574791       0.04611490061
EFA  0.08467916336      0.006234012625   0.12   0.001457370977  -0.003225785385 -0.004683156363    0.03442369742       0.03470991845
EEM  0.02114592945      0.001303126526   0.05   0.001920555371  -0.006063023694 -0.007983579064    0.04987896215       0.05031281741
XLE  -0.1258359667      -0.01170729452   0.02   0.001868622671   -0.01350773005  -0.01537635272    0.05613635762       0.05662035777
XLF    0.152923812       0.01249260725   0.02   0.001651748585  -0.006086844439 -0.007738593024    0.04824703335       0.04866128976
XLK   0.3630966255       0.02788283426   0.02   0.002247409912 -0.0006826468237 -0.002930056736    0.05473644241       0.05523789566
XLU   0.2478391124       0.01899156526   0.02  0.0006370414982   0.007320923154  0.006683881656    0.03665410627       0.03711374962
XLV   0.1066038915       0.00809957333   0.02   0.001580756781 -0.0005207950062 -0.002101551787    0.04079607552       0.04120903601
SHY  0.03629670137      0.001569117519   0.05 -2.316431494e-05  0.0005444782983 0.0005676426133   0.002926051051      0.002957380804
IEF   0.1163557125      0.008540056678   0.09 -8.284418083e-05   0.003119368965  0.003202213146    0.01333609059       0.01346178129
TLT   0.2414061783       0.01919857284   0.08 -9.914725205e-05   0.007271012432  0.007370159684    0.03038737126        0.0306818285
TIP  0.09296684451      0.006484958148   0.04  3.681082003e-05   0.001774882276  0.001738071456    0.01026999283       0.01039081693
LQD   0.1655876164       0.01244529272   0.08  0.0001861463188   0.002659078332  0.002472932014    0.01260369265       0.01275787171
HYG  0.06908019289      0.004485705109   0.04   0.000522959446  -0.001102549333 -0.001625508778    0.01346968827       0.01360570698
GLD   0.2043713558       0.01607687141   0.04  0.0001716874536   0.003967996156  0.003796308702    0.03090051512       0.03130539854
DBC -0.07183199299     -0.007575680692   0.03  0.0008339975208  -0.009450335434  -0.01028433295    0.03965390346        0.0400835027
VNQ   0.1585881312       0.01190436153   0.05   0.001180353484   0.003469785066  0.002289431582    0.03915410268        0.0396512747
P mu_BL: [0.0089714028, -0.0079898261]  P Pi: [-0.0003395568, 0.0018002122]
```

### 3.7 φ (Bayes-Stein) at the 5 dates

Σ is the monthly `lw_cc` Σ and T = 36. The first row is φ at the first decision date.

```
phi (Bayes-Stein, Sigma = lw_cc monthly, T = 36)
      date          phi      mu_hat_min    mu_hat_max       mu_BS_min      mu_BS_max
2010-04-30  0.707698872  -0.01585181009 0.01592012957 -0.003233936319 0.006053037484
2012-12-31 0.4771793667  0.001018814922 0.01510825686 0.0007369646422 0.008103215598
2016-06-30 0.5390395979  -0.01249883771 0.01326759542 -0.005588755122 0.006288550257
2020-02-28 0.5690549765 -0.008284943473 0.01548166596 -0.003634768612 0.006607333448
2026-07-31 0.6941275021 -0.005024831346 0.01774849222 -0.001736876603 0.005228856762
```

### 3.7 Round trip and tiny-Ω tests on real Σ

- Set A on (Π, Σ) with γ = δ, against w_mkt (tolerance 1e-8).
- Max |Pμ_BL − Q| with Ω × 1e-10 (tolerance 1e-6).

```
      date  setA_on_Pi_max_abs_diff_w_mkt  tiny_omega_max_abs_Pmu_minus_Q
2010-04-30                      1.249e-15                       4.987e-12
2012-12-31                      2.776e-15                       8.056e-12
2016-06-30                      3.775e-15                       5.213e-12
2020-02-28                      1.818e-15                       3.535e-12
2026-07-31                      1.339e-15                       6.961e-12
```

## Tests run

`.venv\Scripts\python -m pytest --disable-socket`

```
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser
configfile: pyproject.toml
testpaths: tests
plugins: platformdirs-4.12.2, socket-0.8.1
collected 204 items

tests\test_allocators.py ............................................... [ 23%]
........................................................................ [ 58%]
.....                                                                    [ 60%]
tests\test_bl.py ....................                                    [ 70%]
tests\test_calendar.py .....                                             [ 73%]
tests\test_config.py ...                                                 [ 74%]
tests\test_cov.py ...........                                            [ 79%]
tests\test_cov_eval.py ...                                               [ 81%]
tests\test_cov_lw.py .....                                               [ 83%]
tests\test_data.py ........                                              [ 87%]
tests\test_hrp.py ...                                                    [ 89%]
tests\test_manifest.py .                                                 [ 89%]
tests\test_placeholder.py .                                              [ 90%]
tests\test_returns.py ...                                                [ 91%]
tests\test_returns_model.py .......                                      [ 95%]
tests\test_risk.py ....                                                  [ 97%]
tests\test_solver.py ....                                                [ 99%]
tests\test_stats.py ..                                                   [100%]

============================= 204 passed in 6.43s =============================
```

## Fresh-clone check

Amendment 3: I cloned the pushed repo (at `5aa4f29`) into `%TEMP%\pcs3` and built the venv with `uv venv --seed --python 3.11 .venv`, `pip install -r requirements-lock.txt` and `pip install -e . --no-deps`. Then I ran `.venv\Scripts\python -m pytest --disable-socket -q`. Full output:

```
........................................................................ [ 35%]
........................................................................ [ 70%]
............................................................             [100%]
204 passed in 1461.15s (0:24:21)
```

That first run took 24 minutes; every other run took 6 to 12 s. The shell wrapper's 10-minute limit moved it to the background before it finished, but the output above is complete. To see whether a test was slow, I reran the same command in the same clone with `--durations=8` before deleting it:

```
........................................................................ [ 35%]
........................................................................ [ 70%]
............................................................             [100%]
============================= slowest 8 durations =============================
0.66s call     tests/test_cov_eval.py::test_qlike_on_synthetic_perfect_forecast
0.63s call     tests/test_allocators.py::test_turnover_never_exceeds_tau_eff[2010-04-30]
0.49s call     tests/test_allocators.py::test_turnover_never_exceeds_tau_eff[2012-12-31]
0.43s call     tests/test_allocators.py::test_turnover_never_exceeds_tau_eff[2026-07-31]
0.38s call     tests/test_returns.py::test_compounded_daily_equals_holding_return
0.35s call     tests/test_allocators.py::test_turnover_never_exceeds_tau_eff[2020-02-28]
0.31s call     tests/test_allocators.py::test_turnover_never_exceeds_tau_eff[2016-06-30]
0.28s call     tests/test_cov_lw.py::test_lw_cc_matches_pypfopt[real_2010_04_30]
204 passed in 12.47s
```

So no test is slow. The 24 minutes went on the first run in a newly built venv. The likely cause is first-time imports and `.pyc` compilation of the installed packages, possibly slowed by an on-access scan of new files in `%TEMP%`. I did not check which. The folder was then deleted.

## Runtime per step

Test time per step's test file, each run alone on this machine (wall time reported by pytest).

| step | runtime |
|---|---|
| 3.0 | config and text only; full suite 5.2 s after the change |
| 3.1 | `test_solver.py` 1.2 s |
| 3.2 | `test_risk.py` 0.1 s |
| 3.3 to 3.5 | `test_allocators.py` 3.7 s (124 tests) |
| 3.6 | `test_hrp.py` 1.5 s |
| 3.7 | `test_bl.py` 1.5 s, `test_returns_model.py` 0.1 s |

## Deviations from PLAN.md

None in method. Points the reviewer should see:

1. **`mu_sample` was built at step 3.3, not 3.7.** The 3.3 and 3.4 tests need μ = `mu_sample` (amendment 3.4 names it), so it went into `pc/returns_model.py` at the first step that uses it. 3.7 added `mu_bayes_stein`. `mu_sample` takes the months [month(t) − 35, month(t)] through the helper `trailing_months`, which raises unless all 36 months are present. A date offset was avoided because t − 36 months can land before a month's last trading day (2015-02-27 − 36 months = 2012-02-27 < 2012-02-29) and pick up a 37th row.
2. **Allocators read solver settings from the repo's `config.toml`.** Kickoff Section 6 fixes the allocator signature (mu, Sigma, w_prev, cons), and `Constraints` has no solver fields. So `pc/solver.py` loads `[solver]` once from `Path(pc/solver.py).parents[1] / "config.toml"` (`solver_config()`, cached) for `clarabel_tol`, `scs_eps` and the 3 `rp_*` values. No number is hard-coded.
3. **Solver bookkeeping in `AllocResult`.** Its fields are fixed, so retries are recorded in the strings. `solver` is every solver called during the allocator call, in order, joined by "+". For example, `mv_constrained` with a turnover limit gives `CLARABEL+CLARABEL` (the LP, then the QP), and a QP that retried gives `CLARABEL+CLARABEL+SCS`. The SCS retry count is `solver.count("SCS")`. `status` is the first failing solve's status, else `optimal`. If the LP falls back, the QP is not run and the allocator holds w_prev. For the other allocators: mv_unconstrained `closed_form`, risk_parity `L-BFGS-B`, hrp and equal_weight `none`. On fallback, `objective` and `turnover_dual` are NaN.
4. **risk_parity when scipy reports failure.** The kickoff's hold rule is written for cvxpy. If L-BFGS-B returns `success = False`, `status` is scipy's message, `fallback` stays False and the weights are still x/1′x. On the 20 test cases every status is `optimal`.
5. **Helpers not in kickoff Section 6.**
   - `pc/solver.py`: `SolveRecord`, `merge_records`, `solve`, `solver_config`, `turnover_feasibility`, `symmetrise`, `TAU_RELAX`.
   - `pc/allocators.py`: `check_index`, `fallback_weights`, `solved_result`, `_bounds`, `mv_problem` (the KKT test reads its constraint duals), `RP_LOWER`.
   - `pc/hrp.py`: `quasi_diag_order`, `cluster_var`, `bisect_weights`.
   - `pc/bl.py`: `momentum_window` (the window test reads it), `omega`, and `posterior(..., omega_diag)`. `bl_posterior` is `posterior` with Ω = diag(PτΣP′). The tiny-Ω test calls `posterior` with Ω × 1e-10, since the fixed `bl_posterior` signature has no Ω argument.
   - `pc/returns_model.py`: `trailing_months`.
   - Literals under convention 22: `TAU_RELAX = 1e-6` and `RP_LOWER = 1e-12`, each with a comment citing kickoff 5.3.
6. **No-view posterior.** With 0 view rows, `posterior` returns Π itself and Σ + τΣ. That is the formula with A⁻¹ = τΣ, and it makes "returns Π exactly" hold bitwise rather than to rounding.
7. **Test inputs the instruction file left open.**
   - `test_mv_constrained_no_tau_no_cost_equals_set_b` uses w_prev = 1/N.
   - The KKT test runs all 4 estimators at 2016-06-30.
   - The binding, slack and τ_eff tests use `lw_cc` at the 5 dates. Their w_prev is 1/N and the SPY-0.45 drifted vector; the τ values are 0.05 (binding), 2 (slack) and the 7 `turnover_grid.taus`.
   - The 3.3 tests run 5 dates × 4 estimators.
   - `test_hrp_matches_pypfopt` compares the 2 quasi-diagonal orders inside the test before it compares weights.
8. **Tolerances I set where `PLAN.md` gives none.**
   - Finite-difference gradient check in `test_euler_identity`: rtol 1e-6, h = 1e-6. Element-wise w_i ∂σ/∂w_i = RC_i: atol 1e-15.
   - Weight sums: 1e-12 for the closed forms and risk parity.
   - Bayes-Stein constant μ: φ = 1 to 1e-12, μ unchanged to rtol 1e-12.
   - Q against the basket means: 1e-15.
   - Binding test: turnover = τ to 1e-7, dual > 1e-8. Slack test: turnover < 2 − 1e-3.
9. **Extra tests.**
   - `test_index_mismatch_raises`.
   - `test_allocator_fallback_holds_w_prev_or_equal_weight` covers both branches through `min_variance` and `mv_constrained`. The step 3.1 test can only reach the shared result helper, because no allocator exists at 3.1.
   - `test_mu_sample_is_mean_of_36_months_ending_at_t`, `test_momentum_q_is_view_on_window_mean_excess` and `test_black_litterman_is_mv_constrained_on_posterior`.
   - `test_momentum_window_is_11_months_skipping_t` also overwrites months t and t − 12 and checks that P and Q do not change.
10. **Monthly total returns for the views.** `momentum_views` takes `monthly_total` as an input, and Section 1 has no public function for it. The tests and evidence build it as `_month_end_closes(prices).pct_change()`, from `pc/returns.py`, on the same index as `monthly_excess_returns`. Section 4's backtest will need the same series. No new function was added to `pc/returns.py`, because Section 1 owns that file.

## Not verified

- The SCS branch has never produced a solution here: it ran only under the monkeypatch, where it "fails" by construction. Whether SCS at eps 1e-9 would return `optimal` on these problems is untested.
- The L-BFGS-B `success = False` path (Deviation 4) never ran.
- `mu_bayes_stein` is checked only for φ ∈ [0, 1] and for constant μ. It is not cross-checked against an external implementation.
- `black_litterman` is checked only as identical to `mv_constrained` on (μ_BL, Σ_BL), which is all convention 21 asks for.
- Why the first fresh-clone run took 24 minutes (see Fresh-clone check).

## Open questions

Appended to `decisions/OPEN.md`:

- **4. Step 3.7: which ticker leaves the short leg on a tie at the bottom boundary** (implemented as option 1). Option 1: one ranking, highest first, ties by config order; short = the last 6, so on a bottom tie the later ticker is short. Option 2: config order wins each selection; on a bottom tie the earlier ticker is short. The two readings agree at the top boundary, and no tie occurs on the real data.

## Files changed

Added: `decisions/section_2_review.md`, `pc/solver.py`, `pc/allocators.py`, `pc/hrp.py`, `pc/bl.py`, `pc/returns_model.py`, `tests/test_solver.py`, `tests/test_allocators.py`, `tests/test_hrp.py`, `tests/test_bl.py`, `tests/test_returns_model.py`, `review/section_3.md`, `instructions/03_section_3.status.md`.
Modified: `config.toml` (`clarabel_tol`), `pc/config.py` (`SolverConfig.clarabel_tol`), `pc/risk.py`, `decisions/OPEN.md` (decision 3 out, decision 4 in), `docs/CONVENTIONS_RESOLVED.md` (convention 22), `tests/conftest.py` (`REAL_DATES`, `RealData`, session fixture `real`), `tests/test_risk.py`.
Deleted: none. `CLAUDE.md` and `PLAN.md` were not staged.

## Reviewer reads

1. `decisions/OPEN.md` (decision 4).
2. `pc/solver.py` (policy, bookkeeping, feasibility LP).
3. `pc/allocators.py`: `solved_result`, `mv_problem`, `mv_constrained`, then the rest.
4. `pc/bl.py`: `momentum_views`, `posterior`.
5. `pc/hrp.py`.
6. This file: Deviations 1 to 4, then Evidence 1 to 4.
7. `tests/test_allocators.py`: the 3.4 tests.
