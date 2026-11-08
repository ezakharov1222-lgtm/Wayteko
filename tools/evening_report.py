"""Единый вечерний отчёт WAYTEKO: клиенты + личные задачи, по приоритетам, не длиннее 2 страниц.
python3 tools/evening_report.py <выгрузка>/clients <выгрузка>/tasks <summary.json|-> ГГГГ-ММ-ДД <файл.xlsx> <папка вывода> [предупреждение]
Пишет в папку вывода: report.html (htmlBody письма), report.txt (body письма), subject.txt,
и добавляет в начало Excel-файла лист «Сводка» с тем же содержанием."""
import os, sys, json, glob, html, datetime as dt

cdir, tdir, summ, day, xlsx, out = sys.argv[1:7]
warn = sys.argv[7] if len(sys.argv) > 7 else ""
D = dt.date.fromisoformat(day); TS = D.isoformat(); TM = (D + dt.timedelta(1)).isoformat()
W7 = (D + dt.timedelta(7)).isoformat()
WD = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
APP = "https://ezakharov1222-lgtm.github.io/Wayteko/"

def load(d):
    r = []
    for p in sorted(glob.glob(os.path.join(d, "*.json"))):
        x = json.load(open(p, encoding="utf-8")); x = x["data"] if isinstance(x.get("data"), dict) else x
        x = dict(x); x["_id"] = os.path.basename(p)[:-5]; r.append(x)
    return r

cl = load(cdir); tasks = load(tdir) if os.path.isdir(tdir) else []
S = json.load(open(summ)) if summ != "-" and os.path.exists(summ) else {}
f = lambda s: f"{s[8:10]}.{s[5:7]}"
fd = lambda s: f"{WD[dt.date.fromisoformat(s).weekday()]} {f(s)}"
cut = lambda s, n: (s if len(s) <= n else s[:n - 1].rstrip(" ,.;") + "…")
names = {c["_id"]: c.get("name", "") for c in cl}
RANK = {"hot": 0, "dealer": 1, "warm": 2, "cold": 3}
ICON = {"hot": "🔥", "warm": "🌤", "cold": "❄", "dealer": "✅"}
work = [c for c in cl if c.get("temp") not in ("branch", "refused")]

def last(c):
    ts = [t for t in c.get("touches") or [] if t and t.get("t")]
    return ts[-1]["t"] if ts else (c.get("intro") or "")
def step(c): return cut(" ".join(((c.get("plan") or "").strip() or last(c)).split()), 110)
def contact(c):
    fio = (c.get("fio") or "").strip(); ph = (c.get("phone") or "").split(";")[0].strip()
    ph = ph.replace("Моб.:", "").strip()
    return ", ".join(x for x in (fio, ph) if x)
def cline(c, extra=""):
    k = contact(c)
    return f"{ICON.get(c.get('temp'), '')} {c.get('name', '')}{extra}" + (f" — {k}" if k else "") + f" — {step(c)}"

# ---- данные
touched = [c for c in cl if any((t or {}).get("d") == TS for t in c.get("touches") or [])]
ntouch = sum(1 for c in cl for t in c.get("touches") or [] if (t or {}).get("d") == TS)
over = sorted([c for c in work if c.get("next") and c["next"] < TS], key=lambda c: (c["next"], RANK.get(c.get("temp"), 9)))
tom = sorted([c for c in work if c.get("next") == TM], key=lambda c: (RANK.get(c.get("temp"), 9), c.get("name", "")))
tom_main = [c for c in tom if c.get("temp") in ("hot", "dealer")]; tom_sec = [c for c in tom if c not in tom_main]
week = sorted([c for c in work if c.get("next") and TM < c["next"] <= W7], key=lambda c: (c["next"], RANK.get(c.get("temp"), 9)))
meets = []
for c in cl:
    for m in c.get("meets") or []:
        if m and m.get("d") and TS <= m["d"] <= W7 and not m.get("done"):
            meets.append((m["d"], m.get("t") or "", c, m))
meets.sort(key=lambda x: (x[0], x[1]))
m_soon = [x for x in meets if (dt.date.fromisoformat(x[0]) - D).days <= 3]; m_late = [x for x in meets if x not in m_soon]
cnt = {k: sum(1 for c in work if c.get("temp") == k) for k in ("hot", "warm", "cold", "dealer")}

