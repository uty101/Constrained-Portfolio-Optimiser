from pc.backtest import build_registry

REGISTRY_IDS = [
    "mv_unconstrained|sample|sample|A",
    "mv_unconstrained|lw_cc|sample|A",
    "mv_unconstrained|ewma|sample|A",
    "mv_unconstrained|pca3|sample|A",
    "mv_constrained|sample|sample|C",
    "mv_constrained|lw_cc|sample|C",
    "mv_constrained|ewma|sample|C",
    "mv_constrained|pca3|sample|C",
    "mv_constrained|lw_cc|bayes_stein|C",
    "min_variance|sample|none|B",
    "min_variance|lw_cc|none|B",
    "min_variance|ewma|none|B",
    "min_variance|pca3|none|B",
    "risk_parity|sample|none|none",
    "risk_parity|lw_cc|none|none",
    "risk_parity|ewma|none|none",
    "risk_parity|pca3|none|none",
    "black_litterman|sample|bl|C",
    "black_litterman|lw_cc|bl|C",
    "black_litterman|ewma|bl|C",
    "black_litterman|pca3|bl|C",
    "hrp|sample|none|none",
    "hrp|lw_cc|none|none",
    "hrp|ewma|none|none",
    "hrp|pca3|none|none",
    "equal_weight|none|none|none",
]


def test_registry_26_exact_ids(cfg):
    specs = build_registry(cfg)
    ids = [s.id for s in specs]
    assert len(ids) == 26
    assert len(set(ids)) == 26
    assert ids == REGISTRY_IDS
    for s in specs:
        assert s.id == f"{s.allocator}|{s.cov}|{s.mu_model}|{s.cons_set}"
