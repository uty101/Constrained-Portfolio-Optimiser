# Review — Section 4: Walk-forward and headline results

## Section

Section 4, walk-forward and headline results. **Completed in session 4b.** Session 4 stopped under rule 4 at step 4.2 (below). Session 4b (`instructions/04b_section_4_completion.md`) completed step 4.2 and ran steps 4.3 to 4.6. Its evidence is under `### Session 4b` at the end of Evidence. The session 4 text is kept as the record of the stop.

## Steps completed

- 4.0 `8e33e83` section 4: reviewer decisions for section 3 (`decisions/section_3_review.md`, convention 23, `decisions/OPEN.md` emptied)
- 4.0 `fbaba6b` step 4.0: window_daily on calendar-month periods (with the 4 regenerated cov_eval CSVs)
- 4.1 `9ef7ca6` step 4.1: strategy registry, 26 ids
- 4.2 `d72f7c5` step 4.2: walk-forward engine (stopped under rule 4: test_no_look_ahead part b)
- `29170e1` section 4: open decision 5 (look-ahead part b and the ruin rule)
- `ad5cc43` section 4: review file (session 4); `9ce9717` status: session 4

Session 4b:

- `4ca9b86` section 4: reviewer decisions, open decision 5 (`decisions/section_4_review.md`, `decisions/OPEN.md` emptied)
- 4.2 `dcebb48` step 4.2: look-ahead part (b) on the information set, rp_max_rc_dev (with both parquet outputs)
- 4.3 `f6b8761` step 4.3: strategy metrics, metrics_all.csv
- 4.4 `b32b5e6` step 4.4: bootstrap Sharpe intervals, sharpe_intervals.csv
- 4.5 `e7dcd83` step 4.5: primary results table, results_primary.csv
- 4.6 `e5e84cf` step 4.6: charts 1 and 2, frontier against out-of-sample and stacked weights
- `7d88eda` section 4: open decision 6 (Sharpe ddof)

## Rule 4 stop: `test_no_look_ahead` part (b) (session 4; resolved in session 4b by decision 5, option 2)

Amendment 4.2.9(b) multiplies every price dated after t = 2010-06-30 (the 3rd decision date) by its own Uniform(0.5, 1.5) factor, seed `run.seed_master`. It then asserts that the weights at t of the specs that do not use w_prev are unchanged.

The previous decision's holding period runs from 2010-06-01 to 2010-07-01. It ends after t, so the perturbation changes that realised return. `mv_unconstrained|sample|sample|A` holds 39.9 gross leverage there, and its return goes from +4.7% to −458.4%. Amendment 4.2.8 then marks the fund ruined, and it is not solved at t. With no weights at t, the row-key comparison fails (72 rows against 90). No input used at t changed: the fund stops because of a realised return, not because of look-ahead. Part (a) passes in full: weights and drifted w_prev at all 3 dates ≤ t are equal under `==` for all 8 specs.

The amendment also says "the 6 specs" for part (b). Excluding the 2 `mv_constrained` specs and `black_litterman` from the 8 leaves 5, and the test asserts 5.

Rule 5 forbids rewriting the test so that it passes, so the test is committed exactly as specified and fails. Two options are in `decisions/OPEN.md`, item 5. The diagnostic run, `mv_unconstrained|sample|sample|A` over the first 6 decision dates:

```
  decision_date  exec_date next_exec_date  n_hold_days
0    2010-04-30 2010-05-03     2010-06-01           20
1    2010-05-28 2010-06-01     2010-07-01           22
2    2010-06-30 2010-07-01     2010-08-02           21
3    2010-07-30 2010-08-02     2010-09-01           22
base
  decision_date  exec_date next_exec_date  ret_gross   ret_net  gross_leverage  ruined   status
0    2010-04-30 2010-05-03     2010-06-01   0.291528  0.291528       38.549435   False  optimal
1    2010-05-28 2010-06-01     2010-07-01   0.047211  0.043078       39.863491   False  optimal
2    2010-06-30 2010-07-01     2010-08-02  -0.084468 -0.086536       41.998340   False  optimal
3    2010-07-30 2010-08-02     2010-09-01   0.215580  0.211775       42.948747   False  optimal
4    2010-08-31 2010-09-01     2010-10-01   0.159565  0.157515       37.563414   False  optimal
5    2010-09-30 2010-10-01     2010-11-01   0.210406  0.206538       42.836965   False  optimal
perturbed after t
  decision_date  exec_date next_exec_date  ret_gross   ret_net  gross_leverage  ruined      status
0    2010-04-30 2010-05-03     2010-06-01   0.291528  0.291528       38.549435   False     optimal
1    2010-05-28 2010-06-01     2010-07-01  -4.583686 -1.000000       39.863491    True     optimal
2    2010-06-30 2010-07-01     2010-08-02        NaN       NaN             NaN    True  not_solved
3    2010-07-30 2010-08-02     2010-09-01        NaN       NaN             NaN    True  not_solved
4    2010-08-31 2010-09-01     2010-10-01        NaN       NaN             NaN    True  not_solved
5    2010-09-30 2010-10-01     2010-11-01        NaN       NaN             NaN    True  not_solved
```

## Evidence

### Step 4.0.c: windows under the old rule, extra trading days per window, 196 decision dates

The old window had extra trading days from the month before the 36, counted per window (`extra_days  windows`). This matches the instruction's counts:

```
0    137
1     28
2     27
3      4
```

### Instruction evidence 1: `cov_eval.csv` and `cov_eval_qlike_diff.csv`, old against new

`ewma` is unchanged to the printed digits because the dropped rows carry weights of order 0.97^756. No sign of `diff_vs_lw_cc` flips, and no 90% interval moves to the other side of zero. The step 2.2, 3.5 and 3.6 tests on real-data windows pass unchanged (full suite below).

```
### cov_eval.csv old vs new

estimator portfolio_set  qlike_mean_old  qlike_mean_new  bias_ratio_old  bias_ratio_new  band_lo_old  band_lo_new  band_hi_old  band_hi_new  mean_cond_before_old  mean_cond_before_new  n_ridged_old  n_ridged_new
   sample            ew       -5.854662       -5.854601        0.964685        0.964717     0.916915     0.916915     1.083085     1.083085          10548.367930          10547.936270             0             0
   sample           gmv      -10.942003      -10.942254        1.049475        1.049164     0.916915     0.916915     1.083085     1.083085          10548.367930          10547.936270             0             0
   sample        random       -5.843166       -5.843100        0.963110        0.963145     0.916915     0.916915     1.083085     1.083085          10548.367930          10547.936270             0             0
    lw_cc            ew       -5.854211       -5.854153        0.968583        0.968615     0.916915     0.916915     1.083085     1.083085           8675.543245           8674.830029             0             0
    lw_cc           gmv      -10.901352      -10.901585        1.011532        1.011114     0.916915     0.916915     1.083085     1.083085           8675.543245           8674.830029             0             0
    lw_cc        random       -5.843015       -5.842951        0.965838        0.965874     0.916915     0.916915     1.083085     1.083085           8675.543245           8674.830029             0             0
     ewma            ew       -6.093641       -6.093641        1.039886        1.039886     0.916915     0.916915     1.083085     1.083085          17974.809340          17974.809340             0             0
     ewma           gmv      -10.451710      -10.451710        1.380937        1.380937     0.916915     0.916915     1.083085     1.083085          17974.809340          17974.809340             0             0
     ewma        random       -6.062971       -6.062971        1.041285        1.041285     0.916915     0.916915     1.083085     1.083085          17974.809340          17974.809340             0             0
     pca3            ew       -5.862030       -5.861978        0.948822        0.948852     0.916915     0.916915     1.083085     1.083085           8430.163061           8428.723168             0             0
     pca3           gmv      -10.536559      -10.536979        1.151663        1.151528     0.916915     0.916915     1.083085     1.083085           8430.163061           8428.723168             0             0
     pca3        random       -5.849162       -5.849103        0.949129        0.949163     0.916915     0.916915     1.083085     1.083085           8430.163061           8428.723168             0             0

max abs change per column, cov_eval.csv

          column  max_abs_change
      qlike_mean        0.000420
      bias_ratio        0.000418
         band_lo        0.000000
         band_hi        0.000000
mean_cond_before        1.439893
        n_ridged        0.000000

### cov_eval_qlike_diff.csv old vs new

estimator portfolio_set  diff_vs_lw_cc_old  diff_vs_lw_cc_new   p05_old   p05_new   p95_old   p95_new  frac_le_0_old  frac_le_0_new
   sample            ew          -0.000451          -0.000448 -0.005818 -0.005815  0.003253  0.003257         0.5300         0.5297
   sample           gmv          -0.040651          -0.040669 -0.084657 -0.084695  0.006012  0.005954         0.9247         0.9249
   sample        random          -0.000151          -0.000149 -0.003789 -0.003787  0.002424  0.002427         0.4883         0.4878
     ewma            ew          -0.239430          -0.239488 -0.575783 -0.575984 -0.005263 -0.005369         0.9566         0.9567
     ewma           gmv           0.449642           0.449875 -0.068783 -0.068463  1.239743  1.240137         0.1193         0.1190
     ewma        random          -0.219956          -0.220019 -0.519770 -0.519939 -0.009364 -0.009495         0.9636         0.9637
     pca3            ew          -0.007819          -0.007825 -0.039208 -0.039204  0.011579  0.011570         0.6423         0.6424
     pca3           gmv           0.364793           0.364606  0.267050  0.266772  0.476043  0.476041         0.0000         0.0000
     pca3        random          -0.006147          -0.006152 -0.031731 -0.031744  0.009585  0.009578         0.6418         0.6418

max abs change per column, cov_eval_qlike_diff.csv

       column  max_abs_change
diff_vs_lw_cc        0.000233
          p05        0.000321
          p95        0.000395
    frac_le_0        0.000500

rows where diff_vs_lw_cc changes sign: 0

rows where the 90% interval moves to the other side of zero (excludes zero before xor after): 0
```

### 4.1 The 26 registry ids

```
mv_unconstrained|sample|sample|A
mv_unconstrained|lw_cc|sample|A
mv_unconstrained|ewma|sample|A
mv_unconstrained|pca3|sample|A
mv_constrained|sample|sample|C
mv_constrained|lw_cc|sample|C
mv_constrained|ewma|sample|C
mv_constrained|pca3|sample|C
mv_constrained|lw_cc|bayes_stein|C
min_variance|sample|none|B
min_variance|lw_cc|none|B
min_variance|ewma|none|B
min_variance|pca3|none|B
risk_parity|sample|none|none
risk_parity|lw_cc|none|none
risk_parity|ewma|none|none
risk_parity|pca3|none|none
black_litterman|sample|bl|C
black_litterman|lw_cc|bl|C
black_litterman|ewma|bl|C
black_litterman|pca3|bl|C
hrp|sample|none|none
hrp|lw_cc|none|none
hrp|ewma|none|none
hrp|pca3|none|none
equal_weight|none|none|none
```

