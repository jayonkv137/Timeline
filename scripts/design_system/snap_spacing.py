"""Snap off-grid padding / margin / gap values to the COTRACE space scale.

    python3 scripts/design_system/snap_spacing.py <file.css|file.html> [--dry-run]

Second pass after migrate_to_tokens.py. Each remaining px value inside padding, margin, gap,
row-gap or column-gap moves to the nearest step of the 4px grid (2px half-steps); ties go to the
smaller step (product UI stays dense). Positions (top/left/width/height) are never touched.
In .html files only the <style> blocks are rewritten.
"""
import collections, re, sys
from pathlib import Path

SPACE = {0: "0", 1: "px", 2: "0-5", 4: "1", 6: "1-5", 8: "2", 10: "2-5", 12: "3", 14: "3-5", 16: "4", 20: "5",
         24: "6", 28: "7", 32: "8", 40: "10", 48: "12", 64: "16"}
STEPS = sorted(SPACE)
moved = collections.Counter()

def nearest(n):
    return min(STEPS, key=lambda s: (abs(s - n), s))

def snap_css(css):
    def decl(m):
        prop, value = m.group(1), m.group(2)
        if not (prop in ("padding", "margin", "gap", "row-gap", "column-gap") or prop.startswith(("padding-", "margin-"))):
            return m.group(0)
        def px(v):
            n = float(v.group(1))
            if n > 80:
                return v.group(0)
            step = nearest(n)
            moved[f"{v.group(1)}px → {step}px"] += 1
            return f"var(--p-space-{SPACE[step]})"
        return m.group(0).replace(value, re.sub(r"(?<![\w.(-])(\d+(?:\.\d+)?)px", px, value), 1)
    return re.sub(r"(?<=[{;])\s*([a-z-]+)\s*:\s*([^;{}]+)", decl, css)

def main():
    path = Path(sys.argv[1])
    text = path.read_text()
    if path.suffix == ".html":
        out = re.sub(r"(<style[^>]*>)(.*?)(</style>)", lambda m: m.group(1) + snap_css(m.group(2)) + m.group(3), text, flags=re.S)
    else:
        out = snap_css(text)
    if "--dry-run" not in sys.argv:
        path.write_text(out)
    print(f"{path.name}: snapped {sum(moved.values())} values")
    for k, n in sorted(moved.items(), key=lambda kv: -kv[1]):
        print(f"  {n:3}  {k}")

if __name__ == "__main__":
    main()
