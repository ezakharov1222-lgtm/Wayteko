"""Компактная зашифрованная резервная копия всех данных WAYTEKO для отправки письмом.
python3 tools/backup_pack.py ГГГГ-ММ-ДД <файл_результата.json>
Внутри: общая копия приложения (клиенты, удалённые, гости, задачи; без GitHub-токена) и последний снимок
интернет-версии (клиенты + задачи). Сжато xz и зашифровано тем же паролем (AES-256-GCM, PBKDF2 250k).
Открыть: python3 tools/decrypt.py <файл> out.json. Пароль — из WAYTEKO_PW."""
import os, sys, json, base64, hashlib, lzma, datetime as dt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
day, dst = sys.argv[1], sys.argv[2]
pw = os.environ.get("WAYTEKO_PW") or sys.exit("нет WAYTEKO_PW")
b, e = base64.b64decode, lambda x: base64.b64encode(x).decode()
def dec(p):
    box = json.load(open(p))
    k = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), b(box["salt"]), box["iter"], 32)
    return json.loads(AESGCM(k).decrypt(b(box["iv"]), b(box["ct"]), None))
app = dec("data/app.enc.json") if os.path.exists("data/app.enc.json") else {}
app.pop("gh", None)
online = dec("data/clients.enc.json") if os.path.exists("data/clients.enc.json") else {}
data = {"backup": "WAYTEKO", "date": day, "made": dt.datetime.now(dt.timezone.utc).isoformat(), "app": app, "online": online}
raw = lzma.compress(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), preset=9 | lzma.PRESET_EXTREME)
salt, iv, it = os.urandom(16), os.urandom(12), 250000
key = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, it, 32)
box = {"v": 1, "fmt": "xz-json", "iter": it, "salt": e(salt), "iv": e(iv), "ct": e(AESGCM(key).encrypt(iv, raw, None))}
json.dump(box, open(dst, "w"), separators=(",", ":"))
print(f"клиентов в приложении: {len(app.get('clients', []))}, в интернет-версии: {len(online.get('clients', []))}, "
      f"задач: {len([t for t in app.get('tasks', []) if not t.get('del')])}, гостей: {len(app.get('guests', []))}; файл {os.path.getsize(dst)} байт")