P = {"urgent": 0, "high": 1}
PI = {"urgent": "🔴", "high": "🟠"}
tk = [t for t in tasks if not t.get("del") and t.get("d")]
pr = lambda t: P.get(t.get("prio"), 2)
tkey = lambda t: (pr(t), t.get("d", ""), t.get("created", ""))
def tline(t, date=False):
    who = names.get(t.get("cid")) or t.get("cname") or ""
    s = (PI.get(t.get("prio"), "") + " " if t.get("prio") in PI else "") + (f"{who} — " if who else "") + " ".join((t.get("text") or "").split())
    if t.get("owner"): s += f" (👤 {t['owner']})"
    if date: s += f" — было на {f(t['d'])}"
    return cut(s, 130)
t_today = [t for t in tk if t["d"] == TS]
t_done = [t for t in t_today if t.get("done")]
t_open = sorted([t for t in t_today if not t.get("done")], key=tkey)
t_over = sorted([t for t in tk if not t.get("done") and t["d"] < TS], key=tkey)
t_tom = sorted([t for t in tk if t["d"] == TM and not t.get("done")], key=tkey)
t_urg = [t for t in t_open + t_over if pr(t) == 0]

# ---- структура отчёта: (заголовок, цвет, [(подзаголовок, [строки])])
def more(lst, n, fn):
    r = [fn(x) for x in lst[:n]]
    return r + ([f"…и ещё {len(lst) - n}"] if len(lst) > n else [])
mline = lambda x: f"{f(x[0])} {x[1]} — {x[2].get('name', '')} — {x[3].get('place') or 'место не указано'} — {cut(' '.join((x[3].get('note') or '').split()), 90)}" + (f" ⚠ через {(dt.date.fromisoformat(x[0]) - D).days} дн." if x in m_soon else "")

secs = []
s1 = []
if over: s1.append((f"Просроченные созвоны ({len(over)})", more(over, 8, lambda c: cline(c, f" (созвон был {f(c['next'])})"))))
if m_soon: s1.append((f"Встречи в ближайшие 3 дня ({len(m_soon)})", [mline(x) for x in m_soon]))
if t_urg: s1.append((f"Срочные задачи не закрыты ({len(t_urg)})", more(t_urg, 6, lambda t: tline(t, t["d"] < TS))))
secs.append(("1. Срочно — сделать в первую очередь", "#c0392b", s1 or [("", ["Срочного нет: просроченных созвонов, близких встреч и срочных задач нет."])]))

s2 = []
if tom_main: s2.append((f"Основные — горячие и дилеры ({len(tom_main)})", more(tom_main, 10, cline)))
if tom_sec: s2.append((f"Второстепенные — тёплые и холодные ({len(tom_sec)})", more(tom_sec, 10, cline)))
secs.append((f"2. Созвоны на завтра, {fd(TM)} — всего {len(tom)}", "#d35400", s2 or [("", ["Созвонов на завтра нет."])]))

s3 = []
t_rest_over = [t for t in t_over if pr(t) != 0]; t_rest_open = [t for t in t_open if pr(t) != 0]
if t_rest_open: s3.append((f"Не выполнено сегодня ({len(t_rest_open)})", more(t_rest_open, 6, tline)))
if t_rest_over: s3.append((f"Хвосты с прошлых дней ({len(t_rest_over)})", more(t_rest_over, 6, lambda t: tline(t, True))))
s3.append((f"На завтра ({len(t_tom)})", more(t_tom, 6, tline) or ["задач пока нет"]))
secs.append((f"3. Мои задачи — сегодня выполнено {len(t_done)} из {len(t_today)}", "#2c3e50", s3))

s4 = []
if m_late: s4.append((f"Встречи ({len(m_late)})", [mline(x) for x in m_late]))
if week:
    hot = [c for c in week if c.get("temp") in ("hot", "dealer")]
    s4.append((f"Созвоны на неделю ({len(week)}, из них горячих {len(hot)})",
               more(week, 8, lambda c: f"{f(c['next'])} {ICON.get(c.get('temp'), '')} {c.get('name', '')}")))
