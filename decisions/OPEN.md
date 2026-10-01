# Open decisions

## 7. Step 5.1: the covariance of the 3 zero-dispersion references (implemented as option 1, needs confirming)

PLAN 5.1 and amendment 5.1 name min variance, risk parity and HRP as the references, but give no covariance estimator for them. Amendment 5.1 fixes Σ for the 4 μ-based strategies only (sample Σ for `mv_unconstrained`, Σ_lw_cc for the 3 set B strategies). The references do not read μ, so their dispersion is 0 under either option; the choice moves only their `w_base` rows in `sensitivity.csv` and their 3 panels in Chart 3.

- Option 1 (implemented): Σ_lw_cc for all 3, the covariance the perturbations are drawn from and the one the set B strategies use: `min_variance|lw_cc|none|B`, `risk_parity|lw_cc|none|none`, `hrp|lw_cc|none|none`. `pc.sensitivity.REFERENCE_STRATEGIES`.
- Option 2: each reference's primary-table covariance: `min_variance|lw_cc|none|B`, `risk_parity|ewma|none|none`, `hrp|sample|none|none`.

## 8. Step 5.5: the in-sample max Sharpe of the set A frontier has no maximum (implemented as option 1, needs confirming)

Amendment 5.5 asks for "the in-sample max Sharpe of the set A and set B frontiers, from the Chart 1 inputs". On those inputs 1′Σ⁻¹μ = −43.40 < 0, so the GMV fund's excess return is negative (−0.29% a year) and the budget-1 frontier's Sharpe ratio rises with the target return towards √(A − B²/C) = 1.7175 without reaching it (A = μ′Σ⁻¹μ, B = 1′Σ⁻¹μ, C = 1′Σ⁻¹1). The closed-form tangency √A = 1.7536 belongs to the portfolio Σ⁻¹μ/B, whose budget is 1 only with a negative mean return and Sharpe −1.7536. Set B is unaffected: its maximum 1.0983 is attained (CLARABEL `optimal`) and the best of its 50 Chart 1 points is 1.0983.

- Option 1 (implemented): the supremum √(A − B²/C) = 1.7175, with `status = "supremum_not_attained"` and NaN tangency return and vol in `frontier_max_sharpe.csv`. When B > 0 the same code reports √A at the tangency.
- Option 2: the best Sharpe of the 50 points Chart 1 plots on the set A curve, 1.7081. It depends on where the plotted curve stops (3 times the largest single-asset excess return, amendment 4.6).

## 9. Step 5.5: "the largest τ whose point lies below the 45° line" is decided by solver noise (implemented as option 1, needs confirming)

In `turnover_frontier.csv` every τ from 0.05 to 0.75 lies above the line. τ = 1.00 lies below it by 5e-8 bp a year: return given up −1.21e-7 bp against cost saved −7.09e-8 bp. The limit never binds at τ = 1.00 (`n_binding` 0, mean dual 1.3e-12 bp per 1%), so both differences against no limit are solver noise around 0, and the answer 1.00 says nothing about the limit.

- Option 1 (implemented): the literal comparison, `exante_return_given_up_bp_pa < cost_saved_bp_pa`. The answer is τ = 1.00.
- Option 2: a τ with `n_binding = 0` lies on the line, not below it. No τ qualifies and the answer is NaN, meaning no limit in the grid was worth it ex ante.