### 4.2 Synthetic 3-asset, 5-period path: hand computation against the engine

These are the prices, rf and Config of `tests/test_backtest.py::synthetic`. Costs are 3, 6 and 10 bp. `wealth_hand` is `hand_wealth` in the test: drift, renormalise, cost, then (1 − cost)(1 + w′r). The mv_unconstrained targets are read from the engine's `weights_long`, so the check covers the bookkeeping, not the solve.

```
### mv_unconstrained|sample|sample|A

decision_date              cost          ret_gross            ret_net     wealth_engine       wealth_hand  abs_diff
   2018-01-31 0.000000000000000 -0.074830422846953 -0.074830422846953 0.925169577153047 0.925169577153047       0.0
   2018-02-28 0.000341419877653 -0.041334536881623 -0.041661844326751 0.886625306253850 0.886625306253850       0.0
   2018-03-30 0.000197144355968  0.053885110720413  0.053677343218997 0.934216997124286 0.934216997124286       0.0
   2018-04-30 0.000545724498899  0.041696333160858  0.041127853951439 0.972639337340966 0.972639337340966       0.0
   2018-05-31 0.000183514994185 -0.017172510145166 -0.017352873726251 0.955761249738904 0.955761249738904       0.0

### equal_weight|none|none|none

decision_date              cost          ret_gross            ret_net     wealth_engine       wealth_hand  abs_diff
   2018-01-31 0.000000000000000  0.020329498283897  0.020329498283897 1.020329498283897 1.020329498283897       0.0
   2018-02-28 0.000027203808401  0.002879309972241  0.002852027835643 1.023239506414530 1.023239506414530       0.0
   2018-03-30 0.000029264834905 -0.009289223083549 -0.009318216070874 1.013704739601505 1.013704739601505       0.0
   2018-04-30 0.000040115590364 -0.012918671866459 -0.012958269216675 1.000568880679530 1.000568880679530       0.0
   2018-05-31 0.000021079502813  0.029617853180554  0.029596149348121 1.030181866705204 1.030181866705204       0.0
```

### 4.2 Output shapes

```
periods shape (5096, 25)  weights_long shape (88686, 8)

```

### Instruction evidence 2: per strategy, full 196-date run (n_months, ruined, SCS retries, fallbacks, tau_relaxed months, rp_not_converged, ridged months)

`n_months` counts months with a non-NaN `ret_net`, the ruin month included. `scs_retries` is the total of `solver.count("SCS")`. The two `risk_parity` rows with `rp_not_converged = 1` hold scipy's message as the status (decision 4 of section 3). Ridged months are 0 everywhere.

```
                                    n_months  ruined ruin_month  scs_retries  fallbacks  tau_relaxed  rp_not_converged  ridged
strategy_id                                                                                                                   
mv_unconstrained|sample|sample|A         191    True 2026-02-27            0          0            0                 0       0
mv_unconstrained|lw_cc|sample|A          196   False        NaT            0          0            0                 0       0
mv_unconstrained|ewma|sample|A            37    True 2013-04-30            0          0            0                 0       0
mv_unconstrained|pca3|sample|A           191    True 2026-02-27            0          0            0                 0       0
mv_constrained|sample|sample|C           196   False        NaT           64          0            0                 0       0
mv_constrained|lw_cc|sample|C            196   False        NaT           56          0            0                 0       0
mv_constrained|ewma|sample|C             196   False        NaT           53          0            0                 0       0
mv_constrained|pca3|sample|C             196   False        NaT           74          0            0                 0       0
mv_constrained|lw_cc|bayes_stein|C       196   False        NaT          129          0            0                 0       0
min_variance|sample|none|B               196   False        NaT            0          0            0                 0       0
min_variance|lw_cc|none|B                196   False        NaT            0          0            0                 0       0
min_variance|ewma|none|B                 196   False        NaT            0          0            0                 0       0
min_variance|pca3|none|B                 196   False        NaT            0          0            0                 0       0
risk_parity|sample|none|none             196   False        NaT            0          0            0                 0       0
risk_parity|lw_cc|none|none              196   False        NaT            0          0            0                 0       0
risk_parity|ewma|none|none               196   False        NaT            0          0            0                 1       0
risk_parity|pca3|none|none               196   False        NaT            0          0            0                 1       0
black_litterman|sample|bl|C              196   False        NaT           93          0            0                 0       0
black_litterman|lw_cc|bl|C               196   False        NaT          120          0            0                 0       0
black_litterman|ewma|bl|C                196   False        NaT          148          0            0                 0       0
black_litterman|pca3|bl|C                196   False        NaT          136          0            0                 0       0
hrp|sample|none|none                     196   False        NaT            0          0            0                 0       0
hrp|lw_cc|none|none                      196   False        NaT            0          0            0                 0       0
hrp|ewma|none|none                       196   False        NaT            0          0            0                 0       0
hrp|pca3|none|none                       196   False        NaT            0          0            0                 0       0
equal_weight|none|none|none              196   False        NaT            0          0            0                 0       0
```

Solver strings seen, with counts. `none` on the 5 and 159 post-ruin months of the set A strategies is the not-solved row.

```
                       strategy_id                    solver  months
  mv_unconstrained|sample|sample|A               closed_form     191
  mv_unconstrained|sample|sample|A                      none       5
   mv_unconstrained|lw_cc|sample|A               closed_form     196
    mv_unconstrained|ewma|sample|A               closed_form      37
    mv_unconstrained|ewma|sample|A                      none     159
    mv_unconstrained|pca3|sample|A               closed_form     191
    mv_unconstrained|pca3|sample|A                      none       5
    mv_constrained|sample|sample|C                  CLARABEL       1
    mv_constrained|sample|sample|C         CLARABEL+CLARABEL     140
    mv_constrained|sample|sample|C     CLARABEL+CLARABEL+SCS      42
    mv_constrained|sample|sample|C CLARABEL+SCS+CLARABEL+SCS       9
    mv_constrained|sample|sample|C     CLARABEL+SCS+CLARABEL       4
     mv_constrained|lw_cc|sample|C                  CLARABEL       1
     mv_constrained|lw_cc|sample|C         CLARABEL+CLARABEL     142
     mv_constrained|lw_cc|sample|C CLARABEL+SCS+CLARABEL+SCS       3
     mv_constrained|lw_cc|sample|C     CLARABEL+CLARABEL+SCS      49
     mv_constrained|lw_cc|sample|C     CLARABEL+SCS+CLARABEL       1
      mv_constrained|ewma|sample|C                  CLARABEL       1
      mv_constrained|ewma|sample|C         CLARABEL+CLARABEL     149
      mv_constrained|ewma|sample|C     CLARABEL+CLARABEL+SCS      36
      mv_constrained|ewma|sample|C CLARABEL+SCS+CLARABEL+SCS       7
      mv_constrained|ewma|sample|C     CLARABEL+SCS+CLARABEL       3
      mv_constrained|pca3|sample|C                  CLARABEL       1
      mv_constrained|pca3|sample|C         CLARABEL+CLARABEL     128
      mv_constrained|pca3|sample|C     CLARABEL+CLARABEL+SCS      57
      mv_constrained|pca3|sample|C     CLARABEL+SCS+CLARABEL       3
      mv_constrained|pca3|sample|C CLARABEL+SCS+CLARABEL+SCS       7
mv_constrained|lw_cc|bayes_stein|C                  CLARABEL       1
mv_constrained|lw_cc|bayes_stein|C     CLARABEL+CLARABEL+SCS      89
mv_constrained|lw_cc|bayes_stein|C CLARABEL+SCS+CLARABEL+SCS      20
mv_constrained|lw_cc|bayes_stein|C         CLARABEL+CLARABEL      86
        min_variance|sample|none|B                  CLARABEL     196
         min_variance|lw_cc|none|B                  CLARABEL     196
          min_variance|ewma|none|B                  CLARABEL     196
          min_variance|pca3|none|B                  CLARABEL     196
      risk_parity|sample|none|none                  L-BFGS-B     196
       risk_parity|lw_cc|none|none                  L-BFGS-B     196
        risk_parity|ewma|none|none                  L-BFGS-B     196
        risk_parity|pca3|none|none                  L-BFGS-B     196
       black_litterman|sample|bl|C                  CLARABEL       1
       black_litterman|sample|bl|C         CLARABEL+CLARABEL     126
       black_litterman|sample|bl|C CLARABEL+SCS+CLARABEL+SCS      24
       black_litterman|sample|bl|C     CLARABEL+CLARABEL+SCS      40
       black_litterman|sample|bl|C     CLARABEL+SCS+CLARABEL       5
        black_litterman|lw_cc|bl|C                  CLARABEL       1
        black_litterman|lw_cc|bl|C         CLARABEL+CLARABEL     109
        black_litterman|lw_cc|bl|C CLARABEL+SCS+CLARABEL+SCS      34
        black_litterman|lw_cc|bl|C     CLARABEL+CLARABEL+SCS      48
        black_litterman|lw_cc|bl|C     CLARABEL+SCS+CLARABEL       4
         black_litterman|ewma|bl|C                  CLARABEL       1
         black_litterman|ewma|bl|C         CLARABEL+CLARABEL      85
         black_litterman|ewma|bl|C     CLARABEL+CLARABEL+SCS      70
         black_litterman|ewma|bl|C CLARABEL+SCS+CLARABEL+SCS      38
         black_litterman|ewma|bl|C     CLARABEL+SCS+CLARABEL       2
         black_litterman|pca3|bl|C                  CLARABEL       1
         black_litterman|pca3|bl|C         CLARABEL+CLARABEL      88
         black_litterman|pca3|bl|C CLARABEL+SCS+CLARABEL+SCS      29
         black_litterman|pca3|bl|C     CLARABEL+CLARABEL+SCS      76
         black_litterman|pca3|bl|C     CLARABEL+SCS+CLARABEL       2
              hrp|sample|none|none                      none     196
               hrp|lw_cc|none|none                      none     196
                hrp|ewma|none|none                      none     196
                hrp|pca3|none|none                      none     196
       equal_weight|none|none|none                      none     196
```

### 4.2 `periods`, first and last 3 rows, `min_variance|lw_cc|none|B`

