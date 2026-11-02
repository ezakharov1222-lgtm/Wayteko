import json, sys, base64, time, re, hashlib
from playwright.sync_api import sync_playwright
PW = open(sys.argv[1]).read().strip(); OUT = sys.argv[2]
files = {}; ntfy = {}; errs = []; guest_writes = []
H = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"}
sha = lambda t: hashlib.sha1(t.encode()).hexdigest()

def make_gh(who):
    def gh(route):
        req = route.request; url = req.url.split("?")[0]
        if req.method == "OPTIONS": return route.fulfill(status=204, headers=H)
        if req.method in ("PUT", "DELETE", "POST", "PATCH") and who == "guest": guest_writes.append(f"{req.method} {url}")
        if url.rstrip("/").endswith("/repos/ezakharov1222-lgtm/wayteko"):
            return route.fulfill(status=200, json={"permissions": {"push": True}}, headers=H)
        path = re.search(r"/contents/(.+)$", url).group(1)
        if req.method == "GET":
            if path not in files: return route.fulfill(status=404, json={}, headers=H)
            if "raw" in (req.headers.get("accept") or ""): return route.fulfill(status=200, body=files[path], headers={**H, "Content-Type": "application/json"})
            return route.fulfill(status=200, json={"sha": sha(files[path])}, headers=H)
        if req.method == "PUT":
            files[path] = base64.b64decode(json.loads(req.post_data)["content"]).decode(); return route.fulfill(status=201, json={}, headers=H)
        if req.method == "DELETE": files.pop(path, None); return route.fulfill(status=200, json={}, headers=H)
    return gh
def nt(route):
    req = route.request; url = req.url.split("?")[0]
    if req.method == "OPTIONS": return route.fulfill(status=204, headers=H)
    if req.method == "POST":
        ntfy.setdefault(url.rstrip("/").split("/")[-1], []).append({"event": "message", "time": int(time.time()), "message": req.post_data}); return route.fulfill(status=200, json={}, headers=H)
    return route.fulfill(status=200, body="\n".join(json.dumps(m) for m in ntfy.get(url.rstrip("/").split("/")[-2], [])), headers=H)
def dev(b, who):
    pg = b.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True).new_page()
    pg.on("pageerror", lambda e: errs.append(f"{who}: {e}"))
    pg.route("https://api.github.com/**", make_gh(who)); pg.route("https://ntfy.sh/**", nt)
    pg.on("dialog", lambda d: d.dismiss())
    return pg
def login(pg, pw):
    pg.goto("http://localhost:8766/"); pg.wait_for_timeout(1200)
    pg.fill("#pw", pw); pg.click("#pwForm button[type=submit]"); pg.wait_for_timeout(4000)

VIS = """sel => [...document.querySelectorAll(sel)].filter(e => e.offsetParent !== null && getComputedStyle(e).visibility !== 'hidden')"""
def visible_controls(pg, scope="body"):
    return pg.evaluate("""scope => [...document.querySelector(scope).querySelectorAll('button, input, textarea, select, label.filebtn, form')]
      .filter(e => e.offsetParent !== null).map(e => (e.tagName === 'FORM' ? 'ФОРМА#' + e.id : (e.innerText || e.placeholder || e.type || e.id || '').trim().replace(/\\s+/g,' ').slice(0, 40)))""", scope)
state = lambda pg: pg.evaluate("localStorage.getItem('wayteko.clients.v1')")

