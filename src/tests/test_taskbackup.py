import json, sys, re
from playwright.sync_api import sync_playwright
PW = open(sys.argv[1]).read().strip(); OUT = sys.argv[2]; errs = []
H = {"Access-Control-Allow-Origin": "*"}
def dev(b):
    pg = b.new_context(viewport={"width": 390, "height": 900}, accept_downloads=True).new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("https://api.github.com/**", lambda r: r.fulfill(status=404, json={}, headers=H)); pg.route("https://ntfy.sh/**", lambda r: r.fulfill(status=200, body="", headers=H)); return pg
def login(pg):
    pg.goto("http://localhost:8766/"); pg.wait_for_timeout(1200); pg.fill("#pw", PW); pg.click("#pwForm button[type=submit]"); pg.wait_for_timeout(4000)
with sync_playwright() as p:
    b = p.chromium.launch(); A = dev(b); login(A)
    A.click("#tabs button[data-tab=tasks]"); A.fill("#tk_text", "Задача для бэкапа"); A.click("#taskForm button[type=submit]"); A.wait_for_timeout(300)
    A.click("#dataBtn")
    with A.expect_download() as d: A.click("button[data-act=backup]")
    path = OUT + "/backup.json"; d.value.save_as(path); bk = json.load(open(path))
    print("1 резервная копия: клиентов", len(bk["clients"]), "| задач", len(bk.get("tasks", [])), [t["text"] for t in bk.get("tasks", [])])
    B = dev(b); login(B); B.click("#dataBtn"); B.set_input_files("#importFile", path); B.wait_for_timeout(800)
    B.click("button[data-act=imp-replace]"); B.wait_for_timeout(500)
    if B.locator(".panel button[data-close]").count(): B.locator(".panel button[data-close]").first.click()
    B.click("#tabs button[data-tab=tasks]"); B.wait_for_timeout(300)
    print("2 новое устройство после загрузки копии видит задачи:", B.locator("#view .task .ttext").all_inner_texts())
    b.close()
print("ERRORS:", errs or "нет")
