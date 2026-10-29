"""Builds docs/USER_GUIDE.pdf from docs/guide/USER_GUIDE.html (screenshots in docs/img).
Usage: pip install playwright && python3 -m playwright install chromium && python3 docs/guide/build_guide.py
Fonts: run `npm install` in video-tools/ first for the exact fonts, otherwise system fonts are used."""
import pathlib
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).resolve().parent
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto((HERE / "USER_GUIDE.html").as_uri()); pg.wait_for_timeout(900)
    pg.pdf(path=str(HERE.parent / "USER_GUIDE.pdf"), format="A4", print_background=True, display_header_footer=True, header_template="<span></span>",
           footer_template='<div style="font:8px Arial;color:#778;width:100%;text-align:center">Vigi-Track user guide · <span class="pageNumber"></span>/<span class="totalPages"></span></div>',
           margin={"top": "16mm", "bottom": "18mm", "left": "16mm", "right": "16mm"})
    b.close()
print(HERE.parent / "USER_GUIDE.pdf")
