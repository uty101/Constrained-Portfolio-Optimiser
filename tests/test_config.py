import tomllib
from dataclasses import fields, is_dataclass

from conftest import ROOT


def _key_mismatches(toml_table: dict, obj, prefix: str = "") -> list[str]:
    """Keys in the TOML table that are not fields of obj, and the reverse.

    Dataclass fields recurse; dict fields (ticker-keyed tables) are compared
    key for key.
    """
    if is_dataclass(obj):
        obj_keys = {f.name for f in fields(obj)}
        child = lambda k: getattr(obj, k)  # noqa: E731
    else:
        obj_keys = set(obj)
        child = lambda k: obj[k]  # noqa: E731
    out = [f"{prefix}{k} not in Config" for k in toml_table.keys() - obj_keys]
    out += [f"{prefix}{k} not in config.toml" for k in obj_keys - toml_table.keys()]
    for k in toml_table.keys() & obj_keys:
        if isinstance(toml_table[k], dict):
            value = child(k)
            if not (is_dataclass(value) or isinstance(value, dict)):
                out.append(f"{prefix}{k} is a table in config.toml but not in Config")
                continue
            out += _key_mismatches(toml_table[k], value, f"{prefix}{k}.")
    return out


def test_config_keys_match_fields(cfg):
    with open(ROOT / "config.toml", "rb") as f:
        raw = tomllib.load(f)
    assert _key_mismatches(raw, cfg) == []


def test_w_mkt_sums_to_one(cfg):
    assert abs(sum(cfg.bl.w_mkt.values()) - 1.0) <= 1e-12


def test_one_way_bp_tickers(cfg):
    assert len(cfg.universe.tickers) == 18
    assert list(cfg.costs.one_way_bp) == list(cfg.universe.tickers)
