"""List each top-level function and class in pc/ whose name appears in no other file under pc/,
scripts/ or tests/ (instruction 07, step 7.5), with the number of times the name appears again in
its own module. A name used only inside its own module is a helper; one used nowhere is dead.

    python scripts/find_unused.py
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEARCH_DIRS = ["pc", "scripts", "tests"]


def top_level_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]


def unused() -> list[tuple[str, str, int]]:
    files = sorted(p for d in SEARCH_DIRS for p in (ROOT / d).rglob("*.py"))
    texts = {p: p.read_text(encoding="utf-8") for p in files}
    hits = []
    for module in sorted((ROOT / "pc").glob("*.py")):
        for name in top_level_names(module):
            word = re.compile(rf"\b{re.escape(name)}\b")
            if not any(word.search(text) for p, text in texts.items() if p != module):
                own = len(word.findall(texts[module])) - 1  # uses in its own module, the definition excluded
                hits.append((module.relative_to(ROOT).as_posix(), name, own))
    return hits


def main() -> int:
    hits = unused()
    for module, name, own in hits:
        print(f"{module}: {name} (other uses in its own module: {own})")
    print(f"{len(hits)} names used in no other file; {sum(own == 0 for *_, own in hits)} used nowhere")
    return 0


if __name__ == "__main__":
    sys.exit(main())
