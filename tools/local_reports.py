import os, sys, json, base64, hashlib, datetime as dt, subprocess
from pathlib import Path
from collections import Counter
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
pw = os.environ["WAYTEKO_PW"].encode()
b = base64.b64decode
e = lambda x: base64.b64encode(x).decode()
box = json.loads(Path("data/app.enc.json").read_text())
key = hashlib.pbkdf2_hmac("sha256", pw, b(box["salt"]), box["iter"], 32)
app = json.loads(AESGCM(key).decrypt(b(box["iv"]), b(box["ct"]), None))
day = dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).date()
iso = day.isoformat()
tom = (day + dt.timedelta(days=1)).isoformat()
clients = [c for c in app["clients"] if c.get("temp") not in ("branch","refused") and c.get("id") not in (app.get("deleted") or [])]
def save(name, value):
    salt, iv = os.urandom(16), os.urandom(12)
    key = hashlib.pbkdf2_hmac("sha256", pw, salt, 250000, 32)
    ct = AESGCM(key).encrypt(iv, value.encode(), None)
    Path(sys.argv[1], name + ".enc.json").write_text(json.dumps({"v":1,"iter":250000,"salt":e(salt),"iv":e(iv),"ct":e(ct)}))
def line(c):
    return " — ".join(str(c.get(k) or "") for k in ("name","fio","phone","next","plan"))
schedule = os.environ.get("SCHEDULE","")
if not schedule or schedule.startswith("40"):
    due = sorted([c for c in clients if c.get("next") and c["next"] <= iso], key=lambda c:(c["next"],c.get("temp")!="hot"))
    save("morning-"+iso, "План звонков "+iso+"\n"+"\n".join(map(line,due)))
if not schedule or schedule.startswith("43"):
    counts = Counter(c.get("temp") for c in clients)
    touches = [(c.get("name"),t.get("t")) for c in clients for t in (c.get("touches") or []) if t.get("d")==iso]
    report = [f"Отчёт WAYTEKO {iso}", f"Клиентов: {len(clients)}", f"Касаний: {len(touches)}", str(dict(counts)), "Завтра:"] + [line(c) for c in clients if c.get("next")==tom] + ["Просрочено:"] + [line(c) for c in clients if c.get("next") and c["next"]<iso]
    save("evening-"+iso, "\n".join(report))
if not schedule or schedule.startswith("17"):
    save("tasks-"+iso, subprocess.check_output([sys.executable,"tools/tasks_report.py","data/app.enc.json",iso],text=True))