```
                                       1960                       1961                       1962                       2153                       2154                       2155
strategy_id       min_variance|lw_cc|none|B  min_variance|lw_cc|none|B  min_variance|lw_cc|none|B  min_variance|lw_cc|none|B  min_variance|lw_cc|none|B  min_variance|lw_cc|none|B
decision_date           2010-04-30 00:00:00        2010-05-28 00:00:00        2010-06-30 00:00:00        2026-05-29 00:00:00        2026-06-30 00:00:00        2026-07-31 00:00:00
exec_date               2010-05-03 00:00:00        2010-06-01 00:00:00        2010-07-01 00:00:00        2026-06-01 00:00:00        2026-07-01 00:00:00        2026-08-03 00:00:00
next_exec_date          2010-06-01 00:00:00        2010-07-01 00:00:00        2010-08-02 00:00:00        2026-07-01 00:00:00        2026-08-03 00:00:00        2026-09-01 00:00:00
ret_gross                         -0.000122                   0.009243                   0.014747                  -0.007479                   0.004551                   0.006744
cost                                    0.0                    0.00001                   0.000007                   0.000003                   0.000007                   0.000009
ret_net                           -0.000122                   0.009233                   0.014739                  -0.007482                   0.004543                   0.006735
rf_hold                            0.000127                   0.000108                   0.000131                   0.003181                   0.003381                   0.003236
excess_net                        -0.000249                   0.009125                   0.014608                  -0.010662                   0.001162                     0.0035
forecast_vol_ann                   0.048424                   0.048539                   0.048215                   0.034339                    0.03411                   0.033195
mu_exante                          0.003648                   0.003902                   0.004395                   0.001059                   0.000808                   0.000653
turnover                                NaN                   0.029232                   0.020157                   0.005562                   0.014601                   0.018477
n_positions                             9.0                        9.0                       11.0                        6.0                        6.0                        5.0
gross_leverage                          1.0                        1.0                        1.0                        1.0                        1.0                        1.0
solver                             CLARABEL                   CLARABEL                   CLARABEL                   CLARABEL                   CLARABEL                   CLARABEL
status                              optimal                    optimal                    optimal                    optimal                    optimal                    optimal
fallback                              False                      False                      False                      False                      False                      False
turnover_dual                           NaN                        NaN                        NaN                        NaN                        NaN                        NaN
tau_relaxed                           False                      False                      False                      False                      False                      False
tau_eff                                 NaN                        NaN                        NaN                        NaN                        NaN                        NaN
cond_before                     7961.615558                8209.500928                8348.281261                2785.227189                2927.274009                 3059.16311
cond_after                      7961.615558                8209.500928                8348.281261                2785.227189                2927.274009                 3059.16311
ridge                                   0.0                        0.0                        0.0                        0.0                        0.0                        0.0
ruined                                False                      False                      False                      False                      False                      False
rp_converged                           True                       True                       True                       True                       True                       True
```

### Instruction evidence 4: `mv_unconstrained|sample|sample|A`

```
min     26.698856
50%     65.301314
max    129.225054

5 worst months by ret_net

decision_date  ret_gross     cost   ret_net  gross_leverage  ruined
   2026-02-27  -1.004302 0.011257 -1.000000       86.675235    True
   2016-03-31  -0.739904 0.022669 -0.745800       62.948203   False
   2013-04-30  -0.699766 0.007681 -0.702072      107.337343   False
   2015-03-31  -0.619743 0.007651 -0.622653       68.466047   False
   2015-07-31  -0.494209 0.015161 -0.501878       66.847728   False

ruined rows

strategy_id
mv_unconstrained|sample|sample|A   2026-02-27
mv_unconstrained|ewma|sample|A     2013-04-30
mv_unconstrained|pca3|sample|A     2026-02-27
```

The full table above also has the other 2 ruined set A strategies: `mv_unconstrained|ewma|sample|A` ruined at 2013-04-30 and `mv_unconstrained|pca3|sample|A` at 2026-02-27.

### Instruction evidence 5 and 6: turnover dual, and the reconciliation at the 3rd decision date

```
### mv_constrained|lw_cc|sample|C, turnover_dual (bp of monthly return per 1% of turnover = dual x 100)

                definition  binding_months  mean_dual_bp_per_1pct  median_dual_bp_per_1pct
turnover >= tau_eff - 1e-6              62         0.061492361039           0.041559088785
      turnover_dual > 1e-8              62         0.061492361039           0.041559088785

months with turnover recorded: 195; max dual over slack months (turnover < tau_eff - 1e-6): 2.119e-11

### reconciliation, min_variance|lw_cc|none|B, decision 2010-06-30, exec 2010-07-01 to 2010-08-02

              w_target  w_prev_drifted           trade              cost_i     c_i          r_hold
ticker                                                                                            
SPY     0.000000000051  0.000000000136 -0.000000000085  2.548480591719e-14  0.0003  0.097314488862
IWM     0.005033157923  0.003090859933  0.001942297990  5.826893968968e-07  0.0003  0.093731866811
EFA     0.000000000008  0.000000000023 -0.000000000015  4.475579651452e-15  0.0003  0.137104946211
EEM     0.000000000011  0.000000000031 -0.000000000021  1.231119384560e-14  0.0006  0.129821524254
XLE     0.000000000009  0.000000000025 -0.000000000016  4.789823936047e-15  0.0003  0.125656515350
XLF     0.000000000024  0.000000000060 -0.000000000036  1.071585070696e-14  0.0003  0.102339043631
XLK     0.046332311294  0.046334045124 -0.000001733830  5.201490599738e-10  0.0003  0.101377886113
XLU     0.008245115891  0.002855850542  0.005389265349  1.616779604635e-06  0.0003  0.102026176581
XLV     0.037971614840  0.038985230362 -0.001013615522  3.040846567104e-07  0.0003  0.041129992093
SHY     0.299999999996  0.298398263353  0.001601736643  4.805209928072e-07  0.0003  0.002036373048
IEF     0.299999999981  0.305783568277 -0.005783568296  1.735070488844e-06  0.0003  0.006418235273
TLT     0.000000000006  0.000000000017 -0.000000000012  3.492355172876e-15  0.0003 -0.024907069554
TIP     0.195354066827  0.195285367070  0.000068699757  4.121985415378e-08  0.0006  0.005115323475
LQD     0.031049254382  0.031247856361 -0.000198601979  5.958059374695e-08  0.0003  0.017811704027
HYG     0.032680873662  0.034846815201 -0.002165941539  1.299564923491e-06  0.0006  0.051984718651
GLD     0.025867714541  0.024791001187  0.001076713355  3.230140064062e-07  0.0003 -0.012816131137
DBC     0.017465890385  0.018381142008 -0.000915251624  5.491509741293e-07  0.0006  0.098399097580
VNQ     0.000000000170  0.000000000288 -0.000000000118  7.107254260220e-14  0.0006  0.136628047403
                 quantity     recomputed  periods.parquet
             sum w_target 1.000000000000              NaN
       sum w_prev_drifted 1.000000000000              NaN
    turnover = sum|trade| 0.020157426185   0.020157426185
        cost = sum cost_i 0.000006992196   0.000006992196
              gross = w'r 0.014746560691   0.014746560691
net = (1-cost)(1+gross)-1 0.014739465384   0.014739465384
```

### Not produced (steps 4.3 to 4.6 not started)

Instruction evidence 3 (`metrics_all.csv`, `sharpe_intervals.csv`, `results_primary.csv`), and PLAN evidence for 4.3 to 4.6.

### Session 4b

Session 4b (`instructions/04b_section_4_completion.md`) finished step 4.2 and ran steps 4.3 to 4.6. Every figure below comes from the final run at `dcebb48`, whose outputs are committed. A second full run (walk forward, 3 tables, 2 charts) reproduced every output file byte for byte: both parquet files, the 3 CSVs and the 2 PNGs, compared by MD5.

**Replacement of session 4 evidence.**
- Instruction evidence 2, 4, 5 and 6 below replace the session 4 versions above. Every value is unchanged from session 4, because the engine's arithmetic did not change; the only addition is the `rp_max_rc_dev` column.
- Instruction evidence 7 (runtime) replaces the session 4 runtime. This run was faster on the same machine.
- The PLAN 4.2 synthetic hand-computed path above stands: `test_synthetic_3_asset_5_period_wealth` passes unchanged.

#### 1. `test_no_look_ahead` part (b), rewritten (decisions/section_4_review.md, 1)

Part (a) is unchanged. Part (b) as committed:

```python
    # (b) prices after t: the information set at t is unchanged (decisions/section_4_review.md, 1).
    # mu and Sigma at t, Black-Litterman's inputs and posterior, and the allocator output at t of
    # the 5 specs that do not use w_prev, called with w_prev = None, are equal under ==.
    def inputs_at_t(prices):
        return DateInputs(t, daily_returns(prices), monthly_excess_returns(prices, real.rf_daily),
                          monthly_total_returns(prices), cfg)

    before = inputs_at_t(real.prices)
    after = inputs_at_t(perturbed_prices(real.prices, t, cfg.run.seed_master))
    assert not perturbed_prices(real.prices, t, cfg.run.seed_master).equals(real.prices)

    def same(x, y):
        assert x.equals(y)
        assert np.array_equal(x.to_numpy(), y.to_numpy())

    for est in cfg.cov.estimators:
        same(before.sigma(est)[0], after.sigma(est)[0])
        log_b, log_a = before.sigma(est)[1], after.sigma(est)[1]
        assert log_b.keys() == log_a.keys()
        assert all(np.array_equal([log_b[k]], [log_a[k]], equal_nan=True) for k in log_b), est
    same(before.mu_sample, after.mu_sample)
    same(before.mu_bayes_stein(), after.mu_bayes_stein())
    same(before.pi("lw_cc"), after.pi("lw_cc"))
    for x, y in zip(before.views(), after.views()):
        same(x, y)
    for x, y in zip(before.bl("lw_cc"), after.bl("lw_cc")):
        same(x, y)

    # The instruction's "6 specs" was a miscount: 8 - 3 = 5 (decisions/section_4_review.md, 1).
    keep = [s for s in specs if s.id not in USES_W_PREV]
    assert len(keep) == 5
    cons = constraint_sets(cfg)
    for spec in keep:
        outs = []
        for inputs in (before, after):
            mu, Sigma, _, _ = inputs.for_spec(spec)
            outs.append(backtest.ALLOCATORS[spec.allocator](mu, Sigma, None, cons[spec.cons_set]))
        x, y = outs
        same(x.weights, y.weights)
        assert (x.solver, x.status, x.fallback) == (y.solver, y.status, y.fallback)
        assert np.array_equal([x.objective], [y.objective], equal_nan=True), spec.id
```

The same comparison, printed. `max_abs_diff` is the largest absolute difference between the unperturbed and perturbed values. The first row shows the perturbation is real:

```
t = 2010-06-30, perturbation: prices dated after t times Uniform(0.5, 1.5), seed run.seed_master

                                                               object      shape  equal_==  max_abs_diff
                                                       prices after t (4889, 18)     False    374.015057
                                                         Sigma sample   (18, 18)      True      0.000000
                                                          Sigma lw_cc   (18, 18)      True      0.000000
                                                           Sigma ewma   (18, 18)      True      0.000000
                                                           Sigma pca3   (18, 18)      True      0.000000
                                                            mu_sample      (18,)      True      0.000000
                                                                mu_BS      (18,)      True      0.000000
                                                             Pi lw_cc      (18,)      True      0.000000
                                                                    P    (2, 18)      True      0.000000
                                                                    Q       (2,)      True      0.000000
                                                          mu_BL lw_cc      (18,)      True      0.000000
                                                       Sigma_BL lw_cc   (18, 18)      True      0.000000
weights at t, mv_unconstrained|sample|sample|A (closed_form, optimal)      (18,)      True      0.000000
           weights at t, min_variance|ewma|none|B (CLARABEL, optimal)      (18,)      True      0.000000
         weights at t, risk_parity|pca3|none|none (L-BFGS-B, optimal)      (18,)      True      0.000000
                   weights at t, hrp|sample|none|none (none, optimal)      (18,)      True      0.000000
            weights at t, equal_weight|none|none|none (none, optimal)      (18,)      True      0.000000
```

