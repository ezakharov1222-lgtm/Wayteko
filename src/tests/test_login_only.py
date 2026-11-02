import json, sys, base64, time, re, hashlib
from playwright.sync_api import sync_playwright
PW = open(sys.argv[1]).read().strip(); OUT = sys.argv[2]
files = {}; errs = []
H = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"}
sha = lambda t: hashlib.sha1(t.encode()).hexdigest()
def gh(route):
    req = route.request; url = req.url.split("?")[0]
    if req.method == "OPTIONS": return route.fulfill(status=204, headers=H)
    if url.rstrip("/").endswith("/repos/ezakharov1222-lgtm/wayteko"): return route.fulfill(status=200, json={"permissions": {"push": True}}, headers=H)
    path = re.search(r"/contents/(.+)$", url).group(1)
    if req.method == "GET":
        if path not in files: return route.fulfill(status=404, json={}, headers=H)
        if "raw" in (req.headers.get("accept") or ""): return route.fulfill(status=200, body=files[path], headers={**H, "Content-Type": "application/json"})
        return route.fulfill(status=200, json={"sha": sha(files[path])}, headers=H)
    if req.method == "PUT": files[path] = base64.b64decode(json.loads(req.post_data)["content"]).decode(); return route.fulfill(status=201, json={}, headers=H)
    if req.method == "DELETE": files.pop(path, None); return route.fulfill(status=200, json={}, headers=H)
def dev(b, offline=False):
    pg = b.new_context(viewport={"width": 390, "height": 844}).new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("https://api.github.com/**", gh); pg.route("https://ntfy.sh/**", lambda r: r.fulfill(status=200, body="", headers=H))
    if offline: pg.route("**/data/**", lambda r: r.abort())
    return pg
VIS = """() => [...document.querySelectorAll('button, input, textarea, select, a, label.filebtn, nav, header, #stats')].filter(e => e.offsetParent !== null)
  .map(e => e.tagName === 'INPUT' ? 'поле:' + e.type : (e.id ? '#' + e.id : '') + ' ' + (e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 30))"""
def screen(pg, label, shot=None):
    v = pg.evaluate(VIS); print(f"{label}:", v)
    if shot: pg.screenshot(path=f"{OUT}/{shot}.png")
    return v
with sync_playwright() as p:
    b = p.chromium.launch()
    A = dev(b); A.goto("http://localhost:8766/")
    A.wait_for_timeout(150); screen(A, "1а первое открытие, через 0,15 с")
    A.wait_for_timeout(3000); screen(A, "1б первое открытие, через 3 с", "lo_first")
    A.fill("#pw", "неверный"); A.click("#pwForm button[type=submit]"); A.wait_for_timeout(2500); screen(A, "2 после неверного пароля")
    A.fill("#pw", PW); A.click("#pwForm button[type=submit]"); A.wait_for_timeout(3500)
    v = screen(A, "3 после верного пароля (кратко)")
    print("   шапка, сводка, вкладки видны:", A.locator("#dataBtn").is_visible(), A.locator("#stats").is_visible(), A.locator("#tabs").is_visible())
    A.click("#dataBtn"); A.click("button[data-act=logout]"); A.wait_for_timeout(500); screen(A, "4 после «Сменить пароль/Выйти»")
    O = dev(b, offline=True); O.goto("http://localhost:8766/"); O.wait_for_timeout(2500); screen(O, "5 первое открытие без интернета")
    # гость, у которого сменили пароль
    A.fill("#pw", PW); A.click("#pwForm button[type=submit]"); A.wait_for_timeout(3500)
    A.click("#dataBtn"); A.fill("#ghtok", "github_pat_TEST"); A.click("#ghForm button[type=submit]"); A.wait_for_timeout(4000)
    A.fill("#gname", "Тест"); A.click("#guestForm button[type=submit]"); A.wait_for_timeout(4000)
    gpw = re.search(r"Пароль: (G-[A-Z0-9-]+)", A.locator(".panel").inner_text()).group(1)
    G = dev(b); G.goto("http://localhost:8766/"); G.wait_for_timeout(1500); G.fill("#pw", gpw); G.click("#pwForm button[type=submit]"); G.wait_for_timeout(3500)
    A.locator(".panel .mrow", has_text="Тест").locator("button[data-act=g-off]").click(); A.wait_for_timeout(3000)
    G.click("#dataBtn"); G.click("button[data-act=sync]"); G.wait_for_timeout(3500); screen(G, "6 гость после удаления доступа", "lo_guest_revoked")
    b.close()
print("ERRORS:", errs or "нет")
