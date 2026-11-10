import json, sys, base64, re, hashlib
from playwright.sync_api import sync_playwright
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
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
    if req.method == "PUT":
        d = json.loads(req.post_data)
        if path in files and d.get("sha") != sha(files[path]): return route.fulfill(status=409, json={}, headers=H)
        files[path] = base64.b64decode(d["content"]).decode(); return route.fulfill(status=201, json={}, headers=H)
    if req.method == "DELETE": files.pop(path, None); return route.fulfill(status=200, json={}, headers=H)
def dev(b):
    pg = b.new_context(viewport={"width": 400, "height": 900}).new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("dialog", lambda d: d.dismiss())
    pg.route("https://api.github.com/**", gh); pg.route("https://ntfy.sh/**", lambda r: r.fulfill(status=200, body="", headers=H)); return pg
def login(pg, name, pw):
    pg.goto("http://localhost:8768/"); pg.wait_for_timeout(1000)
    pg.fill("#uname", name); pg.fill("#pw", pw); pg.click("#pwForm button[type=submit]"); pg.wait_for_timeout(4000)
def decrypt(path, pw):
    box = json.loads(files[path]); d = lambda s: base64.b64decode(s)
    k = hashlib.pbkdf2_hmac("sha256", pw.encode(), d(box["salt"]), box["iter"], 32)
    return json.loads(AESGCM(k).decrypt(d(box["iv"]), d(box["ct"]), None))
def openc(pg, q):
    pg.click("#tabs button[data-tab=all]"); pg.wait_for_timeout(200); pg.fill("#q", q); pg.wait_for_timeout(300); pg.locator("#view button.name").first.click(); pg.wait_for_timeout(300)
def touch(pg, text):
    pg.fill("#t_text", text); pg.fill("#t_next", "2026-11-20"); pg.click("#touchForm button[type=submit]"); pg.wait_for_timeout(500)