`tests/test_backtest.py`: `6 passed` (full output under Tests run below).

#### 2. Instruction evidence 2: per strategy, final run

Columns: n_months, ruined, ruin month, SCS retries, fallbacks, tau_relaxed months, rp_not_converged, ridged months.

```
                                    n_months  ruined ruin_month  scs_retries  fallbacks  tau_relaxed  rp_not_converged  ridged
strategy_id                                                                                                                   
mv_unconstrained|sample|sample|A         191    True 2026-02-27            0          0            0                 0       0
mv_unconstrained|lw_cc|sample|A          196   False        NaT            0          0            0                 0       0
mv_unconstrained|ewma|sample|A            37    True 2013-04-30            0          0            0                 0       0
mv_unconstrained|pca3|sample|A           191    True 2026-02-27            0          0            0                 0       0
mv_constrained|sample|sample|C           196   False        NaT           64          0            0                 0       0
mv_constrained|lw_cc|sample|C            196   False        NaT           56          0            0                 0       0
mv_constrained|ewma|sample|C             196   False        NaT           53          0            0                 0       0
mv_constrained|pca3|sample|C             196   False        NaT           74          0            0                 0       0
mv_constrained|lw_cc|bayes_stein|C       196   False        NaT          129          0            0                 0       0
min_variance|sample|none|B               196   False        NaT            0          0            0                 0       0
min_variance|lw_cc|none|B                196   False        NaT            0          0            0                 0       0
min_variance|ewma|none|B                 196   False        NaT            0          0            0                 0       0
min_variance|pca3|none|B                 196   False        NaT            0          0            0                 0       0
risk_parity|sample|none|none             196   False        NaT            0          0            0                 0       0
risk_parity|lw_cc|none|none              196   False        NaT            0          0            0                 0       0
risk_parity|ewma|none|none               196   False        NaT            0          0            0                 1       0
risk_parity|pca3|none|none               196   False        NaT            0          0            0                 1       0
black_litterman|sample|bl|C              196   False        NaT           93          0            0                 0       0
black_litterman|lw_cc|bl|C               196   False        NaT          120          0            0                 0       0
black_litterman|ewma|bl|C                196   False        NaT          148          0            0                 0       0
black_litterman|pca3|bl|C                196   False        NaT          136          0            0                 0       0
hrp|sample|none|none                     196   False        NaT            0          0            0                 0       0
hrp|lw_cc|none|none                      196   False        NaT            0          0            0                 0       0
hrp|ewma|none|none                       196   False        NaT            0          0            0                 0       0
hrp|pca3|none|none                       196   False        NaT            0          0            0                 0       0
equal_weight|none|none|none              196   False        NaT            0          0            0                 0       0
```

Solver strings seen, with counts:

```
                       strategy_id                    solver  months
  mv_unconstrained|sample|sample|A               closed_form     191
  mv_unconstrained|sample|sample|A                      none       5
   mv_unconstrained|lw_cc|sample|A               closed_form     196
    mv_unconstrained|ewma|sample|A               closed_form      37
    mv_unconstrained|ewma|sample|A                      none     159
    mv_unconstrained|pca3|sample|A               closed_form     191
    mv_unconstrained|pca3|sample|A                      none       5
    mv_constrained|sample|sample|C                  CLARABEL       1
    mv_constrained|sample|sample|C         CLARABEL+CLARABEL     140
    mv_constrained|sample|sample|C     CLARABEL+CLARABEL+SCS      42
    mv_constrained|sample|sample|C CLARABEL+SCS+CLARABEL+SCS       9
    mv_constrained|sample|sample|C     CLARABEL+SCS+CLARABEL       4
     mv_constrained|lw_cc|sample|C                  CLARABEL       1
     mv_constrained|lw_cc|sample|C         CLARABEL+CLARABEL     142
     mv_constrained|lw_cc|sample|C CLARABEL+SCS+CLARABEL+SCS       3
     mv_constrained|lw_cc|sample|C     CLARABEL+CLARABEL+SCS      49
     mv_constrained|lw_cc|sample|C     CLARABEL+SCS+CLARABEL       1
      mv_constrained|ewma|sample|C                  CLARABEL       1
      mv_constrained|ewma|sample|C         CLARABEL+CLARABEL     149
      mv_constrained|ewma|sample|C     CLARABEL+CLARABEL+SCS      36
      mv_constrained|ewma|sample|C CLARABEL+SCS+CLARABEL+SCS       7
      mv_constrained|ewma|sample|C     CLARABEL+SCS+CLARABEL       3
      mv_constrained|pca3|sample|C                  CLARABEL       1
      mv_constrained|pca3|sample|C         CLARABEL+CLARABEL     128
      mv_constrained|pca3|sample|C     CLARABEL+CLARABEL+SCS      57
      mv_constrained|pca3|sample|C     CLARABEL+SCS+CLARABEL       3
      mv_constrained|pca3|sample|C CLARABEL+SCS+CLARABEL+SCS       7
mv_constrained|lw_cc|bayes_stein|C                  CLARABEL       1
mv_constrained|lw_cc|bayes_stein|C     CLARABEL+CLARABEL+SCS      89
mv_constrained|lw_cc|bayes_stein|C CLARABEL+SCS+CLARABEL+SCS      20
mv_constrained|lw_cc|bayes_stein|C         CLARABEL+CLARABEL      86
        min_variance|sample|none|B                  CLARABEL     196
         min_variance|lw_cc|none|B                  CLARABEL     196
          min_variance|ewma|none|B                  CLARABEL     196
          min_variance|pca3|none|B                  CLARABEL     196
      risk_parity|sample|none|none                  L-BFGS-B     196
       risk_parity|lw_cc|none|none                  L-BFGS-B     196
        risk_parity|ewma|none|none                  L-BFGS-B     196
        risk_parity|pca3|none|none                  L-BFGS-B     196
       black_litterman|sample|bl|C                  CLARABEL       1
       black_litterman|sample|bl|C         CLARABEL+CLARABEL     126
       black_litterman|sample|bl|C CLARABEL+SCS+CLARABEL+SCS      24
       black_litterman|sample|bl|C     CLARABEL+CLARABEL+SCS      40
       black_litterman|sample|bl|C     CLARABEL+SCS+CLARABEL       5
        black_litterman|lw_cc|bl|C                  CLARABEL       1
        black_litterman|lw_cc|bl|C         CLARABEL+CLARABEL     109
        black_litterman|lw_cc|bl|C CLARABEL+SCS+CLARABEL+SCS      34
        black_litterman|lw_cc|bl|C     CLARABEL+CLARABEL+SCS      48
        black_litterman|lw_cc|bl|C     CLARABEL+SCS+CLARABEL       4
         black_litterman|ewma|bl|C                  CLARABEL       1
         black_litterman|ewma|bl|C         CLARABEL+CLARABEL      85
         black_litterman|ewma|bl|C     CLARABEL+CLARABEL+SCS      70
         black_litterman|ewma|bl|C CLARABEL+SCS+CLARABEL+SCS      38
         black_litterman|ewma|bl|C     CLARABEL+SCS+CLARABEL       2
         black_litterman|pca3|bl|C                  CLARABEL       1
         black_litterman|pca3|bl|C         CLARABEL+CLARABEL      88
         black_litterman|pca3|bl|C CLARABEL+SCS+CLARABEL+SCS      29
         black_litterman|pca3|bl|C     CLARABEL+CLARABEL+SCS      76
         black_litterman|pca3|bl|C     CLARABEL+SCS+CLARABEL       2
              hrp|sample|none|none                      none     196
               hrp|lw_cc|none|none                      none     196
                hrp|ewma|none|none                      none     196
                hrp|pca3|none|none                      none     196
       equal_weight|none|none|none                      none     196
```

#### 3. Instruction evidence 3: `metrics_all.csv`, `sharpe_intervals.csv`, `results_primary.csv` in full

The Sharpe std uses ddof 1 (`decisions/OPEN.md` item 6, implemented as option 1). A ruined strategy keeps its point Sharpe over the months of its wealth path, and its interval and every difference involving it are NaN (amendment 4.2.8).

`metrics_all.csv`:

```
                           strategy_id  n_months  ruined  ann_return   ann_vol    sharpe    max_dd  forecast_vol_ann  fcst_realised_ratio  mean_turnover  mean_positions  scs_retries  fallbacks  rp_not_converged  ridged_months
0     mv_unconstrained|sample|sample|A       191    True   -1.000000  1.090393  0.622371 -1.000000          0.956309             0.877032      29.078182       17.984293            0          0                 0              0
1      mv_unconstrained|lw_cc|sample|A       196   False    0.062770  1.029541  0.628156 -0.981780          0.920172             0.893769      24.166028       17.984694            0          0                 0              0
2       mv_unconstrained|ewma|sample|A        37    True   -1.000000  2.153179  1.153958 -1.000000          1.561014             0.724981     167.438600       17.972973            0          0                 0              0
3       mv_unconstrained|pca3|sample|A       191    True   -1.000000  1.512246  0.779414 -1.000000          1.046186             0.691809      37.228895       17.973822            0          0                 0              0
4       mv_constrained|sample|sample|C       196   False    0.092342  0.119524  0.672855 -0.174216          0.135873             1.136787       0.176714        4.525510           64          0                 0              0
5        mv_constrained|lw_cc|sample|C       196   False    0.092619  0.119770  0.673838 -0.172778          0.136186             1.137056       0.176746        4.556122           56          0                 0              0
6         mv_constrained|ewma|sample|C       196   False    0.091729  0.122230  0.655955 -0.215423          0.124942             1.022185       0.197348        4.459184           53          0                 0              0
7         mv_constrained|pca3|sample|C       196   False    0.091674  0.120499  0.663288 -0.181173          0.136589             1.133524       0.180481        4.474490           74          0                 0              0
8   mv_constrained|lw_cc|bayes_stein|C       196   False    0.087062  0.101726  0.722733 -0.184901          0.114036             1.121004       0.133855        5.132653          129          0                 0              0
9           min_variance|sample|none|B       196   False    0.032295  0.036430  0.464349 -0.105645          0.035214             0.966616       0.033827        6.622449            0          0                 0              0
10           min_variance|lw_cc|none|B       196   False    0.031865  0.036458  0.452632 -0.106864          0.035336             0.969215       0.032635        6.632653            0          0                 0              0
11            min_variance|ewma|none|B       196   False    0.028439  0.035029  0.376073 -0.121702          0.028951             0.826481       0.210009        6.372449            0          0                 0              0
12            min_variance|pca3|none|B       196   False    0.032659  0.036271  0.475599 -0.104465          0.035669             0.983402       0.036289        6.469388            0          0                 0              0
13        risk_parity|sample|none|none       196   False    0.040097  0.039706  0.627350 -0.092200          0.039038             0.983154       0.021485       18.000000            0          0                 0              0
14         risk_parity|lw_cc|none|none       196   False    0.040323  0.039860  0.630492 -0.092319          0.039366             0.987598       0.021301       18.000000            0          0                 0              0
15          risk_parity|ewma|none|none       196   False    0.038317  0.040657  0.569733 -0.103615          0.034374             0.845452       0.119750       17.928571            0          0                 1              0
16          risk_parity|pca3|none|none       196   False    0.040452  0.040135  0.629211 -0.093228          0.040517             1.009510       0.021855       18.000000            0          0                 1              0
17         black_litterman|sample|bl|C       196   False    0.083093  0.132856  0.553520 -0.214491          0.162579             1.223717       0.230429        5.632653           93          0                 0              0
18          black_litterman|lw_cc|bl|C       196   False    0.082675  0.133285  0.549260 -0.215901          0.162180             1.216795       0.231685        5.607143          120          0                 0              0
19           black_litterman|ewma|bl|C       196   False    0.087992  0.139177  0.567152 -0.265400          0.137753             0.989770       0.248460        4.989796          148          0                 0              0
20           black_litterman|pca3|bl|C       196   False    0.071000  0.131409  0.472438 -0.206818          0.163732             1.245971       0.222082        5.693878          136          0                 0              0
21                hrp|sample|none|none       196   False    0.018185  0.017828  0.156376 -0.062504          0.016498             0.925400       0.021147        6.836735            0          0                 0              0
22                 hrp|lw_cc|none|none       196   False    0.018168  0.017827  0.155387 -0.062555          0.016493             0.925123       0.020885        6.841837            0          0                 0              0
23                  hrp|ewma|none|none       196   False    0.016644  0.019226  0.064236 -0.071549          0.015142             0.787543       0.095051        7.122449            0          0                 0              0
24                  hrp|pca3|none|none       196   False    0.018391  0.017661  0.170525 -0.062934          0.016574             0.938468       0.019815        6.658163            0          0                 0              0
25         equal_weight|none|none|none       196   False    0.082506  0.097640  0.705100 -0.173293          0.112146             1.148557       0.026806       18.000000            0          0                 0              0
```

