"""The README tables, written from the output CSVs as Markdown snippets (instruction 07,
amendment 7.2). README.md embeds each snippet verbatim between marker comments, and
tests/test_report.py checks that the two agree.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pc.config import Config
from pc.stats import PRIMARY_IDS

README_SNIPPETS = ["readme_primary.md", "readme_qlike.md", "readme_turnover.md", "readme_levered.md",
                   "readme_robustness.md"]
QLIKE_SETS = [("ew", "EW"), ("gmv", "GMV"), ("random", "random")]
QLIKE_REFERENCE = "lw_cc"


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def num(x: float, dp: int) -> str:
    """x to dp decimals, with no negative zero."""
    return f"{round(x, dp) + 0.0:.{dp}f}"


def interval(value: float, lo: float, hi: float, dp: int) -> str:
    return f"{num(value, dp)} ({num(lo, dp)} to {num(hi, dp)})"


def code(strategy_id: str) -> str:
    """A strategy id as a code span; its pipes are escaped for a Markdown table cell."""
    return "`" + strategy_id.replace("|", "\\|") + "`"


def is_true(x) -> bool:
    return str(x) == "True"


def markdown_table(header: list[str], rows: list[list[str]], align: list[str]) -> str:
    rule = {"l": "---", "r": "---:"}
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(rule[a] for a in align) + "|"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def primary_table(primary: pd.DataFrame, metrics: pd.DataFrame) -> str:
    ruin = metrics.set_index("strategy_id")["ruin_month"]
    rows = []
    for _, r in primary.iterrows():
        sharpe = (f"ruined ({ruin[r['strategy_id']]})" if is_true(r["ruined"])
                  else interval(r["sharpe"], r["sharpe_p05"], r["sharpe_p95"], 2))
        rows.append([code(r["strategy_id"]), pct(r["ann_return"]), pct(r["ann_vol"]), sharpe, pct(r["max_dd"]),
                     pct(r["mean_turnover"]), num(r["mean_positions"], 1)])
    header = ["Strategy", "Ann. return", "Vol", "Sharpe (90% interval)", "Max DD", "Monthly turnover",
              "Avg positions"]
    return markdown_table(header, rows, ["l", "r", "r", "r", "r", "r", "r"])


def qlike_table(cov_eval: pd.DataFrame, diff: pd.DataFrame) -> str:
    ev = cov_eval.set_index(["estimator", "portfolio_set"])
    df = diff.set_index(["estimator", "portfolio_set"])
    rows = []
    for est in cov_eval["estimator"].drop_duplicates():
        row = [est]
        for pset, _ in QLIKE_SETS:
            e = ev.loc[(est, pset)]
            if est == QLIKE_REFERENCE:
                d = "reference"
            else:
                r = df.loc[(est, pset)]
                d = interval(r["diff_vs_lw_cc"], r["p05"], r["p95"], 3)
            row += [num(e["qlike_mean"], 3), d, num(e["bias_ratio"], 2)]
        rows.append(row)
    header = ["Estimator"]
    for _, label in QLIKE_SETS:
        header += [f"{label} QLIKE", f"{label} diff vs {QLIKE_REFERENCE} (90% interval)", f"{label} bias ratio"]
    band = cov_eval.iloc[0]
    note = (f"\nBias ratio 90% band for a correct forecast over {int(band['n'])} months: "
            f"{num(band['band_lo'], 2)} to {num(band['band_hi'], 2)}. A QLIKE difference below 0 means a better "
            f"forecast than {QLIKE_REFERENCE}.\n")
    return markdown_table(header, rows, ["l"] + ["r"] * (len(header) - 1)) + note


def turnover_table(frontier: pd.DataFrame) -> str:
    rows = []
    for _, r in frontier.loc[frontier["tau"].astype(str) != "none"].iterrows():
        rows.append([str(r["tau"]), str(int(r["n_binding"])), num(r["exante_return_given_up_bp_pa"], 1),
                     num(r["cost_saved_bp_pa"], 1),
                     interval(r["realised_net_vs_none_bp_pa"], r["realised_net_vs_none_p05"],
                              r["realised_net_vs_none_p95"], 1)])
    header = ["τ", "Months binding", "Return given up (bp pa)", "Cost saved (bp pa)",
              "Realised net vs no limit (bp pa, 90% interval)"]
    return markdown_table(header, rows, ["l", "r", "r", "r", "r"])


def levered_table(levered: pd.DataFrame) -> str:
    rows = []
    for _, r in levered.iterrows():
        diff = ("benchmark" if r["strategy_id"] == "equal_weight|none|none|none"
                else interval(r["diff_vs_ew"], r["diff_p05"], r["diff_p95"], 2))
        rows.append([code(r["strategy_id"]), num(r["mean_k"], 2), num(r["max_k"], 2), pct(r["ann_return"]),
                     pct(r["ann_vol"]), interval(r["sharpe"], r["sharpe_p05"], r["sharpe_p95"], 2), diff,
                     pct(r["max_dd"])])
    header = ["Strategy", "Mean k", "Max k", "Ann. return", "Vol", "Sharpe (90% interval)",
              "Sharpe minus equal weight (90% interval)", "Max DD"]
    return markdown_table(header, rows, ["l", "r", "r", "r", "r", "r", "r", "r"])


def cost_table(costs: pd.DataFrame) -> str:
    scales = sorted(costs["cost_scale"].unique())
    rows = []
    for sid in PRIMARY_IDS:
        sub = costs.loc[costs["strategy_id"] == sid].set_index("cost_scale")
        rows.append([code(sid)] + ["ruined" if is_true(sub.at[s, "ruined"]) else num(sub.at[s, "sharpe"], 2)
                                   for s in scales])
    header = ["Strategy"] + [f"Sharpe, costs × {s:g}" for s in scales]
    return markdown_table(header, rows, ["l"] + ["r"] * len(scales))


def monthly_cov_table(monthly: pd.DataFrame) -> str:
    rows = []
    for _, r in monthly.iterrows():
        sharpe = f"ruined ({r['ruin_month']})" if is_true(r["ruined"]) else num(r["sharpe"], 2)
        rows.append([r["sigma_basis"], code(r["strategy_id"]), str(int(r["n_months"])), pct(r["ann_return"]),
                     pct(r["ann_vol"]), sharpe, pct(r["max_dd"]), pct(r["mean_turnover"])])
    header = ["Σ from", "Strategy", "Months", "Ann. return", "Vol", "Sharpe", "Max DD", "Monthly turnover"]
    return markdown_table(header, rows, ["l", "l", "r", "r", "r", "r", "r", "r"])


def robustness_table(costs: pd.DataFrame, monthly: pd.DataFrame) -> str:
    return (f"**Cost scales.** Every one-way cost multiplied by the scale.\n\n{cost_table(costs)}\n"
            f"**Covariance from 36 monthly returns** against the daily estimate.\n\n{monthly_cov_table(monthly)}")


def readme_tables(tables_dir: Path) -> dict[str, str]:
    def read(name: str) -> pd.DataFrame:
        return pd.read_csv(tables_dir / name, dtype={"tau": str, "ruin_month": str}, keep_default_na=True)

    return {
        "readme_primary.md": primary_table(read("results_primary.csv"), read("metrics_all.csv")),
        "readme_qlike.md": qlike_table(read("cov_eval.csv"), read("cov_eval_qlike_diff.csv")),
        "readme_turnover.md": turnover_table(read("turnover_frontier.csv")),
        "readme_levered.md": levered_table(read("levered_risk_based.csv")),
        "readme_robustness.md": robustness_table(read("cost_sensitivity.csv"), read("monthly_cov_strategies.csv")),
    }


def write_readme_tables(cfg: Config) -> list[Path]:
    tables = Path(cfg.outputs.tables_dir)
    paths = []
    for name, text in readme_tables(tables).items():
        path = tables / name
        path.write_bytes(text.encode("utf-8"))
        paths.append(path)
    return paths


def readme_block(readme: str, name: str) -> str:
    """The text between <!-- name --> and <!-- /name --> in README.md, without the newline after
    the opening marker."""
    start, end = f"<!-- {name} -->\n", f"<!-- /{name} -->"
    i = readme.index(start) + len(start)
    return readme[i:readme.index(end, i)]

