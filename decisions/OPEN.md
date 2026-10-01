# Open decisions

## 6. Steps 4.3 to 4.6: ddof of the std in the Sharpe ratio and in Chart 1's x coordinate (implemented as option 1, needs confirming)

Kickoff 5.8 fixes annualised vol as std(r_net, ddof=1) × √12, but writes Sharpe = mean(excess_net)/std(excess_net) × √12 with no ddof. Amendment 4.6 likewise gives Chart 1's x as std(excess_net) × √12 with no ddof. Both feed `metrics_all.csv`, `sharpe_intervals.csv` (point and bootstrap), `results_primary.csv` and Chart 1. Over 196 months the two choices differ by a factor of √(196/195) = 1.00256 on every Sharpe ratio and on every x coordinate. The bootstrap fraction ≤ 0 is unaffected, because the factor is common to all strategies on a path.

- Option 1 (implemented): ddof 1, the same as annualised vol. `pc.stats.SHARPE_DDOF = 1`, used by `sharpe`, `boot_sharpe` and `pc.charts.strategy_points`.
- Option 2: ddof 0.
