"""Inventory every literal visual value in the workspace prototype.

Read-only. Prints colour, font-size, spacing, radius, duration and shadow literals with
counts and the files they come from, so the token set is built from what exists rather
than from memory. Run from the repo root:  python3 scripts/design_system/inventory_prototype.py
"""
import collections, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = [
    "web/src/workspace/workspace.css",
    "web/src/workspace/obsidian-graph.css",
    "web/src/workspace/LocalGraph.tsx",
    "web/src/workspace/Workspace.tsx",
    "web/src/workspace/Brain.tsx",
    "web/src/workspace/brain-engine.js",
    "web/src/workspace/photon.ts",
]
PATTERNS = {
    "hex": re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b(?![0-9a-fA-F])"),
    "rgba": re.compile(r"rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+(?:\s*,\s*[\d.]+)?\s*\)"),
    "font_size": re.compile(r"font-size:\s*([\d.]+px)|font:\s*(?:\d{3}\s+)?([\d.]+px)"),
    "radius": re.compile(r"border-radius:\s*([^;}]+)"),
    "duration": re.compile(r"(?<![\w.])(\d*\.?\d+m?s)\b(?=[\s,;)}'\"]|$)"),
    "shadow": re.compile(r"box-shadow:\s*([^;}]+)"),
    "font_family": re.compile(r"font-family:\s*([^;}]+)"),
    "spacing": re.compile(r"(?:padding|margin|gap|top|bottom|left|right)(?:-[a-z]+)?:\s*([^;}]+)"),
}

def main():
    out = {k: collections.Counter() for k in PATTERNS}
    where = {k: collections.defaultdict(set) for k in PATTERNS}
    for rel in FILES:
        p = ROOT / rel
        if not p.exists():
            continue
        text = p.read_text(errors="ignore")
        for k, pat in PATTERNS.items():
            for m in pat.finditer(text):
                v = next((g for g in m.groups() if g), m.group(0)) if m.groups() else m.group(0)
                v = re.sub(r"\s+", " ", v.strip().lower())
                if k == "duration" and not re.fullmatch(r"\d*\.?\d+m?s", v):
                    continue
                if k == "spacing":
                    for part in v.split():
                        if re.fullmatch(r"-?\d+(\.\d+)?px", part):
                            out[k][part] += 1; where[k][part].add(Path(rel).name)
                    continue
                out[k][v] += 1
                where[k][v].add(Path(rel).name)
    as_json = "--json" in sys.argv
    result = {k: [(v, n, sorted(where[k][v])) for v, n in c.most_common()] for k, c in out.items()}
    if as_json:
        print(json.dumps(result, indent=1)); return
    for k, rows in result.items():
        print(f"\n## {k} ({len(rows)} distinct)")
        for v, n, files in rows[:60]:
            print(f"  {n:4}  {v:48} {', '.join(files)}")

if __name__ == "__main__":
    main()
