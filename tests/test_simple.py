"""End-to-end tests of simple/index.html in headless Chromium (Playwright).
Supabase and api.anthropic.com are faked, so the tests run offline, with no key and no real database.
Usage: pip install playwright && python3 -m playwright install chromium && python3 tests/test_simple.py"""
import json, sys, pathlib
from playwright.sync_api import sync_playwright

REPO = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).parent.parent).resolve()
APP = (REPO / "simple/index.html").as_uri()

results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail)); print(("PASS " if ok else "FAIL ") + name + (f"  -> {detail}" if detail else ""))

DB = [{"drug": "Sertraline", "symptoms": ["abnormal dreams"], "note": "Vivid dreams the first month.", "created_at": "2026-10-20T10:00:00Z"}]
POSTS, AI_CALLS = [], []

def fake_supabase(route):
    req = route.request
    if req.method == "POST":
        row = json.loads(req.post_data); POSTS.append(row)
        DB.append({**row, "created_at": "2026-10-30T09:00:00Z"})
        return route.fulfill(status=201, body="")
    drug = dict(p.split("=", 1) for p in req.url.split("?", 1)[1].split("&")).get("drug")
    rows = [r for r in reversed(DB) if "eq." + r["drug"] == (drug or "").replace("%20", " ")] if drug else [{"drug": r["drug"]} for r in DB]
    route.fulfill(status=200, content_type="application/json", body=json.dumps(rows))

def fake_anthropic(route):
    body = json.loads(route.request.post_data); AI_CALLS.append(body)
    route.fulfill(status=200, content_type="application/json", headers={"access-control-allow-origin": "*"},
                  body=json.dumps({"content": [{"type": "text", "text": '[{"id":"live","effects":["throwing up","chest pain"]}]'}]}))

def open_page(browser, demo=False, **kw):
    page = browser.new_page(**kw); errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("dialog", lambda d: (errors.append("dialog opened: " + d.message), d.dismiss()))
    page.route("https://fonts.googleapis.com/**", lambda r: r.abort())
    page.route("https://*.supabase.co/**", fake_supabase)
    page.route("https://api.anthropic.com/**", fake_anthropic)
    if demo:  # config.js cannot overwrite this, so the app starts in demo mode
        page.add_init_script("Object.defineProperty(window,'VT_CONFIG',{value:{},writable:false})")
    return page, errors