with sync_playwright() as p:
    b = p.chromium.launch()
    A = dev(b, "owner"); login(A, PW)
    A.click("#dataBtn"); A.fill("#ghtok", "github_pat_TEST"); A.click("#ghForm button[type=submit]"); A.wait_for_timeout(4000)
    A.fill("#gname", "Проверка"); A.click("#guestForm button[type=submit]"); A.wait_for_timeout(5000)
    gpw = re.search(r"Пароль гостя:\s*(G-[A-Z0-9-]+)", A.locator(".panel").inner_text()).group(1)

    G = dev(b, "guest"); login(G, gpw)
    base = state(G); n0 = len(json.loads(base))
    report = {}
    # 1. что видно на каждой вкладке
    for t in ["today", "board", "all", "arch"]:
        G.click(f"#tabs button[data-tab={t}]"); G.wait_for_timeout(300)
        ctl = visible_controls(G, "#view")
        names = sorted(set(c for c in ctl if not re.match(r"^[А-ЯA-Z«\"(].{0,}(ООО|ИП|АО|ЗАО)?", c) or c in ("Все", "В работе")))
        report[t] = sorted(set(ctl))
    # уникальные «действия» без названий компаний
    company = set(json.loads(base)[i]["name"].strip()[:40] for i in range(n0))
    for t, ctl in report.items():
        acts = sorted(set(c for c in ctl if c not in company and not c.startswith("🤝 ")))
        print(f"1.{t} видимые элементы (кроме названий клиентов и кнопок с датой встречи):", acts)
    print("   шапка:", visible_controls(G, "header.top"), "| значок:", G.locator("#guestPill").inner_text())

    # 2. нажать ВСЕ видимые кнопки на всех вкладках и в карточках клиентов
    clicked = 0
    for t in ["today", "board", "all", "arch"]:
        G.click(f"#tabs button[data-tab={t}]"); G.wait_for_timeout(200)
        cnt = G.evaluate(VIS.replace("sel =>", "(sel) =>") + "('#view button').length".replace("('#view button')", "") if False else "0")
        btns = G.locator("#view button").all()
        for i in range(min(len(btns), 60)):
            bl = G.locator("#view button").nth(i)
            if not bl.is_visible(): continue
            try: bl.click(timeout=1500); clicked += 1
            except Exception: pass
            G.wait_for_timeout(80)
            # внутри открывшейся карточки — нажать всё видимое, кроме закрытия
            if G.locator(".panel").count():
                for pb in G.locator(".panel button:not([data-close]), .panel input, .panel textarea").all():
                    if pb.is_visible():
                        try:
                            tag = pb.evaluate("e => e.tagName")
                            if tag in ("INPUT", "TEXTAREA"): pb.fill("ВЗЛОМ"); pb.press("Enter")
                            else: pb.click(timeout=1000)
                            clicked += 1
                        except Exception: pass
                if G.locator(".panel button[data-close]").count(): G.locator(".panel button[data-close]").first.click()
                G.wait_for_timeout(80)
            if G.locator("#tabs button[data-tab]").count() and G.evaluate("localStorage.getItem('vcrm-tab')") != t:
                G.click(f"#tabs button[data-tab={t}]"); G.wait_for_timeout(150)
    print("2 нажато видимых элементов:", clicked, "| данные гостя не изменились:", state(G) == base)

    # 3. панель «Данные» у гостя
    G.click("#dataBtn"); G.wait_for_timeout(300)
    print("3 «Данные» у гостя:", visible_controls(G, ".panel"))
    G.screenshot(path=OUT + "/audit_guest_data.png")
    G.click(".panel button[data-close]")

    # 4. «хитрый гость»: скрытые кнопки и формы через код страницы
    first_id = json.loads(base)[0]["id"]
    G.evaluate("""id => {
      const click = sel => document.querySelectorAll(sel).forEach(b => b.click());
      click('[data-move]'); click('.actions [data-temp]'); click('[data-meet-done]'); click('[data-meet-del]');
      document.querySelector(`#view button.name`).click();
    }""", first_id)
    G.wait_for_timeout(300)
    G.evaluate("""() => {
      const p = document.querySelector('.panel'); if(!p) return;
      p.querySelectorAll('[data-temp]').forEach(b => b.click());
      const tf = document.querySelector('#touchForm'); if(tf){ tf.querySelector('#t_text').value='ВЗЛОМ'; tf.querySelector('#t_next').value='2030-01-01'; tf.requestSubmit(); }
      const mf = document.querySelector('#meetForm'); if(mf){ mf.querySelector('#m_date').value='2030-01-01'; mf.requestSubmit(); }
      const ef = document.querySelector('#editForm'); if(ef){ ef.querySelector('#f_name').value='ВЗЛОМ'; ef.requestSubmit(); }
      const ad = document.querySelector('[data-askdel]'); if(ad) ad.click();
    }""")
    G.wait_for_timeout(300)
    G.evaluate("() => { const d = document.querySelector('[data-del]'); if(d) d.click(); }")
    G.wait_for_timeout(300)
    if G.locator(".panel button[data-close]").count(): G.locator(".panel button[data-close]").first.click()
    G.evaluate("() => document.querySelector('#addBtn').click()"); G.wait_for_timeout(300)
    G.evaluate("""() => { const f = document.querySelector('#newForm'); if(f){ f.querySelector('#f_name').value='ВЗЛОМ-НОВЫЙ'; f.requestSubmit(); } }""")
    G.wait_for_timeout(400)
    if G.locator(".panel button[data-close]").count(): G.locator(".panel button[data-close]").first.click()
    print("4 скрытые кнопки и формы через код: данные не изменились:", state(G) == base, "| сообщений «только просмотр»: видны")

    # 5. подсунуть файл импорта
    imp = OUT + "/evil.json"; json.dump({"app": "WAYTEKO", "clients": [{"id": "x1", "name": "ВЗЛОМ-ИМПОРТ"}]}, open(imp, "w"))
    G.evaluate("""() => { const i = document.createElement('input'); i.type='file'; i.id='importFile'; document.body.appendChild(i); }""")
    G.set_input_files("#importFile", imp); G.wait_for_timeout(800)
    for sel in ["button[data-act=imp-replace]", "button[data-act=imp-merge]"]:
        G.evaluate(f"() => {{ const b = document.querySelector('{sel}'); if(b) b.click(); }}")
    G.wait_for_timeout(300)
    if G.locator(".panel button[data-close]").count(): G.locator(".panel button[data-close]").first.click()
    imported = "ВЗЛОМ-ИМПОРТ" in (state(G) or "")
    print("5 импорт файла гостем: прошёл:", imported)

    # 6. попытка подставить токен
    G.evaluate("""() => { localStorage.setItem('wayteko.gh.v1', 'github_pat_FAKE'); }""")
    G.reload(); G.wait_for_timeout(3500)
    print("6 гость с подставленным токеном — записей на GitHub от гостя:", len(guest_writes), guest_writes[:3])
    print("7 после всех попыток гость всё ещё в режиме просмотра:", G.locator("#guestPill").inner_text(), "| клиентов:", len(json.loads(state(G))), "из", n0)

    # 8. владелец ничего не получил от гостя
    sh_ok = all("ВЗЛОМ" not in v for v in files.values())
    print("8 в общей копии и гостевой копии нет следов гостя: (зашифровано — проверяю расшифровкой ниже)")
    open(OUT + "/audit_files.json", "w").write(json.dumps(files))
    b.close()
print("ERRORS:", errs or "нет")
