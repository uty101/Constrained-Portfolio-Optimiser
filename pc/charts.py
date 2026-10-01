"""Chart 1 (in-sample frontiers against out-of-sample strategy points) and Chart 2 (stacked weights).

PLAN 4.6 with instruction 04 amendment 4.6. matplotlib, 150 dpi, one chart per file.
"""

from __future__ import annotations

from pathlib import Path

import cvxpy as cp
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from pc.allocators import Constraints, min_variance  # noqa: E402
from pc.calendar import build_calendar  # noqa: E402
from pc.config import Config  # noqa: E402
from pc.data import load_prices, load_rf_daily  # noqa: E402
from pc.returns import holding_returns, holding_rf  # noqa: E402
from pc.solver import solve, symmetrise  # noqa: E402
from pc.stats import PRIMARY_IDS, SHARPE_DDOF  # noqa: E402

DPI = 150  # kickoff Section 6: figures at 150 dpi
MONTHS_PER_YEAR = 12
# Amendment 4.6: set B has 50 target returns; the closed-form set A curve uses the same count.
FRONTIER_POINTS = 50
# Amendment 4.6: the set A curve runs to 3 times the largest single-asset excess return.
SET_A_RETURN_MULTIPLE = 3
# Amendment 4.6: the x-axis runs from 0 to 30% annualised vol.
X_MAX = 0.30
# Margin added above and below the y data range, as a fraction of that range (presentation only).
Y_PAD = 0.05
CHART2_IDS = ["mv_constrained|lw_cc|sample|C", "risk_parity|ewma|none|none"]


def holding_excess(prices: pd.DataFrame, rf_daily: pd.Series, cfg: Config) -> pd.DataFrame:
    """The 196 holding-period excess returns of the 18 assets: gross exec -> next_exec, minus rf_hold."""
    cal = build_calendar(prices.index, cfg)
    return holding_returns(prices, cal).sub(holding_rf(rf_daily, cal), axis=0)


