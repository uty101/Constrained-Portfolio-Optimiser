# Open decisions

## 7. Step 5.1: the covariance of the 3 zero-dispersion references (implemented as option 1, needs confirming)

PLAN 5.1 and amendment 5.1 name min variance, risk parity and HRP as the references, but give no covariance estimator for them. Amendment 5.1 fixes Σ for the 4 μ-based strategies only (sample Σ for `mv_unconstrained`, Σ_lw_cc for the 3 set B strategies). The references do not read μ, so their dispersion is 0 under either option; the choice moves only their `w_base` rows in `sensitivity.csv` and their 3 panels in Chart 3.

- Option 1 (implemented): Σ_lw_cc for all 3, the covariance the perturbations are drawn from and the one the set B strategies use: `min_variance|lw_cc|none|B`, `risk_parity|lw_cc|none|none`, `hrp|lw_cc|none|none`. `pc.sensitivity.REFERENCE_STRATEGIES`.
- Option 2: each reference's primary-table covariance: `min_variance|lw_cc|none|B`, `risk_parity|ewma|none|none`, `hrp|sample|none|none`.
