"""PDF еженедельного отчёта руководителю — в оформлении образца (Главное, плитки, Приоритет А, Приоритет Б, Пауза).
python3 tools/weekly_render.py /tmp/wayteko/weekly_input.json /tmp/wayteko/weekly_answers.json /tmp/wayteko/WAYTEKO_отчёт_ДД.ММ.ГГГГ.pdf

weekly_answers.json пишет Claude:
{"greeting": "Сергей Алексеевич, добрый день!",
 "intro": "Ниже — состояние работы с потенциальными дилерами. ...",
 "main": [{"lead": "30 компаний в работе, 100 касаний отработано.", "text": "Просроченных контактов нет."}, ...],
 "intent": ["id", ...],                       # прямо подтвердили намерение взять дилерство
 "notes": {"A": "Ближайшие подписания: ...", "B": "Здесь сосредоточен основной потенциал."},
 "rows": {"id": {"group": "dealer|A|B_next|B_paused|B_meet|B_lost|B_other|pause|skip", "stage": "...", "perspective": "...", "rank": 1}}}
Касания, выручка, суммы и плитки считаются здесь из weekly_input.json."""
import sys, json, html, asyncio

inp, ans, out = sys.argv[1:4]
D = json.load(open(inp, encoding="utf-8")); A = json.load(open(ans, encoding="utf-8"))
C = {c["id"]: c for c in D["clients"]}
R = A.get("rows", {})
e = lambda s: html.escape(str(s or ""))


def num(v, d=1):
    s = f"{v:,.{d}f}".replace(",", " ").replace(".", ",")
    return s


def rev_cell(c):
    v = c.get("revenue_2025_mln")
    return "<i>нет данных</i>" if v is None else f"{num(v)}&nbsp;млн"


def total(ids):
    s = sum((C[i].get("revenue_2025_mln") or 0) for i in ids)
    return f"{num(s / 1000)} млрд ₽" if s >= 1000 else f"{num(s)} млн ₽"


def short(n):
    import re
    n = re.sub(r",?\s*ООО$", "", n.strip())
    m = re.match(r"^ИП\s+(\S+)", n)
    return "ИП " + m.group(1) if m else n


def plural(n, one, few, many):
    n10, n100 = n % 10, n % 100
    return one if n10 == 1 and n100 != 11 else few if 2 <= n10 <= 4 and not 12 <= n100 <= 14 else many


def ids_of(g):
    ids = [i for i, r in R.items() if r.get("group") == g and i in C]
    return sorted(ids, key=lambda i: (R[i].get("rank", 999), -(C[i].get("revenue_2025_mln") or 0)))


def table(ids, hl=False):
    rows = "".join(f"""<tr class="{'hl' if hl else ''}"><td><b>{e(C[i]['name'])}</b><div class="reg">{e(C[i]['region'])}</div></td>
      <td class="c">{C[i]['touches_count']}</td><td class="c">{rev_cell(C[i])}</td><td>{e(R[i].get('stage'))}</td><td>{e(R[i].get('perspective'))}</td></tr>""" for i in ids)
    return f"""<table><thead><tr><th style="width:22%">Компания, регион</th><th class="c" style="width:6%">Касаний</th><th class="c" style="width:10%">Выручка<br>2025</th>
      <th style="width:31%">Стадия</th><th>Перспектива</th></tr></thead><tbody>{rows}</tbody></table>"""


def sub(title, ids):
    if not ids: return ""
    return f"""<div class="sub"><b>{e(title)}</b> · {len(ids)} {plural(len(ids), 'компания', 'компании', 'компаний')} · {total(ids)}</div>{table(ids)}"""


T = D["totals"]; intent = [i for i in A.get("intent", []) if i in C]
dealers, a_ids = ids_of("dealer"), ids_of("A")
b_groups = [("На выходе в приоритет А", ids_of("B_next")), ("В проработке", ids_of("B_other")), ("Переговоры приостановлены", ids_of("B_paused")),
            ("Встречи назначены", ids_of("B_meet")), ("Контакт потерян", ids_of("B_lost"))]
b_all = [i for _, l in b_groups for i in l]; pause = ids_of("pause")
new = [c for c in D["clients"] if c.get("new_import")]
tiles = [(T["companies_in_work"], "компаний в работе", "#1f3864"), (T["touches_total"], "касаний отработано", "#1f3864"),
         (len(a_ids), "на подписании", "#c55a11"), (len(intent), "подтвердили намерение", "#548235")]