with sync_playwright() as p:
    b = p.chromium.launch()

    # ---- Shared database (Supabase faked) ----
    pg, err = open_page(b, viewport={"width": 1280, "height": 900})
    pg.goto(APP); pg.wait_for_timeout(500)
    check("database mode: pill says Shared database", pg.inner_text("#mode").strip() == "Shared database")
    check("12 drug tiles, then Show all 37", pg.locator(".tile").count() == 12 and "37" in pg.inner_text("#showMore"))
    check("tile badge counts existing reports", "1 report" in pg.inner_text('.tile[data-d="Sertraline"]'))
    pg.fill("#q", "ssri"); pg.wait_for_timeout(100)
    check("search filters tiles by class", pg.locator(".tile").count() == 5)
    pg.fill("#q", "sertr"); pg.keyboard.press("Enter"); pg.wait_for_timeout(500)
    check("Enter opens the first match", pg.evaluate("location.hash") == "#Sertraline")
    check("Read: headline counts effects not in the leaflet", "not in the leaflet" in pg.inner_text("#headline"), pg.inner_text("#headline"))
    check("Read: 8 rows, then Show all", pg.locator("#list .row").count() == 8 and pg.locator("#showAll").count() == 1)
    pg.click("label:has(#onlyNew)"); pg.wait_for_timeout(100)
    check("Read: filter keeps only effects not in the leaflet", pg.locator("#list .row").count() == pg.locator("#list .row.alert").count() > 0)
    check("Read: a user report is merged in", "1 reported" in pg.inner_text('#list button[data-name="abnormal dreams"]'))
    pg.click('#list button[data-name="abnormal dreams"]'); pg.wait_for_timeout(100)
    check("Read: opening a symptom shows the user note", "Vivid dreams" in pg.inner_text("#list"))

    # ---- Report, with the AI helper ----
    pg.click("#tabReport"); pg.wait_for_timeout(300)
    check("Report: no box ticked at start", pg.locator("#chips input:checked").count() == 0)
    check("Report: AI badge says a key is needed", pg.inner_text("#aiPillTxt") == "AI needs a key")
    pg.click('.ex2[data-fx="0"]')
    ticked = sorted(pg.eval_on_selector_all("#chips input:checked", "l => l.map(x => x.value)"))
    check("AI example 1 ticks dizziness + insomnia, without a key", ticked == ["dizziness", "insomnia"], ticked)
    check("AI example 1 explains the ignored nausea", "nausea" in pg.inner_text("#freeStatus") and "computed in advance" in pg.inner_text("#freeStatus"))
    pg.fill("#freeText", "I keep vomiting and my chest hurts"); pg.click("#freeBtn")
    check("own sentence without a key: clear message, no API call", "AI is off" in pg.inner_text("#freeStatus") and not AI_CALLS)
    pg.fill("#freeKeyRow input", "sk-ant-test")
    check("key typed in Report also fills Why AI", pg.input_value("#apiKey") == "sk-ant-test" and "your key" in pg.inner_text("#aiPillTxt"))
    pg.click("#freeBtn"); pg.wait_for_timeout(300)
    ticked = sorted(pg.eval_on_selector_all("#chips input:checked", "l => l.map(x => x.value)"))
    check("own sentence with a key: AI called, terms mapped, old AI ticks replaced", ticked == ["chest pain", "nausea"], ticked)
    check("AI call uses the full app's prompt and model", AI_CALLS and "pharmacovigilance assistant" in AI_CALLS[-1]["messages"][0]["content"] and AI_CALLS[-1]["model"] == "claude-haiku-5-5")
    pg.fill("#note", "<img src=x onerror=alert(1)> felt sick")
    pg.click("#sendBtn"); pg.wait_for_timeout(600)
    check("send: one row posted with drug, symptoms and note", POSTS and POSTS[-1]["drug"] == "Sertraline" and sorted(POSTS[-1]["symptoms"]) == ["chest pain", "nausea"], POSTS)
    check("send: back to Read with a thank you", pg.evaluate("location.hash") == "#Sertraline" and "Thank you" in pg.inner_text("#sum"))
    pg.click('#list button[data-name="chest pain"]'); pg.wait_for_timeout(100)
    check("untrusted note is shown as text, not run", "<img src=x" in pg.inner_text("#list") and pg.locator("#list img").count() == 0)

    # ---- Why AI and the menu ----
    check("Why AI: example 1 shows 3 keyword hits vs 1 real effect", pg.inner_text("#kwN").startswith("3") and pg.inner_text("#aiN").startswith("1"))
    pg.click('.ex[data-ex="1"]')
    check("Why AI: example 2 strikes the feared weight gain", "feared" in pg.inner_text("#aiList"))
    pg.click('.links button[data-go="how"]'); pg.wait_for_timeout(700)
    check("menu scrolls without changing the drug in the address", pg.evaluate("location.hash") == "#Sertraline")
    pg.click('.links button[data-go="drugs"]'); pg.wait_for_timeout(500)
    check("menu Drugs goes back to the tiles", pg.is_visible("#drugs") and pg.evaluate("location.hash") == "")
    pg.fill("#q", "Ozempic"); pg.wait_for_timeout(100)
    check("unknown drug offers to report for it", pg.locator(".tile.add").count() == 1)
    check("no JS errors (database mode)", not err, err)

    # ---- Demo mode (config.js empty) ----
    dp, derr = open_page(b, demo=True)
    dp.goto(APP + "#Mirena/report"); dp.wait_for_timeout(500)
    check("demo mode: pill says Demo mode", dp.inner_text("#mode").startswith("Demo mode"))
    dp.click("#chips .chip >> nth=0"); dp.click("#sendBtn"); dp.wait_for_timeout(400)
    saved = dp.evaluate("JSON.parse(localStorage.getItem('vt_reports') || '[]').length")
    check("demo mode: report kept in the browser", saved == 1 and "1 report" in dp.inner_text("#sum"))
    check("no JS errors (demo mode)", not derr, derr)

    # ---- Phone, dark mode ----
    mp, merr = open_page(b, viewport={"width": 375, "height": 800}, color_scheme="dark")
    mp.goto(APP + "#Sertraline"); mp.wait_for_timeout(500)
    ov = mp.evaluate("document.documentElement.scrollWidth - innerWidth")
    check("no horizontal scroll at 375px", ov <= 0, f"overflow {ov}px")
    check("no JS errors (phone)", not merr, merr)
    b.close()

failed = [r for r in results if not r[1]]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
