"""Rewrite literal visual values in a stylesheet to COTRACE token variables.

    python3 scripts/design_system/migrate_to_tokens.py web/src/workspace/workspace.css [--dry-run]

Rules (DS v0.1 baseline migration):
  colour   neutral greys snap to the nearest dark-scale step (OKLab distance), then take the semantic
           name for the CSS property they sit in (background -> surface/bg, color -> text,
           border/outline -> border); otherwise the primitive step variable. Party, focus and
           overlay colours map by exact value. Anything else stays literal and is reported.
  size     font-size snaps to the type scale (10px floor); border-radius snaps to the radius scale;
           padding/margin/gap convert only on exact scale matches (layout stays pixel-identical).
  motion   transition durations map to fast/base/slow; long ambient animations stay and are reported.
Prints a debt report of everything left literal.
"""
import collections, json, math, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOKENS = json.loads((ROOT / "web/src/design-system/tokens/tokens.json").read_text())
DARK = {int(k): v["$value"] for k, v in TOKENS["primitive"]["color"]["neutral-dark"].items() if k.isdigit()}

def rgb(h):
    h = h.lstrip("#")
    if len(h) == 3: h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

def oklab(h):
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(c) for c in rgb(h))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (x ** (1 / 3) for x in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)

def chroma(h):
    _, a, b = oklab(h); return math.hypot(a, b)

def nearest_step(h):
    L = oklab(h)
    return min(DARK, key=lambda k: math.dist(L, oklab(DARK[k])))

EXACT_COLOR = {
    "#38bdf8": "--color-party-human-solid", "#fb923c": "--color-party-ai-solid",
    "#7dd3fc": "--color-party-human-text", "#fdba74": "--color-party-ai-text",
    "#d3ab94": "--color-party-human-solid",  # Codex v1 clay 'human' — unified to the one party colour
    "#8eafc5": "--color-party-ai-solid",     # Codex v1 muted-blue 'AI' — unified
    "#b7cbd7": "--color-focus-ring", "#090a0f": "--p-color-neutral-dark-1", "#141417": "--color-bg-graph",
    "#ffffff": "--p-color-white", "#fff": "--p-color-white", "#000": "--p-color-black", "#000000": "--p-color-black",
}
EXACT_RGBA = {
    "rgba(9,10,15,.92)": "--color-surface-overlay", "rgba(9,10,15,0.92)": "--color-surface-overlay",
    "rgba(255,255,255,0.16)": "--color-border-on-overlay", "rgba(255,255,255,0.12)": "--scrubber-rail",
}
SEMANTIC = {
    "bg": {1: "--color-bg-canvas", 3: "--color-bg-app", 4: "--color-surface-panel", 5: "--color-surface-raised", 6: "--color-surface-hover"},
    "text": {13: "--color-text-strong", 12: "--color-text-primary", 11: "--color-text-secondary", 10: "--color-text-muted", 9: "--color-text-faint", 8: "--color-text-disabled"},
    "border": {5: "--color-border-subtle", 6: "--color-border-default", 7: "--color-border-strong"},
}
FONT = {8: "2xs", 8.5: "2xs", 9: "2xs", 9.5: "2xs", 10: "2xs", 10.5: "xs", 11: "xs", 11.5: "sm", 12: "sm", 13: "base", 14: "base",
        15: "md", 16: "lg", 18: "lg", 20: "xl", 21: "xl", 23: "2xl", 24: "2xl", 25: "2xl", 27: "3xl", 45: "display"}
RADIUS = {1: "xs", 2: "xs", 3: "sm", 4: "sm", 5: "sm", 6: "md", 7: "md", 8: "lg", 9: "lg", 10: "lg", 11: "xl", 12: "xl", 15: "2xl", 16: "2xl", 20: "3xl", 9999: "pill"}
SPACE = {0: "0", 1: "px", 2: "0-5", 4: "1", 6: "1-5", 8: "2", 10: "2-5", 12: "3", 14: "3-5", 16: "4", 20: "5", 24: "6", 28: "7", 32: "8", 40: "10", 48: "12", 64: "16"}
SHADOW = {"0 4px 12px #0004": "--elevation-2", "0 8px 24px #0002": "--elevation-1", "0 10px 30px #0005": "--elevation-3"}

debt = collections.Counter()
done = collections.Counter()

def role(prop):
    if prop in ("color", "caret-color", "-webkit-text-fill-color"): return "text"
    if prop.startswith("background") or prop in ("fill",): return "bg"
    if prop.startswith("border") or prop.startswith("outline"): return "border"
    return None

def color_var(hexv, prop):
    h = hexv.lower()
    if h in EXACT_COLOR: done["colour exact"] += 1; return f"var({EXACT_COLOR[h]})"
    if len(h) in (5, 9):  # #rgba / #rrggbbaa
        return alpha_hex(h, prop) or hexv
    if len(h) not in (4, 7):
        debt[f"odd colour {h} ({prop})"] += 1; return hexv
    if chroma(h) > 0.045:
        debt[f"chromatic colour {h} ({prop})"] += 1; return hexv
    step = nearest_step(h)
    r = role(prop)
    name = SEMANTIC.get(r, {}).get(step) if r else None
    done["grey snapped"] += 1
    return f"var({name or f'--p-color-neutral-dark-{step}'})"

WHITE_A = [4,5,6,8,10,12,14,16,18,22,25,30,40,45,55,70,85,90]
BLACK_A = [13,20,27,33,45,55,75,85,90,95]

