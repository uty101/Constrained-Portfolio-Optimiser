import numpy as np
import pandas as pd
from PIL import Image

from pc.charts import (
    X_MAX,
    frontier_inputs,
    frontier_set_a,
    frontier_set_b,
    plot_frontier,
    plot_weights_stacked,
    strategy_points,
)

TICKERS = ["A", "B", "C", "D", "E", "F"]


def test_charts_write_png(cfg, tmp_path):
    rng = np.random.default_rng(cfg.run.seed_master)
    n = 60
    excess = pd.DataFrame(rng.normal(0.004, 0.03, (n, len(TICKERS))), columns=TICKERS)
    mu, Sigma = frontier_inputs(excess)
    front_a, front_b = frontier_set_a(mu, Sigma), frontier_set_b(mu, Sigma, cfg)
    assert len(front_a) == len(front_b) == 50
    assert front_b["vol"].notna().all()
    # Every set B point is at or above the unconstrained frontier's vol at the same return.
    m_ = mu.to_numpy()
    inv = np.linalg.solve(Sigma.to_numpy(), np.column_stack([m_, np.ones(len(m_))]))
    A, B, C = m_ @ inv[:, 0], inv[:, 0].sum(), inv[:, 1].sum()
    t = front_b["target_return"].to_numpy()
    assert (front_b["vol"].to_numpy() >= np.sqrt((C * t**2 - 2 * B * t + A) / (A * C - B**2)) - 1e-7).all()

    dates = pd.date_range("2020-01-31", periods=n, freq="ME")
    ids = ["s|x|y|A", "far|x|y|A", "flat|none|none|none"]
    periods = pd.concat([
        pd.DataFrame({"strategy_id": sid, "decision_date": dates, "excess_net": rng.normal(0.005, sd, n),
                      "ruined": False})
        for sid, sd in (("s|x|y|A", 0.02), ("far|x|y|A", 0.5), ("flat|none|none|none", 0.01))
    ], ignore_index=True)
    points = strategy_points(periods, ids)
    assert points.loc[1, "ann_vol"] > X_MAX

    chart1 = tmp_path / "frontier_vs_oos.png"
    text = plot_frontier(front_a, front_b, points, chart1)
    assert "far|x|y|A" in text and "s|x|y|A" not in text

    weights = pd.concat([
        pd.DataFrame({"strategy_id": sid, "decision_date": d, "ticker": TICKERS, "w_target": w})
        for sid in ("p1", "p2") for d in dates for w in [rng.dirichlet(np.ones(len(TICKERS)))]
    ], ignore_index=True)
    chart2 = tmp_path / "weights_stacked.png"
    plot_weights_stacked(weights, ["p1", "p2"], TICKERS, chart2)

    for path in (chart1, chart2):
        assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
        with Image.open(path) as im:
            assert tuple(round(v) for v in im.info["dpi"]) == (150, 150)
