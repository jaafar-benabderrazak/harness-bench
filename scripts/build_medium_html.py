"""
Convert writeup/article.md to a Medium-friendly HTML file.

Medium's article editor accepts pasted HTML but drops: <script>, <style>,
Mermaid diagram rendering, and <details>/<summary> collapsibles. This
script produces an HTML rendering that works when pasted into Medium by:

- Stripping the Jekyll front-matter block.
- Stripping the <script> blocks (Mermaid bootstrap).
- Replacing each ```mermaid fenced block with an italicized caption
  describing the diagram (the article's surrounding prose already
  conveys the content; the diagram was illustrative).
- Flattening <details>/<summary> into a heading + exposed content.

Usage:
    python scripts/build_medium_html.py

Writes: writeup/article-medium.html
"""

from __future__ import annotations

import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "writeup" / "article.md"
OUT = ROOT / "writeup" / "article-medium.html"


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5 :]
    return text


def strip_script_blocks(text: str) -> str:
    return re.sub(r"<script\b[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)


def replace_mermaid_blocks(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        body = match.group(1)
        subgraph_label = re.search(r'subgraph\s+\w+\s*\[\s*"([^"]+)"\s*\]', body)
        if subgraph_label:
            label = subgraph_label.group(1).strip()
        else:
            first_line = body.strip().splitlines()[0] if body.strip() else ""
            label = re.sub(r"^(flowchart|graph)\s+(LR|TD|TB|RL|BT)\s*", "", first_line).strip() or "control-flow diagram"
        return f"\n*[Diagram omitted for Medium — {label}.]*\n"

    pattern = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
    return pattern.sub(replace, text)


def flatten_details(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        summary = match.group(1).strip()
        summary = re.sub(r"</?b>", "", summary, flags=re.IGNORECASE).strip()
        body = match.group(2).strip()
        return f"\n#### {summary}\n\n{body}\n"

    pattern = re.compile(
        r"<details>\s*<summary>(.*?)</summary>(.*?)</details>",
        re.DOTALL | re.IGNORECASE,
    )
    return pattern.sub(replace, text)


def prepare_markdown(raw: str) -> str:
    text = strip_frontmatter(raw)
    text = strip_script_blocks(text)
    text = replace_mermaid_blocks(text)
    text = flatten_details(text)
    return text


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{
    font-family: Georgia, 'Times New Roman', serif;
    max-width: 720px;
    margin: 40px auto;
    padding: 0 20px;
    line-height: 1.6;
    color: #242424;
    background: #fff;
  }}
  h1, h2, h3, h4 {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #111; }}
  h1 {{ font-size: 2em; line-height: 1.2; margin-top: 0; }}
  h2 {{ font-size: 1.5em; margin-top: 2em; }}
  h3 {{ font-size: 1.2em; margin-top: 1.6em; }}
  h4 {{ font-size: 1.05em; margin-top: 1.4em; }}
  img {{ max-width: 100%; height: auto; display: block; margin: 1.5em auto; }}
  code {{ background: #f3f3f3; padding: 2px 5px; border-radius: 3px; font-size: 0.95em; }}
  pre {{ background: #f7f7f7; padding: 14px; overflow-x: auto; border-radius: 4px; }}
  pre code {{ background: none; padding: 0; }}
  table {{ border-collapse: collapse; margin: 1.5em 0; width: 100%; font-size: 0.95em; }}
  th, td {{ border: 1px solid #d0d0d0; padding: 8px 12px; text-align: left; }}
  th {{ background: #f7f7f7; }}
  blockquote {{ border-left: 3px solid #aaa; margin: 1.5em 0; padding-left: 1em; color: #555; }}
  em {{ color: #6a6a6a; }}
  hr {{ border: none; border-top: 1px solid #d0d0d0; margin: 2em 0; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def main() -> None:
    raw = SRC.read_text(encoding="utf-8")
    cleaned = prepare_markdown(raw)

    md = markdown.Markdown(
        extensions=[
            "extra",
            "sane_lists",
            "smarty",
            "tables",
            "toc",
        ]
    )
    body = md.convert(cleaned)

    # Extract title from first H1 for the <title> tag.
    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", body, flags=re.DOTALL)
    title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else "Article"

    html = HTML_TEMPLATE.format(title=title, body=body)
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
