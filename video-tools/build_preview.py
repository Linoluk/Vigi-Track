"""Builds preview.html: the published page wrapped in the same skeleton as claude.ai, with local fonts,
local Papa Parse and the recording-only Claude stand-in (mock.js)."""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent
FONTS = ROOT / "node_modules/@fontsource"

def build(with_mock=True):
    full = (ROOT.parent / "app" / "index.html").read_text()
    src = full.split("<body>", 1)[1].rsplit("</body>", 1)[0]
    css = f"""
:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
body{{margin:0;font:14px system-ui}} img{{max-width:100%}} [hidden]{{display:none!important}}
@font-face{{font-family:"Bricolage Grotesque";font-weight:500;font-style:normal;src:url(file://{FONTS}/bricolage-grotesque/files/bricolage-grotesque-latin-500-normal.woff2)}}
@font-face{{font-family:"Bricolage Grotesque";font-weight:700;font-style:normal;src:url(file://{FONTS}/bricolage-grotesque/files/bricolage-grotesque-latin-700-normal.woff2)}}
@font-face{{font-family:"Bricolage Grotesque";font-weight:800;font-style:normal;src:url(file://{FONTS}/bricolage-grotesque/files/bricolage-grotesque-latin-800-normal.woff2)}}
@font-face{{font-family:"Instrument Sans";font-weight:400;font-style:normal;src:url(file://{FONTS}/instrument-sans/files/instrument-sans-latin-400-normal.woff2)}}
@font-face{{font-family:"Instrument Sans";font-weight:500;font-style:normal;src:url(file://{FONTS}/instrument-sans/files/instrument-sans-latin-500-normal.woff2)}}
@font-face{{font-family:"Instrument Sans";font-weight:600;font-style:normal;src:url(file://{FONTS}/instrument-sans/files/instrument-sans-latin-600-normal.woff2)}}
@font-face{{font-family:"Instrument Sans";font-weight:700;font-style:normal;src:url(file://{FONTS}/instrument-sans/files/instrument-sans-latin-700-normal.woff2)}}
@font-face{{font-family:"Newsreader";font-weight:400;font-style:italic;src:url(file://{FONTS}/newsreader/files/newsreader-latin-400-italic.woff2)}}
@font-face{{font-family:"Newsreader";font-weight:500;font-style:italic;src:url(file://{FONTS}/newsreader/files/newsreader-latin-500-italic.woff2)}}
"""
    body = re.sub(r'<link[^>]+fonts.googleapis[^>]+>\n?', '', src)
    body = body.replace('https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js',
                        f'file://{ROOT}/node_modules/papaparse/papaparse.min.js')
    mock = f'<script src="file://{ROOT}/mock.js"></script>' if with_mock else ''
    html = (f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            f'<style>{css}</style>{mock}</head><body>{body}</body></html>')
    out = ROOT / "preview.html"
    out.write_text(html)
    return out

if __name__ == "__main__":
    print(build())