`sharpe_intervals.csv`. Columns are renamed for print width only: `EW` = `equal_weight|none|none|none` and `MV` = `min_variance|lw_cc|none|B`. The file carries the full ids, for example `diff_vs_equal_weight|none|none|none`. The bootstrap uses 10,000 paths, mean block 6 and seed `run.bootstrap_seed`, with the same paths for every strategy.

```
                           strategy_id  ruined    sharpe  sharpe_p05  sharpe_p95  diff_vs_EW  diff_p05_vs_EW  diff_p95_vs_EW  frac_le_0_vs_EW  diff_vs_MV  diff_p05_vs_MV  diff_p95_vs_MV  frac_le_0_vs_MV
0     mv_unconstrained|sample|sample|A    True  0.622371         NaN         NaN         NaN             NaN             NaN              NaN         NaN             NaN             NaN              NaN
1      mv_unconstrained|lw_cc|sample|A   False  0.628156    0.198771    1.071190   -0.076945       -0.670889        0.443490           0.6113    0.175523       -0.430054        0.675263           0.3305
2       mv_unconstrained|ewma|sample|A    True  1.153958         NaN         NaN         NaN             NaN             NaN              NaN         NaN             NaN             NaN              NaN
3       mv_unconstrained|pca3|sample|A    True  0.779414         NaN         NaN         NaN             NaN             NaN              NaN         NaN             NaN             NaN              NaN
4       mv_constrained|sample|sample|C   False  0.672855    0.360651    1.027657   -0.032245       -0.310445        0.215652           0.6002    0.220223       -0.220803        0.591316           0.2014
5        mv_constrained|lw_cc|sample|C   False  0.673838    0.363273    1.026701   -0.031262       -0.309009        0.215949           0.5965    0.221206       -0.222360        0.594134           0.2018
6         mv_constrained|ewma|sample|C   False  0.655955    0.339952    1.008693   -0.049145       -0.301045        0.181784           0.6522    0.203323       -0.249109        0.583216           0.2247
7         mv_constrained|pca3|sample|C   False  0.663288    0.350290    1.016614   -0.041813       -0.316807        0.201193           0.6228    0.210655       -0.233428        0.580817           0.2140
8   mv_constrained|lw_cc|bayes_stein|C   False  0.722733    0.352173    1.115705    0.017633       -0.305559        0.315881           0.4863    0.270101       -0.125916        0.603237           0.1311
9           min_variance|sample|none|B   False  0.464349    0.006079    1.024720   -0.240751       -0.628143        0.204006           0.8240    0.011717        0.004861        0.020028           0.0012
10           min_variance|lw_cc|none|B   False  0.452632   -0.002685    1.010246   -0.252468       -0.640389        0.192814           0.8354    0.000000        0.000000        0.000000           1.0000
11            min_variance|ewma|none|B   False  0.376073   -0.095904    0.964529   -0.329028       -0.720729        0.127366           0.8867   -0.076559       -0.168255        0.031878           0.8809
12            min_variance|pca3|none|B   False  0.475599    0.014671    1.039967   -0.229502       -0.617436        0.220767           0.8091    0.022967        0.004153        0.045046           0.0200
13        risk_parity|sample|none|none   False  0.627350    0.218027    1.125944   -0.077750       -0.356831        0.240375           0.6593    0.174718       -0.008810        0.354827           0.0576
14         risk_parity|lw_cc|none|none   False  0.630492    0.220947    1.127695   -0.074608       -0.352183        0.240725           0.6548    0.177860       -0.006673        0.358508           0.0557
15          risk_parity|ewma|none|none   False  0.569733    0.169872    1.091148   -0.135368       -0.415953        0.226259           0.7429    0.117100       -0.077138        0.320041           0.1480
16          risk_parity|pca3|none|none   False  0.629211    0.218706    1.129715   -0.075890       -0.354370        0.241906           0.6552    0.176579       -0.003187        0.352226           0.0525
17         black_litterman|sample|bl|C   False  0.553520    0.268061    0.858502   -0.151580       -0.507629        0.161973           0.7845    0.100888       -0.499522        0.620250           0.3923
18          black_litterman|lw_cc|bl|C   False  0.549260    0.264796    0.853977   -0.155841       -0.510702        0.157397           0.7905    0.096628       -0.502310        0.614543           0.3975
19           black_litterman|ewma|bl|C   False  0.567152    0.270766    0.908712   -0.137948       -0.495733        0.195010           0.7459    0.114520       -0.513156        0.654475           0.3801
20           black_litterman|pca3|bl|C   False  0.472438    0.197775    0.776752   -0.232662       -0.554984        0.041218           0.9176    0.019806       -0.551429        0.510285           0.4888
21                hrp|sample|none|none   False  0.156376   -0.312472    0.725426   -0.548725       -1.023344       -0.012881           0.9529   -0.296256       -0.541581       -0.040267           0.9709
22                 hrp|lw_cc|none|none   False  0.155387   -0.312194    0.723778   -0.549713       -1.024074       -0.014276           0.9535   -0.297245       -0.542335       -0.041275           0.9713
23                  hrp|ewma|none|none   False  0.064236   -0.377306    0.622402   -0.640865       -1.095534       -0.108249           0.9748   -0.388396       -0.639802       -0.134424           0.9911
24                  hrp|pca3|none|none   False  0.170525   -0.297544    0.734302   -0.534575       -1.004762       -0.001242           0.9502   -0.282107       -0.538426       -0.014513           0.9585
25         equal_weight|none|none|none   False  0.705100    0.387164    1.110210    0.000000        0.000000        0.000000           1.0000    0.252468       -0.192814        0.640389           0.1646
```

`results_primary.csv`:

```
                        strategy_id         allocator covariance  ruined  ann_return   ann_vol    sharpe  sharpe_p05  sharpe_p95  forecast_vol_ann  realised_vol_ann  fcst_realised_ratio  mean_turnover    max_dd  mean_positions  fallbacks  ridged_months
0  mv_unconstrained|sample|sample|A  mv_unconstrained     sample    True   -1.000000  1.090393  0.622371         NaN         NaN          0.956309          1.090393             0.877032      29.078182 -1.000000       17.984293          0              0
1     mv_constrained|lw_cc|sample|C    mv_constrained      lw_cc   False    0.092619  0.119770  0.673838    0.363273    1.026701          0.136186          0.119770             1.137056       0.176746 -0.172778        4.556122          0              0
2         min_variance|lw_cc|none|B      min_variance      lw_cc   False    0.031865  0.036458  0.452632   -0.002685    1.010246          0.035336          0.036458             0.969215       0.032635 -0.106864        6.632653          0              0
3        risk_parity|ewma|none|none       risk_parity       ewma   False    0.038317  0.040657  0.569733    0.169872    1.091148          0.034374          0.040657             0.845452       0.119750 -0.103615       17.928571          0              0
4        black_litterman|lw_cc|bl|C   black_litterman      lw_cc   False    0.082675  0.133285  0.549260    0.264796    0.853977          0.162180          0.133285             1.216795       0.231685 -0.215901        5.607143          0              0
5              hrp|sample|none|none               hrp     sample   False    0.018185  0.017828  0.156376   -0.312472    0.725426          0.016498          0.017828             0.925400       0.021147 -0.062504        6.836735          0              0
6       equal_weight|none|none|none      equal_weight       none   False    0.082506  0.097640  0.705100    0.387164    1.110210          0.112146          0.097640             1.148557       0.026806 -0.173293       18.000000          0              0
```

#### 4. Instruction evidence 4: `mv_unconstrained|sample|sample|A`

```
gross leverage, months solved
min     26.698856
50%     65.301314
max    129.225054

5 worst months by ret_net
decision_date  ret_gross     cost   ret_net  gross_leverage  ruined
   2026-02-27  -1.004302 0.011257 -1.000000       86.675235    True
   2016-03-31  -0.739904 0.022669 -0.745800       62.948203   False
   2013-04-30  -0.699766 0.007681 -0.702072      107.337343   False
   2015-03-31  -0.619743 0.007651 -0.622653       68.466047   False
   2015-07-31  -0.494209 0.015161 -0.501878       66.847728   False

ruin month
decision_date  exec_date next_exec_date  ret_gross  ret_net  gross_leverage
   2026-02-27 2026-03-02     2026-04-01  -1.004302     -1.0       86.675235
```

#### 5. Instruction evidence 5: `mv_constrained|lw_cc|sample|C` turnover dual

```
                                  value
months_with_turnover       1.950000e+02
binding_months             6.200000e+01
binding_with_dual_gt_1e-8  6.200000e+01
mean_dual_bp_per_1pct      6.149236e-02
median_dual_bp_per_1pct    4.155909e-02
max_abs_dual_slack         2.119435e-11

Binding: turnover >= tau_eff - 1e-6. bp of monthly return per 1% of turnover = dual x 100.
```

