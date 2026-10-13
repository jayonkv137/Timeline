"""Schematic use-case illustrations for the Symbiot documentation (one SVG per step).

Simple, flat, consistent: light app window (max white 240 per the DM website rules), dark map panel,
blue = you, orange = AI. Run: python3 make_schematics.py  → writes step-1.svg … step-6.svg next to this file.
"""
from pathlib import Path

W, H = 1600, 1000
BG, WIN, LINE, TXT, MUTED = "#e6e6e6", "#efefef", "#c9c9c9", "#2b2f36", "#8a9099"
MAP, MAPLINE, NODE = "#20252c", "#4a5563", "#d9dee5"
YOU, AI = "#1fa2e0", "#f07a24"
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"
OUT = Path(__file__).resolve().parent


def text(x, y, s, size=26, color=TXT, weight=400, anchor="start"):
    return f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{s}</text>'


def bar(x, y, w, h=14, color="#cfd3d8", r=7):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{color}"/>'


def header(n, title):
    return (f'<circle cx="108" cy="78" r="30" fill="{TXT}"/>' + text(108, 89, str(n), 30, "#efefef", 700, "middle")
            + text(158, 90, title, 38, TXT, 600))


def window(sidebar=False):
    s = f'<rect x="80" y="140" width="1440" height="800" rx="18" fill="{WIN}" stroke="{LINE}" stroke-width="2"/>'
    s += f'<rect x="1010" y="140" width="510" height="800" rx="18" fill="{MAP}"/><rect x="1010" y="140" width="40" height="800" fill="{MAP}"/>'
    if sidebar:
        s += f'<line x1="300" y1="140" x2="300" y2="940" stroke="{LINE}" stroke-width="2"/>'
    return s


def user_msg(x, y, w=420, lines=2):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{30 + 26 * lines}" rx="16" fill="#dcdfe3"/>'
    for i in range(lines):
        s += bar(x + 22, y + 22 + 26 * i, w - 60 - (i * 60), 12, "#aab1ba")
    return s


def ai_msg(x, y, w=600, lines=3):
    s = ""
    for i in range(lines):
        s += bar(x, y + 26 * i, w - (i % 2) * 90, 12, "#c3c8ce")
    return s


def goal(cx, cy, label=None):
    s = f'<circle cx="{cx}" cy="{cy}" r="34" fill="none" stroke="{NODE}" stroke-width="2" opacity=".5"/><circle cx="{cx}" cy="{cy}" r="22" fill="{NODE}"/>'
    if label:
        s += text(cx, cy + 66, label, 20, "#e8ecf1", 600, "middle")
    return s


