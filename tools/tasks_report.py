"""Отчёт о задачах дня (личные задачи владельца) по общей копии приложения.
python3 tools/tasks_report.py data/app.enc.json ГГГГ-ММ-ДД
Пароль — из WAYTEKO_PW. Печатает готовый текст письма."""
import os, sys, json, base64, hashlib, datetime as dt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

path, day = sys.argv[1], dt.date.fromisoformat(sys.argv[2])
pw = os.environ.get("WAYTEKO_PW") or sys.exit("нет WAYTEKO_PW")
box = json.load(open(path)); b = base64.b64decode
key = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), b(box["salt"]), box["iter"], 32)
app = json.loads(AESGCM(key).decrypt(b(box["iv"]), b(box["ct"]), None))

MSK = dt.timezone(dt.timedelta(hours=3))
WD = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
P = {"urgent": ("🔴 Срочно", 0), "high": ("🟠 Важно", 1), "normal": ("", 2)}
names = {c.get("id"): c.get("name", "") for c in app.get("clients", []) if isinstance(c, dict)}
tasks = [t for t in app.get("tasks", []) or [] if isinstance(t, dict) and not t.get("del") and t.get("d")]
prio = lambda t: t.get("prio") if t.get("prio") in P else "normal"
key_ = lambda t: (P[prio(t)][1], t.get("d", ""), t.get("created", ""))
d_ = lambda s: dt.date.fromisoformat(s)
dshort = lambda s: f"{WD[d_(s).weekday()]}, {d_(s):%d.%m}"

def line(t, show_date=False):
    who = names.get(t.get("cid")) or t.get("cname") or ""
    parts = [P[prio(t)][0]] if P[prio(t)][0] else []
    parts.append(f"{who} — {t.get('text', '').strip()}" if who else t.get("text", "").strip())
    tail = []
    if t.get("owner"): tail.append(f"👤 {t['owner']}")
    if show_date: tail.append(f"было на {dshort(t['d'])}")
    return "• " + " ".join(parts) + (f" ({'; '.join(tail)})" if tail else "")

iso = day.isoformat(); tom = (day + dt.timedelta(days=1)).isoformat()
today = [t for t in tasks if t["d"] == iso]
done = sorted([t for t in today if t.get("done")], key=key_)
open_ = sorted([t for t in today if not t.get("done")], key=key_)
over = sorted([t for t in tasks if not t.get("done") and t["d"] < iso], key=key_)
nxt = sorted([t for t in tasks if t["d"] == tom], key=key_)
urgent_open = sum(1 for t in open_ + over if prio(t) == "urgent")

out = [f"Задачи WAYTEKO за {day:%d.%m.%Y}", ""]
if today:
    out.append(f"Итог дня: выполнено {len(done)} из {len(today)}" + (f", не выполнено {len(open_)}" if open_ else " — всё закрыто ✅")
               + (f"; срочных не закрыто: {urgent_open}" if urgent_open else "") + ".")
else:
    out.append("На сегодня задач не было." + (f" Срочных хвостов не закрыто: {urgent_open}." if urgent_open else ""))
if open_: out += ["", f"⬜ Не выполнено сегодня ({len(open_)}):"] + [line(t) for t in open_]
if done: out += ["", f"✅ Выполнено сегодня ({len(done)}):"] + [line(t) for t in done]
if over: out += ["", f"⏰ Хвосты с прошлых дней ({len(over)}):"] + [line(t, True) for t in over[:20]] + ([f"…и ещё {len(over) - 20}"] if len(over) > 20 else [])
out += ["", f"📅 На завтра, {dshort(tom)} ({len(nxt)}):"] + ([line(t) for t in nxt] if nxt else ["• задач пока нет"])
if app.get("updated"):
    try: out += ["", f"Данные приложения на {dt.datetime.fromisoformat(app['updated'].replace('Z', '+00:00')).astimezone(MSK):%d.%m %H:%M} (МСК)."]
    except Exception: pass
out.append("Приложение: https://ezakharov1222-lgtm.github.io/Wayteko/")
print("\n".join(out))