#### 6. Instruction evidence 6: reconciliation, `min_variance|lw_cc|none|B` at the 3rd decision date

```
min_variance|lw_cc|none|B, decision 2010-06-30, exec 2010-07-01 to 2010-08-02

              w_target  w_prev_drifted           trade              cost_i     c_i          r_hold
ticker                                                                                            
SPY     0.000000000051  0.000000000136 -0.000000000085  2.548480591719e-14  0.0003  0.097314488862
IWM     0.005033157923  0.003090859933  0.001942297990  5.826893968968e-07  0.0003  0.093731866811
EFA     0.000000000008  0.000000000023 -0.000000000015  4.475579651452e-15  0.0003  0.137104946211
EEM     0.000000000011  0.000000000031 -0.000000000021  1.231119384560e-14  0.0006  0.129821524254
XLE     0.000000000009  0.000000000025 -0.000000000016  4.789823936047e-15  0.0003  0.125656515350
XLF     0.000000000024  0.000000000060 -0.000000000036  1.071585070696e-14  0.0003  0.102339043631
XLK     0.046332311294  0.046334045124 -0.000001733830  5.201490599738e-10  0.0003  0.101377886113
XLU     0.008245115891  0.002855850542  0.005389265349  1.616779604635e-06  0.0003  0.102026176581
XLV     0.037971614840  0.038985230362 -0.001013615522  3.040846567104e-07  0.0003  0.041129992093
SHY     0.299999999996  0.298398263353  0.001601736643  4.805209928072e-07  0.0003  0.002036373048
IEF     0.299999999981  0.305783568277 -0.005783568296  1.735070488844e-06  0.0003  0.006418235273
TLT     0.000000000006  0.000000000017 -0.000000000012  3.492355172876e-15  0.0003 -0.024907069554
TIP     0.195354066827  0.195285367070  0.000068699757  4.121985415378e-08  0.0006  0.005115323475
LQD     0.031049254382  0.031247856361 -0.000198601979  5.958059374695e-08  0.0003  0.017811704027
HYG     0.032680873662  0.034846815201 -0.002165941539  1.299564923491e-06  0.0006  0.051984718651
GLD     0.025867714541  0.024791001187  0.001076713355  3.230140064062e-07  0.0003 -0.012816131137
DBC     0.017465890385  0.018381142008 -0.000915251624  5.491509741293e-07  0.0006  0.098399097580
VNQ     0.000000000170  0.000000000288 -0.000000000118  7.107254260220e-14  0.0006  0.136628047403

                 quantity     recomputed  periods.parquet
             sum w_target 1.000000000000              NaN
       sum w_prev_drifted 1.000000000000              NaN
    turnover = sum|trade| 0.020157426185   0.020157426185
        cost = sum cost_i 0.000006992196   0.000006992196
              gross = w'r 0.014746560691   0.014746560691
net = (1-cost)(1+gross)-1 0.014739465384   0.014739465384
```

#### 7. `rp_max_rc_dev` for every `rp_converged = False` month

`recomputed` takes the committed weights and the conditioned Σ at that date and recomputes max |pct RC − 1/N|. The two non-converged months here are `ewma` at 2012-06-29 and `pca3` at 2023-01-31, while the reviewer's run had `ewma` at 2010-08-31. That fits the reviewer's note that the flag can differ across platforms. Both sit at about 6e-9, within the range of the converged months (max 7.1e-8, summary below).

```
               strategy_id decision_date     status  rp_max_rc_dev   recomputed
risk_parity|ewma|none|none    2012-06-29 ABNORMAL:    6.329068e-09 6.329068e-09
risk_parity|pca3|none|none    2023-01-31 ABNORMAL:    4.872754e-09 4.872754e-09

rp_max_rc_dev over all risk parity months, by strategy
                              count           max           50%
strategy_id                                                    
risk_parity|sample|none|none  196.0  5.315367e-08  6.950925e-09
risk_parity|lw_cc|none|none   196.0  7.058417e-08  6.337453e-09
risk_parity|ewma|none|none    196.0  4.680835e-08  5.965639e-09
risk_parity|pca3|none|none    196.0  3.683656e-08  6.501821e-09
```

#### 8. Charts

Chart 1, `outputs/figures/frontier_vs_oos.png`:

![Chart 1: in-sample frontiers and out-of-sample strategies](../outputs/figures/frontier_vs_oos.png)

Text box contents:

```
Outside the axes (ann. vol, ann. excess return):
mv_unconstrained (mv_unconstrained|sample|sample|A): 109.1%, 67.9%, ruined
```

Chart 2, `outputs/figures/weights_stacked.png`:

![Chart 2: stacked target weights](../outputs/figures/weights_stacked.png)

PLAN 4.6 evidence: the frontier inputs, every frontier point and the strategy coordinates plotted. Each set B point is a CLARABEL solve, and all 50 are `optimal`.

```
Frontier inputs: annualised mean excess return per asset
SPY    0.127806
IWM    0.105317
EFA    0.069062
EEM    0.052051
XLE    0.102652
XLF    0.111830
XLK    0.186111
XLU    0.093495
XLV    0.116780
SHY   -0.001970
IEF    0.010514
TLT    0.016673
TIP    0.012784
LQD    0.022790
HYG    0.037629
GLD    0.073255
DBC    0.027539
VNQ    0.077119

Set A frontier (closed form)
    target_return       vol
0       -0.002887  0.008156
1        0.008567  0.010535
2        0.020020  0.015633
3        0.031474  0.021605
4        0.042927  0.027894
5        0.054381  0.034326
6        0.065834  0.040835
7        0.077287  0.047388
8        0.088741  0.053969
9        0.100194  0.060570
10       0.111648  0.067184
11       0.123101  0.073808
12       0.134555  0.080439
13       0.146008  0.087076
14       0.157462  0.093717
15       0.168915  0.100362
16       0.180369  0.107010
17       0.191822  0.113661
18       0.203276  0.120313
19       0.214729  0.126967
20       0.226183  0.133623
21       0.237636  0.140280
22       0.249089  0.146938
23       0.260543  0.153596
24       0.271996  0.160256
25       0.283450  0.166917
26       0.294903  0.173578
27       0.306357  0.180239
28       0.317810  0.186901
29       0.329264  0.193564
30       0.340717  0.200227
31       0.352171  0.206890
32       0.363624  0.213554
33       0.375078  0.220218
34       0.386531  0.226882
35       0.397985  0.233546
36       0.409438  0.240211
37       0.420892  0.246876
38       0.432345  0.253541
39       0.443798  0.260207
40       0.455252  0.266872
41       0.466705  0.273538
42       0.478159  0.280204
43       0.489612  0.286870
44       0.501066  0.293536
45       0.512519  0.300202
46       0.523973  0.306868
47       0.535426  0.313534
48       0.546880  0.320201
49       0.558333  0.326867

Set B frontier (each point a solve)
    target_return       vol    solver   status
0        0.014183  0.035017  CLARABEL  optimal
1        0.016758  0.035273  CLARABEL  optimal
2        0.019334  0.035868  CLARABEL  optimal
3        0.021910  0.036666  CLARABEL  optimal
4        0.024485  0.037595  CLARABEL  optimal
5        0.027061  0.038628  CLARABEL  optimal
6        0.029637  0.039757  CLARABEL  optimal
7        0.032213  0.040975  CLARABEL  optimal
8        0.034788  0.042273  CLARABEL  optimal
9        0.037364  0.043640  CLARABEL  optimal
10       0.039940  0.045069  CLARABEL  optimal
11       0.042515  0.046556  CLARABEL  optimal
12       0.045091  0.048096  CLARABEL  optimal
13       0.047667  0.049685  CLARABEL  optimal
14       0.050243  0.051317  CLARABEL  optimal
15       0.052818  0.052988  CLARABEL  optimal
16       0.055394  0.054721  CLARABEL  optimal
17       0.057970  0.056523  CLARABEL  optimal
18       0.060545  0.058382  CLARABEL  optimal
19       0.063121  0.060293  CLARABEL  optimal
20       0.065697  0.062251  CLARABEL  optimal
21       0.068272  0.064255  CLARABEL  optimal
22       0.070848  0.066314  CLARABEL  optimal
23       0.073424  0.068423  CLARABEL  optimal
24       0.076000  0.070577  CLARABEL  optimal
25       0.078575  0.072773  CLARABEL  optimal
26       0.081151  0.075005  CLARABEL  optimal
27       0.083727  0.077246  CLARABEL  optimal
28       0.086302  0.079489  CLARABEL  optimal
29       0.088878  0.081732  CLARABEL  optimal
30       0.091454  0.083975  CLARABEL  optimal
31       0.094029  0.086220  CLARABEL  optimal
32       0.096605  0.088465  CLARABEL  optimal
33       0.099181  0.090711  CLARABEL  optimal
34       0.101757  0.092957  CLARABEL  optimal
35       0.104332  0.095204  CLARABEL  optimal
36       0.106908  0.097452  CLARABEL  optimal
37       0.109484  0.099719  CLARABEL  optimal
38       0.112059  0.102034  CLARABEL  optimal
39       0.114635  0.104387  CLARABEL  optimal
40       0.117211  0.106771  CLARABEL  optimal
41       0.119786  0.109187  CLARABEL  optimal
42       0.122362  0.111784  CLARABEL  optimal
43       0.124938  0.114838  CLARABEL  optimal
44       0.127514  0.118615  CLARABEL  optimal
45       0.130089  0.123018  CLARABEL  optimal
46       0.132665  0.127982  CLARABEL  optimal
47       0.135241  0.133445  CLARABEL  optimal
48       0.137816  0.139575  CLARABEL  optimal
49       0.140392  0.150541  CLARABEL  optimal

Strategy points
                        strategy_id             label   ann_vol  ann_excess  ruined
0  mv_unconstrained|sample|sample|A  mv_unconstrained  1.090751    0.678852    True
1     mv_constrained|lw_cc|sample|C    mv_constrained  0.119633    0.080613   False
2         min_variance|lw_cc|none|B      min_variance  0.036621    0.016576   False
3        risk_parity|ewma|none|none       risk_parity  0.040348    0.022988   False
4        black_litterman|lw_cc|bl|C   black_litterman  0.133011    0.073058   False
5              hrp|sample|none|none               hrp  0.017246    0.002697   False
6       equal_weight|none|none|none      equal_weight  0.097643    0.068848   False

axes: x 0 to 0.30, y -0.028084 to 0.526263

outside the axes
                        strategy_id             label   ann_vol  ann_excess  ruined
0  mv_unconstrained|sample|sample|A  mv_unconstrained  1.090751    0.678852    True
```

#### 9. Runtime per step, session 4b