body = f"""<p class="hi"><b>{e(A.get('greeting', 'Добрый день!'))}</b></p><p class="muted">{e(A.get('intro', ''))}</p>
<h2>ГЛАВНОЕ</h2><ul class="main">{''.join(f"<li><b>{e(m.get('lead'))}</b> {e(m.get('text'))}</li>" for m in A.get('main', []))}</ul>
<div class="tiles">{''.join(f'<div><b style="color:{c}">{n}</b><span>{e(l)}</span></div>' for n, l, c in tiles)}</div>"""
if dealers:
    body += f"""<h2>ДИЛЕРЫ — ДОГОВОР ПОДПИСАН</h2><p class="muted">{len(dealers)} {plural(len(dealers), 'компания', 'компании', 'компаний')}, суммарный оборот — {total(dealers)}.</p>{table(dealers, True)}"""
if a_ids:
    body += f"""<h2>ПРИОРИТЕТ А — СТАДИЯ ПОДПИСАНИЯ</h2><p class="muted">Суммарный оборот {len(a_ids)} {plural(len(a_ids), 'компании', 'компаний', 'компаний')} — {total(a_ids)}. {e(A.get('notes', {}).get('A', ''))}</p>{table(a_ids, True)}"""
if b_all:
    body += f"""<h2>ПРИОРИТЕТ Б — В ПРОРАБОТКЕ</h2><p class="muted">{len(b_all)} {plural(len(b_all), 'компания', 'компании', 'компаний')}, суммарный оборот — {total(b_all)}. {e(A.get('notes', {}).get('B', ''))}</p>""" + "".join(sub(t, l) for t, l in b_groups)
if pause:
    body += f"""<h2>НА ПАУЗЕ — ВОЗВРАТ ПО ГРАФИКУ</h2>{table(pause)}"""
if new:
    body += f"""<h2>НОВЫЕ В РАБОТЕ — ПЕРВИЧНЫЙ ПРОЗВОН</h2><p class="muted">{len(new)} {plural(len(new), 'компания', 'компании', 'компаний')} из списка дилеров, касаний ещё не было, прозвон распределён на неделю: {e(', '.join(short(c['name']) for c in new))}.</p>"""

page = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 10mm 11mm 10mm 11mm; }}
body {{ font-family: Inter, "DejaVu Sans", Arial, sans-serif; font-size: 8.6px; color: #222; line-height: 1.28; }}
.hi {{ font-size: 11.5px; margin: 0 0 6px; }} .muted {{ color: #555; margin: 0 0 5px; font-size: 9.4px; }}
h2 {{ color: #1f3864; font-size: 12px; letter-spacing: .04em; margin: 10px 0 5px; padding-bottom: 4px; border-bottom: 2px solid #1f3864; }}
ul.main {{ list-style: none; padding: 0; margin: 0 0 6px; font-size: 9.4px; }} ul.main li {{ margin: 0 0 3px; padding-left: 14px; text-indent: -14px; }}
ul.main li::before {{ content: "— "; color: #1f3864; font-weight: 700; }}
.tiles {{ display: flex; background: #f3f5f8; margin: 6px 0 4px; }} .tiles div {{ flex: 1; text-align: center; padding: 5px 4px; border-right: 2px solid #fff; }}
.tiles b {{ display: block; font-size: 20px; line-height: 1.1; }} .tiles span {{ font-size: 8.5px; color: #555; }}
table {{ width: 100%; border-collapse: collapse; margin: 0 0 8px; page-break-inside: auto; }} tr {{ page-break-inside: avoid; }}
th {{ background: #1f3864; color: #fff; text-align: left; font-size: 7.8px; padding: 3px 5px; }} th.c, td.c {{ text-align: center; }}
td {{ padding: 2.5px 5px; border-bottom: 1px solid #dde2ea; vertical-align: middle; }} tr.hl td {{ background: #fbe9df; }}
.reg {{ color: #888; font-size: 7.6px; }} .sub {{ color: #1f3864; margin: 6px 0 3px; font-size: 9.4px; }} .sub b {{ color: #2f5597; }}
</style></head><body>{body}</body></html>"""


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        br = await p.chromium.launch(); pg = await br.new_page()
        await pg.set_content(page, wait_until="load"); await pg.pdf(path=out, format="A4", print_background=True, prefer_css_page_size=True)
        await br.close()
asyncio.run(main())
open(out.replace(".pdf", ".html"), "w", encoding="utf-8").write(page)
print("готово:", out, "| групп:", {"dealer": len(dealers), "A": len(a_ids), "B": len(b_all), "pause": len(pause), "new": len(new)},
      "| не распределены:", [C[i]["name"] for i in C if i not in R and not C[i].get("new_import")])
