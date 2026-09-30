# Black-Litterman prior and views

Issuer AUM is not point-in-time, so the prior is a fixed strategic w_mkt (equities 0.50, bonds 0.38, real assets 0.12; values in `config.toml`).
Π = δΣw_mkt with δ = 2.5; τ = 1/36; Ω = diag(PτΣP′).
View 1: 12-1 momentum, +1/6 on the top 6, −1/6 on the bottom 6, ties by config order; Q₁ the long-short mean monthly excess return over t−12 to t−1.
View 2: +1/4 on SPY, IWM, EFA, EEM against −1/3 on SHY, IEF, TLT; Q₂ the basket difference in mean monthly excess return over t−12 to t−1.
The optimiser uses μ_BL with Σ_BL; the round-trip test uses Σ.
