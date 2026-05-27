"""Re-render every HTML tile in this folder to its matching PNG, picking up the
fresh app screenshots installed 2026-05-27. Detects story tiles by class.

Usage:
  python _batch_rerender.py            # render every tile
  python _batch_rerender.py 05 23      # render only tiles whose stem starts with these prefixes
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_RENDER = Path.home() / ".claude" / "skills" / "tradelinkers-social" / "scripts" / "render_post.py"


def is_story(html: str) -> bool:
    # Story templates render as 1080x1920. Detect by aspect ratio of the canvas
    # or the presence of "1920" in inline CSS.
    return "story-canvas" in html or "1080x1920" in html or "height: 1920" in html


def main() -> int:
    if not SKILL_RENDER.exists():
        print(f"render_post.py not found at {SKILL_RENDER}")
        return 2

    prefixes = sys.argv[1:]
    tiles = sorted(HERE.glob("*.html"))
    if prefixes:
        tiles = [t for t in tiles if any(t.stem.startswith(p) for p in prefixes)]

    if not tiles:
        print("No tiles matched.")
        return 0

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for html in tiles:
                text = html.read_text(encoding="utf-8")
                story = is_story(text)
                width = 1080
                height = 1920 if story else 1080
                out = html.with_suffix(".png")

                ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1)
                page = ctx.new_page()
                page.goto(html.resolve().as_uri(), wait_until="networkidle")
                page.evaluate("() => document.fonts && document.fonts.ready ? document.fonts.ready : null")
                page.wait_for_timeout(250)
                canvas = page.locator(".post-canvas").first
                canvas.screenshot(path=str(out), omit_background=False)
                ctx.close()
                print(f"  {out.name}  ({width}x{height})")
        finally:
            browser.close()

    print(f"Done — re-rendered {len(tiles)} tiles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
