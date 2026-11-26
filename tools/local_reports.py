import os, sys, json, base64, hashlib, datetime as dt, subprocess
from pathlib import Path
from collections import Counter
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
pw = os.environ["WAYTEKO_PW"].encode()
b = base64.b64decode
e = lambda x: base64.b64encode(x).decode()
box = json.loads(Path("data/app.enc.json").read_text())
key = hashlib.pbkdf2_hmac("sha256", pw, b(box["salt"]), box["iter"], 32)
app = json.loads(AESGCM(key).decrypt(b(box["iv"]), b(box["ct"]), None))
day = dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).date()
iso = day.isoformat()
tom = (day + dt.timedelta(days=1)).isoformat()
clients = [c for c in app["clients"] if c.get("temp") not in ("branch","refused") and c.get("id") not in (app.get("deleted") or [])]
def save(name, value):
    salt, iv = os.urandom(16), os.urandom(12)
    key = hashlib.pbkdf2_hmac("sha256", pw, salt, 250000, 32)
    ct = AESGCM(key).encrypt(iv, value.encode(), None)
    Path(sys.argv[1], name + ".enc.json").write_text(json.dumps({"v":1,"iter":250000,"salt":e(salt),"iv":e(iv),"ct":e(ct)}))
def line(c):
    return " — ".join(str(c.get(k) or "") for k in ("name","fio","phone","next","plan"))
schedule = os.environ.get("SCHEDULE","")
if not schedule or schedule.startswith("40"):
    due = sorted([c for c in clients if c.get("next") and c["next"] <= iso], key=lambda c:(c["next"],c.get("temp")!="hot"))
    from html import escape
    def clean(value, limit=280):
        text = " ".join(str(value or "").split())
        return escape(text if len(text) <= limit else text[:limit-1].rsplit(" ", 1)[0] + "…")
    def section(title, color, group):
        parts = [f'<h3 style="color:{color};border-bottom:2px solid {color};padding-bottom:5px">{title} ({len(group)})</h3>']
        for c in group:
            ts = [t for t in (c.get("touches") or []) if t and t.get("t")]
            last = ts[-1] if ts else {}
            note = clean(last.get("t") or c.get("intro") or "Нет записи")
            date = clean(last.get("d"))
            plan = clean(c.get("plan") or "Уточнить статус и согласовать следующий шаг (рекомендация)")
            icon = {"hot":"🔥","warm":"🌤️","cold":"❄️","dealer":"✅"}.get(c.get("temp"),"")
            parts.append(f'<p style="margin:10px 0"><b>{icon} {clean(c.get("name"))} — {clean(c.get("fio"))}</b> · {clean(c.get("phone"))}<br>Последнее касание {date}: {note}<br><b>Что сделать:</b> {plan}</p>')
        return "".join(parts)
    overdue = [c for c in due if c["next"] < iso]
    today = [c for c in due if c["next"] == iso]
    html = f'<div style="font:15px/1.4 Arial,sans-serif;background:#fff;color:#111;padding:12px"><h2>План касаний WAYTEKO на {day:%d.%m.%Y}</h2><p>Просрочено {len(overdue)} · на сегодня {len(today)}</p>'
    html += section("1. Просроченные касания", "#c62818", overdue)
    html += section("2. Созвоны на сегодня", "#d35400", today)
    html += '<p><a href="https://ezakharov1222-lgtm.github.io/Wayteko/">Открыть WAYTEKO</a></p></div>'
    save("morning-"+iso, html)
if not schedule or schedule.startswith("43"):
    counts = Counter(c.get("temp") for c in clients)
    touches = [(c.get("name"),t.get("t")) for c in clients for t in (c.get("touches") or []) if t.get("d")==iso]
    report = [f"Отчёт WAYTEKO {iso}", f"Клиентов: {len(clients)}", f"Касаний: {len(touches)}", str(dict(counts)), "Завтра:"] + [line(c) for c in clients if c.get("next")==tom] + ["Просрочено:"] + [line(c) for c in clients if c.get("next") and c["next"]<iso]
    save("evening-"+iso, "\n".join(report))
if not schedule or schedule.startswith("17"):
    save("tasks-"+iso, subprocess.check_output([sys.executable,"tools/tasks_report.py","data/app.enc.json",iso],text=True))
