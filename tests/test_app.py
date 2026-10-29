"""End-to-end tests of app/index.html in headless Chromium (Playwright).
api.anthropic.com is faked with the gold answers of video-tools/mock.js, so the AI path runs offline, with no key.
Usage: pip install playwright && python3 -m playwright install chromium && python3 tests/test_app.py
Screenshots go to a temporary folder printed at the end."""
import json, re, sys, pathlib, tempfile
from playwright.sync_api import sync_playwright

REPO = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).parent.parent).resolve()
APP_REAL = (REPO / "app/index.html").as_uri()
APP = APP_REAL + "?demo"
OUT = pathlib.Path(tempfile.mkdtemp(prefix="vigitrack-test-"))
mock_js = (REPO / "video-tools/mock.js").read_text()
GOLD = json.loads(re.sub(r"(\w+):\[", r'"\1":[', re.search(r"const GOLD=(\{.*?\n\});", mock_js, re.S).group(1)).replace("\n", ""))

results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail)); print(("PASS " if ok else "FAIL ") + name + (f"  -> {detail}" if detail else ""))

API_LOG = []
API_MODE = {"status": 200, "delay": 0, "bad_json": False}
def fake_api(route):
    req = route.request
    body = json.loads(req.post_data or "{}")
    API_LOG.append(body)
    if API_MODE["status"] != 200:
        return route.fulfill(status=API_MODE["status"], body='{"type":"error"}', headers={"access-control-allow-origin": "*"})
    msgs = body["messages"]
    if "tools" in body:
        # agent: round 1 -> call both tools, round 2 -> answer
        last = msgs[-1]
        if isinstance(last["content"], str):
            content = [{"type": "text", "text": "Let me look."},
                       {"type": "tool_use", "id": "t1", "name": "get_signal_summary", "input": {}},
                       {"type": "tool_use", "id": "t2", "name": "get_reviews_for_effect", "input": {"effect": "joint ache", "limit": 3}}]
            stop = "tool_use"
        else:
            tr = {c["tool_use_id"]: c["content"] for c in last["content"]}
            content = [{"type": "text", "text": "**Report** TOOLDATA " + json.dumps({k: len(v) for k, v in tr.items()}) + " <img src=x onerror=alert(1)>"}]
            stop = "end_turn"
    else:
        prompt = msgs[0]["content"]
        ids = re.findall(r"^\[([^\]]+)\] ", prompt, re.M)
        arr = [{"id": i, "effects": GOLD.get(i, ["nightmares"] if i == "live" else [])} for i in ids]
        txt = "garbage" if API_MODE["bad_json"] else "```json\n" + json.dumps(arr) + "\n```"
        content = [{"type": "text", "text": txt}]; stop = "end_turn"
    route.fulfill(status=200, content_type="application/json", headers={"access-control-allow-origin": "*"},
                  body=json.dumps({"content": content, "stop_reason": stop}))

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    errors = []; failed = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and errors.append(m.text))
    pg.on("requestfailed", lambda r: failed.append(r.url))
    pg.route("https://api.anthropic.com/**", fake_api)
    pg.add_init_script("""(()=>{const f=window.fetch; window.__delay=0; window.fetch=(u,o={})=>new Promise((res,rej)=>{
      const t=setTimeout(()=>f(u,o).then(res,rej), String(u).includes('anthropic')?window.__delay:0);
      o.signal&&o.signal.addEventListener('abort',()=>{clearTimeout(t);rej(new DOMException('aborted','AbortError'))});});})()""")
    pg.goto(APP); pg.wait_for_timeout(1500)
    T = lambda sel: pg.locator(sel).inner_text()

    check("no JS errors on load", not errors, errors)
    check("no failed network requests", not failed, failed)
    check("PapaParse loaded", pg.evaluate("!!window.Papa"))
    check("title", pg.title() == "Vigi-Track", pg.title())
    check("engine pill = keyword mode outside Claude", "Keyword" in T("#enginePillTxt"), T("#enginePillTxt"))
    check("AI radio disabled without key", pg.evaluate("$('engAI').disabled"))
    check("5 tiles", pg.locator(".tile").count() == 5)
    check("headline on load", "keyword search read 14 reviews" in T("#headline").lower(), T("#headline"))
    check("?demo opens the demo", pg.evaluate("S.source")=="demo")

    # ---- keyword mode, every drug
    kw = {}
    for d in ["Zentrolix", "Calmarin", "Dormexa", "Asmira", "Glucovia"]:
        pg.click(f'.tile[data-d="{d}"]'); pg.wait_for_timeout(150)
        kw[d] = pg.locator(".acard h3").all_inner_texts()
    print("keyword alerts:", kw)
    check("keyword mode: Zentrolix shows 'Anxiety' false alarm (by design)", "Anxiety" in kw["Zentrolix"])
    pg.click('.tile[data-d="Calmarin"]'); pg.wait_for_timeout(100)
    pg.click("#leafToggle"); pg.click('#known label:has(input[data-k="cough"])'); pg.click("#leafToggle")
    pg.click('.tile[data-d="Dormexa"]'); pg.wait_for_timeout(100); pg.click('.tile[data-d="Calmarin"]'); pg.wait_for_timeout(100)
    check("leaflet edits kept when coming back to a drug", not pg.evaluate("S.known.has('cough')"))
    pg.click("#leafToggle"); pg.click('#known label:has(input[data-k="cough"])'); pg.click("#leafToggle")

    # ---- leaflet edit -> tile badge consistency
    pg.click('.tile[data-d="Zentrolix"]'); pg.wait_for_timeout(100)
    before = pg.locator('.tile[data-d="Zentrolix"] .badge').inner_text()
    pg.click("#leafToggle"); pg.click('#known label:has(input[data-k="anxiety"])'); pg.wait_for_timeout(100)
    after_cards = pg.locator(".acard").count()
    after = pg.locator('.tile[data-d="Zentrolix"] .badge').inner_text()
    check("tile badge updates after editing leaflet", before != after, f"badge '{before}' -> '{after}', cards now {after_cards}")
    pg.fill("#addKnown", "Heart racing"); pg.press("#addKnown", "Enter")
    check("custom leaflet entry is normalised (heart racing -> palpitations)", pg.evaluate("S.known.has('palpitations')"))
    pg.evaluate("S.known.delete('palpitations'); S.known.delete('anxiety'); renderKnown(); renderResults()")
    pg.click("#leafToggle")

    # ---- API key path
    pg.fill("#apiKey", "nope"); pg.click("#useKey")
    check("bad key format rejected", "does not look" in T("#keyStatus"))
    pg.fill("#apiKey", "sk-ant-test"); pg.click("#useKey"); pg.wait_for_timeout(100)
    check("key enables AI", pg.evaluate("$('engAI').checked && !$('engAI').disabled"), T("#enginePillTxt"))
    check("key field cleared", pg.input_value("#apiKey") == "")

    pg.click('.tile[data-d="Calmarin"]'); pg.wait_for_timeout(100)  # resets the edited Zentrolix leaflet
    ai = {}
    for d in ["Zentrolix", "Calmarin", "Dormexa", "Asmira", "Glucovia"]:
        pg.click(f'.tile[data-d="{d}"]'); pg.wait_for_timeout(100)
        pg.evaluate("$('engAI').checked=true; updateRunLabel()")
        pg.click("#run"); pg.wait_for_function("!$('run').disabled", timeout=10000); pg.wait_for_timeout(100)
        ai[d] = pg.locator(".acard h3").all_inner_texts()
    print("AI alerts:", ai)
    exp = {"Zentrolix": ["Palpitations", "Hair loss"], "Calmarin": ["Muscle pain", "Tinnitus"],
           "Dormexa": ["Abnormal dreams", "Memory problems", "Sleepwalking", "Taste changes"],
           "Asmira": ["Abnormal dreams", "Mood changes"], "Glucovia": ["Joint pain", "Blurred vision"]}
    for d in exp: check(f"AI alerts {d}", ai[d] == exp[d], f"got {ai[d]}")
    check("API extraction uses haiku", API_LOG and API_LOG[-1]["model"] == "claude-haiku-5-5", API_LOG and API_LOG[-1]["model"])
    check("agg line after AI run", "false alarm" in T("#agg"), T("#agg"))

    # ---- agent with tools
    pg.click("#suggs button:nth-child(1)"); pg.wait_for_function("!$('ask').disabled", timeout=10000); pg.wait_for_timeout(200)
    bub = pg.locator(".bub.ag").last
    check("agent answered", "TOOLDATA" in bub.inner_text(), bub.inner_text()[:200])
    check("agent output escaped (no <img> injected)", pg.locator(".bub.ag img").count() == 0)
    check("agent bold rendered", pg.locator(".bub.ag strong").count() >= 1)
    check("agent tool steps shown", pg.locator(".bub.ag .steps span").count() == 2, pg.locator(".bub.ag .steps").inner_text())
    check("agent uses sonnet", API_LOG[-1]["model"] == "claude-sonnet-5-5")
    m = re.search(r'"t2": (\d+)', bub.inner_text())
    check("get_reviews_for_effect('heart racing') canonicalised & returns reviews", m and int(m.group(1)) > 5, bub.inner_text()[:200])

    # ---- live tester
    pg.click("#tryBtn"); pg.wait_for_function("!$('tryBtn').disabled", timeout=5000)
    check("tester AI result", "abnormal dreams" in T("#aiList"), T("#aiList"))
    check("tester keyword strike-through reasons", pg.locator("#aiList li.no").count() == 2, T("#aiList"))

    # ---- error paths
    for status, word in [(401, "API key was refused"), (429, "Too many"), (500, "could not finish")]:
        API_MODE["status"] = status
        pg.click("#run"); pg.wait_for_function("!$('run').disabled", timeout=5000)
        check(f"HTTP {status} message", word.lower() in T("#runLog").lower(), T("#runLog"))
    API_MODE["status"] = 200; API_MODE["bad_json"] = True
    pg.click("#run"); pg.wait_for_function("!$('run').disabled", timeout=5000)
    check("bad JSON message", "could not be read" in T("#runLog"), T("#runLog")); API_MODE["bad_json"] = False

    # ---- stop button
    pg.evaluate("window.__delay=1500")
    pg.click("#run"); pg.wait_for_timeout(300); pg.click("#stopRun"); pg.wait_for_function("!$('run').disabled", timeout=8000)
    check("stop cancels run", "Stopped" in T("#runLog"), T("#runLog"))

    # ---- race: switch drug while AI run in flight
    pg.click('.tile[data-d="Zentrolix"]'); pg.wait_for_timeout(100)
    pg.evaluate("$('engAI').checked=true"); pg.click("#run"); pg.wait_for_timeout(300)
    pg.click('.tile[data-d="Glucovia"]'); pg.wait_for_timeout(3000)
    shown = pg.evaluate("({drug:S.drug, ids:S.result.list.map(r=>r.id).slice(0,3), headline:$('headline').innerText})")
    check("switching drug mid-run does not mix results", all(i.startswith("g") for i in shown["ids"]), shown)
    pg.evaluate("window.__delay=0")
    pg.wait_for_function("!$('run').disabled", timeout=8000)

    # ---- race: switch drug while agent answering
    pg.click('.tile[data-d="Asmira"]'); pg.wait_for_timeout(100); pg.evaluate("$('engAI').checked=true"); pg.click("#run")
    pg.wait_for_function("!$('run').disabled", timeout=8000)
    pg.evaluate("window.__delay=1000")
    pg.click("#suggs button:nth-child(2)"); pg.wait_for_timeout(200)
    pg.click('.tile[data-d="Calmarin"]'); pg.wait_for_timeout(2600)
    st = pg.evaluate("({askDisabled:$('ask').disabled, status:$('askStatus').innerText, engine:S.result.engine})")
    check("switching drug mid-question keeps agent state coherent", st["askDisabled"] and "Done" not in st["status"], st)
    pg.evaluate("window.__delay=0")

    # ---- upload: the repo CSV, then Kaggle-style TSV with entities and an unnamed id column
    pg.set_input_files("#file", str(REPO / "data/demo_reviews.csv")); pg.wait_for_timeout(800)
    check("upload demo CSV", "66" in T("#loadStatus") and pg.locator(".tile").count() == 5, T("#loadStatus"))
    check("uploaded data: leaflet empty (real-data mode)", pg.evaluate("S.known.size") == 0)
    tsv = OUT / "kaggle_like.tsv"
    lines = ["\tdrugName\tcondition\treview\trating\tdate\tusefulCount"]
    for i in range(30):
        lines.append(f'{1000+i}\tDrug{i%12}\tPain\t"&quot;I couldn&#039;t sleep &amp; my heart is pounding&quot; <b>x</b>"\t{i%10+1}\tMay 1, 2015\t{i}')
    tsv.write_text("\n".join(lines))
    pg.set_input_files("#file", str(tsv)); pg.wait_for_timeout(800)
    first = pg.evaluate("S.reviews[0]")
    check("TSV parsed, id from unnamed column", first["id"] == "1000", first)
    check("HTML entities decoded", first["text"].startswith("I couldn't sleep & my heart"), first["text"])
    check(">10 drugs shows dropdown", pg.is_visible("#moreWrap"))
    check("no XSS from review text", pg.locator(".q b").count() == 0)
    opts = pg.locator("#drug option").count()
    check("dropdown lists every uploaded drug", opts == 12, opts)
    pg.click("#loadDemo"); pg.wait_for_timeout(300)
    check("back to demo", pg.locator(".tile").count() == 5 and pg.evaluate("S.isDemo"))

    check("no JS errors overall (except the HTTP errors the test provokes)", not [e for e in errors if "status of 4" not in e and "status of 5" not in e], errors)
    pg.screenshot(path=str(OUT / "desktop.png"), full_page=True)

    # ---- real data (default)
    r = b.new_context(viewport={"width": 1440, "height": 900}); rp = r.new_page(); rerr = []
    rp.on("pageerror", lambda e: rerr.append(str(e))); rp.on("console", lambda m: m.type == "error" and rerr.append(m.text))
    rp.goto(APP_REAL); rp.wait_for_timeout(2000)
    info = rp.evaluate("({src:S.source, drugs:S.order.length, n:S.reviews.length, drug:S.drug, tiles:document.querySelectorAll('.tile').length, opts:$('drug').options.length, meta:$('whoMeta').innerText, leaf:[...S.known].length, src2:$('leafSrc').innerText, title:$('leafTitle').innerText, head:$('headline').innerText, line:$('dataLine').innerText})")
    print("real:", info)
    check("real data opens by default", info["src"] == "real" and info["drugs"] == 37 and info["n"] == 5550)
    check("real: 10 tiles + dropdown of 37", info["tiles"] == 10 and info["opts"] == 37 and rp.is_visible("#moreWrap"))
    check("real: leaflet pre-filled from FDA label", info["leaf"] > 5 and "FDA label" in info["src2"] and info["title"] == "The FDA label lists")
    check("real: results shown at once", "read 150 reviews" in info["head"].lower(), info["head"])
    check("real: no JS errors", not rerr, rerr)
    rp.select_option("#drug", "Varenicline"); rp.wait_for_timeout(200)
    check("real: picking a drug outside the tiles adds its tile", rp.locator('.tile[data-d="Varenicline"].sel').count() == 1)
    allk = {}
    for name in rp.evaluate("S.order"):
        rp.select_option("#drug", name); rp.wait_for_timeout(30)
        allk[name] = rp.locator(".acard h3").all_inner_texts()
    check("real: inLeaflet uses label text for terms outside the vocabulary", rp.evaluate("(S.drug='Sertraline', S.known=new Set(), [inLeaflet('serotonin syndrome'), inLeaflet('flying unicorns')])") == [True, False])
    rp.click("#toDemo"); rp.wait_for_timeout(300)
    check("real -> demo switch", rp.evaluate("S.source") == "demo" and rp.locator(".tile").count() == 5)
    rp.click("#toReal"); rp.wait_for_timeout(500)
    check("demo -> real switch", rp.evaluate("S.source") == "real")
    rp.screenshot(path=str(OUT / "real.png"), full_page=False)
    r.close()

    # ---- mobile + dark
    m = b.new_context(viewport={"width": 375, "height": 800}, color_scheme="dark", device_scale_factor=2)
    mp = m.new_page(); mp.goto(APP); mp.wait_for_timeout(1200)
    ov = mp.evaluate("document.documentElement.scrollWidth - innerWidth")
    check("no horizontal scroll at 375px", ov <= 0, f"overflow {ov}px")
    wide = mp.evaluate("[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,5).map(e=>e.tagName+'.'+e.className)")
    check("no element past the right edge at 375px", not wide, wide)
    mp.screenshot(path=str(OUT / "mobile_dark.png"), full_page=True)

    # ---- Claude runtime path (window.claude provided, as in claude.ai) via mock.js
    c = b.new_context(); cp = c.new_page(); cerr = []
    cp.on("pageerror", lambda e: cerr.append(str(e)))
    cp.add_init_script(mock_js); cp.goto(APP); cp.wait_for_timeout(1200)
    check("claude runtime: pill on & AI preselected", "AI agent on" in cp.inner_text("#enginePillTxt") and cp.evaluate("$('engAI').checked"))
    cp.click('.tile[data-d="Asmira"]'); cp.click("#run"); cp.wait_for_function("!$('run').disabled", timeout=8000)
    check("claude runtime: Asmira headline 83% / 2 alerts", "83%" in cp.inner_text("#headline") and cp.locator(".acard").count() == 2, cp.inner_text("#headline"))
    check("claude runtime: no JS errors", not cerr, cerr)
    b.close()

fails = sum(1 for r in results if not r[1])
print("\nSUMMARY: %d pass, %d fail   (screenshots in %s)" % (len(results) - fails, fails, OUT))
sys.exit(1 if fails else 0)
