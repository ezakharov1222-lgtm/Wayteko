"""Сводит изменения редакторов (data/e-*.enc.json) в общую копию владельца data/app.enc.json — на случай,
когда устройства владельца выключены. Запускается в ежечасной и вечерней задачах. Пароль — из WAYTEKO_PW.
python3 tools/merge_editors.py      (в корне репозитория)
Правила объединения те же, что в приложении (mergeClient): база — более свежая версия карточки,
касания, встречи и журнал изменений объединяются, удалённые владельцем клиенты не возвращаются."""
import os, sys, json, base64, hashlib, datetime as dt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

pw = os.environ.get("WAYTEKO_PW") or sys.exit("нет WAYTEKO_PW")
b, e = base64.b64decode, lambda x: base64.b64encode(x).decode()
APP, HIST_MAX = "data/app.enc.json", 60


def dec(path, p):
    box = json.load(open(path))
    k = hashlib.pbkdf2_hmac("sha256", p.encode("utf-8"), b(box["salt"]), box["iter"], 32)
    return json.loads(AESGCM(k).decrypt(b(box["iv"]), b(box["ct"]), None))


def enc(obj, path, p):
    salt, iv, it = os.urandom(16), os.urandom(12), 250000
    k = hashlib.pbkdf2_hmac("sha256", p.encode("utf-8"), salt, it, 32)
    ct = AESGCM(k).encrypt(iv, json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), None)
    json.dump({"v": 1, "iter": it, "salt": e(salt), "iv": e(iv), "ct": e(ct)}, open(path, "w"), separators=(",", ":"))


def merge_client(a, c):
    if not a: return c
    if not c: return a
    base, other = (c, a) if (c.get("updated") or "") > (a.get("updated") or "") else (a, c)
    tm = {}
    for t in (other.get("touches") or []) + (base.get("touches") or []):
        if t and t.get("t"):
            k = f"{t.get('d') or ''}|{t['t']}"; tm[k] = {**tm.get(k, {}), **t}
    touches = sorted(tm.values(), key=lambda t: (t.get("d") or "", t.get("at") or ""))
    mm = {}
    for m in (other.get("meets") or []) + (base.get("meets") or []):
        if m and m.get("id"):
            p = mm.get(m["id"])
            mm[m["id"]] = {**p, **m, "del": bool(p.get("del") or m.get("del")), "done": bool(p.get("done") or m.get("done"))} if p else m
    hm = {}
    for h in (other.get("hist") or []) + (base.get("hist") or []):
        if h: hm[f"{h.get('at') or ''}|{h.get('by') or ''}|{h.get('a') or ''}"] = h
    hist = sorted(hm.values(), key=lambda h: h.get("at") or "")[-HIST_MAX:]
    out = {**base, "touches": touches}
    if mm: out["meets"] = list(mm.values())
    if hist: out["hist"] = hist
    return out


def merge_list(cur, incoming, deleted):
    by = {c["id"]: c for c in cur if c.get("id")}; n = 0
    for r in incoming or []:
        if not r or not r.get("id") or r["id"] in deleted or not r.get("name"): continue
        l = by.get(r["id"]); m = merge_client(l, r)
        if l is None or m != l: by[r["id"]] = m; n += 1
    for d in deleted:
        if by.pop(d, None) is not None: n += 1
    return list(by.values()), n


app = dec(APP, pw)
deleted = set(app.get("deleted") or [])
eds = [x for x in (app.get("editors") or []) if x.get("pw") and not x.get("off")]
total, files = 0, {}
for x in eds:
    path = f"data/e-{hashlib.sha256(('wayteko-editor:' + x['pw']).encode()).hexdigest()[:16]}.enc.json"
    if not os.path.exists(path): continue
    try:
        snap = dec(path, x["pw"])
    except Exception:
        print(f"не открылся файл редактора {x.get('name')}"); continue
    app["clients"], n = merge_list(app.get("clients") or [], snap.get("clients"), deleted)
    total += n; files[path] = (x, snap)
now = dt.datetime.now(dt.timezone.utc).isoformat()
if total:
    app["updated"] = now
    enc(app, APP, pw)
upd = 0
for path, (x, snap) in files.items():
    merged, n = merge_list(snap.get("clients") or [], app["clients"], deleted)
    if n:
        enc({"updated": now, "clients": merged, "deleted": sorted(deleted), "gh": app.get("gh") or snap.get("gh"),
             "editor": {"id": x.get("id"), "name": x.get("name") or ""}}, path, x["pw"]); upd += 1
print(f"редакторов: {len(eds)}; изменений от редакторов в общей копии: {total}; обновлено копий редакторов: {upd}")