| step | runtime |
|---|---|
| 4.2 completion | full 26-strategy, 196-date run 49.8 s wall (second run 62.4 s); `test_backtest.py` 7.7 s |
| 4.3 | `write_metrics` 0.18 s; `test_stats.py` 0.6 s for the whole file |
| 4.4 | `write_sharpe_intervals` 2.1 s (10,000 bootstrap paths) |
| 4.5 | `write_results_primary` 0.02 s |
| 4.6 | `write_charts` 1.3 s; `test_charts.py` 5.5 s |

Step 4.2 per strategy, in seconds, final run. Each figure covers allocation and bookkeeping; `shared` is μ and Σ at each date, computed once:

```
mv_unconstrained|sample|sample|A       0.26
mv_unconstrained|lw_cc|sample|A        0.26
mv_unconstrained|ewma|sample|A         0.05
mv_unconstrained|pca3|sample|A         0.25
mv_constrained|sample|sample|C         3.19
mv_constrained|lw_cc|sample|C          3.06
mv_constrained|ewma|sample|C           3.18
mv_constrained|pca3|sample|C           3.25
mv_constrained|lw_cc|bayes_stein|C     3.55
min_variance|sample|none|B             1.26
min_variance|lw_cc|none|B              1.23
min_variance|ewma|none|B               1.23
min_variance|pca3|none|B               1.22
risk_parity|sample|none|none           2.17
risk_parity|lw_cc|none|none            1.94
risk_parity|ewma|none|none             1.94
risk_parity|pca3|none|none             1.92
black_litterman|sample|bl|C            3.45
black_litterman|lw_cc|bl|C             3.49
black_litterman|ewma|bl|C              3.72
black_litterman|pca3|bl|C              3.56
hrp|sample|none|none                   0.48
hrp|lw_cc|none|none                    0.44
hrp|ewma|none|none                     0.42
hrp|pca3|none|none                     0.43
equal_weight|none|none|none            0.24
shared                                 3.07
total                                 49.79
```

#### 10. Fresh-clone check, session 4b

Clone of the pushed `main` at `7d88eda` into `%TEMP%\pcs4b`, `.venv` built as in amendment 2, `.venv\Scripts\python -m pytest --disable-socket -q`, then the folder was deleted.

```
........................................................................ [ 33%]
........................................................................ [ 66%]
........................................................................ [ 99%]
.                                                                        [100%]
============================== warnings summary ===============================
tests/test_backtest.py: 16 warnings
  C:\Users\astha\AppData\Local\Temp\pcs4b\pc\solver.py:77: UserWarning: Solution may be inaccurate. Try another solver, adjusting the solver settings, or solve with verbose=True for more information.
    prob.solve(solver=name, **_options(name, scfg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
217 passed, 16 warnings in 53.51s
```

Local run of the same command:

```
........................................................................ [ 33%]
........................................................................ [ 66%]
........................................................................ [ 99%]
.                                                                        [100%]
============================== warnings summary ===============================
tests/test_backtest.py: 16 warnings
  C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser\pc\solver.py:77: UserWarning: Solution may be inaccurate. Try another solver, adjusting the solver settings, or solve with verbose=True for more information.
    prob.solve(solver=name, **_options(name, scfg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
217 passed, 16 warnings in 27.46s
```

## Tests run

`.venv\Scripts\python -m pytest --disable-socket -q`

```
........................................................................ [ 34%]
.......................................................F................ [ 68%]
...................................................................      [100%]
================================== FAILURES ===================================
_____________________________ test_no_look_ahead ______________________________

real = <conftest.RealData object at 0x000001A0FB28BC90>

    def test_no_look_ahead(real):
        cfg = real.cfg
        cal = build_calendar(real.prices.index, cfg)
        cfg6 = with_calendar(cfg, cal.decision_date.iloc[0], cal.decision_date.iloc[5], 6)
        specs = specs_by_id(cfg, LOOK_AHEAD_SPECS)
        t, exec_t = cal.decision_date.iloc[2], cal.exec_date.iloc[2]
        base, _ = run_walk_forward(specs, real.prices, real.rf_daily, cfg6)
        keys = ["strategy_id", "decision_date", "ticker"]
    
        # (a) prices after exec_date(t): every weight at decision dates <= t is unchanged.
        wa, _ = run_walk_forward(specs, perturbed_prices(real.prices, exec_t, cfg.run.seed_master), real.rf_daily, cfg6)
        b, a = base[base.decision_date <= t], wa[wa.decision_date <= t]
        assert len(b) == 3 * 8 * 18
        assert b[keys].reset_index(drop=True).equals(a[keys].reset_index(drop=True))
        assert np.array_equal(b.w_target.to_numpy(), a.w_target.to_numpy())
        assert np.array_equal(b.w_prev_drifted.to_numpy(), a.w_prev_drifted.to_numpy(), equal_nan=True)
        # The perturbation reaches the run: some weight after t differs.
        later = base[base.decision_date > t].merge(wa[wa.decision_date > t], on=keys)
        assert (later.w_target_x != later.w_target_y).any()
    
        # (b) prices after t: weights at t of the specs that do not use w_prev are unchanged.
        wb, _ = run_walk_forward(specs, perturbed_prices(real.prices, t, cfg.run.seed_master), real.rf_daily, cfg6)
        keep = [s for s in LOOK_AHEAD_SPECS if s not in USES_W_PREV]
        # The instruction names 3 exclusions from 8 specs and calls the rest "the 6 specs"; 8 - 3 = 5.
        assert len(keep) == 5
        b = base[(base.decision_date == t) & base.strategy_id.isin(keep)]
        a = wb[(wb.decision_date == t) & wb.strategy_id.isin(keep)]
        assert len(b) == len(keep) * 18
>       assert b[keys].reset_index(drop=True).equals(a[keys].reset_index(drop=True))
E       assert False
E        +  where False = equals(                    strategy_id decision_date ticker\n0      min_variance|ewma|none|B    2010-06-30    SPY\n1      min_v..._weight|none|none|none    2010-06-30    DBC\n71  equal_weight|none|none|none    2010-06-30    VNQ\n\n[72 rows x 3 columns])
E        +    where equals =                          strategy_id decision_date ticker\n0   mv_unconstrained|sample|sample|A    2010-06-30    SPY\n1 ...ht|none|none|none    2010-06-30    DBC\n89       equal_weight|none|none|none    2010-06-30    VNQ\n\n[90 rows x 3 columns].equals
E        +      where                          strategy_id decision_date ticker\n0   mv_unconstrained|sample|sample|A    2010-06-30    SPY\n1 ...ht|none|none|none    2010-06-30    DBC\n89       equal_weight|none|none|none    2010-06-30    VNQ\n\n[90 rows x 3 columns] = reset_index(drop=True)
E        +        where reset_index =                           strategy_id decision_date ticker\n36   mv_unconstrained|sample|sample|A    2010-06-30    SPY\n...t|none|none|none    2010-06-30    DBC\n809       equal_weight|none|none|none    2010-06-30    VNQ\n\n[90 rows x 3 columns].reset_index
E        +    and                       strategy_id decision_date ticker\n0      min_variance|ewma|none|B    2010-06-30    SPY\n1      min_v..._weight|none|none|none    2010-06-30    DBC\n71  equal_weight|none|none|none    2010-06-30    VNQ\n\n[72 rows x 3 columns] = reset_index(drop=True)
E        +      where reset_index =                      strategy_id decision_date ticker\n288     min_variance|ewma|none|B    2010-06-30    SPY\n289     mi...weight|none|none|none    2010-06-30    DBC\n737  equal_weight|none|none|none    2010-06-30    VNQ\n\n[72 rows x 3 columns].reset_index

tests\test_backtest.py:204: AssertionError
============================== warnings summary ===============================
tests/test_backtest.py: 23 warnings
  C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser\pc\solver.py:77: UserWarning: Solution may be inaccurate. Try another solver, adjusting the solver settings, or solve with verbose=True for more information.
    prob.solve(solver=name, **_options(name, scfg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
FAILED tests/test_backtest.py::test_no_look_ahead - assert False
1 failed, 210 passed, 23 warnings in 11.76s
```

## Fresh-clone check

Clone of `29170e1` into `%TEMP%\pcs4`, `.venv` built as in amendment 2, `.venv\Scripts\python -m pytest --disable-socket -q`, then the folder was deleted.

```
........................................................................ [ 34%]
.......................................................F................ [ 68%]
...................................................................      [100%]
================================== FAILURES ===================================
_____________________________ test_no_look_ahead ______________________________

real = <conftest.RealData object at 0x000001F4D3DD2E10>

    def test_no_look_ahead(real):
        cfg = real.cfg
        cal = build_calendar(real.prices.index, cfg)
        cfg6 = with_calendar(cfg, cal.decision_date.iloc[0], cal.decision_date.iloc[5], 6)
        specs = specs_by_id(cfg, LOOK_AHEAD_SPECS)
        t, exec_t = cal.decision_date.iloc[2], cal.exec_date.iloc[2]
        base, _ = run_walk_forward(specs, real.prices, real.rf_daily, cfg6)
        keys = ["strategy_id", "decision_date", "ticker"]
    
        # (a) prices after exec_date(t): every weight at decision dates <= t is unchanged.
        wa, _ = run_walk_forward(specs, perturbed_prices(real.prices, exec_t, cfg.run.seed_master), real.rf_daily, cfg6)
        b, a = base[base.decision_date <= t], wa[wa.decision_date <= t]
        assert len(b) == 3 * 8 * 18
        assert b[keys].reset_index(drop=True).equals(a[keys].reset_index(drop=True))
        assert np.array_equal(b.w_target.to_numpy(), a.w_target.to_numpy())
        assert np.array_equal(b.w_prev_drifted.to_numpy(), a.w_prev_drifted.to_numpy(), equal_nan=True)
        # The perturbation reaches the run: some weight after t differs.
        later = base[base.decision_date > t].merge(wa[wa.decision_date > t], on=keys)
        assert (later.w_target_x != later.w_target_y).any()
    
        # (b) prices after t: weights at t of the specs that do not use w_prev are unchanged.
        wb, _ = run_walk_forward(specs, perturbed_prices(real.prices, t, cfg.run.seed_master), real.rf_daily, cfg6)
        keep = [s for s in LOOK_AHEAD_SPECS if s not in USES_W_PREV]
        # The instruction names 3 exclusions from 8 specs and calls the rest "the 6 specs"; 8 - 3 = 5.
        assert len(keep) == 5
        b = base[(base.decision_date == t) & base.strategy_id.isin(keep)]
        a = wb[(wb.decision_date == t) & wb.strategy_id.isin(keep)]
        assert len(b) == len(keep) * 18
>       assert b[keys].reset_index(drop=True).equals(a[keys].reset_index(drop=True))
E       assert False
E        +  where False = equals(                    strategy_id decision_date ticker\n0      min_variance|ewma|none|B    2010-06-30    SPY\n1      min_v..._weight|none|none|none    2010-06-30    DBC\n71  equal_weight|none|none|none    2010-06-30    VNQ\n\n[72 rows x 3 columns])
E        +    where equals =                          strategy_id decision_date ticker\n0   mv_unconstrained|sample|sample|A    2010-06-30    SPY\n1 ...ht|none|none|none    2010-06-30    DBC\n89       equal_weight|none|none|none    2010-06-30    VNQ\n\n[90 rows x 3 columns].equals
E        +      where                          strategy_id decision_date ticker\n0   mv_unconstrained|sample|sample|A    2010-06-30    SPY\n1 ...ht|none|none|none    2010-06-30    DBC\n89       equal_weight|none|none|none    2010-06-30    VNQ\n\n[90 rows x 3 columns] = reset_index(drop=True)
E        +        where reset_index =                           strategy_id decision_date ticker\n36   mv_unconstrained|sample|sample|A    2010-06-30    SPY\n...t|none|none|none    2010-06-30    DBC\n809       equal_weight|none|none|none    2010-06-30    VNQ\n\n[90 rows x 3 columns].reset_index
E        +    and                       strategy_id decision_date ticker\n0      min_variance|ewma|none|B    2010-06-30    SPY\n1      min_v..._weight|none|none|none    2010-06-30    DBC\n71  equal_weight|none|none|none    2010-06-30    VNQ\n\n[72 rows x 3 columns] = reset_index(drop=True)
E        +      where reset_index =                      strategy_id decision_date ticker\n288     min_variance|ewma|none|B    2010-06-30    SPY\n289     mi...weight|none|none|none    2010-06-30    DBC\n737  equal_weight|none|none|none    2010-06-30    VNQ\n\n[72 rows x 3 columns].reset_index

tests\test_backtest.py:204: AssertionError
============================== warnings summary ===============================
tests/test_backtest.py: 23 warnings
  C:\Users\astha\AppData\Local\Temp\pcs4\pc\solver.py:77: UserWarning: Solution may be inaccurate. Try another solver, adjusting the solver settings, or solve with verbose=True for more information.
    prob.solve(solver=name, **_options(name, scfg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
FAILED tests/test_backtest.py::test_no_look_ahead - assert False
1 failed, 210 passed, 23 warnings in 19.15s
```

