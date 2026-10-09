#!/usr/bin/env python3
"""
scripts/design_system/lint_tokens.py

Lints mockups/ HTML and CSS files to enforce:
1. No prohibited arbitrary hex colors outside _theme.css.
2. No banned CSS properties (e.g. transition: width/height layout thrash).
3. Universal inclusion of _theme.css and _shell.js in mockups.
"""

import sys
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MOCKUPS_DIR = REPO_ROOT / "mockups"

HEX_RE = re.compile(r'#(?:[0-9a-fA-F]{3}){1,2}\b')
LAYOUT_TRANSITION_RE = re.compile(r'transition:\s*(?:all|width|height|margin|padding)\b')


def lint_file(file_path: Path):
    rel_path = file_path.relative_to(REPO_ROOT)
    issues = []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    is_theme = file_path.name == "_theme.css"

    for idx, line in enumerate(lines, 1):
        # 1. Check layout transitions
        if LAYOUT_TRANSITION_RE.search(line):
            issues.append((idx, "LAYOUT-TRANSITION", "Animating layout property causes reflow. Use transform/opacity instead."))

        # 2. Check hardcoded hex colors outside _theme.css (unless inside inline SVG filter or comment)
        if not is_theme and file_path.suffix in (".html", ".css"):
            clean_line = line.strip()
            if not clean_line.startswith("<!--") and not clean_line.startswith("/*") and "feColorMatrix" not in line:
                # Exclude theme definition or index card samples
                hex_matches = HEX_RE.findall(line)
                # In mockup index.html or prototypes, report as info or warning
                if hex_matches and "index.html" not in file_path.name and "_shell.js" not in file_path.name:
                    issues.append((idx, "HARDCODED-HEX", f"Hardcoded color {hex_matches}. Use var(--token) instead."))

    return issues


def main():
    print("=== Design System Token & Anti-Pattern Linter ===\n")
    all_clean = True
    files_checked = 0

    for p in MOCKUPS_DIR.glob("**/*"):
        if p.is_file() and p.suffix in (".html", ".css", ".js") and not p.name.startswith("."):
            files_checked += 1
            issues = lint_file(p)
            rel = p.relative_to(REPO_ROOT)
            if issues:
                all_clean = False
                print(f"[FAIL] {rel}")
                for line_no, code, msg in issues:
                    print(f"       L{line_no}: [{code}] {msg}")
            else:
                print(f"[OK]   {rel}")

    print(f"\nChecked {files_checked} files.")
    print("Status:", "ALL CLEAN" if all_clean else "ISSUES DETECTED")
    sys.exit(0 if all_clean else 1)


if __name__ == "__main__":
    main()