with sync_playwright() as p:
    b = p.chromium.launch()
    A = dev(b); A.goto("http://localhost:8768/"); A.wait_for_timeout(800)
    A.fill("#uname", "Евгений"); A.fill("#pw", PW); A.click("#pwForm button[type=submit]"); A.wait_for_timeout(800)
    print("1 одно слово в имени — не пускает:", A.locator("#pwForm").count() == 1)
    A.fill("#uname", "Евгений Захаров"); A.click("#pwForm button[type=submit]"); A.wait_for_timeout(4000)
    print("2 вошёл, плашка:", A.locator("#userPill").inner_text(), "| вкладка задач видна:", A.locator("#tabs [data-tab=tasks]").is_visible())
    A.click("#dataBtn"); A.fill("#ghtok", "github_pat_TEST"); A.click("#ghForm button[type=submit]"); A.wait_for_timeout(3500)
    A.fill("#ename", "Анна"); A.click("#editorForm button[type=submit]"); A.wait_for_timeout(3500)
    epw = re.search(r"Пароль: (E-[A-Z0-9-]+)", A.locator(".panel").inner_text()).group(1)
    print("3 редактор добавлен, пароль:", epw[:6] + "…", "| файл редактора:", [f for f in files if f.startswith("data/e-")])
    A.click(".panel button[data-close]")
    openc(A, "АЗИАН"); touch(A, "Владелец: звонок Альберту"); A.click(".panel button[data-close]"); A.wait_for_timeout(2500)
    E = dev(b); login(E, "Анна Смирнова", epw)
    print("4 редактор вошёл:", E.locator("#userPill").inner_text(), "| задачи скрыты:", not E.locator("#tabs [data-tab=tasks]").is_visible(), "| клиентов:", E.evaluate("JSON.parse(localStorage.getItem('wayteko.clients.v1')).length"))
    openc(E, "АЗИАН")
    print("5 у редактора видно касание владельца:", "Владелец: звонок Альберту" in E.locator(".panel").inner_text(), "| кнопка удаления скрыта:", not E.locator("[data-askdel]").is_visible())
    touch(E, "Редактор: отправила КП")
    print("6 роль на устройстве:", E.evaluate("localStorage.getItem('wayteko.role.v1')"), "| задач в памяти:", E.evaluate("localStorage.getItem('wayteko.tasks.v1')"))
    E.click(".panel button[data-close]"); E.click("#addBtn"); E.wait_for_timeout(300); E.fill("#f_name", "ТЕСТ Новый от Анны"); E.click("#newForm button[type=submit]"); E.wait_for_timeout(600)
    print("6b после создания у редактора:", E.evaluate("(JSON.parse(localStorage.getItem('wayteko.clients.v1')).find(c=>c.name==='ТЕСТ Новый от Анны')||{}).createdBy"), E.locator("#toast").inner_text())
    E.click(".panel button[data-close]")
    openc(A, "АЗИАН"); touch(A, "Владелец: второе касание одновременно"); A.click(".panel button[data-close]")
    E.wait_for_timeout(3500); A.wait_for_timeout(3000)
    A.click("#dataBtn"); A.click("[data-act=devsync]"); A.wait_for_timeout(3000); A.click(".panel button[data-close]")
    openc(A, "АЗИАН"); txt = A.locator(".panel").inner_text()
    print("7 у владельца все 3 касания:", all(x in txt for x in ["Владелец: звонок Альберту", "Редактор: отправила КП", "Владелец: второе касание одновременно"]))
    print("8 подписи:", "👤 Анна Смирнова" in txt, "👤 Евгений Захаров" in txt)
    A.locator(".panel details summary", has_text="Журнал").click(); A.wait_for_timeout(200)
    j = A.locator(".panel details .hist").inner_text(); print("9 журнал:", j.replace("\n", " | ")[:220])
    A.screenshot(path=OUT + "/roles_owner_card.png", full_page=True); A.click(".panel button[data-close]")
    ef0 = [f for f in files if f.startswith("data/e-")][0]; print("10a в файле редактора:", [c.get("createdBy") for c in decrypt(ef0, epw)["clients"] if c["name"].startswith("ТЕСТ")])
    print("10 новый клиент от редактора у владельца:", A.evaluate("(JSON.parse(localStorage.getItem('wayteko.clients.v1')).find(c=>c.name==='ТЕСТ Новый от Анны')||{}).createdBy"))
    A.wait_for_timeout(3000)
    main = decrypt("data/app.enc.json", PW); ef = [f for f in files if f.startswith("data/e-")][0]; ed = decrypt(ef, epw)
    print("11 общая копия: редакторов", len(main.get("editors", [])), "| в копии редактора задач нет:", "tasks" not in ed, "| касаний АЗИАН в копии редактора:", len([c for c in ed["clients"] if "АЗИАН" in c["name"].upper()][0]["touches"]))
    G = dev(b); A.click("#dataBtn"); A.fill("#gname", "Гость Тест"); A.click("#guestForm button[type=submit]"); A.wait_for_timeout(3000)
    gpw = re.search(r"Пароль: (G-[A-Z0-9-]+)", A.locator(".panel").inner_text()).group(1); A.click(".panel button[data-close]")
    login(G, "Пётр Гостев", gpw); print("12 гость вошёл как гость:", G.evaluate("localStorage.getItem('wayteko.role.v1')"), "| плашка:", G.locator("#guestPill").inner_text())
    E2 = dev(b); E2.add_init_script("try{localStorage.setItem('wayteko.pw.v1','" + PW + "')}catch(e){}"); E2.goto("http://localhost:8768/"); E2.wait_for_timeout(2500)
    print("13 старое устройство без имени — просит имя:", E2.locator("#nameForm").count() == 1)
    b.close()
json.dump({"files": files, "epw": epw}, open(OUT + "/rolefiles.json", "w"))
print("ERRORS:", errs or "нет")