## Runtime per step

| step | runtime |
|---|---|
| 4.0 | `write_cov_eval` 3.9 s; full suite 10.1 s after the change |
| 4.1 | `test_backtest.py::test_registry_26_exact_ids` 0.05 s |
| 4.2 | full 26-strategy, 196-date run 81.8 s wall (`write_walk_forward`); `test_backtest.py` 5.6 s |

Step 4.2 per strategy, in seconds. Each figure covers allocation and bookkeeping. `shared` is μ and Σ at each date, computed once (amendment 4.2.1) and reused:

```
mv_unconstrained|sample|sample|A       0.43
mv_unconstrained|lw_cc|sample|A        0.45
mv_unconstrained|ewma|sample|A         0.09
mv_unconstrained|pca3|sample|A         0.44
mv_constrained|sample|sample|C         5.37
mv_constrained|lw_cc|sample|C          5.02
mv_constrained|ewma|sample|C           5.07
mv_constrained|pca3|sample|C           5.26
mv_constrained|lw_cc|bayes_stein|C     5.68
min_variance|sample|none|B             2.06
min_variance|lw_cc|none|B              2.00
min_variance|ewma|none|B               1.99
min_variance|pca3|none|B               2.03
risk_parity|sample|none|none           3.67
risk_parity|lw_cc|none|none            3.50
risk_parity|ewma|none|none             3.50
risk_parity|pca3|none|none             3.40
black_litterman|sample|bl|C            5.28
black_litterman|lw_cc|bl|C             5.34
black_litterman|ewma|bl|C              5.82
black_litterman|pca3|bl|C              5.91
hrp|sample|none|none                   0.75
hrp|lw_cc|none|none                    0.70
hrp|ewma|none|none                     0.69
hrp|pca3|none|none                     0.70
equal_weight|none|none|none            0.39
shared                                 5.05
total                                 81.81
```

## Deviations from PLAN.md

1. **Choices in step 4.2 that the documents imply but do not state. Please confirm.**
   - First period in `weights_long`: `w_prev_drifted` and `trade` are NaN and `cost_i` is 0, consistent with cost 0 and turnover NaN in `periods`.
   - Months after ruin are kept in `periods` with NaN numeric fields, `ruined = True`, `solver = "none"` and `status = "not_solved"`, and have no `weights_long` rows.
   - `rp_converged` is True on those rows.
2. **`window_daily` raises** `ValueError` unless every one of the `months` calendar months has at least one daily row. This is the row-count check of convention 23.
3. **`test_window_boundaries_exclusive_start_inclusive_end` is renamed `test_window_boundaries`**, the name the instruction uses, because "exclusive start" no longer describes the rule.
4. **Helpers outside kickoff Section 6**, all in `pc/backtest.py`: `walk_forward` (returns the two frames plus per-strategy seconds, wrapped by `run_walk_forward`), `write_walk_forward`, `DateInputs` (the per-date cache), `drift`, `cost_vector`, `constraint_sets`, `monthly_total_returns`, and the `ALLOCATORS` table.
5. **Literals with comments** (convention 22): `NO_COV_ESTIMATOR = "lw_cc"` (amendment 4.2.3), `BP_PER_UNIT = 1e4` (bp to decimals) and `MONTHS_PER_YEAR = 12` (√12 in amendment 4.2.5).
6. **Test tolerances I set:**
   - The synthetic wealth match uses 1e-12, the PLAN figure; the measured difference is 0.0.
   - Drift uses 1e-15.
   - First period `ret_net` against `ret_gross` uses 1e-15, because (1 + g) − 1 is not g exactly.
   - Set C turnover ≤ τ_eff + 1e-7 uses the step 3.4 figure.
7. **`outputs/results/*.parquet` were not committed in session 4**, because step 4.2 was not complete. Session 4b commits them at `dcebb48`.

Session 4b:

8. **Sharpe ddof** (`decisions/OPEN.md` item 6, implemented as option 1). Kickoff 5.8 gives no ddof for the Sharpe std, so ddof 1 is used, as for annualised vol. The same `pc.stats.SHARPE_DDOF` sets Chart 1's x coordinate.
9. **Ruined strategies in `sharpe_intervals.csv`** keep their point Sharpe over the months of their wealth path, the same value as `metrics_all.csv`. Their interval and every difference involving them are NaN. Amendment 4.2.8 asks for NaN intervals; it does not ask for a NaN point Sharpe.
10. **`sharpe_intervals.csv` is wide.** It has one row per strategy, and for each benchmark the columns `diff_vs_<id>`, `diff_p05_vs_<id>`, `diff_p95_vs_<id>` and `frac_le_0_vs_<id>`, with the full benchmark id. `diff_vs_<id>` is the full-sample Sharpe difference.
11. **`metrics_all.csv` columns:** strategy_id, n_months, ruined, ann_return, ann_vol, sharpe, max_dd, forecast_vol_ann (the mean), fcst_realised_ratio, mean_turnover, mean_positions, scs_retries, fallbacks, rp_not_converged and ridged_months. ridged_months is there because `results_primary.csv` is built from `metrics_all.csv`.
12. **`max_dd`** is measured on the net wealth path with the starting wealth of 1 counted as the first peak.
13. **`results_primary.csv`** carries `ruined` (amendment 4.2.8, "shows `ruined` in every table"). `realised_vol_ann` equals `ann_vol`; both are kept so the forecast/realised ratio can be checked from its parts.
14. **Chart 1 choices the documents do not fix:**
    - The set A curve is drawn at 50 points, the set B count.
    - The y-axis spans every frontier and strategy point with vol from 0 to 30%, plus 5% padding.
    - A point is outside the axes when its vol is outside [0, 30%] or its return is outside that y range.
    - The maximum feasible set B return is an LP solved under the solver policy.
    - The set B minimum variance fund is `min_variance` with set B bounds.
15. **`pc.stats` reads `[bootstrap] ci` from the repo's `config.toml`** through a package-relative path, as `pc.solver` does (section 3 decision 2), because `sharpe_intervals` has no Config argument.
16. **New helpers:**
    - In `pc/stats.py`: `sharpe`, `max_drawdown`, `boot_sharpe`, `results_primary`, and the `write_*` functions.
    - In `pc/charts.py`: `holding_excess`, `frontier_inputs`, `frontier_set_a`, `frontier_set_b`, `strategy_points`, `y_limits`, `outside_axes`, `plot_frontier`, `plot_weights_stacked` and `write_charts`.
    - In `pc/backtest.py`: `DateInputs.views` and `DateInputs.pi`, so that part (b) compares the objects the engine uses.

## Not verified

- Session 4: byte-identical parquet on a second run was not checked. Session 4b checked it: a second full run reproduced both parquet files, the 3 CSVs and the 2 PNGs by MD5 (`### Session 4b`).
- The 23 `UserWarning: Solution may be inaccurate` lines in the test run come from CLARABEL statuses of `optimal_inaccurate`, which the policy retries with SCS. They were not investigated further.

## Open questions

Session 4: `decisions/OPEN.md` item 5, `test_no_look_ahead` part (b) under the ruin rule. It was resolved in session 4b as option 2.

Session 4b: `decisions/OPEN.md` item 6, the ddof of the Sharpe std and of Chart 1's x coordinate.
- Option 1 (implemented): ddof 1.
- Option 2: ddof 0.

## Files changed

- Added: `decisions/section_3_review.md`, `pc/backtest.py`, `tests/test_backtest.py`, `review/section_4.md`, `instructions/04_section_4.status.md`.
- Added in session 4b: `decisions/section_4_review.md`, `pc/charts.py`, `tests/test_charts.py`, `outputs/results/weights_long.parquet`, `outputs/results/periods.parquet`, `outputs/tables/metrics_all.csv`, `outputs/tables/sharpe_intervals.csv`, `outputs/tables/results_primary.csv`, `outputs/figures/frontier_vs_oos.png`, `outputs/figures/weights_stacked.png`, `instructions/04b_section_4_completion.status.md`.
- Modified in session 4b: `decisions/OPEN.md`, `pc/backtest.py`, `pc/stats.py`, `tests/test_backtest.py`, `tests/test_stats.py`, `review/section_4.md`.
- Modified: `decisions/OPEN.md`, `docs/CONVENTIONS_RESOLVED.md`, `pc/cov.py`, `tests/test_cov.py`, `outputs/tables/cov_eval.csv`, `outputs/tables/cov_eval_qlike_diff.csv`, `outputs/tables/cov_eval_by_date.csv`, `outputs/tables/cov_diagnostics.csv`.

## Reviewer reads

1. `### Session 4b` above: part (b) (item 1), then `results_primary.csv` and `sharpe_intervals.csv` (item 3) and Chart 1 (item 8).
2. `decisions/OPEN.md` item 6 (Sharpe ddof).
3. `pc/stats.py`: `strategy_metrics`, `sharpe_intervals`, `results_primary`.
4. `pc/charts.py`: `frontier_set_a`, `frontier_set_b`, `strategy_points`, `plot_frontier`.
5. `tests/test_backtest.py::test_no_look_ahead` and `tests/test_stats.py`.
6. Deviations 8 to 16.
