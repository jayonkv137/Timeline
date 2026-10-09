#!/usr/bin/env python3
"""
scripts/design_system/check_contrast.py

Computes relative luminance and WCAG 2.2 contrast ratios for design system palettes.
Validates 4.5:1 floor for body text and 3:1 for large text/interactive marks.
"""

import math
import sys


def parse_hex(hex_str: str):
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join([c * 2 for c in hex_str])
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))


def relative_luminance(rgb):
    def channel_lum(val):
        c = val / 255.0
        return c / 12.92 if c <= 0.03928 else math.pow((c + 0.055) / 1.055, 2.4)
    r, g, b = rgb
    return 0.2126 * channel_lum(r) + 0.7152 * channel_lum(g) + 0.0722 * channel_lum(b)


def contrast_ratio(hex1: str, hex2: str) -> float:
    l1 = relative_luminance(parse_hex(hex1))
    l2 = relative_luminance(parse_hex(hex2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def check_palette(pairs):
    print("=== Design System Contrast Audit (WCAG 2.2) ===\n")
    all_pass = True
    for fg, bg, role, min_ratio in pairs:
        ratio = contrast_ratio(fg, bg)
        passes = ratio >= min_ratio
        status = "PASS" if passes else "FAIL"
        if not passes:
            all_pass = False
        print(f"[{status}] {role:28} | FG: {fg:7} BG: {bg:7} | Ratio: {ratio:5.2f}:1 (Req: {min_ratio}:1)")

    print("\nResult:", "ALL PASS" if all_pass else "FAILURES DETECTED")
    return all_pass


def main():
    # Audit baseline pairs from mockups/_theme.css
    test_pairs = [
        # (FG, BG, Role, Required Ratio)
        ("#141416", "#faf9f6", "Light Body Text", 4.5),
        ("#57575e", "#faf9f6", "Light Secondary Text", 4.5),
        ("#0057FF", "#faf9f6", "Light You Accent (Blue)", 4.5),
        ("#E85A0A", "#faf9f6", "Light AI Accent (Orange)", 3.0),
        ("#f5f6f8", "#121316", "Dark Body Text", 4.5),
        ("#a0a3af", "#121316", "Dark Secondary Text", 4.5),
        ("#38bdf8", "#141417", "Obsidian Cyan Accent", 4.5),
        ("#fb923c", "#141417", "Obsidian Amber Accent", 4.5),
        ("#ffffff", "#000000", "High-Contrast Body", 7.0),
    ]

    ok = check_palette(test_pairs)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
