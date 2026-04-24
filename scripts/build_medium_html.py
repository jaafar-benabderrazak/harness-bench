"""
Convert writeup/article.md to a Medium-friendly HTML file.

Medium's article editor accepts pasted HTML but drops: <script>, <style>,
Mermaid diagram rendering, and <details>/<summary> collapsibles. This
script produces an HTML rendering that works when pasted into Medium by:

- Stripping the Jekyll front-matter block.
- Stripping the <script> blocks (Mermaid bootstrap).
- Rendering each ```mermaid fenced block to a PNG via mermaid-cli (`mmdc`)
  under writeup/diagrams/ and replacing the fence with an <img> reference.
- Flattening <details>/<summary> into a heading + exposed content.

Requires:
    pip install markdown pymdown-extensions
    npm install -g @mermaid-js/mermaid-cli   (provides `mmdc`)

Usage:
    python scripts/build_medium_html.py

Writes: writeup/article-medium.html + writeup/diagrams/diagram-NN.png
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "writeup" / "article.md"
OUT = ROOT / "writeup" / "article-medium.html"
DIAGRAMS_DIR = ROOT / "writeup" / "diagrams"


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5 :]
    return text


def strip_script_blocks(text: str) -> str:
    return re.sub(r"<script\b[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)


def _mmdc_available() -> bool:
    return shutil.which("mmdc") is not None


def _label_for(body: str) -> str:
    subgraph_label = re.search(r'subgraph\s+\w+\s*\[\s*"([^"]+)"\s*\]', body)
    if subgraph_label:
        return subgraph_label.group(1).strip()
    first_line = body.strip().splitlines()[0] if body.strip() else ""
    stripped = re.sub(r"^(flowchart|graph)\s+(LR|TD|TB|RL|BT)\s*", "", first_line).strip()
    return stripped or "control-flow diagram"


def _render_mermaid(body: str, out_path: Path) -> bool:
    """Render a Mermaid source string to PNG via mmdc. Returns True on success."""
    mmdc = shutil.which("mmdc") or "mmdc"  # full path avoids Windows .cmd shim issues
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".mmd", encoding="utf-8", delete=False
    ) as handle:
        handle.write(body)
        src_path = Path(handle.name)
    try:
        result = subprocess.run(
            [
                mmdc,
                "--input", str(src_path),
                "--output", str(out_path),
                "--backgroundColor", "white",
                "--scale", "2",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            shell=False,
        )
        if result.returncode != 0:
            print(f"  [mmdc] failed for {out_path.name}: {result.stderr.strip()[:200]}")
            return False
        return out_path.exists()
    except FileNotFoundError:
        # Windows .cmd shims sometimes evade CreateProcess — retry via shell.
        result = subprocess.run(
            f'mmdc --input "{src_path}" --output "{out_path}" --backgroundColor white --scale 2',
            capture_output=True,
            text=True,
            timeout=60,
            shell=True,
        )
        if result.returncode != 0:
            print(f"  [mmdc shell] failed for {out_path.name}: {result.stderr.strip()[:200]}")
            return False
        return out_path.exists()
    finally:
        src_path.unlink(missing_ok=True)


def _preceding_heading(text: str, start: int) -> str | None:
    """Find the nearest Markdown heading that appears before `start` in `text`."""
    prefix = text[:start]
    matches = list(re.finditer(r"^#{1,6}\s+(.+?)\s*$", prefix, flags=re.MULTILINE))
    if not matches:
        return None
    return matches[-1].group(1).strip()


def replace_mermaid_blocks(text: str) -> str:
    DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    has_mmdc = _mmdc_available()
    if not has_mmdc:
        print("  [warn] `mmdc` not found on PATH — falling back to caption stubs")

    counter = {"n": 0}

    def replace(match: re.Match[str]) -> str:
        body = match.group(1)
        label = _label_for(body)
        if label == "control-flow diagram":
            heading = _preceding_heading(text, match.start())
            if heading:
                label = heading

        counter["n"] += 1
        # Stable filename: index + short content hash keeps the file reproducible across runs.
        digest = hashlib.sha1(body.encode("utf-8")).hexdigest()[:8]
        filename = f"diagram-{counter['n']:02d}-{digest}.png"
        out_path = DIAGRAMS_DIR / filename

        if has_mmdc and (not out_path.exists() or out_path.stat().st_size == 0):
            if not _render_mermaid(body.strip() + "\n", out_path):
                return f"\n*[Diagram omitted for Medium — {label}.]*\n"

        if has_mmdc and out_path.exists():
            rel = f"diagrams/{filename}"
            return f"\n![{label}]({rel})\n"
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
