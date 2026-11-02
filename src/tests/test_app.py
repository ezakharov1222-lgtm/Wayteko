import subprocess, time, sys
from playwright.sync_api import sync_playwright
SP="/tmp/claude-0/-home-claude/afd04b57-3082-56bf-abd5-685c59d92c6c/scratchpad"
srv=subprocess.Popen([sys.executable,"-m","http.server","8765","-d",f"{SP}/app"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1)
errs=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,is_mobile=True,has_touch=True)
    pg=ctx.new_page(); pg.on("pageerror",lambda e: errs.append(str(e))); pg.on("console",lambda m: m.type=="error" and errs.append(m.text))
    pg.goto("http://localhost:8765/"); pg.wait_for_timeout(800)
    print("welcome:", pg.locator(".welcome h2").inner_text())
    pg.screenshot(path=f"{SP}/shot_welcome.png")
    pg.set_input_files("#importFile0", f"{SP}/WAYTEKO_база_23.10.2026.json"); pg.wait_for_timeout(500)
    print("stats:", pg.locator("#stats").inner_text().replace("\n"," | "))
    print("banner:", pg.locator("#banner").inner_text())
    print("cards on today:", pg.locator(".card").count())
    pg.screenshot(path=f"{SP}/shot_today.png")
    # записать касание первому клиенту
    first=pg.locator(".card .name").first.inner_text()
    pg.locator(".card [data-focus]").first.click(); pg.wait_for_timeout(300)
    pg.fill("#t_text","ТЕСТ: договорились созвониться"); pg.locator("[data-setnext]").first.click()
    pg.locator("#touchForm button[type=submit]").click(); pg.wait_for_timeout(300)
    print("after touch toast:", pg.locator("#toast").inner_text(), "| ics btn:", pg.locator("[data-ics]").count())
    pg.screenshot(path=f"{SP}/shot_panel.png", full_page=False)
    pg.locator(".panel button[data-close]").click()
    # перезагрузка — данные остаются
    pg.reload(); pg.wait_for_timeout(600)
    n=pg.evaluate("JSON.parse(localStorage.getItem('wayteko.clients.v1')).length")
    has=pg.evaluate("JSON.parse(localStorage.getItem('wayteko.clients.v1')).some(c=>(c.touches||[]).some(t=>t.t.startsWith('ТЕСТ')))")
    print("after reload clients:", n, "test touch kept:", has, "| first was:", first)
    # панель данных и вкладки
    pg.click("#dataBtn"); pg.wait_for_timeout(300); pg.screenshot(path=f"{SP}/shot_data.png")
    pg.locator(".panel button[data-close]").click()
    for t in ("board","all","arch"):
        pg.click(f'[data-tab="{t}"]'); pg.wait_for_timeout(200)
    print("arch cards:", pg.locator(".card").count())
    sw=pg.evaluate("navigator.serviceWorker.getRegistration().then(r=>!!r)")
    print("service worker:", sw)
    # оффлайн
    pg.wait_for_timeout(800); ctx.set_offline(True); pg.reload(); pg.wait_for_timeout(600)
    print("offline title:", pg.locator(".brand h1").inner_text(), "| clients:", pg.locator("#stats").inner_text().split("\n")[0])
    b.close()
finally:
  srv.terminate()
print("errors:", errs)
