# Review — Section 4: Walk-forward and headline results

## Section

Section 4, walk-forward and headline results. **Stopped under rule 4 at step 4.2.** Step 4.0 and step 4.1 are complete. Step 4.2 is built and run in full, but `test_no_look_ahead` part (b), as specified in amendment 4.2.9, fails. Steps 4.3 to 4.6 were not started.

## Steps completed

- 4.0 `8e33e83` section 4: reviewer decisions for section 3 (`decisions/section_3_review.md`, convention 23, `decisions/OPEN.md` emptied)
- 4.0 `fbaba6b` step 4.0: window_daily on calendar-month periods (with the 4 regenerated cov_eval CSVs)
- 4.1 `9ef7ca6` step 4.1: strategy registry, 26 ids
- 4.2 `d72f7c5` step 4.2: walk-forward engine (stopped under rule 4: test_no_look_ahead part b)
- `29170e1` section 4: open decision 5 (look-ahead part b and the ruin rule)
- 4.3, 4.4, 4.5, 4.6: not started.

## Rule 4 stop: `test_no_look_ahead` part (b)

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
7. **`outputs/results/*.parquet` are not committed**, because step 4.2 is not complete. They regenerate in about 82 s.

## Not verified

- Byte-identical parquet on a second run (rule 9 covers CSV outputs) was not checked.
- The 23 `UserWarning: Solution may be inaccurate` lines in the test run come from CLARABEL statuses of `optimal_inaccurate`, which the policy retries with SCS. They were not investigated further.

## Open questions

`decisions/OPEN.md` item 5: `test_no_look_ahead` part (b) under the ruin rule, with 2 options. It also covers the "6 specs" count.

## Files changed

- Added: `decisions/section_3_review.md`, `pc/backtest.py`, `tests/test_backtest.py`, `review/section_4.md`, `instructions/04_section_4.status.md`.
- Modified: `decisions/OPEN.md`, `docs/CONVENTIONS_RESOLVED.md`, `pc/cov.py`, `tests/test_cov.py`, `outputs/tables/cov_eval.csv`, `outputs/tables/cov_eval_qlike_diff.csv`, `outputs/tables/cov_eval_by_date.csv`, `outputs/tables/cov_diagnostics.csv`.

## Reviewer reads

1. `decisions/OPEN.md` item 5, and "Rule 4 stop" above.
2. `tests/test_backtest.py::test_no_look_ahead`.
3. `pc/backtest.py`: `walk_forward` and `DateInputs`.
4. Deviations 1 above.
5. `pc/cov.py::window_daily` and `tests/test_cov.py::test_window_boundaries`, `test_window_matches_calendar_months_real`.
