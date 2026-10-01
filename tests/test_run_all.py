import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_ALL = ROOT / "scripts" / "run_all.py"
NETWORK_MODULES = {"yfinance", "requests", "urllib", "http", "socket", "pull_data", "scripts"}


def test_run_all_is_importable_and_offline():
    # No network import at module level: neither a network library nor scripts/pull_data.py.
    tree = ast.parse(RUN_ALL.read_text(encoding="utf-8"))
    imported = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert not imported & NETWORK_MODULES, imported & NETWORK_MODULES

    # Importable with sockets disabled (the suite runs under --disable-socket).
    spec = importlib.util.spec_from_file_location("run_all", RUN_ALL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)
    names = [name for name, _ in module.writers()]
    assert names[0] == "data.write_data_issues"
    assert names[-1] == "cli.main (6.5 demo)"