def frontier_inputs(excess: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """Annualised mu = mean x 12 and Sigma = sample covariance (ddof 1) x 12."""
    mu = excess.mean() * MONTHS_PER_YEAR
    Sigma = pd.DataFrame(np.cov(excess.to_numpy(dtype=float), rowvar=False, ddof=1) * MONTHS_PER_YEAR,
                         index=excess.columns, columns=excess.columns)
    return mu, Sigma


def frontier_set_a(mu: pd.Series, Sigma: pd.DataFrame) -> pd.DataFrame:
    """Budget-only frontier, closed form: var(m) = (C m^2 - 2 B m + A) / (A C - B^2),
    A = mu'S^-1 mu, B = 1'S^-1 mu, C = 1'S^-1 1, from the GMV return B/C to 3 max(mu)."""
    m_ = mu.to_numpy(dtype=float)
    inv = np.linalg.solve(Sigma.to_numpy(dtype=float), np.column_stack([m_, np.ones(len(m_))]))
    A, B, C = m_ @ inv[:, 0], inv[:, 0].sum(), inv[:, 1].sum()
    targets = np.linspace(B / C, SET_A_RETURN_MULTIPLE * m_.max(), FRONTIER_POINTS)
    var = (C * targets**2 - 2 * B * targets + A) / (A * C - B**2)
    return pd.DataFrame({"target_return": targets, "vol": np.sqrt(var)})


def frontier_set_b(mu: pd.Series, Sigma: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Long-only capped frontier: 50 targets from the set B minimum variance fund's return to the
    largest return feasible under lower <= w <= upper, each min w'Sigma w s.t. mu'w = target, a
    CLARABEL solve under the solver policy. vol is NaN where the solve fell back."""
    cons = Constraints(lower=cfg.mv.lower, upper=cfg.mv.upper)
    mvf = min_variance(mu, Sigma, None, cons)
    if mvf.fallback:
        raise ValueError(f"set B minimum variance fund did not solve: {mvf.status}")
    m_ = mu.to_numpy(dtype=float)
    S = symmetrise(Sigma)
    n = len(m_)

    w = cp.Variable(n)
    bounds = [cp.sum(w) == 1, w >= cfg.mv.lower, w <= cfg.mv.upper]
    lp = cp.Problem(cp.Maximize(m_ @ w), bounds)
    rec = solve(lp)
    if rec.fallback:
        raise ValueError(f"set B maximum return LP did not solve: {rec.status}")
    lo, hi = float(m_ @ mvf.weights.to_numpy()), float(lp.value)

    rows = []
    for target in np.linspace(lo, hi, FRONTIER_POINTS):
        w = cp.Variable(n)
        prob = cp.Problem(cp.Minimize(cp.quad_form(w, S)),
                          [cp.sum(w) == 1, w >= cfg.mv.lower, w <= cfg.mv.upper, m_ @ w == target])
        r = solve(prob)
        vol = np.nan if r.fallback else float(np.sqrt(max(prob.value, 0.0)))
        rows.append({"target_return": target, "vol": vol, "solver": r.solver, "status": r.status})
    return pd.DataFrame(rows)


def strategy_points(periods: pd.DataFrame, ids: list[str]) -> pd.DataFrame:
    """x = std(excess_net) sqrt(12), y = mean(excess_net) x 12, over the months with a return."""
    rows = []
    for sid in ids:
        p = periods[periods["strategy_id"] == sid]
        x = p["excess_net"].dropna().to_numpy(dtype=float)
        rows.append({
            "strategy_id": sid,
            "label": sid.split("|")[0],
            "ann_vol": float(np.std(x, ddof=SHARPE_DDOF) * np.sqrt(MONTHS_PER_YEAR)),
            "ann_excess": float(x.mean() * MONTHS_PER_YEAR),
            "ruined": bool(p["ruined"].any()),
        })
    return pd.DataFrame(rows)


def y_limits(front_a: pd.DataFrame, front_b: pd.DataFrame, points: pd.DataFrame) -> tuple[float, float]:
    """The range of every frontier point and strategy point with 0 <= vol <= X_MAX, padded by Y_PAD."""
    ys = [f.loc[f["vol"].between(0, X_MAX), "target_return"] for f in (front_a, front_b)]
    ys.append(points.loc[points["ann_vol"].between(0, X_MAX), "ann_excess"])
    y = pd.concat(ys).dropna()
    lo, hi = float(y.min()), float(y.max())
    pad = Y_PAD * (hi - lo)
    return lo - pad, hi + pad


def outside_axes(points: pd.DataFrame, ylim: tuple[float, float]) -> pd.DataFrame:
    inside = points["ann_vol"].between(0, X_MAX) & points["ann_excess"].between(*ylim)
    return points[~inside]


def outside_text(outside: pd.DataFrame) -> str:
    lines = ["Outside the axes (ann. vol, ann. excess return):"]
    for row in outside.itertuples():
        flag = ", ruined" if row.ruined else ""
        lines.append(f"{row.label} ({row.strategy_id}): {row.ann_vol:.1%}, {row.ann_excess:.1%}{flag}")
    return "\n".join(lines)


def plot_frontier(front_a: pd.DataFrame, front_b: pd.DataFrame, points: pd.DataFrame, path: Path) -> str:
    """Chart 1. Returns the text box contents ("" when every point is inside the axes)."""
    ylim = y_limits(front_a, front_b, points)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(front_a["vol"], front_a["target_return"], color="#1f77b4", lw=1.6,
            label="Set A frontier (budget only), in-sample")
    ax.plot(front_b["vol"], front_b["target_return"], color="#d62728", lw=1.6, marker="o", ms=2.5,
            label="Set B frontier (0 ≤ w ≤ 0.30), in-sample")
    inside = points[points["ann_vol"].between(0, X_MAX) & points["ann_excess"].between(*ylim)]
    ax.scatter(inside["ann_vol"], inside["ann_excess"], color="black", zorder=3, s=22,
               label="Strategies, out-of-sample (net, excess)")
    for row in inside.itertuples():
        ax.annotate(row.label, (row.ann_vol, row.ann_excess), xytext=(5, 4), textcoords="offset points", fontsize=8)
    text = ""
    outside = outside_axes(points, ylim)
    if len(outside):
        text = outside_text(outside)
        ax.text(0.98, 0.02, text, transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5,
                bbox={"boxstyle": "round", "facecolor": "white", "edgecolor": "0.6"})
    ax.set_xlim(0, X_MAX)
    ax.set_ylim(*ylim)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_xlabel("Annualised volatility of monthly excess returns")
    ax.set_ylabel("Annualised mean monthly excess return")
    ax.set_title("In-sample frontiers and out-of-sample strategies, 196 holding periods")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return text


def plot_weights_stacked(weights_long: pd.DataFrame, ids: list[str], tickers: list[str], path: Path) -> None:
    """Chart 2: one panel per strategy, stacked target weights through time, y from 0 to 1."""
    colors = plt.get_cmap("tab20").colors
    fig, axes = plt.subplots(len(ids), 1, figsize=(11, 4 * len(ids)), sharex=True)
    for ax, sid in zip(np.atleast_1d(axes), ids):
        w = weights_long[weights_long["strategy_id"] == sid].pivot(
            index="decision_date", columns="ticker", values="w_target")[tickers]
        ax.stackplot(w.index, w.T.to_numpy(), labels=tickers, colors=colors[: len(tickers)], linewidth=0)
        ax.set_ylim(0, 1)
        ax.set_xlim(w.index[0], w.index[-1])
        ax.set_title(sid, fontsize=10)
        ax.set_ylabel("Target weight")
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    np.atleast_1d(axes)[0].legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=7.5, ncol=1)
    np.atleast_1d(axes)[-1].set_xlabel("Decision date")
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


def write_charts(cfg: Config) -> dict:
    """Both charts from the committed data and the step 4.2 outputs; returns what was plotted."""
    prices = load_prices(cfg)
    rf_daily = load_rf_daily(cfg, prices.index)
    mu, Sigma = frontier_inputs(holding_excess(prices, rf_daily, cfg))
    front_a, front_b = frontier_set_a(mu, Sigma), frontier_set_b(mu, Sigma, cfg)
    results = Path(cfg.outputs.results_dir)
    periods = pd.read_parquet(results / "periods.parquet")
    points = strategy_points(periods, PRIMARY_IDS)
    figures = Path(cfg.outputs.figures_dir)
    text = plot_frontier(front_a, front_b, points, figures / "frontier_vs_oos.png")
    plot_weights_stacked(pd.read_parquet(results / "weights_long.parquet"), CHART2_IDS,
                         list(cfg.universe.tickers), figures / "weights_stacked.png")
    return {"mu": mu, "front_a": front_a, "front_b": front_b, "points": points, "text_box": text,
            "ylim": y_limits(front_a, front_b, points)}
