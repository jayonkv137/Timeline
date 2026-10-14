#!/usr/bin/env python3
"""Convert docs/symbiot/symbiot-documentation.md into a self-contained preview.html."""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / "docs" / "symbiot" / "symbiot-documentation.md"
HTML_OUT = ROOT / "docs" / "symbiot" / "preview.html"


def render_markdown_to_html(md_text: str) -> str:
    lines = md_text.splitlines()
    html_parts: list[str] = []
    in_table = False
    in_ul = False
    in_blockquote = False

    def close_blocks():
        nonlocal in_table, in_ul, in_blockquote
        res = ""
        if in_table:
            res += "</table>\n"
            in_table = False
        if in_ul:
            res += "</ul>\n"
            in_ul = False
        if in_blockquote:
            res += "</blockquote>\n"
            in_blockquote = False
        return res

    for line in lines:
        stripped = line.strip()

        # Empty line
        if not stripped:
            html_parts.append(close_blocks())
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            html_parts.append(close_blocks())
            html_parts.append("<hr />")
            continue

        # Images: ![caption](url)
        img_match = re.match(r"^!\[(.*?)\]\((.*?)\)$", stripped)
        if img_match:
            html_parts.append(close_blocks())
            caption, url = img_match.groups()
            html_parts.append(
                f'<figure class="doc-figure">'
                f'<img src="{html.escape(url)}" alt="{html.escape(caption)}" />'
                f'<figcaption>{html.escape(caption)}</figcaption>'
                f'</figure>'
            )
            continue

        # Headings
        if stripped.startswith("### "):
            html_parts.append(close_blocks())
            html_parts.append(f"<h3>{parse_inline(stripped[4:])}</h3>")
            continue
        if stripped.startswith("## "):
            html_parts.append(close_blocks())
            html_parts.append(f"<h2>{parse_inline(stripped[3:])}</h2>")
            continue
        if stripped.startswith("# "):
            html_parts.append(close_blocks())
            html_parts.append(f"<h1>{parse_inline(stripped[2:])}</h1>")
            continue

        # Blockquote
        if stripped.startswith("> "):
            if not in_blockquote:
                html_parts.append(close_blocks())
                html_parts.append("<blockquote>")
                in_blockquote = True
            html_parts.append(f"<p>{parse_inline(stripped[2:])}</p>")
            continue

        # Unordered list: - or *
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_ul:
                html_parts.append(close_blocks())
                html_parts.append("<ul>")
                in_ul = True
            html_parts.append(f"<li>{parse_inline(stripped[2:])}</li>")
            continue

        # Numbered list: 1. 2.
        num_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if num_match:
            html_parts.append(close_blocks())
            html_parts.append(f'<p class="numbered-step">{parse_inline(num_match.group(1))}</p>')
            continue

        # Table rows: | Col1 | Col2 |
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            # Header separator row: |---|---|
            if all(re.match(r"^:?-+:?$", c) for c in cells):
                continue
            if not in_table:
                html_parts.append(close_blocks())
                html_parts.append("<table>\n")
                in_table = True
                html_parts.append("<tr>" + "".join(f"<th>{parse_inline(c)}</th>" for c in cells) + "</tr>")
            else:
                html_parts.append("<tr>" + "".join(f"<td>{parse_inline(c)}</td>" for c in cells) + "</tr>")
            continue

        # Regular paragraph
        html_parts.append(close_blocks())
        html_parts.append(f"<p>{parse_inline(stripped)}</p>")

    html_parts.append(close_blocks())
    return "\n".join(p for p in html_parts if p)


def parse_inline(text: str) -> str:
    # Bold italic
    text = re.sub(r"\*\*\*(.*?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    # Bold
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    # Italic
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)
    # Inline code
    text = re.sub(r"`(.*?)`", r"<code>\1</code>", text)
    # Links: [text](url)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2" target="_blank">\1</a>', text)
    return text


def main():
    md = MD_PATH.read_text(encoding="utf-8")
    body = render_markdown_to_html(md)

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Symbiot — Project Documentation</title>
  <style>
    :root {{
      --bg: #090a0f;
      --card-bg: #12141c;
      --border: #232736;
      --text: #e2e8f0;
      --text-muted: #94a3b8;
      --accent-human: #38bdf8;
      --accent-ai: #fb923c;
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-sans);
      line-height: 1.65;
      padding: 40px 20px 80px;
    }}
    .container {{
      max-width: 860px;
      margin: 0 auto;
    }}
    header.brand-nav {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--border);
      padding-bottom: 16px;
      margin-bottom: 32px;
    }}
    .badge-course {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      background: #1e293b;
      color: #cbd5e1;
      padding: 4px 10px;
      border-radius: 9999px;
      border: 1px solid var(--border);
    }}
    h1, h2, h3 {{
      color: #f8fafc;
      font-weight: 600;
      line-height: 1.3;
      margin-top: 36px;
      margin-bottom: 16px;
    }}
    h1 {{ font-size: 32px; }}
    h2 {{
      font-size: 22px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 8px;
    }}
    h3 {{ font-size: 18px; }}
    p {{
      margin-bottom: 16px;
      color: #cbd5e1;
    }}
    ul {{
      margin-left: 24px;
      margin-bottom: 20px;
    }}
    li {{
      margin-bottom: 6px;
      color: #cbd5e1;
    }}
    hr {{
      border: 0;
      height: 1px;
      background: var(--border);
      margin: 40px 0;
    }}
    blockquote {{
      border-left: 3px solid var(--accent-human);
      background: rgba(56, 189, 248, 0.05);
      padding: 12px 18px;
      border-radius: 0 8px 8px 0;
      margin: 20px 0;
      font-style: italic;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0;
      font-size: 14px;
      background: var(--card-bg);
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid var(--border);
    }}
    th, td {{
      padding: 12px 14px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }}
    th {{
      background: #181c26;
      color: #94a3b8;
      font-weight: 600;
    }}
    figure.doc-figure {{
      margin: 28px 0;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 10px 25px rgba(0,0,0,0.4);
    }}
    figure.doc-figure img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    figcaption {{
      padding: 10px 16px;
      font-size: 13px;
      color: var(--text-muted);
      background: #12141c;
      border-top: 1px solid var(--border);
      font-style: italic;
    }}
    code {{
      background: #1e293b;
      color: #38bdf8;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 13px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}
    a {{
      color: var(--accent-human);
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    .numbered-step {{
      font-weight: 500;
      color: #f1f5f9;
      margin-top: 20px;
      margin-bottom: 8px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header class="brand-nav">
      <span class="badge-course">Designing for Competence · 2026</span>
      <span style="font-size: 13px; color: var(--text-muted);">Digital Media Bremen Project Documentation</span>
    </header>
    <main>
      {body}
    </main>
  </div>
</body>
</html>"""

    HTML_OUT.write_text(page_html, encoding="utf-8")
    print(f"Generated preview at: {HTML_OUT}")


if __name__ == "__main__":
    main()
