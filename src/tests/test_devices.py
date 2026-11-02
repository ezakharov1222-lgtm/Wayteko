import json, sys, base64, time, re, hashlib, base64 as b64
from playwright.sync_api import sync_playwright
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
PW = open(sys.argv[1]).read().strip(); OUT = sys.argv[2]
files = {}; ntfy = {}; errs = []; stats = {"put": 0, "conflict": 0}
H = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"}
sha = lambda t: hashlib.sha1(t.encode()).hexdigest()

def gh(route):
    req = route.request; url = req.url.split("?")[0]
    if req.method == "OPTIONS": return route.fulfill(status=204, headers=H)
    if url.rstrip("/").endswith("/repos/ezakharov1222-lgtm/wayteko"):
        return route.fulfill(status=200, json={"permissions": {"push": True}}, headers=H)
    path = re.search(r"/contents/(.+)$", url).group(1)
    if req.method == "GET":
        if path not in files: return route.fulfill(status=404, json={}, headers=H)
        if "raw" in (req.headers.get("accept") or ""):
            return route.fulfill(status=200, body=files[path], headers={**H, "Content-Type": "application/json"})
        return route.fulfill(status=200, json={"sha": sha(files[path])}, headers=H)
    if req.method == "PUT":
        d = json.loads(req.post_data)
        if path in files and d.get("sha") != sha(files[path]):
            stats["conflict"] += 1; return route.fulfill(status=409, json={"message": "sha mismatch"}, headers=H)
        files[path] = base64.b64decode(d["content"]).decode(); stats["put"] += 1
        return route.fulfill(status=201, json={}, headers=H)
    if req.method == "DELETE":
        files.pop(path, None); return route.fulfill(status=200, json={}, headers=H)

def nt(route):
    req = route.request; url = req.url.split("?")[0]
    if req.method == "OPTIONS": return route.fulfill(status=204, headers=H)
    if req.method == "POST":
        ntfy.setdefault(url.rstrip("/").split("/")[-1], []).append({"event": "message", "time": int(time.time()), "message": req.post_data})
        return route.fulfill(status=200, json={}, headers=H)
    return route.fulfill(status=200, body="\n".join(json.dumps(m) for m in ntfy.get(url.rstrip("/").split("/")[-2], [])), headers=H)

def dev(b):
    pg = b.new_context(viewport={"width": 390, "height": 844}).new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("https://api.github.com/**", gh); pg.route("https://ntfy.sh/**", nt)
    return pg
def login(pg, pw):
    pg.goto("http://localhost:8766/"); pg.wait_for_timeout(1200)
    pg.fill("#pw", pw); pg.click("#pwForm button[type=submit]"); pg.wait_for_timeout(4000)
def touch(pg, name, text):
    pg.locator("#view button.name", has_text=name).first.click(); pg.wait_for_timeout(300)
    pg.fill("#t_text", text); pg.locator("button[data-setnext]").first.click()
    pg.click("#touchForm button[type=submit]"); pg.wait_for_timeout(200); pg.click(".panel button[data-close]")
def has(pg, name, text):
    pg.locator("#view button.name", has_text=name).first.click(); pg.wait_for_timeout(300)
    ok = text in pg.locator(".panel").inner_text(); pg.click(".panel button[data-close]"); return ok
def devsync(pg):
    pg.click("#dataBtn"); pg.click("button[data-act=devsync]"); pg.wait_for_timeout(3000); pg.click(".panel button[data-close]")
def shared():
    box = json.loads(files["data/app.enc.json"]); d = lambda s: b64.b64decode(s)
    key = hashlib.pbkdf2_hmac("sha256", PW.encode(), d(box["salt"]), box["iter"], 32)
    return json.loads(AESGCM(key).decrypt(d(box["iv"]), d(box["ct"]), None))

with sync_playwright() as p:
    b = p.chromium.launch()
    A = dev(b); login(A, PW)
    A.click("#dataBtn"); A.fill("#ghtok", "github_pat_TEST"); A.click("#ghForm button[type=submit]"); A.wait_for_timeout(4000)
    A.fill("#gname", "Иван"); A.click("#guestForm button[type=submit]"); A.wait_for_timeout(5000)
    gpw = re.search(r"Пароль гостя:\s*(G-[A-Z0-9-]+)", A.locator(".panel").inner_text()).group(1)
    A.click(".panel button[data-close]")
    names = A.locator("#view .card button.name").all_inner_texts()
    n1, n2, n3 = names[0], names[1], names[2]
    print("1 телефон: токен подключён, гостевой доступ создан")

    B = dev(b); login(B, PW); B.wait_for_timeout(4000)
    tokB = B.evaluate("localStorage.getItem('wayteko.gh.v1')"); gB = json.loads(B.evaluate("localStorage.getItem('wayteko.guest.v1')") or "{}")
    print("2 новый компьютер после входа: токен получен:", bool(tokB), "| гостевой пароль известен:", gB.get("pw") == gpw)

    touch(A, n1, "С ТЕЛЕФОНА"); A.wait_for_timeout(5000)
    devsync(B)
    print("3 компьютер видит запись с телефона:", has(B, n1, "С ТЕЛЕФОНА"))

    touch(B, n2, "С КОМПЬЮТЕРА")
    B.locator("#view button.name", has_text=n3).first.click(); B.wait_for_timeout(300)
    B.click("button[data-askdel]"); B.click("button[data-del]"); B.wait_for_timeout(5000)
    devsync(A)
    print("4 телефон видит запись с компьютера:", has(A, n2, "С КОМПЬЮТЕРА"), "| удалённый на компьютере клиент исчез на телефоне:", A.locator("#view button.name", has_text=n3).count() == 0)

    # одновременные правки на двух устройствах
    names2 = A.locator("#view .card button.name").all_inner_texts()
    n4, n5 = [x for x in names2 if x not in (n1, n2)][:2]
    touch(A, n4, "ОДНОВРЕМЕННО-ТЕЛЕФОН"); touch(B, n5, "ОДНОВРЕМЕННО-КОМПЬЮТЕР"); A.wait_for_timeout(9000)
    sh = shared(); byname = {c["name"]: c for c in sh["clients"]}
    t = lambda n: " ".join(x["t"] for x in byname[n].get("touches", []))
    print("5 общая копия после одновременных правок: обе сохранились:", "ОДНОВРЕМЕННО-ТЕЛЕФОН" in t(n4) and "ОДНОВРЕМЕННО-КОМПЬЮТЕР" in t(n5),
          "| конфликтов версий отработано:", stats["conflict"], "| удалённый в копии:", n3 not in byname)

    G = dev(b); login(G, gpw)
    print("6 гость видит правки с обоих устройств:", has(G, n1, "С ТЕЛЕФОНА") and has(G, n2, "С КОМПЬЮТЕРА"), "| гость в режиме просмотра:", G.locator("#guestPill").inner_text())
    B.click("#dataBtn"); B.wait_for_timeout(3000)
    print("7 компьютер (без ручного токена) видит гостя:", re.search(r"Статус:\s*([^\n]+)", B.locator(".panel").inner_text()).group(1))
    B.screenshot(path=OUT + "/dev_B_panel.png")
    b.close()
print("ERRORS:", errs or "нет")
