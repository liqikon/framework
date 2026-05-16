#!/usr/bin/env python3
"""
sb-creator-pptx — Inject HTML→Editable PPTX export logic into a target HTML.

Usage:
    python3 inject.py <html_path>
        [--selector .screen-section]
        [--slide-width 13.33]
        [--slide-height 7.5]
        [--output-name <basename>]   # default: <html_basename>_editable
        [--no-backup]
        [--no-button]                # script only, no UI button
"""
import argparse
import os
import re
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"

MARKER_START = "<!-- BEGIN sb-creator-pptx (auto-injected) -->"
MARKER_END = "<!-- END sb-creator-pptx -->"


def render_template(template: str, selector: str, slide_w: float, slide_h: float, out_name: str) -> str:
    return (template
            .replace("__SECTION_SELECTOR__", selector)
            .replace("__SLIDE_WIDTH__", f"{slide_w}")
            .replace("__SLIDE_HEIGHT__", f"{slide_h}")
            .replace("__OUTPUT_NAME__", out_name))


def build_injection_block(selector: str, slide_w: float, slide_h: float, out_name: str, include_button: bool) -> str:
    js_template = (SCRIPTS_DIR / "pptx-export.js").read_text(encoding="utf-8")
    js = render_template(js_template, selector, slide_w, slide_h, out_name)

    button_html = (SCRIPTS_DIR / "button-snippet.html").read_text(encoding="utf-8") if include_button else ""

    return f"""{MARKER_START}
{button_html}
<script>
{js}
</script>
{MARKER_END}
"""


def strip_existing(html: str) -> str:
    """Remove any previously injected block between markers."""
    pattern = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END) + r"\n?",
        re.DOTALL,
    )
    return pattern.sub("", html)


def inject(html: str, block: str) -> str:
    """Insert the injection block immediately before </body>."""
    # Case-insensitive search for last </body>
    m = list(re.finditer(r"</body\s*>", html, re.IGNORECASE))
    if not m:
        # No </body>, append to end
        return html.rstrip() + "\n" + block + "\n"
    last = m[-1]
    return html[:last.start()] + block + "\n" + html[last.start():]


def main():
    ap = argparse.ArgumentParser(description="Inject HTML→Editable PPTX export into an HTML file.")
    ap.add_argument("html_path", help="Target HTML file path")
    ap.add_argument("--selector", default=".screen-section", help="CSS selector for slide sections (default: .screen-section)")
    ap.add_argument("--slide-width", type=float, default=13.33, help="Slide width in inches (default: 13.33)")
    ap.add_argument("--slide-height", type=float, default=7.5, help="Slide height in inches (default: 7.5)")
    ap.add_argument("--output-name", default=None, help="Output PPTX basename (no .pptx). Default: <html_basename>_editable")
    ap.add_argument("--no-backup", action="store_true", help="Skip creating .bak.html backup")
    ap.add_argument("--no-button", action="store_true", help="Inject script only, no UI button")
    args = ap.parse_args()

    target = Path(args.html_path).resolve()
    if not target.exists():
        print(f"ERROR: file not found: {target}", file=sys.stderr)
        sys.exit(1)
    if target.suffix.lower() not in (".html", ".htm"):
        print(f"WARNING: target is not .html/.htm: {target.suffix}", file=sys.stderr)

    out_name = args.output_name or (target.stem + "_editable")

    # Backup
    if not args.no_backup:
        backup = target.with_suffix(target.suffix + ".bak.html") if not target.suffix.endswith(".bak.html") else target.with_name(target.name + ".bak")
        shutil.copy2(target, backup)
        print(f"backup: {backup.name}")

    html = target.read_text(encoding="utf-8")
    original_len = len(html)
    html = strip_existing(html)
    if len(html) < original_len:
        print("existing injection: replaced")
    else:
        print("existing injection: none → new insert")

    block = build_injection_block(
        selector=args.selector,
        slide_w=args.slide_width,
        slide_h=args.slide_height,
        out_name=out_name,
        include_button=not args.no_button,
    )
    html = inject(html, block)
    target.write_text(html, encoding="utf-8")

    print(f"injected → {target.name}")
    print(f"  selector       : {args.selector}")
    print(f"  slide size     : {args.slide_width} x {args.slide_height} in")
    print(f"  output pptx    : {out_name}.pptx")
    print(f"  button         : {'on' if not args.no_button else 'off'}")
    print(f"\nNext: 브라우저에서 {target.name} 열고 우상단 'PPTX 다운로드' 버튼 클릭")


if __name__ == "__main__":
    main()
