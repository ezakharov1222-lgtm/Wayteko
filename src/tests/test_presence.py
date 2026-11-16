import sys, json, time, re
src = open(sys.argv[3]).read().split("with sync_playwright() as p:")[0].replace("localhost:8770","localhost:8771")
src = src.replace('''pg.route("https://ntfy.sh/**", lambda r: r.fulfill(status=200, body="", headers=H)); return pg''', '''pg.route("https://ntfy.sh/**", ntfy); return pg''')
topics = {}
def ntfy(route):
    req = route.request; u = req.url
    if req.method == "OPTIONS": return route.fulfill(status=204, headers=H)
    t = u.split("ntfy.sh/")[1].split("/")[0].split("?")[0]
    if req.method == "POST": topics.setdefault(t, []).append({"event": "message", "time": int(time.time()), "message": req.post_data or ""}); return route.fulfill(status=200, body="{}", headers=H)
    return route.fulfill(status=200, body="\n".join(json.dumps(x) for x in topics.get(t, [])), headers=H)
exec(src)
with sync_playwright() as p:
    b = p.chromium.launch(); O = OUT + "/shots/"
    A = dev(b); login(A, "", PW); A.fill("#uname", "Евгений Захаров"); A.click("#nameForm button[type=submit]"); A.wait_for_timeout(300)
    A.click("#dataBtn"); A.fill("#ghtok", "github_pat_TEST"); A.click("#ghForm button[type=submit]"); A.wait_for_timeout(3500)
    A.fill("#ename", "Татьяна Ширшова"); A.click("#editorForm button[type=submit]"); A.wait_for_timeout(3500)
    epw = re.search(r"Пароль: (E-[A-Z0-9-]+)", A.locator(".panel").inner_text()).group(1)
    A.wait_for_timeout(1500)
    print("1 до входа:", A.locator(".panel .mrow", has_text="Татьяна").first.inner_text().split("\n")[0])
    A.click(".panel button[data-close]")
    E = dev(b); login(E, "", epw); E.wait_for_timeout(1500)
    print("2 ntfy сигналов от редактора:", sum(len(v) for v in topics.values()))
    A.click("#dataBtn"); A.wait_for_timeout(2500)
    print("3 уведомление у владельца:", A.locator("#notices").inner_text().replace("\n", " | "))
    print("4 статус в списке:", A.locator(".panel .mrow", has_text="Татьяна").first.inner_text().split("\n")[0], "| шапка:", A.locator("#guestPill").inner_text())
    A.click(".panel button[data-close]"); A.wait_for_timeout(300); A.screenshot(path=O + "pres_notice.png")
    print("5 у редактора уведомлений нет:", E.locator("#notices").is_hidden())
    A.reload(); A.wait_for_timeout(3000)
    print("6 после перезагрузки уведомление висит:", A.locator("#notices .notice").count())
    A.click("[data-ndel='0']"); A.wait_for_timeout(300); print("7 после ✕:", A.locator("#notices .notice").count())
    A.click("#dataBtn"); A.wait_for_timeout(2500); print("8 повторного уведомления нет:", A.locator("#notices .notice").count())
    E.close(); time.sleep(1)
    A.click(".panel button[data-close]"); A.click("#dataBtn"); A.wait_for_timeout(2500)
    print("9 после выхода редактора:", A.locator(".panel .mrow", has_text="Татьяна").first.inner_text().split("\n")[0])
    A.locator(".panel .box", has_text="Доступ с редактированием").screenshot(path=O + "pres_row.png")
    b.close()
print("ERRORS:", errs or "нет")
