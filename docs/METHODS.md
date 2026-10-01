# Methods

This is the maths of the repo as finally built: kickoff Section 5 with the corrections of kickoff Section 2 and every later reviewer decision. The 23 timing, unit and data conventions are in [CONVENTIONS_RESOLVED.md](CONVENTIONS_RESOLVED.md) and are not repeated here. Where a choice was made after the kickoff, the paragraph names the `decisions/section_*_review.md` file that made it. Every parameter is in `config.toml`.

Notation: $N=18$ assets, $t$ a decision date (the last trading day of a month), $w$ the target weights, $w^{prev}$ the previous target drifted to the execution close, $\mathbf{1}$ a vector of ones. All optimisation inputs are monthly decimals.

## 1. Windows

A window of $m$ months ending at $t$ covers the calendar months $p-m+1$ to $p$, where $p$ is the month of $t$ (convention 23). The estimation window is $m=36$. The 12-1 momentum window covers the months $p-11$ to $p-1$: 11 months, with month $p$ skipped (`pc.bl.momentum_window`). Daily covariance windows hold the daily returns dated in $(t-36\text{ months}, t]$ by the same calendar-month rule.

## 2. Expected returns

The sample mean is the average of the 36 monthly excess returns in the window:

$$\hat\mu=\frac{1}{36}\sum_{s=p-35}^{p} r^{ex}_s$$

Bayes-Stein (Jorion 1986) shrinks it towards the minimum-variance mean, with $\Sigma$ the monthly Ledoit-Wolf covariance at $t$ and $T=36$:

$$\mu_0=\frac{\mathbf{1}'\Sigma^{-1}\hat\mu}{\mathbf{1}'\Sigma^{-1}\mathbf{1}},\qquad \phi=\frac{N+2}{(N+2)+T(\hat\mu-\mu_0\mathbf{1})'\Sigma^{-1}(\hat\mu-\mu_0\mathbf{1})},\qquad \mu_{BS}=(1-\phi)\hat\mu+\phi\mu_0\mathbf{1}$$

## 3. Covariance

Each estimator takes the daily simple returns $X$ ($T$ rows) in the window and returns a monthly covariance, the daily estimate times 21.

**Sample.** `np.cov(X, ddof=1)`.

**Ledoit-Wolf constant correlation** (Ledoit and Wolf 2004). With $X_m$ the demeaned returns,

$$S=\frac{X_m'X_m}{T},\qquad F_{ii}=S_{ii},\qquad F_{ij}=\bar r\sqrt{S_{ii}S_{jj}},\qquad \delta^*=\max\left(0,\min\left(1,\frac{\hat\pi-\hat\rho}{\hat\gamma T}\right)\right),\qquad \hat\Sigma=\delta^*F+(1-\delta^*)S$$

where $\bar r$ is the average off-diagonal sample correlation, $\hat\pi$ the sum of the asymptotic variances of the entries of $S$, $\hat\rho$ its constant-correlation counterpart and $\hat\gamma=\lVert F-S\rVert_F^2$. Production uses ddof 0, as in the authors' `covCor.m`. The `ddof=1` variant exists only for the cross-check against PyPortfolioOpt, which uses ddof 1 (convention 13).

**EWMA.** With $n$ rows in the window, newest first, $\lambda=0.97$ on daily data and no demeaning:

$$\Sigma=\sum_{k=0}^{n-1}w_k\,r_{t-k}r_{t-k}',\qquad w_k=\frac{(1-\lambda)\lambda^k}{1-\lambda^n}$$

**3-factor PCA.** With $R$ the sample correlation, $V_3\Lambda_3V_3'$ its top 3 eigenpairs and $D$ the diagonal of sample vols:

$$R_f=V_3\Lambda_3V_3'+\operatorname{diag}\left(1-\operatorname{diag}(V_3\Lambda_3V_3')\right),\qquad \Sigma=DR_fD$$

**Conditioning.** Every $\Sigma$ passes through a ridge before any allocator sees it. If $\operatorname{cond}(\Sigma)>10^6$,

$$\Sigma\leftarrow\Sigma+rI,\qquad r=\max\left(0,\frac{\lambda_{max}-10^6\lambda_{min}}{10^6-1}\right)$$

which sets the condition number to exactly $10^6$ (convention 15). In this sample the ridge never fired, on daily data or on the 36 monthly returns of step 5.4.

## 4. Black-Litterman

The prior is a fixed strategic portfolio $w_{mkt}$ (`config.toml`, `[bl.w_mkt]`), with $\delta=2.5$ and $\tau=1/36$:

$$\Pi=\delta\Sigma w_{mkt}$$

