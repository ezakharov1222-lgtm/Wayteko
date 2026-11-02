import json, sys, base64, time, re, hashlib
from playwright.sync_api import sync_playwright
PW = open(sys.argv[1]).read().strip(); OUT = sys.argv[2]
files = {}; ntfy = {}; errs = []
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
    if req.method == "PUT":
        d = json.loads(req.post_data)
        if path in files and d.get("sha") != sha(files[path]): return route.fulfill(status=409, json={}, headers=H)
        files[path] = base64.b64decode(d["content"]).decode(); return route.fulfill(status=201, json={}, headers=H)
    if req.method == "DELETE": files.pop(path, None); return route.fulfill(status=200, json={}, headers=H)
def nt(route):
    req = route.request; url = req.url.split("?")[0]
    if req.method == "OPTIONS": return route.fulfill(status=204, headers=H)
    if req.method == "POST":
        ntfy.setdefault(url.rstrip("/").split("/")[-1], []).append({"event": "message", "time": int(time.time()), "message": req.post_data}); return route.fulfill(status=200, json={}, headers=H)
    return route.fulfill(status=200, body="\n".join(json.dumps(m) for m in ntfy.get(url.rstrip("/").split("/")[-2], [])), headers=H)
def dev(b, init=None):
    ctx = b.new_context(viewport={"width": 390, "height": 900})
    if init: ctx.add_init_script(init)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("https://api.github.com/**", gh); pg.route("https://ntfy.sh/**", nt); return pg
def login(pg, pw):
    pg.goto("http://localhost:8766/"); pg.wait_for_timeout(1200)
    pg.fill("#pw", pw); pg.click("#pwForm button[type=submit]"); pg.wait_for_timeout(4000)
def guests_panel(pg):
    txt = pg.locator(".panel").inner_text()
    return re.findall(r"\n([^\n·]+?) · ([^\n]+)\nПароль: (G-[A-Z0-9-]+)", txt)
def open_data(pg):
    if not pg.locator(".panel").count(): pg.click("#dataBtn")
    pg.wait_for_timeout(2500)

OLD = "G-OLDP-ASS2-WORD"
with sync_playwright() as p:
    b = p.chromium.launch()
    # владелец со «старым» единственным гостем (как сейчас на телефоне)
    A = dev(b, "if(!localStorage.getItem('wayteko.guests.v2') && !sessionStorage.getItem('x')){ sessionStorage.setItem('x','1'); localStorage.setItem('wayteko.guest.v1', JSON.stringify({pw:'%s', name:'Старый гость', created:'2026-10-30T02:17:00Z'})); }" % OLD)
    login(A, PW)
    A.click("#dataBtn"); A.fill("#ghtok", "github_pat_TEST"); A.click("#ghForm button[type=submit]"); A.wait_for_timeout(5000)
    print("1 перенос старого гостя:", [(n, pw == OLD) for n, st, pw in guests_panel(A)], "| файл старого гостя:", "data/app.guest.enc.json" in files)
    for name in ["Иван", "Пётр", "Ольга"]:
        A.fill("#gname", name); A.click("#guestForm button[type=submit]"); A.wait_for_timeout(3500)
    gl = guests_panel(A)
    print("2 гостей:", len(gl), [n for n, _, _ in gl], "| форма добавления пятого:", A.locator("#guestForm").count(), "| надпись про максимум:", "максимум" in A.locator(".panel").inner_text())
    pw_by = {n: pw for n, _, pw in gl}
    print("   пароли разные:", len(set(pw_by.values())) == 4, "| гостевых файлов:", len([f for f in files if "g-" in f or "guest" in f]))
    A.screenshot(path=OUT + "/mg_owner.png", full_page=True)
    A.click(".panel button[data-close]")

    G = {}
    for name in ["Старый гость", "Иван", "Пётр", "Ольга"]:
        G[name] = dev(b); login(G[name], pw_by[name])
    for name, pg in G.items():
        pg.click("#dataBtn"); pg.wait_for_timeout(300)
        print(f"3 {name}: вошёл как гость:", pg.locator("#guestPill").inner_text() == "👁 Гость · только просмотр", "| имя в его «Данных»:", name in pg.locator(".panel").inner_text(), "| кнопок изменения:", pg.locator("#addBtn:visible, [data-focus]:visible").count())
        pg.click(".panel button[data-close]")
    G["Ольга"].evaluate("() => document.dispatchEvent(new Event('visibilitychange'))")
    open_data(A)
    st = {n: s_ for n, s_, _ in guests_panel(A)}
    print("4 статусы у владельца:", st, "| шапка:", A.locator("#guestPill").inner_text())

    # смена пароля Пети и удаление Ольги
    gid = lambda name: A.locator(".panel .mrow", has_text=name).locator("button[data-act=g-new]").get_attribute("data-gid")
    A.locator(".panel .mrow", has_text="Пётр").locator("button[data-act=g-new]").click(); A.wait_for_timeout(4000)
    A.locator(".panel .mrow", has_text="Ольга").locator("button[data-act=g-off]").click(); A.wait_for_timeout(4000)
    gl2 = guests_panel(A)
    print("5 после смены/удаления у владельца:", [n for n, _, _ in gl2], "| у Петра новый пароль:", dict((n, pw) for n, _, pw in gl2).get("Пётр") != pw_by["Пётр"], "| форма добавления снова есть:", A.locator("#guestForm").count() == 1)
    for name, pg in G.items():
        pg.click("#dataBtn"); pg.click("button[data-act=sync]"); pg.wait_for_timeout(3500)
        out = pg.locator("#pwForm").count() == 1
        print(f"6 {name}: {'потерял доступ' if out else 'доступ сохранён'}")
        if not out and pg.locator(".panel").count(): pg.click(".panel button[data-close]")
    print("   вход Петра по новому паролю:", end=" ")
    newp = dict((n, pw) for n, _, pw in gl2)["Пётр"]; login(G["Пётр"], newp); print(G["Пётр"].locator("#guestPill").inner_text())

    # второе устройство владельца видит тот же список
    A.click(".panel button[data-close]"); A.wait_for_timeout(5000)
    B = dev(b); login(B, PW); B.wait_for_timeout(3000); open_data(B)
    print("7 второе устройство владельца видит гостей:", [n for n, _, _ in guests_panel(B)])
    b.close()
print("ERRORS:", errs or "нет")
