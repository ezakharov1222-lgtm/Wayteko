"""Переносит данные из приложения WAYTEKO (главный источник) в интернет-версию.
python3 tools/merge_app.py <data/app.enc.json> <папка выгрузки clients/*.json> <versions.json> <папка результата>
Пароль — из WAYTEKO_PW. versions.json — {"id": версия документа} из ответа ArtifactData list.
Пишет <результат>/docs/<id>.json и <результат>/writes_N.json (до 50 записей, готовы для ArtifactData batch),
а также summary.json. Клиенты, удалённые в приложении, удаляются; клиенты, которых в приложении просто нет,
не трогаются. Если клиент менялся и там, и там — берётся более свежая правка (при равенстве — приложение)."""
import os, sys, json, glob, base64, hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

app_path, dump_dir, ver_path, out = sys.argv[1:5]
pw = os.environ.get("WAYTEKO_PW") or sys.exit("нет WAYTEKO_PW")
box = json.load(open(app_path))
b = lambda s: base64.b64decode(s)
key = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), b(box["salt"]), box["iter"], 32)
app = json.loads(AESGCM(key).decrypt(b(box["iv"]), b(box["ct"]), None))
# служебные поля приложения в интернет-версию не переносятся
for k in ("gh", "guests", "guest"): app.pop(k, None)
versions = json.load(open(ver_path))

art = {}
for p in glob.glob(os.path.join(dump_dir, "*.json")):
    d = json.load(open(p, encoding="utf-8"))
    d = d["data"] if isinstance(d.get("data"), dict) else d
    art[os.path.basename(p)[:-5]] = d

SKIP = {"id"}
clean = lambda d: {k: v for k, v in d.items() if k not in SKIP}
os.makedirs(f"{out}/docs", exist_ok=True)
writes, s = [], {"app_updated": app.get("updated"), "app_clients": len(app.get("clients", [])), "added": [], "changed": [], "deleted": [], "kept_online_newer": []}

for c in app.get("clients", []):
    cid = c.get("id")
    if not cid or not c.get("name"): continue
    doc = clean(c); a = art.get(cid)
    if a is None:
        op = {"op": "set", "collection": "clients", "doc_id": cid}; s["added"].append(c["name"])
    elif clean(a) == doc:
        continue
    elif (a.get("updated") or "") > (doc.get("updated") or ""):
        s["kept_online_newer"].append(c["name"]); continue
    else:
        if cid not in versions: sys.exit(f"нет версии для {cid} в versions.json")
        op = {"op": "set", "collection": "clients", "doc_id": cid, "if_version": int(versions[cid])}; s["changed"].append(c["name"])
    path = os.path.abspath(f"{out}/docs/{cid}.json")
    json.dump(doc, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    op["file_path"] = path; writes.append(op)

app_ids = {c.get("id") for c in app.get("clients", [])}
for cid in app.get("deleted", []):
    if cid in art and cid not in app_ids:
        if cid not in versions: sys.exit(f"нет версии для {cid} в versions.json")
        writes.append({"op": "delete", "collection": "clients", "doc_id": cid, "if_version": int(versions[cid])})
        s["deleted"].append(art[cid].get("name", cid))

# личные задачи владельца -> коллекция tasks интернет-версии (в отчёт и файл не попадают)
tasks_dir = sys.argv[5] if len(sys.argv) > 5 else os.path.join(os.path.dirname(os.path.abspath(dump_dir)), "tasks")
art_t = {}
for p in glob.glob(os.path.join(tasks_dir, "*.json")):
    d = json.load(open(p, encoding="utf-8")); d = d["data"] if isinstance(d.get("data"), dict) else d
    art_t[os.path.basename(p)[:-5]] = d
ts = {"set": 0, "deleted": 0}
os.makedirs(f"{out}/tasks", exist_ok=True)
for t in app.get("tasks", []) or []:
    tid = t.get("id") if isinstance(t, dict) else None
    if not tid: continue
    a = art_t.get(tid)
    if t.get("del"):
        if a is not None:
            if tid not in versions: sys.exit(f"нет версии для задачи {tid} в versions.json")
            writes.append({"op": "delete", "collection": "tasks", "doc_id": tid, "if_version": int(versions[tid])}); ts["deleted"] += 1
        continue
    doc = clean(t)
    if a is not None and clean(a) == doc: continue
    op = {"op": "set", "collection": "tasks", "doc_id": tid}
    if a is not None:
        if tid not in versions: sys.exit(f"нет версии для задачи {tid} в versions.json")
        op["if_version"] = int(versions[tid])
    path = os.path.abspath(f"{out}/tasks/{tid}.json")
    json.dump(doc, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    op["file_path"] = path; writes.append(op); ts["set"] += 1
s["tasks_sync_not_for_report"] = ts

for f in glob.glob(f"{out}/writes_*.json"): os.remove(f)
for i in range(0, len(writes), 50):
    json.dump(writes[i:i + 50], open(f"{out}/writes_{i // 50 + 1}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(s, open(f"{out}/summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"Приложение от {s['app_updated']}: клиентов {s['app_clients']}; новых {len(s['added'])}, изменено {len(s['changed'])}, "
      f"удалено {len(s['deleted'])}, в интернет-версии свежее {len(s['kept_online_newer'])}; задачи: записать {ts['set']}, удалить {ts['deleted']}; пакетов записи: {(len(writes) + 49) // 50}")
