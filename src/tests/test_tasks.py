import json, sys, base64, time, re, hashlib
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
    pg = b.new_context(viewport={"width": 390, "height": 900}).new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("https://api.github.com/**", gh); pg.route("https://ntfy.sh/**", lambda r: r.fulfill(status=200, body="", headers=H)); return pg
def login(pg, pw):
    pg.goto("http://localhost:8766/"); pg.wait_for_timeout(1200); pg.fill("#pw", pw); pg.click("#pwForm button[type=submit]"); pg.wait_for_timeout(4000)
def decrypt(path, pw):
    box = json.loads(files[path]); d = lambda s: base64.b64decode(s)
    k = hashlib.pbkdf2_hmac("sha256", pw.encode(), d(box["salt"]), box["iter"], 32)
    return json.loads(AESGCM(k).decrypt(d(box["iv"]), d(box["ct"]), None))
def add(pg, client, text):
    pg.fill("#tk_client", client); pg.fill("#tk_text", text); pg.click("#taskForm button[type=submit]"); pg.wait_for_timeout(300)
tasks_on_screen = lambda pg: pg.locator("#view .task .ttext").all_inner_texts()
with sync_playwright() as p:
    b = p.chromium.launch()
    A = dev(b); login(A, PW)
    A.click("#dataBtn"); A.fill("#ghtok", "github_pat_TEST"); A.click("#ghForm button[type=submit]"); A.wait_for_timeout(4000)
    A.fill("#gname", "Иван"); A.click("#guestForm button[type=submit]"); A.wait_for_timeout(4000)
    gpw = re.search(r"Пароль: (G-[A-Z0-9-]+)", A.locator(".panel").inner_text()).group(1)
    A.click(".panel button[data-close]")
    cname = A.locator("#view .card button.name").first.inner_text()
    A.click("#tabs button[data-tab=tasks]"); A.wait_for_timeout(300)
    print("1 вкладка «Задачи» у владельца открыта:", A.locator("#taskForm").count() == 1)
    add(A, cname, "Отправить КП"); add(A, "", "Подготовить отчёт для директора"); add(A, "Новая компания", "Позвонить по рекомендации")
    print("2 задачи на сегодня:", tasks_on_screen(A), "| клиент кликабелен:", A.locator("#view .task button.name").first.inner_text() == cname, "| счётчик:", A.locator("#tasksBadge").inner_text())
    A.locator("#view .task", has_text="Подготовить отчёт").locator("button[data-tdone]").click(); A.wait_for_timeout(300)
    print("3 отмечена выполненной (зачёркнута):", A.locator("#view .task.done .ttext").all_inner_texts(), "| счётчик:", A.locator("#tasksBadge").inner_text())
    A.click("button[data-tday='-1']"); add(A, "", "Вчерашняя задача"); A.click("button[data-tday='1']"); A.click("button[data-tday='1']"); add(A, "", "Задача на завтра")
    A.click("button[data-tday='0']"); A.wait_for_timeout(300)
    print("4 блок «Не выполнено раньше»:", A.locator("#view h2.sec", has_text="Не выполнено").count() == 1, "| счётчик (сегодня + просрочено):", A.locator("#tasksBadge").inner_text())
    A.locator("#view .task", has_text="Вчерашняя").locator("button[data-tmove]").click(); A.wait_for_timeout(300)
    print("5 перенесена на сегодня:", "Вчерашняя задача" in tasks_on_screen(A), "| блок просроченных исчез:", A.locator("#view h2.sec", has_text="Не выполнено").count() == 0)
    A.locator("#view .task", has_text="Позвонить по рекомендации").locator("button[data-tdel]").click(); A.wait_for_timeout(300)
    print("6 после удаления:", tasks_on_screen(A))
    A.screenshot(path=OUT + "/tasks_owner.png", full_page=True)
    A.locator("#view .task button.name").first.click(); A.wait_for_timeout(300)
    print("7 клик по клиенту открывает его карточку:", A.locator(".panel h2").inner_text() == cname); A.click(".panel button[data-close]")
    A.wait_for_timeout(5000)

    B = dev(b); login(B, PW); B.wait_for_timeout(4000)
    B.click("#tabs button[data-tab=tasks]"); B.wait_for_timeout(300)
    print("8 второе устройство владельца видит задачи:", tasks_on_screen(B))
    sh = decrypt("data/app.enc.json", PW)
    print("9 задачи в общей копии владельца:", len([t for t in sh.get("tasks", []) if not t.get("del")]))
    gpath = [f for f in files if f.startswith("data/g-")][0]
    gc = decrypt(gpath, gpw)
    print("10 гостевая копия: ключи", sorted(gc.keys()), "| задач в ней:", "tasks" in gc, "| текст задач встречается:", "Отправить КП" in json.dumps(gc, ensure_ascii=False))

    G = dev(b); G.add_init_script("try{localStorage.setItem('vcrm-tab','tasks')}catch(e){}"); login(G, gpw)
    print("11 гость: вкладка «Задачи» видна:", G.locator("#tabs button[data-tab=tasks]").is_visible(), "| открылась вкладка:", G.evaluate("[...document.querySelectorAll('#tabs button')].find(b=>b.getAttribute('aria-selected')==='true').innerText"),
          "| задачи в памяти гостя:", G.evaluate("localStorage.getItem('wayteko.tasks.v1')"), "| форма задач:", G.locator("#taskForm").count())
    G.evaluate("() => { const b = document.querySelector('#tabs button[data-tab=tasks]'); b && b.click(); }"); G.wait_for_timeout(300)
    print("12 гость нажал скрытую вкладку через код — форма задач:", G.locator("#taskForm").count(), "| текст задач на экране:", "Отправить КП" in G.locator("body").inner_text())
    b.close()
print("ERRORS:", errs or "нет")
