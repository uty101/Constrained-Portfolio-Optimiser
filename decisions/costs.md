# Costs

One-way cost 3 bp for SPY, IWM, EFA, XLE, XLF, XLK, XLU, XLV, SHY, IEF, TLT, LQD, GLD; 6 bp for EEM, TIP, HYG, DBC, VNQ.
cost = Σ c_i |w_i − w_prev_i| against drifted weights; net = (1 − cost)(1 + gross) − 1.
Turnover is two-way, Σ |w_i − w_prev_i|; set C caps it at τ = 0.30 and puts the cost term in the objective.
If a drifted weight above its cap makes τ infeasible, τ_eff = τ_min + 1e-6 and `tau_relaxed = True`.
Cost scales 0, 1 and 3 are run as a sensitivity on the 7 primary strategies.