secs.append(("4. Дальше на неделе — второстепенное", "#7f8c8d", s4 or [("", ["Встреч и созвонов на неделю пока не назначено."])]))

s5 = [("Касания сегодня", [f"{ntouch} — " + ", ".join(c.get("name", "") for c in touched[:10]) + (" …" if len(touched) > 10 else "")] if ntouch else ["не записано"])]
ch = []
for k, lbl in (("added", "новых"), ("changed", "изменено"), ("deleted", "удалено")):
    v = S.get(k) or []
    ch.append(f"{lbl} {len(v)}" + (f" ({', '.join(v)})" if v and len(v) <= 5 else ""))
s5.append(("Из приложения", ["; ".join(ch)] if S else ["данных из приложения нет"]))
secs.append(("5. Итог дня", "#7f8c8d", s5))

kpi = f"В работе {len(work)} · 🔥 {cnt['hot']} · 🌤 {cnt['warm']} · ❄ {cnt['cold']} · дилеров {cnt['dealer']} из 25 · просрочено {len(over)} · завтра {len(tom)} · задач на завтра {len(t_tom)}"
title = f"Отчёт WAYTEKO за {D:%d.%m.%Y}"

# ---- текст
T = [title, kpi, ""]
for h, _, subs in secs:
    T.append(h.upper())
    for sh, rows in subs:
        if sh: T.append(f"  {sh}:")
        T += [("    • " if sh else "  ") + r for r in rows]
    T.append("")
if warn: T += [f"Внимание: {warn}", ""]
T.append(f"Приложение: {APP} · Полная база клиентов — в приложенном Excel-файле")
open(os.path.join(out, "report.txt"), "w").write("\n".join(T))
open(os.path.join(out, "subject.txt"), "w").write(title)

# ---- HTML (почтовый, стили в строке)
e = html.escape
H = [f'<div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:1.35;color:#222;max-width:760px">',
     f'<div style="font-size:18px;font-weight:bold;margin:0 0 4px">{e(title)}</div>',
     f'<div style="background:#f2f4f7;border-radius:6px;padding:6px 10px;margin:0 0 10px;font-size:12px">{e(kpi)}</div>']
for h, col, subs in secs:
    H.append(f'<div style="font-size:14px;font-weight:bold;color:{col};border-bottom:2px solid {col};margin:12px 0 4px;padding-bottom:2px">{e(h)}</div>')
    for sh, rows in subs:
        if sh: H.append(f'<div style="font-weight:bold;margin:6px 0 2px">{e(sh)}</div>')
        H.append('<ul style="margin:0 0 4px 18px;padding:0">' + "".join(f'<li style="margin:0 0 2px">{e(r)}</li>' for r in rows) + "</ul>")
if warn: H.append(f'<div style="margin:12px 0 0;padding:6px 10px;background:#fdecea;color:#c0392b;border-radius:6px"><b>Внимание:</b> {e(warn)}</div>')
H.append(f'<div style="margin:14px 0 0;font-size:12px;color:#666"><a href="{APP}">Открыть приложение</a> · Полная база клиентов — в приложенном Excel-файле</div></div>')
open(os.path.join(out, "report.html"), "w").write("".join(H))

# ---- лист «Сводка» в Excel
if xlsx != "-" and os.path.exists(xlsx):
    from openpyxl import load_workbook
    from openpyxl.styles import Font, Alignment
    wb = load_workbook(xlsx); ws = wb.create_sheet("Сводка", 0); wb.active = 0
    ws.column_dimensions["A"].width = 150
    r = 1
    def put(v, **kw):
        global r
        c = ws.cell(r, 1, v); c.font = Font(name="Calibri", **kw); c.alignment = Alignment(wrap_text=True, vertical="top"); r += 1
    put(title, size=16, bold=True); put(kpi, size=11, color="555555"); r += 1
    for h, col, subs in secs:
        put(h, size=13, bold=True, color=col.lstrip("#").upper())
        for sh, rows in subs:
            if sh: put(sh, size=11, bold=True)
            for x in rows: put("• " + x, size=11)
        r += 1
    if warn: put(f"Внимание: {warn}", size=11, bold=True, color="C0392B")
    wb.save(xlsx)
print(f"OK: {title}; строк текста {len(T)}")
