import json, sys
from playwright.sync_api import sync_playwright
PW = open(sys.argv[1]).read().strip(); OUT = sys.argv[2]; errs = []; H = {"Access-Control-Allow-Origin": "*"}
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width": 390, "height": 900}, accept_downloads=True).new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("https://api.github.com/**", lambda r: r.fulfill(status=404, json={}, headers=H)); pg.route("https://ntfy.sh/**", lambda r: r.fulfill(status=200, body="", headers=H))
    pg.goto("http://localhost:8766/"); pg.wait_for_timeout(1200); pg.fill("#pw", PW); pg.click("#pwForm button[type=submit]"); pg.wait_for_timeout(4000)
    pg.click("#tabs button[data-tab=tasks]"); pg.wait_for_timeout(300)
    print("1 поле «Ответственный» есть:", pg.locator("#tk_owner").count() == 1, "| подпись:", pg.locator("label.f", has=pg.locator("#tk_owner")).inner_text().split("\n")[0])
    pg.fill("#tk_owner", "Иван Петров"); pg.fill("#tk_text", "Подготовить спецификацию"); pg.click("#taskForm button[type=submit]"); pg.wait_for_timeout(300)
    print("2 в списке:", pg.locator("#view .task .towner").all_inner_texts(), "| поле после добавления:", pg.locator("#tk_owner").input_value())
    print("3 подсказки имён:", pg.evaluate("[...document.querySelectorAll('#tk_owners option')].map(o=>o.value)"))
    pg.fill("#tk_owner", ""); pg.fill("#tk_text", "Без ответственного"); pg.click("#taskForm button[type=submit]"); pg.wait_for_timeout(300)
    print("4 задача без ответственного:", [t for t in pg.locator("#view .task").all_inner_texts() if "Без ответственного" in t])
    pg.screenshot(path=OUT + "/owner.png", full_page=True)
    pg.click("#dataBtn")
    with pg.expect_download() as d: pg.click("button[data-act=backup]")
    bk = json.load(open(d.value.path()))
    print("5 в резервной копии:", [(t["text"], t.get("owner")) for t in bk["tasks"]])
    b.close()
print("ERRORS:", errs or "нет")
