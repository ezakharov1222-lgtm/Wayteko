"""Совет эксперта по каждому клиенту в работе — обновляется после каждого нового касания.

python3 tools/advice.py todo  <out.json>      — какие клиенты ждут нового совета (появилось касание или совета ещё нет);
                                               пишет их полную историю в out.json, печатает число
python3 tools/advice.py apply <answers.json>  — answers.json: {"<id клиента>": {"r": "sales|lawyer|marketing|finance|logistics",
                                               "t": "текст совета"}}; проверяет и записывает data/advice.enc.json
Пароль — из WAYTEKO_PW. Данные берутся из data/app.enc.json (общая копия всех устройств владельца).
Ключ касания k = "<число касаний>|<дата последнего касания>" — так же считает приложение (touchKey)."""
import os, sys, json, base64, hashlib, datetime as dt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

APP, ADV = "data/app.enc.json", "data/advice.enc.json"
ROLES = {"sales", "lawyer", "marketing", "finance", "logistics"}
ACTIVE = {"hot", "warm", "cold", "dealer"}
MAXLEN = 80
pw = os.environ.get("WAYTEKO_PW") or sys.exit("нет WAYTEKO_PW")
b, e = base64.b64decode, lambda x: base64.b64encode(x).decode()


def dec(path):
    box = json.load(open(path))
    k = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), b(box["salt"]), box["iter"], 32)
    return json.loads(AESGCM(k).decrypt(b(box["iv"]), b(box["ct"]), None))


def enc(obj, path):
    salt, iv, it = os.urandom(16), os.urandom(12), 250000
    k = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, it, 32)
    ct = AESGCM(k).encrypt(iv, json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), None)
    json.dump({"v": 1, "iter": it, "salt": e(salt), "iv": e(iv), "ct": e(ct)}, open(path, "w"), separators=(",", ":"))


def tkey(c):
    t = [x for x in (c.get("touches") or []) if x and x.get("t")]
    return f"{len(t)}|{t[-1].get('d', '') if t else ''}"


app = dec(APP)
adv = dec(ADV) if os.path.exists(ADV) else {"updated": "", "items": {}}
items = adv.setdefault("items", {})
clients = {c["id"]: c for c in app.get("clients", []) if isinstance(c, dict) and c.get("id")}
cmd, path = sys.argv[1], sys.argv[2]

if cmd == "todo":
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).date().isoformat()
    todo = []
    for c in clients.values():
        if c.get("temp") not in ACTIVE or c.get("id") in (app.get("deleted") or []):
            continue
        if not (c.get("touches") or c.get("intro")):
            continue
        a = items.get(c["id"])
        if a and a.get("k") == tkey(c):
            continue
        todo.append({"id": c["id"], "name": c.get("name"), "status": c.get("temp"), "region": c.get("region"),
                     "contact": c.get("fio"), "position": c.get("position"), "intro": c.get("intro"),
                     "next_call": c.get("next"), "plan": c.get("plan"),
                     "touches": [x for x in (c.get("touches") or []) if x and x.get("t")],
                     "meets": c.get("meets") or [], "previous_advice": (a or {}).get("t")})
    json.dump({"today": today, "clients": todo}, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"ждут нового совета: {len(todo)}")

elif cmd == "apply":
    ans = json.load(open(path, encoding="utf-8"))
    errs, done = [], 0
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    for cid, v in ans.items():
        c = clients.get(cid)
        if not c:
            errs.append(f"{cid}: нет такого клиента"); continue
        r, t = (v or {}).get("r"), " ".join(str((v or {}).get("t") or "").split())
        if r not in ROLES:
            errs.append(f"{cid}: роль должна быть одной из {sorted(ROLES)}"); continue
        if not t or len(t) > MAXLEN:
            errs.append(f"{cid}: текст {len(t)} симв., нужно 1–{MAXLEN} — сократите"); continue
        items[cid] = {"cid": cid, "r": r, "t": t, "k": tkey(c), "at": now}; done += 1
    if done:
        adv["updated"] = now
        enc(adv, ADV)
    print(f"записано советов: {done}" + (f"; ошибки ({len(errs)}):\n" + "\n".join(errs) if errs else ""))
    sys.exit(1 if errs else 0)
else:
    sys.exit("команда: todo | apply")
