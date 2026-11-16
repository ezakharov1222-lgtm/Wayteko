"""Данные для еженедельного отчёта руководителю (дилерская сеть).
python3 tools/weekly_data.py ГГГГ-ММ-ДД /tmp/wayteko/weekly_input.json
Берёт клиентов из data/app.enc.json (общая копия приложения). Пароль — из WAYTEKO_PW.
В отчёт идут клиенты в работе (кроме «Филиал» и «Отказ»). Цифры (касания, выручка, просрочки) считает скрипт —
Claude их не придумывает, а только распределяет клиентов по группам и пишет «Стадия» и «Перспектива»."""
import os, sys, json, base64, hashlib, datetime as dt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

day, out = dt.date.fromisoformat(sys.argv[1]), sys.argv[2]
pw = os.environ.get("WAYTEKO_PW") or sys.exit("нет WAYTEKO_PW")
box = json.load(open("data/app.enc.json")); b = base64.b64decode
key = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), b(box["salt"]), box["iter"], 32)
app = json.loads(AESGCM(key).decrypt(b(box["iv"]), b(box["ct"]), None))
deleted = set(app.get("deleted") or [])
adv = {}
if os.path.exists("data/advice.enc.json"):
    ab = json.load(open("data/advice.enc.json"))
    ak = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), b(ab["salt"]), ab["iter"], 32)
    adv = json.loads(AESGCM(ak).decrypt(b(ab["iv"]), b(ab["ct"]), None)).get("items", {})


def rev(c):
    v = str(c.get("revenue") if c.get("revenue") is not None else "").replace(",", ".").replace(" ", "")
    try: return round(float(v), 1)
    except ValueError: return None


def ctr(c):
    v = c.get("contract")
    return "work" if v in (True, "work") else "signed" if v == "signed" else ""


iso = day.isoformat(); week_ago = (day - dt.timedelta(days=7)).isoformat()
rows = []
for c in app.get("clients") or []:
    if not c.get("id") or c["id"] in deleted or c.get("temp") in ("branch", "refused"): continue
    t = [x for x in (c.get("touches") or []) if x and x.get("t")]
    imported = any("импорт списка" in (h.get("a") or "") for h in (c.get("hist") or []))
    rows.append({"id": c["id"], "name": c.get("name"), "region": (c.get("region") or "").strip(), "status": c.get("temp"),
                 "contract": ctr(c), "touches_count": len(t), "revenue_2025_mln": rev(c), "next_call": c.get("next") or "",
                 "overdue": bool(c.get("next") and c["next"] < iso), "plan": c.get("plan") or "", "intro": c.get("intro") or "",
                 "touches": [{"d": x.get("d"), "t": x.get("t")} for x in t], "meets": [m for m in (c.get("meets") or []) if m and not m.get("del")],
                 "ai_advice": (adv.get(c["id"]) or {}).get("t", ""), "new_import": imported and not t})
work = [r for r in rows if not r["new_import"]]
data = {"date": iso, "totals": {
    "companies_in_work": len(work), "touches_total": sum(r["touches_count"] for r in work),
    "touches_week": sum(1 for r in work for x in r["touches"] if (x.get("d") or "") > week_ago),
    "overdue": sum(1 for r in work if r["overdue"]), "new_import": sum(1 for r in rows if r["new_import"])}, "clients": rows}
json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(data["totals"], ensure_ascii=False))
