import json, datetime as dt, pathlib
from playwright.sync_api import sync_playwright
APP = "file:///tmp/claude-0/-home-claude/afd04b57-3082-56bf-abd5-685c59d92c6c/scratchpad/app/index.html"
today = dt.date.today()
iso = lambda d: d.isoformat()
clients = [
 {"id":"a1","name":"Тест Альфа","temp":"hot","fio":"Иванов","phone":"+7 900 000-00-01","touches":[],"next":iso(today+dt.timedelta(days=1)),"created":"2026-10-01T00:00:00Z","meets":[{"id":"m1","d":iso(today+dt.timedelta(days=2)),"t":"14:00","place":"Офис клиента","note":"Подписание протокола","done":False}]},
 {"id":"b2","name":"Тест Бета","temp":"warm","touches":[],"next":iso(today+dt.timedelta(days=3)),"created":"2026-10-02T00:00:00Z","meets":[{"id":"m2","d":iso(today+dt.timedelta(days=10)),"t":"","place":"","note":"","done":False}]},
 {"id":"c3","name":"Тест Гамма","temp":"cold","touches":[],"next":iso(today+dt.timedelta(days=5)),"created":"2026-10-03T00:00:00Z","meets":[]},
]
errors = []
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width":390,"height":844}, device_scale_factor=1)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append("console: "+m.text) if m.type=="error" else None)
    pg.goto(APP)
    pg.evaluate("c => localStorage.setItem('wayteko.clients.v1', JSON.stringify(c))", clients)
    pg.reload(); pg.wait_for_timeout(400)
    # 1. предупреждение: только встреча через 2 дня (в окне 3 дней), через 10 — нет
    banner = pg.locator("#view .banner").inner_text()
    print("BANNER:", banner.replace("\n"," | "))
    assert "Тест Альфа" in banner and "Тест Бета" not in banner
    # 2. кнопка встречи на карточке: активная у Альфы, «назначить» у Гаммы
    print("BTN Альфа:", pg.locator("button.meet-on").first.inner_text())
    print("BTN неактивные:", [x.inner_text() for x in pg.locator("button.btn.small:not(.meet-on)").all() if "🤝" in x.inner_text()][:3])
    pg.screenshot(path="/tmp/claude-0/-home-claude/afd04b57-3082-56bf-abd5-685c59d92c6c/scratchpad/mt/today.png", full_page=False)
    # 3. назначить встречу клиенту Гамме через кнопку на карточке
    pg.locator("button[data-meet-open='c3']").first.click(); pg.wait_for_timeout(300)
    pg.locator("#m_date").fill(iso(today+dt.timedelta(days=3)))
    pg.locator("#m_time").fill("11:30")
    pg.locator("#m_place").fill("Zoom")
    pg.locator("#m_note").fill("Обсудить цены")
    pg.locator("#meetForm button[type=submit]").click(); pg.wait_for_timeout(400)
    stored = json.loads(pg.evaluate("localStorage.getItem('wayteko.clients.v1')"))
    gamma = [c for c in stored if c["id"]=="c3"][0]
    print("NEW MEET:", gamma["meets"])
    assert len(gamma["meets"])==1 and gamma["meets"][0]["d"]==iso(today+dt.timedelta(days=3))
    # 4. Гамма — встреча через 3 дня должна попасть в предупреждение
    pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
    banner2 = pg.locator("#view .banner").inner_text()
    print("BANNER2:", banner2.replace("\n"," | "))
    assert "Тест Гамма" in banner2
    # 5. отметить встречу Альфы состоявшейся
    pg.locator("#view .banner").first.wait_for()
    pg.locator("button[data-meet-done='m1']").first.click(); pg.wait_for_timeout(300)
    stored = json.loads(pg.evaluate("localStorage.getItem('wayteko.clients.v1')"))
    alpha = [c for c in stored if c["id"]=="a1"][0]
    print("ALPHA done:", alpha["meets"][0]["done"])
    assert alpha["meets"][0]["done"] is True
    pg.wait_for_timeout(200)
    print("BANNER3:", pg.locator("#view .banner").inner_text().replace("\n"," | ") if pg.locator("#view .banner").count() else "нет")
    # 6. перезагрузка — данные сохраняются
    pg.reload(); pg.wait_for_timeout(300)
    print("после перезагрузки meet-on кнопок:", pg.locator("button.meet-on").count())
    pg.screenshot(path="/tmp/claude-0/-home-claude/afd04b57-3082-56bf-abd5-685c59d92c6c/scratchpad/mt/after.png", full_page=False)
    # 7. карточка с кнопкой «В календарь» (экспорт .ics)
    pg.locator("button[data-meet-open='c3']").first.click(); pg.wait_for_timeout(300)
    print("ICS кнопка есть:", pg.locator("button[data-meet-ics]").count())
    b.close()
print("ERRORS:", errors or "нет")
