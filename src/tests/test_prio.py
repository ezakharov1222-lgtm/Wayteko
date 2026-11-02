import json, sys
from playwright.sync_api import sync_playwright
PW = open(sys.argv[1]).read().strip(); OUT = sys.argv[2]; errs = []; H = {"Access-Control-Allow-Origin": "*"}
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width": 390, "height": 900}).new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("https://api.github.com/**", lambda r: r.fulfill(status=404, json={}, headers=H)); pg.route("https://ntfy.sh/**", lambda r: r.fulfill(status=200, body="", headers=H))
    pg.goto("http://localhost:8766/"); pg.wait_for_timeout(1200); pg.fill("#pw", PW); pg.click("#pwForm button[type=submit]"); pg.wait_for_timeout(4000)
    pg.click("#tabs button[data-tab=tasks]"); pg.wait_for_timeout(300)
    print("1 кнопки срочности:", pg.locator(".prio-pick button").all_inner_texts(), "| выбрана по умолчанию:", pg.locator(".prio-pick button[aria-pressed=true]").inner_text())
    def add(text, prio):
        pg.fill("#tk_text", text)
        if prio: pg.click(f".prio-pick button[data-tprio={prio}]")
        pg.click("#taskForm button[type=submit]"); pg.wait_for_timeout(300)
    add("Обычная задача", None); add("Важная задача", "high"); add("Срочная задача", "urgent")
    print("2 после добавления срочность сбросилась на:", pg.locator(".prio-pick button[aria-pressed=true]").inner_text())
    order = [(r.locator(".pbadge").inner_text(), r.locator(".ttext").inner_text()) for r in pg.locator("#view .task").all()]
    print("3 порядок в списке:", order)
    print("4 счётчик на вкладке:", pg.locator("#tasksBadge").inner_text(), "| ярко-красный:", pg.locator("#tasksBadge.hot").count() == 1)
    pg.screenshot(path=OUT + "/prio_tasks.png", full_page=True)
    pg.locator("#view .task", has_text="Обычная задача").locator(".pbadge").click(); pg.wait_for_timeout(200)
    print("5 нажатие на значок: Обычная ->", pg.locator("#view .task", has_text="Обычная задача").locator(".pbadge").inner_text())
    pg.locator("#view .task", has_text="Срочная задача").locator("button[data-tdone]").click(); pg.wait_for_timeout(200)
    print("6 срочная выполнена — ушла вниз:", [r.locator(".ttext").inner_text() for r in pg.locator("#view .task").all()][-1])
    pg.locator("#view .task", has_text="Срочная задача").locator("button[data-tdone]").click(); pg.wait_for_timeout(200)
    pg.click("#tabs button[data-tab=today]"); pg.wait_for_timeout(300)
    print("7 плашка на «Сегодня»:", pg.locator(".ubanner").inner_text().replace("\n", " ") if pg.locator(".ubanner").count() else "нет")
    pg.screenshot(path=OUT + "/prio_today.png")
    pg.click(".ubanner"); pg.wait_for_timeout(300)
    print("8 нажатие на плашку открывает:", pg.evaluate("[...document.querySelectorAll('#tabs button')].find(b=>b.getAttribute('aria-selected')==='true').innerText"))
    b.close()
print("ERRORS:", errs or "нет")
