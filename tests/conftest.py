from pathlib import Path

import pytest

from pc.config import load_config

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _run_from_repo_root(monkeypatch):
    # Paths in config.toml are relative to the repo root.
    monkeypatch.chdir(ROOT)


@pytest.fixture
def cfg():
    return load_config(ROOT / "config.toml")
