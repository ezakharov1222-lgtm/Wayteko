"""Расшифровка резервных копий WAYTEKO.
python3 tools/decrypt.py WAYTEKO_backup_ДАТА.json out.json  -> еженедельная копия из письма
python3 tools/decrypt.py data/clients.enc.json out.json      -> JSON (клиенты + задачи)
python3 tools/decrypt.py data/app.enc.json out.json          -> общая копия приложения (без токена)
python3 tools/decrypt.py data/clients.xlsx.enc.json out.xlsx -> Excel
Пароль — из WAYTEKO_PW (или спросит)."""
import os, sys, json, base64, hashlib, getpass, lzma
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
src, dst = sys.argv[1], sys.argv[2]
pw = os.environ.get("WAYTEKO_PW") or getpass.getpass("Пароль WAYTEKO: ")
box = json.load(open(src)); b = base64.b64decode
key = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), b(box["salt"]), box["iter"], 32)
raw = AESGCM(key).decrypt(b(box["iv"]), b(box["ct"]), None)
if box.get("fmt") == "xz-json": raw = lzma.decompress(raw)
if raw[:2] == b"PK":
    open(dst, "wb").write(raw)
else:
    d = json.loads(raw)
    if isinstance(d, dict): d.pop("gh", None)  # токен GitHub не выгружаем
    json.dump(d, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("готово:", dst)