def alpha_var(r, g, b, a, prop):
    pct = a * 100
    if (r, g, b) == (255, 255, 255):
        best = min(WHITE_A, key=lambda n: abs(n - pct))
        if abs(best - pct) <= 2: done["alpha"] += 1; return f"var(--p-color-white-alpha-{best})"
    if (r, g, b) == (0, 0, 0):
        best = min(BLACK_A, key=lambda n: abs(n - pct))
        if abs(best - pct) <= 2.5: done["alpha"] += 1; return f"var(--p-color-black-alpha-{best})"
    if (r, g, b) == (56, 189, 248) and abs(pct - 15) <= 1: done["alpha"] += 1; return "var(--color-party-human-soft)"
    if (r, g, b) == (56, 189, 248) and abs(pct - 45) <= 5: done["alpha"] += 1; return "var(--color-party-human-line)"
    if (r, g, b) == (251, 146, 60) and abs(pct - 15) <= 1: done["alpha"] += 1; return "var(--color-party-ai-soft)"
    if (r, g, b) == (251, 146, 60) and abs(pct - 45) <= 5: done["alpha"] += 1; return "var(--color-party-ai-line)"
    debt[f"alpha colour rgba({r},{g},{b},{a:.2f}) ({prop})"] += 1
    return None

def alpha_hex(h, prop):
    x = h.lstrip('#')
    if len(x) == 4: r, g, b, a = (int(c * 2, 16) for c in x)
    elif len(x) == 8: r, g, b, a = (int(x[i:i+2], 16) for i in (0, 2, 4, 6))
    else: return None
    return alpha_var(r, g, b, a / 255, prop)

def migrate_value(prop, value):
    if prop == "box-shadow" and value.strip() in SHADOW:
        done["shadow"] += 1; return f"var({SHADOW[value.strip()]})"
    v = re.sub(r"rgba\(\s*9\s*,\s*10\s*,\s*15\s*,\s*\.?0?\.92\s*\)", "var(--color-surface-overlay)", value)
    v = re.sub(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)",
               lambda m: alpha_var(int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4)), prop) or m.group(0), v)
    v = re.sub(r"#[0-9a-fA-F]{3,8}\b", lambda m: color_var(m.group(0), prop), v)
    if prop == "font-size":
        m = re.fullmatch(r"\s*([\d.]+)px\s*", v)
        if m and float(m.group(1)) in FONT: done["font-size"] += 1; return f"var(--p-font-size-{FONT[float(m.group(1))]})"
        if "px" in v: debt[f"font-size {v.strip()}"] += 1
    if prop == "font-family":
        done["font-family"] += 1; return "var(--p-font-family-sans)"
    if prop == "border-radius":
        def rad(m):
            n = float(m.group(1))
            if n in RADIUS: done["radius"] += 1; return f"var(--p-radius-{RADIUS[n]})"
            debt[f"radius {m.group(0)}"] += 1; return m.group(0)
        v = re.sub(r"(\d+(?:\.\d+)?)px", rad, v)
        v = v.replace("50%", "var(--p-radius-round)")
    if prop in ("padding", "margin", "gap", "row-gap", "column-gap") or prop.startswith(("padding-", "margin-")):
        def sp(m):
            n = float(m.group(1))
            if n in SPACE: done["space"] += 1; return f"var(--p-space-{SPACE[n]})"
            debt[f"space {m.group(0)}"] += 1; return m.group(0)
        v = re.sub(r"(?<![\w.-])(\d+(?:\.\d+)?)px", sp, v)
    if prop in ("transition", "transition-duration"):
        def du(m):
            s = float(m.group(1)) * (1 if m.group(2) == "ms" else 1000)
            if s <= 200: done["duration"] += 1; return "var(--p-duration-fast)"
            if s <= 300: done["duration"] += 1; return "var(--p-duration-base)"
            if s <= 450: done["duration"] += 1; return "var(--p-duration-slow)"
            debt[f"long transition {m.group(0)}"] += 1; return m.group(0)
        v = re.sub(r"(?<![\w-])(\d*\.?\d+)(ms|s)\b", du, v)
    if prop in ("animation", "animation-duration") and re.search(r"\d+(\.\d+)?s", v):
        debt[f"ambient animation: {v.strip()[:40]}"] += 1
    return v

DECL = re.compile(r"(?<=[{;])\s*(--[\w-]+|[a-z-]+)\s*:\s*([^;{}]+)")

def migrate(css):
    def repl(m):
        prop, value = m.group(1), m.group(2)
        if prop.startswith("--"): return m.group(0)  # custom properties handled separately
        return m.group(0).replace(value, migrate_value(prop, value), 1)
    out = DECL.sub(repl, css)
    # Legacy custom properties become aliases of the token system.
    aliases = {"--human": "var(--color-party-human-solid)", "--ai": "var(--color-party-ai-solid)", "--stage": "var(--color-bg-canvas)",
               "--muted": "var(--color-text-muted)", "--line": "var(--color-border-default)", "--panel": "var(--color-surface-panel)", "--text": "var(--color-text-primary)"}
    for k, v in aliases.items():
        out = re.sub(rf"{re.escape(k)}:[^;}}]+", f"{k}:{v}", out)
    return out

def main():
    path = Path(sys.argv[1])
    css = path.read_text()
    out = migrate(css)
    if "--dry-run" not in sys.argv:
        path.write_text(out)
    print(f"{path.name}: converted " + ", ".join(f"{k} {n}" for k, n in done.most_common()))
    print(f"left literal ({sum(debt.values())}):")
    for k, n in debt.most_common(): print(f"  {n:3}  {k}")

if __name__ == "__main__":
    main()
