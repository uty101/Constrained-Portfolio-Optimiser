import hashlib
import json
from pathlib import Path


def test_manifest_hashes_match(cfg):
    manifest = json.loads(Path(cfg.data.manifest).read_text(encoding="utf-8"))
    for csv in (cfg.data.prices_csv, cfg.data.rf_csv):
        digest = hashlib.sha256(Path(csv).read_bytes()).hexdigest()
        assert digest == manifest["sha256"][Path(csv).name], csv
