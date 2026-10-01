from pathlib import Path

import pandas as pd

from pc.report import README_SNIPPETS, interval, num, readme_block, turnover_table

ROOT = Path(__file__).resolve().parents[1]


def test_readme_tables_match_snippets(cfg):
    # The committed README embeds each committed snippet verbatim between its marker comments.
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for name in README_SNIPPETS:
        snippet = (ROOT / cfg.outputs.tables_dir / name).read_text(encoding="utf-8")
        assert readme_block(readme, name) == snippet, name


def test_number_formats():
    assert num(-1.2e-07, 1) == "0.0"
    assert num(-0.0027, 2) == "0.00"
    assert interval(0.6738, 0.3633, 1.0267, 2) == "0.67 (0.36 to 1.03)"


def test_turnover_table_drops_none_row():
    frontier = pd.DataFrame({
        "tau": ["0.3", "none"], "n_binding": [62, 0], "exante_return_given_up_bp_pa": [7.88, 0.0],
        "cost_saved_bp_pa": [0.9524, 0.0], "realised_net_vs_none_bp_pa": [-7.84, 0.0],
        "realised_net_vs_none_p05": [-41.76, float("nan")], "realised_net_vs_none_p95": [24.9, float("nan")],
    })
    lines = turnover_table(frontier).splitlines()
    assert len(lines) == 3
    assert lines[2] == "| 0.3 | 62 | 7.9 | 1.0 | -7.8 (-41.8 to 24.9) |"