def outcome(cx, cy, r=26, you=.5, beads=(), dashed=False, label=None):
    """A grey outcome with its share ring (blue arc = your share from 12 o'clock clockwise) and requirement beads."""
    import math
    extra = ' stroke-dasharray="6 6" fill-opacity=".25" stroke="#9aa3ae" stroke-width="2"' if dashed else ""
    s = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#9aa3ae"{extra}/>'
    if not dashed:
        rr = r + 9
        a0, a1 = -math.pi / 2, -math.pi / 2 + 2 * math.pi * you
        def arc(t0, t1, col):
            large = 1 if (t1 - t0) > math.pi else 0
            x0, y0, x1, y1 = cx + rr * math.cos(t0), cy + rr * math.sin(t0), cx + rr * math.cos(t1), cy + rr * math.sin(t1)
            return f'<path d="M{x0:.1f} {y0:.1f} A{rr} {rr} 0 {large} 1 {x1:.1f} {y1:.1f}" fill="none" stroke="{col}" stroke-width="6" stroke-linecap="round"/>'
        if you > 0:
            s += arc(a0 + .08, a1 - .08, YOU)
        if you < 1:
            s += arc(a1 + .08, a0 + 2 * math.pi - .08, AI)
        n = len(beads)
        for i, b in enumerate(beads):
            t = -math.pi / 2 + (i - (n - 1) / 2) * .38
            bx, by = cx + (r + 26) * math.cos(t), cy + (r + 26) * math.sin(t)
            col = YOU if b == "you" else AI
            s += (f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="8" fill="none" stroke="{col}" stroke-width="3"/>' if b.endswith("?")
                  else f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="8" fill="{col}"/>')
    if label:
        s += text(cx, cy + r + 44, label, 18, "#c9d0d8", 400, "middle")
    return s


def tether(x1, y1, x2, y2, dashed=False):
    extra = ' stroke-dasharray="8 8"' if dashed else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{MAPLINE}" stroke-width="3"{extra}/>'


def legend(x, y):
    return (f'<circle cx="{x}" cy="{y}" r="8" fill="{YOU}"/>' + text(x + 18, y + 7, "You", 20, "#c9d0d8")
            + f'<circle cx="{x + 90}" cy="{y}" r="8" fill="{AI}"/>' + text(x + 108, y + 7, "AI", 20, "#c9d0d8"))


def svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{BG}"/>{body}</svg>'


def map_full(cx=1265, cy=500, you_main=.38):
    s = tether(cx, cy, cx - 120, cy - 150) + tether(cx, cy, cx + 130, cy - 120) + tether(cx, cy, cx - 110, cy + 160) + tether(cx, cy, cx + 120, cy + 170)
    s += goal(cx, cy)
    s += outcome(cx - 120, cy - 150, 28, .72, ("you", "you", "ai"), label="Layout")
    s += outcome(cx + 130, cy - 120, 30, .22, ("you", "ai", "ai", "ai", "ai?"), label="Case studies")
    s += outcome(cx - 110, cy + 160, 24, .55, ("you", "ai"), label="Tone")
    s += outcome(cx + 120, cy + 170, 26, you_main, ("ai", "you", "ai"), label="Launch plan")
    return s


steps = {}

# 1 · Chat with the AI as usual
b = header(1, "Chat with the AI as usual") + window()
b += user_msg(560, 200, 400, 2) + ai_msg(340, 320, 620, 4) + user_msg(600, 470, 360, 1) + ai_msg(340, 560, 580, 3)
b += f'<rect x="340" y="830" width="620" height="70" rx="14" fill="#f6f6f6" stroke="{LINE}" stroke-width="2"/>' + bar(366, 858, 260, 12, "#cfd3d8")
b += '<circle cx="1265" cy="470" r="34" fill="none" stroke="#56606c" stroke-width="2" stroke-dasharray="6 6"/>' + text(1265, 530, "not mapped yet", 20, "#8f99a6", 400, "middle")
steps[1] = svg(b)

# 2 · Map this chat
b = header(2, "Map this chat: it builds in the background") + window(sidebar=True)
b += f'<rect x="100" y="180" width="180" height="70" rx="10" fill="#e1e4e8"/>' + text(116, 210, "Portfolio", 20, TXT, 600) + text(116, 236, "Mapping · 2 of 6", 17, MUTED)
b += f'<rect x="116" y="244" width="148" height="4" rx="2" fill="#cfd3d8"/><rect x="116" y="244" width="49" height="4" rx="2" fill="{TXT}"/>'
for i, t in enumerate(["Thesis notes", "Trip plan"]):
    b += text(116, 300 + 60 * i, t, 20, MUTED) + text(116, 324 + 60 * i, "Mapped", 16, "#a3a9b1")
b += f'<rect x="760" y="170" width="220" height="50" rx="25" fill="{TXT}"/>' + text(870, 202, "Map this chat", 20, "#efefef", 600, "middle")
b += user_msg(560, 250, 380, 2) + ai_msg(340, 370, 600, 3) + text(340, 500, "PAIR 03 · not mapped yet", 17, "#a3a9b1") + ai_msg(340, 520, 560, 2)
b += f'<rect x="100" y="880" width="180" height="40" rx="20" fill="{TXT}"/>' + text(190, 905, "Mapping 1 chat", 16, "#efefef", 600, "middle")
b += tether(1265, 520, 1150, 380) + tether(1265, 520, 1390, 400, True)
b += goal(1265, 520) + outcome(1150, 380, 26, .7, ("you", "ai"), label="Layout") + outcome(1390, 400, 26, dashed=True, label="forming…")
steps[2] = svg(b)

# 3 · See who shaped what
b = header(3, "See who shaped each goal") + window()
b += user_msg(560, 200, 400, 2) + ai_msg(340, 320, 620, 4) + user_msg(600, 470, 360, 1) + ai_msg(340, 560, 580, 4)
b += map_full() + legend(1080, 205)
b += f'<rect x="1300" y="232" width="200" height="56" rx="12" fill="#2f3640" stroke="{AI}" stroke-width="2"/>' + text(1400, 268, "78% shaped by AI", 18, "#f2f4f7", 600, "middle")
b += text(1265, 905, "dots = requirements · ring = who shaped it", 17, "#8f99a6", 400, "middle")
steps[3] = svg(b)

# 4 · Trace a requirement back to the exact words
b = header(4, "Click a requirement: see the exact words") + window()
b += user_msg(560, 190, 400, 2) + ai_msg(340, 300, 620, 2)
b += f'<rect x="326" y="372" width="660" height="168" rx="14" fill="none" stroke="{TXT}" stroke-width="2"/>'
b += text(346, 404, "Assistant · exchange 4", 18, MUTED, 600) + bar(346, 422, 520, 12, "#c3c8ce")
b += f'<rect x="342" y="446" width="560" height="34" rx="6" fill="{AI}" fill-opacity=".32"/>' + text(352, 470, "“Add three detailed case studies with process photos”", 21, TXT)
b += bar(346, 500, 480, 12, "#c3c8ce") + ai_msg(340, 580, 600, 3)
b += f'<rect x="340" y="800" width="620" height="54" rx="12" fill="#f6f6f6" stroke="{LINE}" stroke-width="2"/>'
b += f'<rect x="356" y="814" width="118" height="28" rx="6" fill="{AI}" fill-opacity=".3"/>' + text(415, 834, "Introduced", 17, "#7a3a0c", 600, "middle")
b += text(486, 834, "by the AI · exchange 4", 17, MUTED) + text(940, 834, "Back to reading", 17, TXT, 600, "end")
b += map_full()
b += f'<circle cx="1395" cy="342" r="18" fill="none" stroke="#ffffff" stroke-width="3"/>'
b += f'<path d="M1412 352 l28 28 l-10 2 l8 16 l-6 3 l-8 -16 l-8 7 z" fill="#ffffff" stroke="{MAP}" stroke-width="2"/>'
b += f'<path d="M1376 336 C 1150 250, 1040 360, 905 455" fill="none" stroke="{AI}" stroke-width="3" stroke-dasharray="10 8"/>'
steps[4] = svg(b)

# 5 · Come back later: replay how the goals formed
b = header(5, "Come back later: replay how it formed") + window()
b += text(340, 210, "PAIR 02", 17, "#a3a9b1", 600) + user_msg(560, 230, 400, 2) + ai_msg(340, 340, 620, 3)
b += f'<rect x="326" y="186" width="660" height="260" rx="14" fill="none" stroke="{LINE}" stroke-width="2"/>'
b += ai_msg(340, 500, 560, 3) + user_msg(600, 620, 360, 1)
b += tether(1265, 470, 1145, 330) + tether(1265, 470, 1155, 630) + goal(1265, 470)
b += outcome(1145, 330, 28, .8, ("you", "you"), label="Layout") + outcome(1155, 630, 24, .6, ("you",), label="Tone")
b += f'<circle cx="1395" cy="350" r="26" fill="none" stroke="#5b6573" stroke-width="2" stroke-dasharray="6 6"/>'
y = 860
b += f'<line x1="1080" y1="{y}" x2="1450" y2="{y}" stroke="#4a5563" stroke-width="4" stroke-linecap="round"/>'
b += f'<line x1="1080" y1="{y}" x2="1200" y2="{y}" stroke="{NODE}" stroke-width="4" stroke-linecap="round"/>'
for i in range(6):
    x = 1080 + i * 74
    b += f'<circle cx="{x}" cy="{y}" r="9" fill="{NODE if i <= 1 else MAP}" stroke="{NODE}" stroke-width="2"/>'
b += f'<circle cx="1154" cy="{y}" r="15" fill="none" stroke="#ffffff" stroke-width="3"/>' + text(1154, y - 28, "2 / 6", 18, "#e8ecf1", 600, "middle")
steps[5] = svg(b)

# 6 · See all your chats as one brain
b = header(6, "See all your chats as one brain") + f'<rect x="80" y="140" width="1440" height="800" rx="18" fill="{MAP}"/>'
b += ('<path d="M560 600 C 470 560, 470 420, 560 380 C 560 280, 680 230, 770 260 C 820 200, 960 200, 1010 260 C 1110 240, 1200 320, 1180 420 '
      'C 1250 470, 1230 600, 1140 620 C 1120 700, 1000 720, 940 680 C 880 730, 760 720, 720 670 C 640 700, 560 670, 560 600 Z" '
      f'fill="#2a313a" stroke="#5b6573" stroke-width="3"/>')
b += '<path d="M700 330 C 760 380, 720 450, 800 480 M900 280 C 880 360, 960 400, 920 470 M1060 360 C 1000 420, 1080 470, 1020 540 M760 600 C 820 560, 880 620, 950 580" fill="none" stroke="#3b4450" stroke-width="3"/>'
import math
for cx, cy, you, r, name in [(690, 420, .25, 34, "Research"), (850, 330, .7, 26, "Portfolio"), (1060, 430, .3, 30, "Coding"), (820, 590, .55, 22, "Writing"), (980, 600, .2, 20, "")]:
    col = YOU if you >= .5 else AI
    b += f'<circle cx="{cx}" cy="{cy}" r="{r * 2.4}" fill="{col}" fill-opacity=".14"/>'
    b += f'<circle cx="{cx}" cy="{cy}" r="{r * .55}" fill="{NODE}"/>'
    for k in range(5):
        t = k * 2 * math.pi / 5 + .4
        b += f'<line x1="{cx}" y1="{cy}" x2="{cx + r * 1.6 * math.cos(t):.1f}" y2="{cy + r * 1.6 * math.sin(t):.1f}" stroke="{YOU if k / 5 < you else AI}" stroke-width="3"/>'
    if name:
        b += text(cx, cy + r * 1.6 + 30, name, 20, "#e8ecf1", 600, "middle")
b += legend(130, 205) + text(1480, 900, "where you lead (blue) and where the AI leads (orange)", 20, "#8f99a6", 400, "end")
steps[6] = svg(b)

for n, s in steps.items():
    (OUT / f"step-{n}.svg").write_text(s, encoding="utf-8")
print("wrote", ", ".join(f"step-{n}.svg" for n in steps))
