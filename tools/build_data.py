"""Ежедневная сборка данных для приложения WAYTEKO.
python3 tools/build_data.py <папка с выгрузкой clients/*.json> <ГГГГ-ММ-ДД>
Пароль берётся из переменной окружения WAYTEKO_PW. Пишет data/clients.enc.json и data/clients.xlsx.enc.json
(зашифровано AES-256-GCM, ключ из пароля через PBKDF2-SHA256), а также data/meta.json (только время обновления)."""
import os, sys, json, glob, base64, hashlib, subprocess, datetime as dt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

src, day = sys.argv[1], sys.argv[2]
pw = os.environ.get("WAYTEKO_PW") or sys.exit("нет WAYTEKO_PW")
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b64 = lambda b: base64.b64encode(b).decode()

def box(data: bytes, **extra):
    salt, iv, it = os.urandom(16), os.urandom(12), 250000
    key = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, it, 32)
    return {"v": 1, "iter": it, "salt": b64(salt), "iv": b64(iv), "ct": b64(AESGCM(key).encrypt(iv, data, None)), **extra}

clients = []
for p in sorted(glob.glob(os.path.join(src, "*.json"))):
    d = json.load(open(p, encoding="utf-8"))
    d = d["data"] if isinstance(d.get("data"), dict) else d
    d = dict(d); d["id"] = os.path.basename(p)[:-5]
    clients.append(d)
if not clients: sys.exit("выгрузка пустая — ничего не публикую")
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).isoformat(timespec="seconds")
os.makedirs(f"{root}/data", exist_ok=True)
json.dump(box(json.dumps({"updated": now, "clients": clients}, ensure_ascii=False).encode()), open(f"{root}/data/clients.enc.json", "w"))

d = dt.date.fromisoformat(day); name = f"WAYTEKO_клиенты_{d:%d.%m.%Y}.xlsx"
xlsx = f"/tmp/{name}"
subprocess.run([sys.executable, f"{root}/tools/export_vizitki.py", src, xlsx, day], check=True)
json.dump(box(open(xlsx, "rb").read(), name=name), open(f"{root}/data/clients.xlsx.enc.json", "w"))
json.dump({"updated": now}, open(f"{root}/data/meta.json", "w"))
print(f"OK: {len(clients)} клиентов, база от {now}, файл {xlsx}")
