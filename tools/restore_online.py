"""Восстановление интернет-версии из резервной копии (если артефакт пропал или база пустая).
python3 tools/restore_online.py data/clients.enc.json <папка_результата>
(или еженедельная копия из письма WAYTEKO_backup_ДАТА.json — берутся данные приложения)
Пишет writes_N.json (по 50 записей, op "set" в коллекции clients и tasks) для ArtifactData batch
в НОВЫЙ (пустой) артефакт. Пароль — из WAYTEKO_PW."""
import os, sys, json, base64, hashlib, lzma
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
src, out = sys.argv[1], sys.argv[2]
pw = os.environ.get("WAYTEKO_PW") or sys.exit("нет WAYTEKO_PW")
box = json.load(open(src)); b = base64.b64decode
key = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), b(box["salt"]), box["iter"], 32)
raw = AESGCM(key).decrypt(b(box["iv"]), b(box["ct"]), None)
if box.get("fmt") == "xz-json": raw = lzma.decompress(raw)
d = json.loads(raw)
if d.get("backup") == "WAYTEKO": d = d.get("app") or d.get("online") or {}
os.makedirs(f"{out}/docs", exist_ok=True); writes = []
for coll in ("clients", "tasks"):
    for doc in d.get(coll, []) or []:
        doc = dict(doc); did = doc.pop("id", None)
        if not did or (coll == "tasks" and doc.get("del")): continue
        p = os.path.abspath(f"{out}/docs/{coll}_{did}.json")
        json.dump(doc, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        writes.append({"op": "set", "collection": coll, "doc_id": did, "file_path": p})
for i in range(0, len(writes), 50):
    json.dump(writes[i:i+50], open(f"{out}/writes_{i//50+1}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"клиентов и задач к записи: {len(writes)}; пакетов: {(len(writes)+49)//50}")
