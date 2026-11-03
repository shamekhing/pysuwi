"""Convert a Markdown file to PDF."""
from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import url2pathname

DEFAULT_CSS = """
@page { size: A4; margin: 2.2cm; }
body { font-family: serif; font-size: 11pt; line-height: 1.5; }
h1, h2, h3 { font-family: sans-serif; }
pre { background: #f4f4f4; padding: 0.6em; white-space: pre-wrap; }
code { font-family: monospace; font-size: 9.5pt; }
table { border-collapse: collapse; }
td, th { border: 1px solid #999; padding: 4px 8px; }
"""


def _safe_url_fetcher(url: str, base_dir: Path, default_url_fetcher):
    """Allow embedded data and local files beneath the input directory only."""
    parsed = urlsplit(url)
    if parsed.scheme == "data":
        return default_url_fetcher(url)
    if parsed.scheme != "file" or parsed.netloc not in ("", "localhost"):
        raise ValueError(f"Blocked resource URL: {url}")

    path = Path(url2pathname(parsed.path)).resolve()
    if not path.is_relative_to(base_dir):
        raise ValueError(f"Blocked resource outside input directory: {url}")
    return default_url_fetcher(url)


def run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="pysuwi md2pdf",
        description="Convert a Markdown file to PDF.",
    )
    parser.add_argument("-i", "--input", required=True, type=Path,
                        metavar="input.md", help="Markdown source file")
    parser.add_argument("-o", "--output", type=Path, metavar="output.pdf",
                        help="PDF destination (default: input name with .pdf)")
    parser.add_argument("--css", type=Path, metavar="file.css",
                        help="stylesheet replacing the built-in default")
    args = parser.parse_args(argv)

    src: Path = args.input
    dst: Path = args.output or src.with_suffix(".pdf")

    if not src.is_file():
        print(f"pysuwi md2pdf: input not found: {src}", file=sys.stderr)
        return 2
    if dst.resolve() == src.resolve():
        print("pysuwi md2pdf: output would overwrite the input", file=sys.stderr)
        return 2
    if not dst.parent.is_dir():
        print(f"pysuwi md2pdf: output directory missing: {dst.parent}", file=sys.stderr)
        return 2
    if args.css and not args.css.is_file():
        print(f"pysuwi md2pdf: stylesheet not found: {args.css}", file=sys.stderr)
        return 2

    hint = "sudo apt install python3-markdown python3-weasyprint"
    try:
        import markdown
    except ImportError:
        print(f"pysuwi md2pdf: missing python-markdown. Install with: {hint}",
              file=sys.stderr)
        return 3
    try:
        from weasyprint import CSS, HTML, default_url_fetcher
    except (ImportError, OSError):
        print(f"pysuwi md2pdf: WeasyPrint unavailable. Install with: {hint}",
              file=sys.stderr)
        return 3

    body = markdown.markdown(src.read_text(encoding="utf-8"),
                             extensions=["extra", "sane_lists"])
    document = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{html.escape(src.stem)}</title></head>"
        f"<body>{body}</body></html>"
    )
    css_text = args.css.read_text(encoding="utf-8") if args.css else DEFAULT_CSS
    base_dir = src.resolve().parent
    url_fetcher = lambda url: _safe_url_fetcher(  # noqa: E731
        url, base_dir, default_url_fetcher
    )

    HTML(string=document, base_url=str(base_dir), url_fetcher=url_fetcher).write_pdf(
        str(dst),
        stylesheets=[
            CSS(string=css_text, base_url=str(base_dir), url_fetcher=url_fetcher)
        ],
    )
    print(f"wrote {dst}")
    return 0