There are 2 mechanical views. View 1 ranks the 18 assets by compounded total return over the 11-month momentum window in 1 ranking, highest first, ties by config order (`decisions/section_3_review.md`, 1), and puts $+1/6$ on the top 6 and $-1/6$ on the bottom 6. View 2 puts $+1/4$ on SPY, IWM, EFA and EEM and $-1/3$ on SHY, IEF and TLT. For both, $Q=P\bar r^{ex}$ with $\bar r^{ex}$ the mean monthly excess return over the same 11 months.

The view uncertainty is proportional to the prior's, through $\tau\Sigma$:

$$\Omega=\operatorname{diag}\left(P\,\tau\Sigma\,P'\right)$$

The posterior is

$$A=(\tau\Sigma)^{-1}+P'\Omega^{-1}P,\qquad \mu_{BL}=A^{-1}\left[(\tau\Sigma)^{-1}\Pi+P'\Omega^{-1}Q\right],\qquad \Sigma_{BL}=\Sigma+A^{-1}$$

with every inverse applied through `np.linalg.solve`. The Black-Litterman allocator runs the capped mean-variance problem of section 5 on $\mu_{BL}$ and $\Sigma_{BL}$, not on $\Sigma$ (conventions 18 and 21). The round-trip test, which recovers $w_{mkt}$ from $\Pi$, uses $\Sigma$.

## 5. Allocators

**Constraint sets.** A: $\mathbf{1}'w=1$. B: A plus $0\le w_i\le 0.30$. C: B plus $\lVert w-w^{prev}\rVert_1\le\tau_{to}$ with $\tau_{to}=0.30$, and the cost term below in the objective. Risk parity and HRP are long only with no cap.

**Unconstrained mean-variance** (set A), $\gamma=2.5$, in closed form:

$$w=\frac{1}{\gamma}\Sigma^{-1}(\mu-\eta\mathbf{1}),\qquad \eta=\frac{\mathbf{1}'\Sigma^{-1}\mu-\gamma}{\mathbf{1}'\Sigma^{-1}\mathbf{1}}$$

**Capped mean-variance** (set C, or set B with no turnover limit and no cost), solved in cvxpy, with $c$ the one-way costs:

$$\max_w\;\mu'w-\frac{\gamma}{2}w'\Sigma w-c'\lvert w-w^{prev}\rvert$$

The dual value of the turnover constraint is recorded as the turnover shadow price, in monthly return per unit of turnover.

**Minimum variance** (set B): $\min_w w'\Sigma w$. The budget-only form $\Sigma^{-1}\mathbf{1}/(\mathbf{1}'\Sigma^{-1}\mathbf{1})$ is used by tests and by the covariance evaluation.

**Risk parity** (Spinu), solved with L-BFGS-B from $x_0=1/\sqrt{\operatorname{diag}\Sigma}$:

$$\min_{x>0}\;\frac{1}{2}x'\Sigma x-\sum_i b_i\log x_i,\qquad b_i=\frac{1}{N},\qquad w=\frac{x}{\mathbf{1}'x}$$

**HRP** (López de Prado), by hand. The distance is $d_{ij}=\sqrt{\operatorname{clip}((1-\rho_{ij})/2,0,1)}$; single linkage is applied to $d$ directly (convention 14); the quasi-diagonal order is the tree's pre-order; recursive bisection splits the ordered list in halves and gives the first half the share

$$\alpha=1-\frac{V_1}{V_1+V_2}$$

with $V_k$ the variance of half $k$ under inverse-variance weights.

**Equal weight**: $w_i=1/N$ every month, rebalanced, with costs charged.

**Feasibility rule** (set C, convention 17). Before solving, a linear program finds

$$\tau_{min}=\min_w\lVert w-w^{prev}\rVert_1\quad\text{s.t.}\quad\mathbf{1}'w=1,\;0\le w\le 0.30$$

and if $\tau_{min}>\tau_{to}$ the solve uses $\tau_{eff}=\tau_{min}+10^{-6}$ and flags the month.

**Solver policy** (convention 16). CLARABEL at tolerance $10^{-12}$ (`decisions/section_2_review.md`); on any status other than optimal, 1 retry with SCS at $\epsilon=10^{-9}$; if that fails, the fund holds $w^{prev}$ and the month is flagged as a fallback.

## 6. Walk forward

At each execution date the drifted weights and the trade are

$$w^{prev}_i=\frac{w_i(1+r_i)}{\sum_j w_j(1+r_j)},\qquad \text{turnover}=\sum_i\lvert w_i-w^{prev}_i\rvert,\qquad \text{cost}=\sum_i c_i\lvert w_i-w^{prev}_i\rvert$$

with $r$ the gross asset returns since the previous execution close. The net holding return is

