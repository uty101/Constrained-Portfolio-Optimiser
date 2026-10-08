**Cost scales.** Every one-way cost multiplied by the scale.

| Strategy | Sharpe, costs × 0 | Sharpe, costs × 1 | Sharpe, costs × 3 |
|---|---:|---:|---:|
| `mv_unconstrained\|sample\|sample\|A` | ruined | ruined | ruined |
| `mv_constrained\|lw_cc\|sample\|C` | 0.68 | 0.67 | 0.67 |
| `min_variance\|lw_cc\|none\|B` | 0.46 | 0.45 | 0.44 |
| `risk_parity\|ewma\|none\|none` | 0.58 | 0.57 | 0.54 |
| `black_litterman\|lw_cc\|bl\|C` | 0.55 | 0.55 | 0.53 |
| `hrp\|sample\|none\|none` | 0.16 | 0.16 | 0.15 |
| `equal_weight\|none\|none\|none` | 0.71 | 0.71 | 0.70 |

**Covariance from 36 monthly returns** against the daily estimate.

| Σ from | Strategy | Months | Ann. return | Vol | Sharpe | Max DD | Monthly turnover |
|---|---|---:|---:|---:|---:|---:|---:|
| daily | `mv_unconstrained\|sample\|sample\|A` | 191 | −100.0% | 109.0% | ruined (2026-02) | −100.0% | 2907.8% |
| monthly | `mv_unconstrained\|sample\|sample\|A` | 9 | −100.0% | 203.8% | ruined (2010-12) | −100.0% | 41966.1% |
| daily | `min_variance\|sample\|none\|B` | 196 | 3.2% | 3.6% | 0.46 | −10.6% | 3.4% |
| monthly | `min_variance\|sample\|none\|B` | 196 | 3.5% | 3.6% | 0.54 | −9.7% | 6.6% |
