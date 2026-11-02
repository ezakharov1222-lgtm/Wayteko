import json, sys, base64, time, re
from playwright.sync_api import sync_playwright
PW = open(sys.argv[1]).read().strip(); OUT = sys.argv[2]
files = {}; ntfy = {}; errs = []
H = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"}

def gh(route):
    req = route.request; url = req.url.split("?")[0]
    if req.method == "OPTIONS": return route.fulfill(status=204, headers=H)
    if url.rstrip("/").endswith("/repos/ezakharov1222-lgtm/wayteko"):
        return route.fulfill(status=200, json={"permissions": {"push": True}}, headers=H)
    m = re.search(r"/contents/(.+)$", url); path = m.group(1)
    if req.method == "GET":
        if path not in files: return route.fulfill(status=404, json={}, headers=H)
        if "raw" in (req.headers.get("accept") or ""):
            return route.fulfill(status=200, body=files[path], headers={**H, "Content-Type": "application/json"})
        return route.fulfill(status=200, json={"sha": "s%d" % len(files[path])}, headers=H)
    if req.method == "PUT":
        files[path] = base64.b64decode(json.loads(req.post_data)["content"]).decode()
        return route.fulfill(status=201, json={}, headers=H)
    if req.method == "DELETE":
        files.pop(path, None); return route.fulfill(status=200, json={}, headers=H)

def nt(route):
    req = route.request; url = req.url.split("?")[0]
    if req.method == "OPTIONS": return route.fulfill(status=204, headers=H)
    topic = url.rstrip("/").split("/")[-1] if req.method == "POST" else url.rstrip("/").split("/")[-2]
    if req.method == "POST":
        ntfy.setdefault(topic, []).append({"event": "message", "time": int(time.time()), "message": req.post_data})
        return route.fulfill(status=200, json={}, headers=H)
    body = "\n".join(json.dumps(m) for m in ntfy.get(topic, []))
    return route.fulfill(status=200, body=body, headers=H)

def page(b):
    pg = b.new_context(viewport={"width": 390, "height": 844}).new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("https://api.github.com/**", gh); pg.route("https://ntfy.sh/**", nt)
    return pg

with sync_playwright() as p:
    b = p.chromium.launch()
    own = page(b)
    own.goto("http://localhost:8766/"); own.wait_for_timeout(1200)
    own.fill("#pw", PW); own.click("#pwForm button[type=submit]"); own.wait_for_timeout(3000)
    own.click("#dataBtn"); own.wait_for_timeout(300)
    own.fill("#ghtok", "github_pat_TEST"); own.click("#ghForm button[type=submit]"); own.wait_for_timeout(4000)
    own.fill("#gname", "Иван"); own.click("#guestForm button[type=submit]"); own.wait_for_timeout(4000)
    gtext = own.locator(".panel").inner_text()
    gpw = re.search(r"Пароль гостя:\s*(G-[A-Z0-9-]+)", gtext).group(1)
    print("1 владелец создал доступ, пароль гостя:", gpw, "| файлы:", sorted(files))
    own.screenshot(path=OUT + "/g_owner_panel.png", full_page=True)

    gu = page(b)
    gu.goto("http://localhost:8766/"); gu.wait_for_timeout(1200)
    gu.fill("#pw", gpw); gu.click("#pwForm button[type=submit]"); gu.wait_for_timeout(4000)
    print("2 гость вошёл:", gu.locator("#guestPill").inner_text(), "| карточек:", gu.locator(".card").count())
    vis = lambda sel: gu.locator(sel).filter(has=None).evaluate_all("els => els.filter(e => e.offsetParent !== null).length")
    print("3 видимые кнопки изменения у гостя: +Новый", vis("#addBtn"), "| записать касание", vis("[data-focus]"), "| перенести", vis("[data-move]"), "| назначить встречу", vis("[data-meet-open]:not(.meet-on)"))
    gu.locator("#view button.name").first.click(); gu.wait_for_timeout(300)
    print("4 карточка у гостя: форма касания", vis("#touchForm"), "| форма встречи", vis("#meetForm"), "| удалить", vis("[data-askdel]"), "| статусы видно", vis(".temps button"))
    gu.screenshot(path=OUT + "/g_guest_card.png")
    gu.click(".panel button[data-close]")

    # владелец меняет клиента -> гость получает
    own.click(".panel button[data-close]"); own.wait_for_timeout(200)
    own.locator("button[data-focus='1']").first.click(); own.wait_for_timeout(300)
    cname = own.locator(".panel h2").inner_text()
    own.fill("#t_text", "ПРОВЕРКА ГОСТЯ"); own.locator("button[data-setnext]").first.click()
    own.click("#touchForm button[type=submit]"); own.wait_for_timeout(4500)
    own.click(".panel button[data-close]")
    gu.click("#dataBtn"); gu.click("button[data-act=sync]"); gu.wait_for_timeout(3500)
    gu.click(".panel button[data-close]")
    gu.locator("#view button.name", has_text=cname).first.click(); gu.wait_for_timeout(300)
    print("5 гость видит новое касание у", cname, ":", "ПРОВЕРКА ГОСТЯ" in gu.locator(".panel").inner_text())
    gu.click(".panel button[data-close]")

    # присутствие
    own.click("#dataBtn"); own.wait_for_timeout(2500)
    st = re.search(r"Статус:\s*([^\n]+)", own.locator(".panel").inner_text()).group(1)
    print("6 владелец видит статус гостя:", st, "| в шапке:", own.locator("#guestPill").inner_text() if own.locator("#guestPill").is_visible() else "—")
    own.screenshot(path=OUT + "/g_owner_online.png")
    own.click(".panel button[data-close]")

    # смена пароля -> гость теряет доступ
    own.click("#dataBtn"); own.click("button[data-act=g-new]"); own.wait_for_timeout(4000)
    gu.click("#dataBtn"); gu.click("button[data-act=sync]"); gu.wait_for_timeout(3500)
    print("7 после смены пароля у гостя экран входа:", gu.locator("#pwForm").count(), "| клиентов в памяти гостя:", len(json.loads(gu.evaluate("localStorage.getItem('wayteko.clients.v1')") or "[]")))
    st2 = re.search(r"Статус:\s*([^\n]+)", own.locator(".panel").inner_text())
    own.click("button[data-act=g-off]"); own.wait_for_timeout(3000)
    print("8 доступ отключён, гостевой файл удалён:", "data/app.guest.enc.json" not in files)
    b.close()
print("ERRORS:", errs or "нет")