$$r^{net}=(1-\text{cost})(1+w'r^{hold})-1$$

**Ruin rule**, as overridden in instruction 04, amendment 4.2.8. The month whose $r^{net}\le-1$ is kept with $r^{net}$ floored at $-1$, the strategy is flagged ruined from that month on, and later months are not solved. Metrics include the ruin month, so wealth ends at 0, the annualised return is $-100\%$ and the maximum drawdown is $-100\%$. A ruined fund's point Sharpe ratio and every interval involving it are NaN, because a ratio of monthly moments says nothing about a path that ends at 0 (`decisions/section_5_review.md`, 2).

## 7. Statistics

Over $n$ monthly net returns and excess returns:

$$R_{ann}=\prod_s(1+r^{net}_s)^{12/n}-1,\qquad \sigma_{ann}=\operatorname{sd}(r^{net})\sqrt{12},\qquad SR=\frac{\overline{r^{ex}}}{\operatorname{sd}(r^{ex})}\sqrt{12}$$

with both standard deviations at ddof 1 (`decisions/section_5_review.md`, 1). Maximum drawdown is the minimum of $W_s/\max_{u\le s}W_u-1$ on the net wealth path starting at 1.

**Stationary bootstrap** (Politis and Romano), mean block length $L=6$ months, 10,000 replications, seed `bootstrap_seed`. For each replication, in order, with 1 generator `default_rng(seed)`:

$$i_0\sim U\{0,\dots,n-1\},\qquad i_j=\begin{cases}U\{0,\dots,n-1\}&\text{if } u_j<1/L\\(i_{j-1}+1)\bmod n&\text{otherwise}\end{cases},\qquad u_j\sim U(0,1)$$

Every strategy is resampled on the same index paths, so a difference between 2 strategies is taken path by path. A 90% interval is the 5th and 95th percentile by `np.quantile` with its default rule (`decisions/section_2_review.md`, 1), and the fraction of replications at or below 0 is reported next to it.

## 8. Covariance forecast evaluation

For each date, estimator and portfolio $w$ held over the $n_d$ holding days:

$$\hat\sigma^2=w'\Sigma w\,\frac{n_d}{21},\qquad \sigma^2_{real}=\sum_d(w'r_d)^2,\qquad \text{QLIKE}=\log\hat\sigma^2+\frac{\sigma^2_{real}}{\hat\sigma^2}$$

The bias ratio is the standard deviation (ddof 1) over dates of $r_h/\hat\sigma$, with $r_h=\sum_d w'r_d$, and a calibrated forecast lies in $1\pm1.645\sqrt{1/(2n)}$ with probability 90%. The portfolios are equal weight, the estimator's own budget-only minimum-variance portfolio, and 100 Dirichlet(1, …, 1) portfolios drawn once. QLIKE differences against Ledoit-Wolf use the bootstrap above over dates.

## 9. Experiments

**Sensitivity.** At each of 3 dates, $\tilde\mu=\hat\mu+\varepsilon$ with $\varepsilon=ZL'$, $L$ the Cholesky factor of $\Sigma_{lw}/36$, over 1,000 draws. Black-Litterman perturbs the views instead, $\tilde Q=Q+Z_QL_Q'$ with $L_Q$ the Cholesky factor of $P\Sigma_{lw}P'/11$, 11 being the months in the momentum window. The score is the mean over draws of $\sum_i\lvert\tilde w_i-w_i\rvert$.

**Turnover frontier.** For each limit, the expected return given up is $(\overline{\mu'w}_{none}-\overline{\mu'w}_\tau)\times12\times10^4$ bp a year and the cost saved is $(\overline{\text{cost}}_{none}-\overline{\text{cost}}_\tau)\times12\times10^4$, both over months 2 to 196. The realised difference bootstraps the paired monthly $r^{net}_\tau-r^{net}_{none}$.

**Levered risk-based funds** (instruction 05, step 5.6). Each month $k_t=\hat\sigma_{EW,t}/\hat\sigma_{s,t}$, the ratio of forecast annualised vols on $\Sigma_{lw}$, with no cap. The fund holds $k_tw_t$ in the assets and $1-k_t$ in cash at the risk-free rate, and borrowing above 1 pays a spread $s$ of 50 bp a year:

$$g_t=k_tw_t'r^{hold}+(1-k_t)r^{f}_{hold}-\max(k_t-1,0)\,s\,\frac{n_d}{252},\qquad r^{net}_t=(1-\text{cost}_t)(1+g_t)-1$$

Turnover and cost apply to the risky weights only, the drift carries cash at the risk-free rate, and the ruin rule applies. The net return keeps the form used everywhere else in the repo (`decisions/section_6_review.md`, 4).

## 10. Trades

With NAV $=\sum_i q_ip_i+\text{cash}$, the target quantity is $q^*_i=w_i\,\text{NAV}/p_i$ and the trade is $q^*_i-q_i$ rounded toward 0 to the lot size, so rounding never overshoots. Trades below the minimum notional are dropped. If cash after trades and estimated costs is below 0, the largest buy is cut 1 lot at a time until it is not. A universe ticker missing from the positions file is held at 0 and priced at the data close on the decision date (`decisions/section_7_review.md`, 1).
