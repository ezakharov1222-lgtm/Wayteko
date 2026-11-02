import json, sys, base64
from playwright.sync_api import sync_playwright
PW = open(sys.argv[1]).read().strip(); OUT = sys.argv[2]
captured = {}; errs = []
H = {"Access-Control-Allow-Origin": "*"}
def gh(route):
    req = route.request
    if req.method == "GET" and req.url.rstrip("/").endswith("/repos/ezakharov1222-lgtm/wayteko"):
        return route.fulfill(status=200, json={"permissions": {"push": True}}, headers=H)
    if req.method == "GET": return route.fulfill(status=404, json={}, headers=H)
    if req.method == "PUT":
        captured["body"] = json.loads(req.post_data); captured["n"] = captured.get("n", 0) + 1
        return route.fulfill(status=201, json={"content": {"sha": "x"}}, headers=H)
    route.fulfill(status=204, headers={**H, "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"})
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width": 390, "height": 844}).new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("https://api.github.com/**", gh)
    pg.goto("http://localhost:8766/"); pg.wait_for_timeout(1200)
    pg.fill("#pw", PW); pg.click("#pwForm button[type=submit]"); pg.wait_for_timeout(3000)
    pg.click("#dataBtn"); pg.wait_for_timeout(300)
    pg.fill("#ghtok", "github_pat_TEST"); pg.click("#ghForm button[type=submit]"); pg.wait_for_timeout(4000)
    print("1 первая отправка:", captured.get("n"), "|", pg.locator(".panel").inner_text().split("Последняя отправка:")[1][:40].replace("\n", " "))
    pg.screenshot(path=OUT + "/up1.png")
    pg.click(".panel button[data-close]"); pg.wait_for_timeout(200)
    pg.locator("button[data-focus='1']").first.click(); pg.wait_for_timeout(300)
    name = pg.locator(".panel h2").inner_text()
    pg.fill("#t_text", "ТЕСТ из приложения"); pg.locator("button[data-setnext]").first.click()
    pg.click("#touchForm button[type=submit]"); pg.wait_for_timeout(300)
    pg.click(".panel button[data-close]"); pg.wait_for_timeout(200)
    pg.locator("button[data-tab=arch]").click(); pg.wait_for_timeout(300)
    pg.locator("#view button.name").first.click(); pg.wait_for_timeout(300)
    dname = pg.locator(".panel h2").inner_text()
    pg.click("button[data-askdel]"); pg.click("button[data-del]"); pg.wait_for_timeout(5000)
    print("2 отправок всего:", captured["n"], "| изменён:", name, "| удалён:", dname)
    b.close()
open(OUT + "/app.enc.json", "w").write(base64.b64decode(captured["body"]["content"]).decode())
print("ERRORS:", errs or "нет")
