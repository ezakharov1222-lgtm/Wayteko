"""Собирает самостоятельное приложение WAYTEKO (PWA) из версии для Claude."""
import re, json, os
SP = os.path.dirname(os.path.abspath(__file__))          # папка src/ репозитория
SRC = f"{SP}/vaitek-crm.html"
OUT = os.environ.get("OUT") or os.path.dirname(SP)       # по умолчанию — корень репозитория
s = open(SRC, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    assert old in s, "NOT FOUND: " + old[:90]
    s = s.replace(old, new, count)

# ---------- шапка документа и шрифты
rep('<title>WAYTEKO</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600;700&family=Unbounded:wght@500;700&display=swap">\n',
    '')
rep('--display:"Unbounded","Golos Text",system-ui,sans-serif;', '--display:ui-rounded,"SF Pro Rounded",-apple-system,system-ui,"Segoe UI",Roboto,sans-serif;')
rep('--body:"Golos Text",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;', '--body:-apple-system,system-ui,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;')
rep('font-weight:400;font-size:15px;width:100%}', 'font-weight:400;font-size:16px;width:100%}')
rep('.filters input{flex:1 1 220px;', '.filters input{font-size:16px;flex:1 1 220px;')
rep('.brand h1{font-family:var(--display);font-weight:700;font-size:22px;margin:0;letter-spacing:.01em;color:var(--steel)}',
    '.brand h1{font-family:var(--display);font-weight:800;font-size:24px;margin:0;letter-spacing:.06em;color:var(--steel)}')
EXTRA_CSS = """
.hdr-actions{display:flex;gap:8px}
.welcome{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:20px;display:grid;gap:12px}
.welcome h2{font-family:var(--display);margin:0;font-size:20px}
.welcome ol{margin:0;padding-left:20px;display:grid;gap:6px}
.filebtn{position:relative;overflow:hidden;display:inline-flex;align-items:center;justify-content:center}
.filebtn input{position:absolute;inset:0;opacity:0;cursor:pointer;font-size:0}
.stack{display:grid;gap:8px}
.stack .btn{text-align:left}
.note{font-size:13px;color:var(--muted)}
.locked header.top,.locked #stats,.locked #tabs,.locked #banner,.locked #overlay{display:none!important}
.locked .wrap{padding-top:max(32px,env(safe-area-inset-top,0px))}
.gpill{display:inline-block;margin-left:8px;padding:1px 8px;border-radius:999px;font-size:12px;font-weight:600;background:var(--green-bg);color:var(--green)}
.gpill.view{background:var(--steel-soft);color:var(--steel)}
.guest #addBtn,.guest #addBtn2,.guest [data-move],.guest [data-focus],.guest [data-meet-open]:not(.meet-on),.guest [data-meet-done],.guest [data-meet-del],
.guest #touchForm,.guest #meetForm,.guest #editDet,.guest .box:has(> [data-askdel]),.guest .actions .lbl,.guest .actions [data-temp]{display:none!important}
.guest #tabs [data-tab="tasks"]{display:none!important}
.tday{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px;font-size:16px}
.trow{display:flex;align-items:flex-start;gap:10px}
.tbody{flex:1;min-width:0;display:grid;gap:2px}
.tact{display:flex;gap:6px;align-items:center;flex:0 0 auto}
.tcheck{width:30px;height:30px;flex:0 0 auto;border-radius:8px;border:2px solid var(--line);background:var(--surface);font-weight:800;font-size:16px;color:var(--surface);padding:0}
.tcheck[aria-pressed="true"]{background:var(--green);border-color:var(--green)}
.ttext{white-space:pre-wrap;overflow-wrap:anywhere;font-size:15px}
.towner{font-size:13px;color:var(--muted)}
.pbadge{border:0;border-radius:999px;padding:2px 10px;font-size:12px;font-weight:700;line-height:1.6}
.pbadge.p-urgent{background:#e5252a;color:#fff}.pbadge.p-high{background:#ffe1b3;color:#8a4b00}.pbadge.p-normal{background:var(--surface-2);color:var(--muted);border:1px solid var(--line)}
.task.prio-urgent{border-left-color:#e5252a;background:linear-gradient(90deg,rgba(229,37,42,.16),var(--surface) 65%);box-shadow:0 0 0 1px rgba(229,37,42,.35)}
.task.prio-high{border-left-color:#f59e0b}
.task.done{opacity:.7;box-shadow:none}.task.done .pbadge{filter:grayscale(1);opacity:.7}
.prio-pick{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:4px}
.prio-pick button{border:1.5px solid var(--line);background:var(--surface);border-radius:8px;padding:9px 4px;font-weight:700;font-size:13px;color:var(--fg)}
.prio-pick button.p-urgent[aria-pressed="true"]{background:#e5252a;border-color:#e5252a;color:#fff}
.prio-pick button.p-high[aria-pressed="true"]{background:#f59e0b;border-color:#f59e0b;color:#2b1700}
.prio-pick button.p-normal[aria-pressed="true"]{background:var(--steel);border-color:var(--steel);color:var(--surface)}
div.f{display:grid;gap:4px;font-size:13px;color:var(--muted);font-weight:600}
.ubanner{display:flex;width:100%;align-items:center;gap:8px;border:0;border-radius:var(--r);background:#e5252a;color:#fff;padding:12px 14px;margin-bottom:12px;font-size:15px;font-weight:600;text-align:left}
.ubanner span{margin-left:auto;font-weight:700}
.tbadge.hot{color:#e5252a}
.guest .ubanner{display:none!important}
.task.done .ttext{text-decoration:line-through;color:var(--muted)}
.tbadge{display:inline-block;margin-left:4px;font-size:12px;font-weight:700;color:var(--red)}
nav.tabs button[aria-selected="true"] .tbadge{color:var(--surface)}
.guest .temps button{pointer-events:none}.guest .temps button[aria-pressed="false"]{display:none}
"""
rep('@media (max-width:640px){', EXTRA_CSS + '@media (max-width:640px){')
HEAD = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>WAYTEKO</title>
<meta name="description" content="CRM дилерской сети Вайтек Премиум">
<meta name="theme-color" content="#1f4e78">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="WAYTEKO">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" type="image/png" href="icon-192.png">
<style>
html{-webkit-text-size-adjust:100%;color-scheme:light}
:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
body{margin:0;font-size:14px}
img{max-width:100%}
[hidden]{display:none!important}
</style>
"""
s = HEAD + s
rep('</style>\n\n<div class="wrap">', '</style>\n</head>\n<body>\n<div class="wrap">')
s = s.rstrip() + "\n</body>\n</html>\n"

# ---------- шапка, баннер
rep('<button class="btn primary" id="addBtn" type="button">+ Новый клиент</button>',
    '<div class="hdr-actions"><button class="btn" id="dataBtn" type="button">⋯ Данные</button><button class="btn primary" id="addBtn" type="button">+ Новый клиент</button></div>')
rep('<div class="brand"><h1>WAYTEKO</h1><div class="date" id="todayLbl"></div></div>',
    '<div class="brand"><h1>WAYTEKO</h1><div class="date"><span id="todayLbl"></span><span id="guestPill" class="gpill" hidden></span></div></div>')
rep('<button role="tab" data-tab="board" aria-selected="false">Воронка</button>',
    '<button role="tab" data-tab="tasks" aria-selected="false">Задачи<span id="tasksBadge" class="tbadge"></span></button>\n    <button role="tab" data-tab="board" aria-selected="false">Воронка</button>')
rep('  else if(tab==="board") view.innerHTML = renderBoard();', '  else if(tab==="tasks") renderTasks();\n  else if(tab==="board") view.innerHTML = renderBoard();')
rep('view.innerHTML = renderToday(over, today, week);', 'view.innerHTML = urgentBanner() + renderToday(over, today, week);')
rep('<nav class="tabs" role="tablist" id="tabs">', '<div id="banner" hidden></div>\n  <nav class="tabs" role="tablist" id="tabs">')

# ---------- хранение на устройстве
rep('''async function save(id, patch){
  if(!db){ toast("Сохранение недоступно в этом просмотре"); return false; }
  try { await db.collection("clients").doc(id).update({...patch, updated: new Date().toISOString()}); return true; }
  catch(e){ toast(e && e.code==="invalid_argument" ? "Нет прав на изменение" : "Не сохранилось, попробуйте ещё раз"); return false; }
}
async function create(data){
  if(!db){ toast("Сохранение недоступно в этом просмотре"); return null; }
  const id = "c" + Date.now().toString(36);
  try { await db.collection("clients").doc(id).set({...data, touches:[], created:new Date().toISOString(), updated:new Date().toISOString()}); return id; }
  catch(e){ toast(e && e.code==="quota_exceeded" ? "База заполнена" : "Не сохранилось, попробуйте ещё раз"); return null; }
}''', '''// ---------- хранение: только на этом устройстве
const KEY = "wayteko.clients.v1", META = "wayteko.meta.v1";
function loadLocal(){ try { const raw = localStorage.getItem(KEY); return raw ? JSON.parse(raw) : []; } catch(e){ return null; } }
function persist(){ if(isGuest()){ toast(GUEST_MSG); return false; } try { localStorage.setItem(KEY, JSON.stringify(clients)); setMeta({rev: (getMeta().rev||0) + 1}); scheduleUpload(); return true; }
  catch(e){ toast("Не сохранилось: память для приложения недоступна"); return false; } }
function getMeta(){ try { return JSON.parse(localStorage.getItem(META) || "{}"); } catch(e){ return {}; } }
function setMeta(p){ try { localStorage.setItem(META, JSON.stringify({...getMeta(), ...p})); } catch(e){} }
const newId = () => "c" + Date.now().toString(36) + Math.random().toString(36).slice(2,6);
async function save(id, patch){
  if(isGuest()){ toast(GUEST_MSG); return false; }
  const i = clients.findIndex(c => c.id===id); if(i<0) return false;
  const prev = clients[i]; clients[i] = {...prev, ...patch, updated: new Date().toISOString()};
  if(!persist()){ clients[i] = prev; return false; }
  render(); return true;
}
async function create(data){
  if(isGuest()){ toast(GUEST_MSG); return null; }
  const now = new Date().toISOString(), id = newId();
  clients.push({...data, id, touches:[], created:now, updated:now});
  if(!persist()){ clients.pop(); return null; }
  render(); return id;
}
function removeClient(id){ if(isGuest()){ toast(GUEST_MSG); return false; } const before = clients; clients = clients.filter(c => c.id!==id);
  const m0 = getMeta(); setMeta({deleted: [...new Set([...(m0.deleted||[]), id])]});
  if(!persist()){ clients = before; setMeta({deleted: m0.deleted||[]}); return false; } return true; }

// ---------- файлы: резервная копия, Excel, календарь
async function giveFile(name, mime, text){
  const blob = new Blob([text], {type: mime});
  try {
    const file = new File([blob], name, {type: mime});
    if(navigator.canShare && navigator.canShare({files:[file]})){ await navigator.share({files:[file], title:name}); return true; }
  } catch(e){ if(e && e.name==="AbortError") return false; }
  const url = URL.createObjectURL(blob), a = document.createElement("a");
  a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000); return true;
}
const stamp = () => { const d = new Date(); return `${pad(d.getDate())}.${pad(d.getMonth()+1)}.${d.getFullYear()}`; };
async function exportBackup(){
  const data = {app:"WAYTEKO", version:1, exported:new Date().toISOString(), clients, tasks: getTasks()};
  if(await giveFile(`WAYTEKO_копия_${stamp()}.json`, "application/json", JSON.stringify(data, null, 1))){ setMeta({lastBackup: todayIso()}); toast("Резервная копия сохранена"); render(); }
}
const TEMP_TXT = {hot:"Горячий", warm:"Тёплый", cold:"Холодный", dealer:"Дилер", branch:"Филиал", refused:"Отказ"};
const dRu = s => s ? s.split("-").reverse().join(".") : "";
async function exportCsv(){
  const n = Math.max(6, ...clients.map(c => (c.touches||[]).filter(t => t && t.t).length));
  const head = ["№","Компания","ИНН","Выручка 2025, млн ₽","ФИО","Должность","Регион","Телефон","Email","Статус","канал связи","знакомство/намерения"];
  for(let i=1;i<=n;i++) head.push(`дата ${i} касания`, `Итоги ${i} касания`);
  head.push("следующая дата созвона","Статус клиента","Следующий шаг");
  const q = v => { const t = String(v ?? "").replace(/\\r?\\n/g," "); return /[";]/.test(t) ? `"${t.replace(/"/g,'""')}"` : t; };
  const rows = [head.map(q).join(";")];
  [...clients].sort((a,b) => (a.created||"").localeCompare(b.created||"")).forEach((c,i) => {
    const t = (c.touches||[]).filter(x => x && x.t), r = [i+1,c.name,c.inn,c.revenue,c.fio,c.position,c.region,c.phone,c.email,c.status,c.channel,c.intro];
    for(let k=0;k<n;k++) r.push(dRu(t[k]?.d||""), t[k]?.t||"");
    r.push(dRu(c.next), TEMP_TXT[c.temp]||"", c.plan||"");
    rows.push(r.map(q).join(";"));
  });
  if(await giveFile(`WAYTEKO_клиенты_${stamp()}.csv`, "text/csv", "\\ufeff" + rows.join("\\r\\n"))) toast("Таблица выгружена");
}
const icsEsc = s => String(s||"").replace(/\\\\/g,"\\\\\\\\").replace(/([,;])/g,"\\\\$1").replace(/\\r?\\n/g,"\\\\n");
async function exportIcs(c){
  if(!c.next){ toast("Сначала поставьте дату созвона"); return; }
  const d = c.next.replace(/-/g,""), lt = lastTouch(c), now = new Date().toISOString().replace(/[-:]/g,"").replace(/\\.\\d+/,"");
  const desc = [c.phone && "Телефон: "+c.phone, c.fio && "Контакт: "+c.fio, lt && "Было: "+lt.t, "Шаг: "+(c.plan || recFor(c))].filter(Boolean).join("\\n");
  const ics = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//WAYTEKO//CRM//RU","CALSCALE:GREGORIAN","BEGIN:VEVENT",
    `UID:${c.id}-${d}@wayteko`, `DTSTAMP:${now}`, `DTSTART:${d}T090000`, `DTEND:${d}T091500`,
    `SUMMARY:${icsEsc("Звонок: "+c.name)}`, `DESCRIPTION:${icsEsc(desc)}`,
    "BEGIN:VALARM","ACTION:DISPLAY",`DESCRIPTION:${icsEsc("Звонок: "+c.name)}`,"TRIGGER:PT0M","END:VALARM","END:VEVENT","END:VCALENDAR"].join("\\r\\n");
  if(await giveFile(`Звонок_${c.name.replace(/[^\\wА-Яа-яЁё]+/g,"_").slice(0,40)}.ics`, "text/calendar", ics)) toast("Откройте файл, чтобы добавить в календарь");
}
let pendingImport = null, pendingTasks = null;
function normalizeImport(list){
  return list.filter(x => x && typeof x==="object" && x.name).map(x => ({...x, id: x.id || newId(), touches: Array.isArray(x.touches) ? x.touches.filter(t => t && t.t) : [], temp: TEMPS[x.temp] ? x.temp : "warm"}));
}
function applyImport(mode){
  if(!pendingImport) return;
  if(isGuest()){ pendingImport = null; toast(GUEST_MSG); return; }
  const before = clients;
  if(mode==="replace") clients = pendingImport;
  else { const ids = new Set(clients.map(c => c.id)), names = new Set(clients.map(c => c.name.trim().toLowerCase()));
    clients = [...clients, ...pendingImport.filter(c => !ids.has(c.id) && !names.has(c.name.trim().toLowerCase()))]; }
  if(!persist()){ clients = before; return; }
  const added = clients.length - (mode==="replace" ? 0 : before.length);
  let tAdded = 0;
  if(Array.isArray(pendingTasks) && pendingTasks.length && !isGuest()) tAdded = mergeTaskList(pendingTasks);
  pendingTasks = null;
  if(tAdded) toast(`Задач восстановлено: ${tAdded}`);
  pendingImport = null; if(!tAdded) toast(mode==="replace" ? `Загружено клиентов: ${clients.length}` : `Добавлено новых: ${added}`); render();
}
function renderDataPanel(){
  const m = getMeta(), last = m.lastBackup ? fmt(m.lastBackup) + " " + m.lastBackup.slice(0,4) : "ещё не сохранялась";
  return `<div class="scrim" data-close></div><aside class="panel" role="dialog" aria-label="Данные">
    <div class="head"><h2>Данные</h2><button class="btn ghost" data-close type="button" aria-label="Закрыть">✕</button></div>
    <div class="box"><h4>Обновление из интернет-версии</h4>
      <div>Клиентов: <b>${clients.length}</b>. База: <b>${m.lastSync ? esc(fmtStamp(m.lastSync)) : "ещё не загружалась"}</b>${syncState.status==="offline" ? " · сейчас нет связи" : ""}.</div>
      <div class="note">Раз в сутки свежая база из интернет-версии WAYTEKO выкладывается в зашифрованном виде, и приложение подтягивает её при открытии.</div>
      <div class="stack">
        <button class="btn primary" data-act="xlsx" type="button">📥 Скачать файл клиентов (Excel)</button>
        <button class="btn" data-act="sync" type="button">🔄 Обновить сейчас</button></div></div>
    ${uploadBox()}
    ${guestBox()}
    <div class="box"><h4>Резервная копия</h4>
      <div class="note">Последняя резервная копия этого устройства: ${esc(last)}.</div></div>
    ${pendingImport ? `<div class="box"><h4>Загрузка файла</h4><div>В файле клиентов: <b>${pendingImport.length}</b>. Сейчас в приложении: <b>${clients.length}</b>.</div>
      <div class="actions"><button class="btn primary small" data-act="imp-replace" type="button">Заменить всё</button>
      <button class="btn small" data-act="imp-merge" type="button">Добавить только новых</button>
      <button class="btn ghost small" data-act="imp-cancel" type="button">Отмена</button></div></div>` : ""}
    <div class="box"><h4>Действия</h4><div class="stack">
      <button class="btn" data-act="backup" type="button">💾 Сохранить резервную копию (.json)</button>
      <label class="btn filebtn" for="importFile">📥 Загрузить клиентов из файла (.json)<input id="importFile" type="file" accept=".json,application/json"></label>
      <button class="btn" data-act="csv" type="button">📊 Выгрузить таблицу для Excel (.csv)</button></div>
      <div class="note">Резервную копию можно сохранить в «Файлы», отправить себе на почту или в мессенджер. Тем же файлом база переносится на другой телефон или компьютер.</div></div>
    <div class="box"><button class="btn ghost small" data-act="logout" type="button">Сменить пароль на этом устройстве</button></div>
  </aside>`;
}
function welcomeHtml(){
  return `<div class="welcome"><h2>Добро пожаловать в WAYTEKO</h2>
    <div>Клиентов пока нет. Загрузите базу из файла резервной копии или добавьте первого клиента вручную.</div>
    <ol><li>Сохраните файл <b>WAYTEKO_база….json</b> в «Файлы» на телефоне.</li><li>Нажмите «Загрузить из файла» и выберите его.</li></ol>
    <div class="actions"><label class="btn primary filebtn" for="importFile0">📥 Загрузить из файла<input id="importFile0" type="file" accept=".json,application/json"></label>
    <button class="btn" type="button" id="addBtn2">+ Новый клиент</button></div></div>`;
}''')

# ---------- календарь встречи (с напоминанием за 3 дня)
rep('let pendingImport = null, pendingTasks = null;', r'''async function exportMeetIcs(c, m){
  const pad2 = n => String(n).padStart(2,"0");
  const st = new Date(`${m.d}T${m.t || "10:00"}:00`), en = new Date(st.getTime() + 36e5);
  const f = x => `${x.getFullYear()}${pad2(x.getMonth()+1)}${pad2(x.getDate())}T${pad2(x.getHours())}${pad2(x.getMinutes())}00`;
  const now = new Date().toISOString().replace(/[-:]/g,"").replace(/\.\d+/,"");
  const desc = ["Цель: " + (m.note || "—"), c.fio && "Контакт: " + c.fio, c.phone && "Телефон: " + c.phone].filter(Boolean).join("\n");
  const ics = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//WAYTEKO//CRM//RU","CALSCALE:GREGORIAN","BEGIN:VEVENT",
    `UID:${m.id}@wayteko`, `DTSTAMP:${now}`, `DTSTART:${f(st)}`, `DTEND:${f(en)}`,
    `SUMMARY:${icsEsc("Встреча: " + c.name)}`, `LOCATION:${icsEsc(m.place || "")}`, `DESCRIPTION:${icsEsc(desc)}`,
    "BEGIN:VALARM","ACTION:DISPLAY",`DESCRIPTION:${icsEsc("Через 3 дня встреча: " + c.name)}`,"TRIGGER:-P3D","END:VALARM",
    "BEGIN:VALARM","ACTION:DISPLAY",`DESCRIPTION:${icsEsc("Встреча через 15 минут: " + c.name)}`,"TRIGGER:-PT15M","END:VALARM",
    "END:VEVENT","END:VCALENDAR"].join("\r\n");
  if(await giveFile(`Встреча_${c.name.replace(/[^\wА-Яа-яЁё]+/g,"_").slice(0,40)}_${m.d}.ics`, "text/calendar", ics)) toast("Откройте файл, чтобы добавить в календарь");
}
let pendingImport = null, pendingTasks = null;''')

# ---------- ежедневное обновление из интернет-версии (зашифрованный снимок)
rep('// ---------- файлы: резервная копия, Excel, календарь', r'''// ---------- обновление из интернет-версии
const PWKEY = "wayteko.pw.v1";
let syncState = {status:"", updated:"", needPw:false};
const b64d = s => Uint8Array.from(atob(s), ch => ch.charCodeAt(0));
async function openBox(box, pw){
  const k0 = await crypto.subtle.importKey("raw", new TextEncoder().encode(pw), "PBKDF2", false, ["deriveKey"]);
  const k = await crypto.subtle.deriveKey({name:"PBKDF2", salt:b64d(box.salt), iterations:box.iter, hash:"SHA-256"}, k0, {name:"AES-GCM", length:256}, false, ["decrypt"]);
  return new Uint8Array(await crypto.subtle.decrypt({name:"AES-GCM", iv:b64d(box.iv)}, k, b64d(box.ct)));
}
function getPw(){ try { return localStorage.getItem(PWKEY) || ""; } catch(e){ return ""; } }
function setPw(p){ try { p ? localStorage.setItem(PWKEY, p) : localStorage.removeItem(PWKEY); } catch(e){} }
function mergeSnapshot(list){
  const byId = new Map(clients.map(c => [c.id, c])), del = new Set(getMeta().deleted || []); let added = 0, changed = 0;
  for(const r of list){ if(del.has(r.id)) continue; const l = byId.get(r.id);
    if(!l){ byId.set(r.id, r); added++; }
    else if((r.updated||"") > (l.updated||"")){ byId.set(r.id, r); changed++; } }
  clients = [...byId.values()]; return {added, changed};
}
const fmtStamp = s => { if(!s) return ""; const d = new Date(s); return `${d.getDate()} ${MON[d.getMonth()]}, ${pad(d.getHours())}:${pad(d.getMinutes())}`; };
let syncBusy = false;
async function syncNow(pwTry, manual){
  if(syncBusy) return; syncBusy = true;
  try {
    if(isGuest() && !pwTry){ await guestSync(getPw(), manual, false); return; }
    let box;
    try { const r = await fetch("data/clients.enc.json?t=" + Date.now(), {cache:"no-store"}); if(!r.ok) throw 0; box = await r.json(); }
    catch(e){ syncState.status = "offline"; if(manual) toast("Нет связи — работаю с сохранёнными данными"); render(); return; }
    const pw = pwTry || getPw();
    if(!pw){ syncState.needPw = true; render(); return; }
    let snap;
    try { snap = JSON.parse(new TextDecoder().decode(await openBox(box, pw))); }
    catch(e){ if(pwTry && await guestSync(pwTry, manual, true)) return; if(pwTry) toast("Неверный пароль"); else setPw(""); syncState.needPw = true; render(); return; }
    setPw(pw); syncState.needPw = false; syncState.updated = snap.updated; syncState.status = "ok";
    const m = getMeta();
    if(m.lastSync !== snap.updated){
      if(Array.isArray(snap.tasks) && snap.tasks.length && !isGuest()) mergeTaskList(snap.tasks);
      const before = clients, res = mergeSnapshot(normalizeImport(snap.clients || []));
      if(!persist()){ clients = before; render(); return; }
      setMeta({lastSync: snap.updated, lastSyncAt: new Date().toISOString()});
      if(m.lastSync && (res.added || res.changed)) toast(`Обновлено: новых ${res.added}, изменено ${res.changed}`);
      else if(!m.lastSync) toast(`Загружено клиентов: ${clients.length}`);
    } else if(manual) toast("Данные уже свежие");
    render();
  } finally { syncBusy = false; if(isDirty()) scheduleUpload(); if(!isGuest() && getPw()){ syncShared(); startShare(); } }
}

// ---------- отправка из приложения в репозиторий (приложение — главный источник)
const GHKEY = "wayteko.gh.v1", REPO = "ezakharov1222-lgtm/wayteko", UPATH = "data/app.enc.json";
function getGh(){ try { return localStorage.getItem(GHKEY) || ""; } catch(e){ return ""; } }
function setGh(t){ try { t ? localStorage.setItem(GHKEY, t) : localStorage.removeItem(GHKEY); } catch(e){} }
const isDirty = () => { const m = getMeta(); return (m.rev||0) !== (m.upRev||0); };
const b64e = u8 => { let s = ""; for(let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000)); return btoa(s); };
async function sealBox(bytes, pw){
  const salt = crypto.getRandomValues(new Uint8Array(16)), iv = crypto.getRandomValues(new Uint8Array(12)), iter = 250000;
  const k0 = await crypto.subtle.importKey("raw", new TextEncoder().encode(pw), "PBKDF2", false, ["deriveKey"]);
  const k = await crypto.subtle.deriveKey({name:"PBKDF2", salt, iterations:iter, hash:"SHA-256"}, k0, {name:"AES-GCM", length:256}, false, ["encrypt"]);
  return {v:1, iter, salt:b64e(salt), iv:b64e(iv), ct:b64e(new Uint8Array(await crypto.subtle.encrypt({name:"AES-GCM", iv}, k, bytes)))};
}
const ghHeaders = tok => ({Authorization: "Bearer " + tok, Accept: "application/vnd.github+json"});
let upTimer = null, upBusy = false;
function scheduleUpload(){ if(isGuest() || !getGh() || !getPw()) return; clearTimeout(upTimer); upTimer = setTimeout(() => uploadNow(), 1500); }
async function uploadNow(manual){
  const tok = getGh(), pw = getPw();
  if(!tok || !pw){ if(manual) toast("Сначала подключите отправку"); return false; }
  if(upBusy){ scheduleUpload(); return false; }
  upBusy = true; const rev = getMeta().rev || 0;
  try {
    let stampUp = "";
    for(let attempt = 0; attempt < 3; attempt++){
      try { const sh = await fetchShared(); if(sh && sh.updated !== getMeta().sharedSeen){ const res = mergeShared(sh); if(res.changed){ saveLocalOnly(); render(); } } }
      catch(e){ if(e && e.message === "token") throw e; }
      stampUp = new Date().toISOString();
      const body = JSON.stringify({updated: stampUp, clients, deleted: getMeta().deleted || [], guests: getGuests(), tasks: getTasks(), gh: tok});
      const box = await sealBox(new TextEncoder().encode(body), pw);
      try { await putFile(tok, UPATH, box, "Данные из приложения [skip ci]"); break; }
      catch(e){ if(e && e.message === "conflict" && attempt < 2) continue; throw e; }
    }
    if(activeGuests().length) await putGuestCopies(tok).catch(() => {});
    setMeta({upRev: rev, lastUpload: new Date().toISOString(), upErr: "", sharedSeen: stampUp});
    if(manual) toast("Отправлено");
    return true;
  } catch(e){
    setMeta({upErr: e.message==="token" ? "Токен не подходит или истёк — подключите заново" : "Нет связи — отправлю при следующем открытии"});
    if(manual) toast(getMeta().upErr); return false;
  } finally { upBusy = false; if(openId==="data") renderPanel(); if(isDirty() && getMeta().upRev===rev && !getMeta().upErr) scheduleUpload(); }
}
// ---------- синхронизация между устройствами владельца (общая зашифрованная копия data/app.enc.json)
let shareBusy = false, shareTimer = null;
async function fetchShared(){
  const tok = getGh(), h = tok ? {...ghHeaders(tok), Accept: "application/vnd.github.raw"} : {Accept: "application/vnd.github.raw"};
  const r = await fetch(`https://api.github.com/repos/${REPO}/contents/${UPATH}?ref=main&t=${Date.now()}`, {headers: h, cache: "no-store"});
  if(r.status === 404) return null;
  if(r.status === 401) throw new Error("token");
  if(!r.ok) throw new Error("http");
  return JSON.parse(new TextDecoder().decode(await openBox(await r.json(), getPw())));
}
function mergeShared(sh){
  const myDel = getMeta().deleted || [], del = new Set([...myDel, ...(sh.deleted || [])]);
  const remote = new Map((sh.clients || []).filter(c => c && c.id).map(c => [c.id, c]));
  let changed = 0, localAhead = myDel.some(id => !(sh.deleted || []).includes(id));
  const out = [];
  for(const c of clients){
    if(del.has(c.id)){ changed++; continue; }
    const r = remote.get(c.id);
    if(r && (r.updated || "") > (c.updated || "")){ out.push(r); changed++; }
    else { out.push(c); if(!r || (c.updated || "") > (r.updated || "")) localAhead = true; }
  }
  const have = new Set(out.map(c => c.id));
  for(const [id, r] of remote) if(!have.has(id) && !del.has(id)){ out.push(r); changed++; }
  clients = out;
  if(del.size > myDel.length) setMeta({deleted: [...del]});
  let rgl = Array.isArray(sh.guests) ? sh.guests : null;
  if(!rgl && sh.guest && sh.guest.pw) rgl = [{id: "g1", name: sh.guest.name || "", pw: sh.guest.pw, updated: sh.guest.created || "", legacy: true}];
  if(!rgl && sh.guest && sh.guest.off) rgl = [{id: "g1", off: true, updated: sh.guest.created || ""}];
  rgl = rgl || [];
  const lgm = new Map(getGuests().map(g => [g.id, g])); let gch = false;
  for(const r of rgl){ const l = lgm.get(r.id);
    if(!l || (r.updated || "") > (l.updated || "")){ lgm.set(r.id, r); gch = true; }
    else if((l.updated || "") > (r.updated || "")) localAhead = true; }
  for(const id of lgm.keys()) if(!rgl.some(r => r.id === id)) localAhead = true;
  if(gch){ setGuests([...lgm.values()]); guestSeen = {}; changed++; }
  const rt = Array.isArray(sh.tasks) ? sh.tasks : [];
  const ltm = new Map(getTasks().map(t => [t.id, t])); let tch = false;
  for(const r of rt){ if(!r || !r.id) continue; const l = ltm.get(r.id);
    if(!l || (r.updated || "") > (l.updated || "")){ ltm.set(r.id, r); tch = true; }
    else if((l.updated || "") > (r.updated || "")) localAhead = true; }
  for(const id of ltm.keys()) if(!rt.some(r => r && r.id === id)) localAhead = true;
  if(tch){ setTasks([...ltm.values()]); changed++; }
  if(!getGh() && sh.gh){ setGh(sh.gh); setMeta({upErr: "", ghFromDevice: true}); }
  return {changed, localAhead};
}
async function syncShared(manual){
  if(isGuest() || !getPw() || shareBusy || upBusy) return;
  shareBusy = true;
  try {
    const sh = await fetchShared();
    if(!sh){ if(manual) toast("Других устройств пока нет"); return; }
    if(sh.updated === getMeta().sharedSeen){ if(manual) toast("Все устройства синхронизированы"); return; }
    const res = mergeShared(sh);
    setMeta({sharedSeen: sh.updated, sharedAt: new Date().toISOString()});
    if(res.changed){ saveLocalOnly(); toast("Обновлено с другого вашего устройства"); }
    else if(manual) toast("Все устройства синхронизированы");
    if(res.localAhead){ setMeta({rev: (getMeta().rev || 0) + 1}); scheduleUpload(); }
    render(); renderGuestPill(); if(activeGuests().length) checkGuest();
  } catch(e){ if(manual) toast(e && e.message === "token" ? "Токен не подходит" : "Нет связи с другими устройствами"); }
  finally { shareBusy = false; }
}
function startShare(){
  if(shareTimer || isGuest()) return;
  shareTimer = setInterval(() => { if(!document.hidden && !isGuest() && getPw()) syncShared(); }, getGh() ? 60000 : 180000);
}
// ---------- задачи на день (видит только владелец; в гостевые копии не попадают)
const TASKKEY = "wayteko.tasks.v1";
let taskDay = todayIso(), taskPrio = "normal";
const PRIO = {urgent: {l: "🔴 Срочно", r: 0}, high: {l: "🟠 Важно", r: 1}, normal: {l: "⚪ Обычно", r: 2}};
const prioOf = t => PRIO[t && t.prio] ? t.prio : "normal";
const byPrio = (a, b) => (a.done ? 1 : 0) - (b.done ? 1 : 0) || PRIO[prioOf(a)].r - PRIO[prioOf(b)].r || (a.created || "").localeCompare(b.created || "");
function urgentCount(){ const d = todayIso(); return liveTasks().filter(t => !t.done && t.d <= d && prioOf(t) === "urgent").length; }
function urgentBanner(){
  if(isGuest()) return ""; const n = urgentCount();
  return n ? `<button class="ubanner" data-go="tasks" type="button">🔴 Срочные задачи: <b>${n}</b><span>Открыть ›</span></button>` : "";
}
function getTasks(){ try { const v = JSON.parse(localStorage.getItem(TASKKEY) || "[]"); return Array.isArray(v) ? v : []; } catch(e){ return []; } }
function setTasks(l){ try { localStorage.setItem(TASKKEY, JSON.stringify(l)); } catch(e){} }
function saveTasks(l){
  if(isGuest()){ toast(GUEST_MSG); return false; }
  setTasks(l); setMeta({rev: (getMeta().rev || 0) + 1}); scheduleUpload(); return true;
}
const liveTasks = () => getTasks().filter(t => t && !t.del);
function openTasksCount(){ const d = todayIso(); return liveTasks().filter(t => !t.done && t.d <= d).length; }
function renderTasksBadge(){
  const el = document.getElementById("tasksBadge"); if(!el) return;
  const n = isGuest() ? 0 : openTasksCount(), u = isGuest() ? 0 : urgentCount();
  el.textContent = n ? " " + (u ? "🔴" : "") + n : ""; el.classList.toggle("hot", !!u);
}
function taskRow(t, old){
  const c = t.cid ? clients.find(x => x.id === t.cid) : null;
  const who = c ? `<button class="name" data-open="${c.id}" type="button">${esc(c.name)}</button>` : (t.cname ? `<b>${esc(t.cname)}</b>` : "");
  const p = prioOf(t);
  return `<article class="card task prio-${p} ${t.done ? "done" : ""}"><div class="trow">
    <button class="tcheck" data-tdone="${esc(t.id)}" aria-pressed="${!!t.done}" type="button" aria-label="${t.done ? "Снять отметку" : "Отметить выполненной"}">${t.done ? "✓" : ""}</button>
    <div class="tbody"><div><button class="pbadge p-${p}" data-tprio-cycle="${esc(t.id)}" type="button" title="Сменить срочность">${PRIO[p].l}</button></div>${who}<div class="ttext">${esc(t.text)}</div>${t.owner ? `<div class="towner">👤 ${esc(t.owner)}</div>` : ""}${old ? `<div class="muted" style="font-size:12px">было на ${esc(fmtW(t.d))}</div>` : ""}</div>
    <div class="tact">${old ? `<button class="btn small" data-tmove="${esc(t.id)}" type="button">На сегодня</button>` : ""}
      <button class="btn ghost small" data-tdel="${esc(t.id)}" type="button" aria-label="Удалить задачу">✕</button></div></div></article>`;
}
function renderTasks(force){
  if(isGuest()){ tab = "today"; render(); return; }
  const ae = document.activeElement;
  if(!force && ae && view.contains(ae) && /INPUT|TEXTAREA/.test(ae.tagName) && view.querySelector("#taskForm")) return;
  const today = todayIso(), all = liveTasks();
  const day = all.filter(t => t.d === taskDay).sort(byPrio);
  const over = taskDay === today ? all.filter(t => !t.done && t.d < today).sort((a, b) => PRIO[prioOf(a)].r - PRIO[prioOf(b)].r || a.d.localeCompare(b.d)) : [];
  const opts = clients.filter(c => c.temp !== "refused").sort((a, b) => a.name.localeCompare(b.name, "ru")).map(c => `<option value="${esc(c.name)}"></option>`).join("");
  const keep = view.querySelector("#tk_client")?.value || "", keepT = view.querySelector("#tk_text")?.value || "";
  const keepO = view.querySelector("#tk_owner") ? view.querySelector("#tk_owner").value : (getMeta().lastOwner || "");
  const owners = [...new Set(getTasks().map(t => (t.owner || "").trim()).filter(Boolean))].sort((a, b) => a.localeCompare(b, "ru")).map(o => `<option value="${esc(o)}"></option>`).join("");
  view.innerHTML = `<div class="tday"><button class="btn small" data-tday="-1" type="button" aria-label="Предыдущий день">‹</button>
      <b>${taskDay === today ? "Сегодня, " : taskDay === addDays(null, 1) ? "Завтра, " : ""}${esc(fmtW(taskDay))}</b>
      <button class="btn small" data-tday="1" type="button" aria-label="Следующий день">›</button>
      ${taskDay !== today ? `<button class="btn small" data-tday="0" type="button">Сегодня</button>` : ""}</div>
    <form id="taskForm" class="box"><h4>Новая задача${taskDay !== today ? " на " + esc(fmt(taskDay)) : ""}</h4>
      <label class="f">Клиент (необязательно)<input id="tk_client" list="tk_clients" placeholder="Начните вводить название" autocomplete="off" value="${esc(keep)}"></label>
      <datalist id="tk_clients">${opts}</datalist>
      <label class="f">Ответственный<input id="tk_owner" list="tk_owners" placeholder="Кто выполняет задачу" autocomplete="off" maxlength="60" value="${esc(keepO)}"></label>
      <datalist id="tk_owners">${owners}</datalist>
      <div class="f">Срочность<div class="prio-pick" role="radiogroup" aria-label="Срочность">${Object.keys(PRIO).map(k => `<button type="button" class="p-${k}" data-tprio="${k}" role="radio" aria-checked="${taskPrio === k}" aria-pressed="${taskPrio === k}">${PRIO[k].l}</button>`).join("")}</div></div>
      <label class="f">Задача<textarea id="tk_text" placeholder="Например: отправить КП, согласовать встречу, проверить оплату" required>${esc(keepT)}</textarea></label>
      <button class="btn primary" type="submit">Добавить задачу</button></form>
    <h2 class="sec">📋 Задачи на ${taskDay === today ? "сегодня" : esc(fmt(taskDay))} <span class="n">${day.filter(t => !t.done).length} из ${day.length} осталось</span></h2>
    ${day.length ? `<div class="list">${day.map(t => taskRow(t, false)).join("")}</div>` : `<div class="empty">Задач на этот день нет.</div>`}
    ${over.length ? `<h2 class="sec">⏰ Не выполнено раньше <span class="n">${over.length}</span></h2><div class="list">${over.map(t => taskRow(t, true)).join("")}</div>` : ""}
    <p class="note" style="margin-top:14px">🔒 Задачи видите только вы — на всех своих устройствах. Гостям они не показываются и в их копии не попадают.</p>`;
}
function mergeTaskList(list){
  const m = new Map(getTasks().map(t => [t.id, t])); let n = 0;
  for(const r of list){ if(!r || !r.id) continue; const l = m.get(r.id);
    if(!l || (r.updated || "") > (l.updated || "")){ m.set(r.id, r); n++; } }
  if(n){ saveTasks([...m.values()]); renderTasksBadge(); }
  return n;
}
function taskUpdate(id, fn){
  const l = getTasks(), t = l.find(x => x.id === id); if(!t) return;
  fn(t); t.updated = new Date().toISOString();
  if(saveTasks(l)){ renderTasks(true); renderTasksBadge(); }
}
// ---------- гостевой доступ (только просмотр, до 4 гостей) и «в сети»
const ROLEKEY = "wayteko.role.v1", GUESTKEY = "wayteko.guests.v2", OLDGUESTKEY = "wayteko.guest.v1", GPATH = "data/app.guest.enc.json", NTFY = "https://ntfy.sh/", MAXG = 4;
const GUEST_MSG = "Гостевой доступ: только просмотр";
const APP_URL = "https://ezakharov1222-lgtm.github.io/Wayteko/";
const TABNAME = {today:"Сегодня", board:"Воронка", all:"Все клиенты", arch:"Филиал и отказы", data:"Данные"};
function getRole(){ try { return localStorage.getItem(ROLEKEY) || ""; } catch(e){ return ""; } }
function setRole(r){ try { r ? localStorage.setItem(ROLEKEY, r) : localStorage.removeItem(ROLEKEY); } catch(e){} applyRole(); }
function isGuest(){ return getRole() === "guest"; }
function applyRole(){ document.documentElement.classList.toggle("guest", isGuest()); }
function setGuests(l){ try { localStorage.setItem(GUESTKEY, JSON.stringify(l)); } catch(e){} }
function getGuests(){
  try { const v = JSON.parse(localStorage.getItem(GUESTKEY) || "null"); if(Array.isArray(v)) return v; } catch(e){}
  let old = {}; try { old = JSON.parse(localStorage.getItem(OLDGUESTKEY) || "{}"); } catch(e){}
  const list = old.pw ? [{id: "g1", name: old.name || "", pw: old.pw, updated: old.created || new Date().toISOString(), legacy: true}] : [];
  setGuests(list); return list;
}
const activeGuests = () => getGuests().filter(g => g.pw && !g.off);
function saveLocalOnly(){ try { localStorage.setItem(KEY, JSON.stringify(clients)); } catch(e){} }
function genGuestPw(){ const a = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789", r = crypto.getRandomValues(new Uint8Array(12)); let o = "G"; for(let i = 0; i < 12; i++){ if(i % 4 === 0) o += "-"; o += a.at(r.at(i) % a.length); } return o; }
async function hex16(s){ const h = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s))); return Array.from(h.slice(0, 8), b => b.toString(16).padStart(2, "0")).join(""); }
const pathForPw = async pw => `data/g-${await hex16("wayteko-guest:" + pw)}.enc.json`;
const guestPath = async g => g.legacy ? GPATH : pathForPw(g.pw);
async function putFile(tok, path, box, message){
  const api = `https://api.github.com/repos/${REPO}/contents/${path}`;
  const g = await fetch(api + "?ref=main", {headers: ghHeaders(tok), cache: "no-store"});
  if(g.status===401 || g.status===403) throw new Error("token");
  const sha = g.ok ? (await g.json()).sha : undefined;
  const r = await fetch(api, {method:"PUT", headers:{...ghHeaders(tok), "Content-Type":"application/json"},
    body: JSON.stringify({message, content: btoa(JSON.stringify(box)), branch:"main", ...(sha ? {sha} : {})})});
  if(r.status===409 || r.status===422) throw new Error("conflict");
  if(r.status===401 || r.status===403 || r.status===404) throw new Error("token");
  if(!r.ok) throw new Error("http");
}
async function deleteFile(tok, path, message){
  const api = `https://api.github.com/repos/${REPO}/contents/${path}`;
  const g = await fetch(api + "?ref=main", {headers: ghHeaders(tok), cache: "no-store"});
  if(g.status===404) return;
  if(g.status===401 || g.status===403) throw new Error("token");
  if(!g.ok) throw new Error("http");
  const r = await fetch(api, {method:"DELETE", headers:{...ghHeaders(tok), "Content-Type":"application/json"}, body: JSON.stringify({message, sha:(await g.json()).sha, branch:"main"})});
  if(!r.ok) throw new Error("http");
}
async function putOneGuest(tok, g){
  const body = JSON.stringify({updated: new Date().toISOString(), clients, guestName: g.name || ""});
  await putFile(tok, await guestPath(g), await sealBox(new TextEncoder().encode(body), g.pw), "Гостевая копия [skip ci]");
}
async function putGuestCopies(tok){ for(const g of activeGuests()){ try { await putOneGuest(tok, g); } catch(e){ if(e && e.message === "conflict") { try { await putOneGuest(tok, g); } catch(_){} } } } }
async function fetchBoxAt(path){
  const r = await fetch(`https://api.github.com/repos/${REPO}/contents/${path}?ref=main&t=${Date.now()}`, {headers:{Accept:"application/vnd.github.raw"}, cache:"no-store"});
  if(r.status === 404) return null;
  if(!r.ok) throw new Error("http");
  return await r.json();
}
async function fetchGuestBox(pw){ return (await fetchBoxAt(await pathForPw(pw))) || (await fetchBoxAt(GPATH)); }
function guestRevoked(){
  beat("off"); setPw(""); setRole(""); clients = []; saveLocalOnly(); setMeta({lastSync: null});
  syncState.needPw = true; closePanel(); toast("Гостевой доступ изменён или отключён владельцем"); render();
}
async function guestSync(pw, manual, login){
  let box;
  try { box = await fetchGuestBox(pw); }
  catch(e){ if(login) return false; syncState.status = "offline"; if(manual) toast("Нет связи — показываю сохранённые данные"); render(); return true; }
  if(!box){ if(!login) guestRevoked(); return false; }
  let snap;
  try { snap = JSON.parse(new TextDecoder().decode(await openBox(box, pw))); }
  catch(e){ if(!login) guestRevoked(); return false; }
  setPw(pw); setRole("guest"); setTasks([]); syncState.needPw = false; syncState.status = "ok"; syncState.updated = snap.updated;
  clients = normalizeImport(snap.clients || []); saveLocalOnly();
  setMeta({lastSync: snap.updated, guestName: snap.guestName || ""});
  if(login) toast("Гостевой доступ: только просмотр");
  else if(manual) toast("Данные обновлены");
  render(); startPresence(); return true;
}
async function presenceTopic(gpw){
  const h = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode("wayteko-presence:" + gpw)));
  return "wtk" + Array.from(h.slice(0, 12), b => b.toString(16).padStart(2, "0")).join("");
}
async function beat(state){
  if(!isGuest() || !getPw()) return;
  try { const t = await presenceTopic(getPw());
    fetch(NTFY + t, {method:"POST", body: JSON.stringify({s: state, tab: openId==="data" ? "data" : tab}), keepalive: true}).catch(() => {}); } catch(e){}
}
let presTimer = null;
function startPresence(){
  if(presTimer || !isGuest()) return;
  beat("on");
  presTimer = setInterval(() => { if(!document.hidden && isGuest()){ beat("on"); syncNow(); } }, 120000);
}
let guestSeen = {};
async function seenFor(g){
  try {
    const r = await fetch(`${NTFY}${await presenceTopic(g.pw)}/json?poll=1&since=12h`, {cache:"no-store"}); if(!r.ok) throw 0;
    const ev = (await r.text()).split("\n").map(l => { try { return JSON.parse(l); } catch(e){ return null; } }).filter(x => x && x.event === "message");
    const last = ev.at(-1);
    if(!last) return {online:false, at:null};
    let p = {}; try { p = JSON.parse(last.message); } catch(e){}
    return {online: p.s === "on" && Date.now()/1000 - last.time < 170, at: last.time * 1000, tab: p.tab};
  } catch(e){ const prev = guestSeen[g.id]; return prev && !prev.err ? prev : {online:false, at:null, err:true}; }
}
async function checkGuest(){
  const list = activeGuests(); if(!list.length || isGuest()){ guestSeen = {}; renderGuestPill(); return; }
  const res = await Promise.all(list.map(seenFor)); const next = {};
  list.forEach((g, i) => { next[g.id] = res.at(i); }); guestSeen = next;
  renderGuestPill();
  const a = document.activeElement;
  if(openId==="data" && !(a && overlay.contains(a) && /INPUT|TEXTAREA/.test(a.tagName))) renderPanel();
}
function renderGuestPill(){
  const el = document.getElementById("guestPill"); if(!el) return;
  if(isGuest()){ el.hidden = false; el.className = "gpill view"; el.textContent = "👁 Гость · только просмотр"; return; }
  const on = activeGuests().filter(g => guestSeen[g.id] && guestSeen[g.id].online).map(g => g.name || "Гость");
  if(on.length){ el.hidden = false; el.className = "gpill"; el.textContent = "🟢 " + on.join(", ") + " в сети"; }
  else el.hidden = true;
}
function guestMessage(g){
  return `WAYTEKO — гостевой доступ (только просмотр)${g.name ? " для " + g.name : ""}\nСсылка: ${APP_URL}\nПароль: ${g.pw}\n\nОткройте ссылку в Safari и введите пароль. Чтобы поставить на экран: «Поделиться» → «На экран «Домой»», затем откройте значок и введите пароль ещё раз.`;
}
function guestStatus(gs){
  return !gs ? "проверяю…" : gs.online ? `🟢 в сети${gs.tab && TABNAME[gs.tab] ? " · смотрит «" + TABNAME[gs.tab] + "»" : ""}`
    : gs.at ? `был в сети ${esc(fmtStamp(new Date(gs.at).toISOString()))}` : gs.err ? "статус недоступен" : "ещё не заходил";
}
function guestBox(){
  const list = activeGuests();
  const rows = list.map(g => `<div class="mrow">
      <div><b>${esc(g.name || "Гость")}</b> · ${guestStatus(guestSeen[g.id])}</div>
      <div>Пароль: <b style="font-family:ui-monospace,Menlo,monospace;letter-spacing:.03em">${esc(g.pw)}</b></div>
      <div class="actions"><button class="btn primary small" data-act="g-share" data-gid="${esc(g.id)}" type="button">📤 Отправить</button>
        <button class="btn small" data-act="g-copy" data-gid="${esc(g.id)}" type="button">Скопировать</button>
        <button class="btn ghost small" data-act="g-new" data-gid="${esc(g.id)}" type="button">Сменить пароль</button>
        <button class="btn ghost small" data-act="g-off" data-gid="${esc(g.id)}" type="button" style="color:var(--red)">Удалить</button></div></div>`).join("");
  const add = list.length >= MAXG ? `<div class="note">Добавлено максимум — ${MAXG} гостя. Чтобы добавить нового, удалите одного из списка.</div>`
    : getGh() ? `<form id="guestForm" style="display:grid;gap:8px;margin-top:4px"><label class="f">Имя нового гостя (видно только вам)<input id="gname" type="text" placeholder="Например: Иван, директор" required maxlength="40"></label>
      <button class="btn primary" type="submit">Добавить гостя</button></form>`
    : `<div class="note">Сначала подключите отправку в интернет-версию (блок выше) — через неё гости получают данные.</div>`;
  return `<div class="box"><h4>Гостевой доступ · ${list.length} из ${MAXG}</h4>
    <div class="note">Гость может только смотреть клиентов, касания и встречи — без права изменений. У каждого гостя своё имя и свой пароль; пароль вы отправляете сами.</div>
    ${rows}${add}
    ${list.length ? `<div class="note">Гости видят ваши изменения через 2–3 минуты. «В сети» обновляется раз в пару минут. После смены пароля или удаления гость теряет доступ при следующем обновлении.</div>` : ""}</div>`;
}
function guestDataPanel(){
  const m = getMeta();
  return `<div class="scrim" data-close></div><aside class="panel" role="dialog" aria-label="Данные">
    <div class="head"><h2>Данные</h2><button class="btn ghost" data-close type="button" aria-label="Закрыть">✕</button></div>
    <div class="box"><h4>Гостевой доступ${m.guestName ? " · " + esc(m.guestName) : ""}</h4>
      <div>Вы вошли как гость: можно только смотреть, изменения недоступны.</div>
      <div>Клиентов: <b>${clients.length}</b>. Данные от: <b>${m.lastSync ? esc(fmtStamp(m.lastSync)) : "—"}</b>${syncState.status==="offline" ? " · сейчас нет связи" : ""}.</div>
      <div class="note">Данные обновляются автоматически, пока приложение открыто.</div>
      <div class="actions"><button class="btn small" data-act="sync" type="button">🔄 Обновить сейчас</button>
        <button class="btn ghost small" data-act="logout" type="button">Выйти</button></div></div>
  </aside>`;
}
async function guestAction(kind, gid){
  const tok = getGh(); if(!tok){ toast("Сначала подключите отправку"); return; }
  const before = getGuests(), list = before.map(g => ({...g})), now = new Date().toISOString();
  try {
    if(kind === "add"){
      const name = (overlay.querySelector("#gname")?.value || "").trim();
      if(!name){ toast("Укажите имя гостя"); return; }
      if(activeGuests().length >= MAXG){ toast(`Не больше ${MAXG} гостей`); return; }
      const g = {id: "g" + Date.now().toString(36) + Math.random().toString(36).slice(2, 5), name, pw: genGuestPw(), updated: now};
      list.push(g); setGuests(list);
      await putOneGuest(tok, g);
      toast(`Гость «${name}» добавлен — отправьте ему пароль`);
    } else {
      const g = list.find(x => x.id === gid); if(!g || !g.pw) return;
      const oldPath = await guestPath(g);
      if(kind === "new"){
        g.pw = genGuestPw(); g.legacy = false; g.updated = now; setGuests(list);
        await putOneGuest(tok, g);
        await deleteFile(tok, oldPath, "Гостевой пароль сменён [skip ci]").catch(() => {});
        toast(`Пароль для «${g.name || "гостя"}» сменён — старый больше не работает`);
      } else if(kind === "off"){
        await deleteFile(tok, oldPath, "Гостевой доступ удалён [skip ci]");
        g.off = true; delete g.pw; g.updated = now; setGuests(list);
        toast(`Доступ «${g.name || "гостя"}» удалён`);
      }
    }
    delete guestSeen[gid];
    setMeta({rev: (getMeta().rev || 0) + 1}); scheduleUpload();
  } catch(e){ setGuests(before); toast(e && e.message === "token" ? "Токен не подходит — подключите отправку заново" : "Нет связи, попробуйте ещё раз"); }
  renderGuestPill(); renderPanel(); if(activeGuests().length) checkGuest();
}

function uploadBox(){
  const m = getMeta(), on = !!getGh();
  return `<div class="box"><h4>Отправка в интернет-версию</h4>
    <div class="note">Приложение — главный источник. Все ваши устройства с основным паролем обмениваются изменениями раз в минуту и при каждом открытии; каждый вечер Claude переносит общую базу в интернет-версию WAYTEKO и присылает файл.</div>
    ${on ? `<div>Последняя отправка: <b>${m.lastUpload ? esc(fmtStamp(m.lastUpload)) : "ещё не было"}</b>${isDirty() ? " · есть неотправленные изменения" : ""}</div>
      <div>Сверка с другими устройствами: <b>${m.sharedAt ? esc(fmtStamp(m.sharedAt)) : "ещё не было"}</b></div>
      ${m.upErr ? `<div style="color:var(--red)">${esc(m.upErr)}</div>` : ""}
      <div class="actions"><button class="btn primary small" data-act="upload" type="button">⬆️ Отправить сейчас</button>
        <button class="btn small" data-act="devsync" type="button">🔄 Сверить устройства</button>
        <button class="btn ghost small" data-act="ghoff" type="button">Отключить</button></div>`
    : `<form id="ghForm" style="display:grid;gap:8px"><label class="f">Токен GitHub<input id="ghtok" type="password" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="github_pat_…" required></label>
      <button class="btn primary" type="submit">Подключить отправку</button></form>
      <div class="note">Токен вводится один раз. Если он уже подключён на другом вашем устройстве, это устройство получит его само через минуту после входа.</div>`}</div>`;
}
async function downloadXlsx(){
  const pw = getPw(); if(!pw){ toast("Сначала введите пароль"); return; }
  try {
    const r = await fetch("data/clients.xlsx.enc.json?t=" + Date.now(), {cache:"no-store"}); if(!r.ok) throw 0;
    const box = await r.json(), bytes = await openBox(box, pw);
    if(await giveFile(box.name || `WAYTEKO_клиенты_${stamp()}.xlsx`, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", bytes)) toast("Файл клиентов сохранён");
  } catch(e){ toast("Не удалось скачать файл. Проверьте интернет"); }
}
function pwHtml(){
  return `<form class="welcome" id="pwForm"><h2>Вход в WAYTEKO</h2>
    <div>Введите пароль — основной или гостевой. Он нужен один раз: приложение запомнит его на этом устройстве и само будет подтягивать свежую базу.</div>
    <label class="f">Пароль<input id="pw" type="password" autocomplete="current-password" autocapitalize="off" spellcheck="false" required></label>
    <div class="actions"><button class="btn primary" type="submit">Войти</button></div></form>`;
}

// ---------- файлы: резервная копия, Excel, календарь''')

# ---------- рендер: пустая база, баннер копии
rep('''  if(!loaded){ view.innerHTML = `<div class="empty">Загружаю клиентов…</div>`; return; }
  if(tab==="today")''', '''  if(!loaded){ view.innerHTML = `<div class="empty">Загружаю клиентов…</div>`; return; }
  const m = getMeta(), bn = $("#banner"), since = m.lastBackup ? diffDays(todayIso(), m.lastBackup) : null;
  if(clients.length && !m.lastSync && (since===null || since>=7)){ bn.hidden = false; bn.className = "banner";
    bn.innerHTML = `<span>💾 ${since===null ? "Резервная копия ещё не сохранялась" : `Резервной копии <b>${since} дн.</b>`}</span><button class="btn small" data-act="backup" type="button">Сохранить сейчас</button>`; }
  else bn.hidden = true;
  document.documentElement.classList.toggle("locked", !!syncState.needPw);
  if(syncState.needPw){ bn.hidden = true; if(!view.querySelector("#pwForm")) view.innerHTML = pwHtml(); }
  else if(!clients.length) view.innerHTML = welcomeHtml();
  else if(tab==="today")''')
rep('$("#todayLbl").textContent = "Сегодня " + fmtW(todayIso());',
    '{ const ls = getMeta().lastSync; $("#todayLbl").textContent = "Сегодня " + fmtW(todayIso()) + (ls ? " · база от " + fmtStamp(ls) : ""); renderGuestPill(); renderTasksBadge(); }')

# ---------- панель данных и календарь в карточке
rep('''  const c = openId==="new" ? null : clients.find(x => x.id===openId);''',
    '''  if(openId==="data"){ overlay.hidden = false; overlay.innerHTML = isGuest() ? guestDataPanel() : renderDataPanel(); return; }
  const c = openId==="new" ? null : clients.find(x => x.id===openId);''')
rep('''<div class="actions"><span class="lbl">Перенести созвон:</span>${moveBtns(c.id)}</div></div>''',
    '''<div class="actions"><span class="lbl">Перенести созвон:</span>${moveBtns(c.id)}${c.next && s.k!=="arch" ? `<button class="btn small" data-ics="${c.id}" type="button">📅 В календарь</button>` : ""}</div></div>''')

# ---------- события
rep('''  if(t.id==="addBtn"){ openPanel("new"); return; }''',
    '''  if(t.id==="addBtn" || t.id==="addBtn2"){ openPanel("new"); return; }
  if(t.id==="dataBtn"){ pendingImport = null; openPanel("data"); if(!isGuest()) checkGuest(); return; }
  if(t.dataset.act==="backup"){ exportBackup(); return; }
  if(t.dataset.act==="csv"){ exportCsv(); return; }
  if(t.dataset.act==="xlsx"){ downloadXlsx(); return; }
  if(t.dataset.act==="upload"){ await uploadNow(true); return; }
  if(t.dataset.tday !== undefined){ const d = +t.dataset.tday; taskDay = d === 0 ? todayIso() : addDays(taskDay, d); renderTasks(true); return; }
  if(t.dataset.tprio){ taskPrio = t.dataset.tprio; renderTasks(true); return; }
  if(t.dataset.tprioCycle){ const order = ["normal", "high", "urgent"]; taskUpdate(t.dataset.tprioCycle, x => { x.prio = order.at((order.indexOf(prioOf(x)) + 1) % 3); }); return; }
  if(t.dataset.tdone){ taskUpdate(t.dataset.tdone, x => { x.done = !x.done; }); return; }
  if(t.dataset.tmove){ taskUpdate(t.dataset.tmove, x => { x.d = todayIso(); }); toast("Перенесено на сегодня"); return; }
  if(t.dataset.tdel){ taskUpdate(t.dataset.tdel, x => { x.del = true; }); toast("Задача удалена"); return; }
  if(t.dataset.act==="devsync"){ await syncShared(true); return; }
  if(t.dataset.act==="ghoff"){ setGh(""); setMeta({upErr:""}); renderPanel(); return; }
  if(t.dataset.act==="sync"){ await syncNow(null, true); return; }
  if(t.dataset.act==="logout"){ if(isGuest()){ beat("off"); setRole(""); clients = []; saveLocalOnly(); setMeta({lastSync: null}); }
    setPw(""); syncState.needPw = true; closePanel(); render(); return; }
  if(t.dataset.act==="g-share" || t.dataset.act==="g-copy"){ const g = activeGuests().find(x => x.id === t.dataset.gid); if(!g) return; const txt = guestMessage(g);
    if(t.dataset.act==="g-share" && navigator.share){ try { await navigator.share({text: txt}); } catch(_){} return; }
    try { await navigator.clipboard.writeText(txt); toast("Скопировано — вставьте в сообщение гостю"); } catch(_){ toast(g.pw); } return; }
  if(t.dataset.act==="g-new"){ await guestAction("new", t.dataset.gid); return; }
  if(t.dataset.act==="g-off"){ await guestAction("off", t.dataset.gid); return; }
  if(t.dataset.act==="imp-replace"){ applyImport("replace"); return; }
  if(t.dataset.act==="imp-merge"){ applyImport("merge"); return; }
  if(t.dataset.act==="imp-cancel"){ pendingImport = null; renderPanel(); return; }
  if(t.dataset.ics){ const c = clients.find(x => x.id===t.dataset.ics); if(c) exportIcs(c); return; }''')
rep('''  if(t.dataset.del){ try{ await db.collection("clients").doc(t.dataset.del).delete(); toast("Клиент удалён"); closePanel(); }catch(_){ toast("Не удалилось, попробуйте ещё раз"); } return; }''',
    '''  if(t.dataset.del){ if(removeClient(t.dataset.del)){ toast("Клиент удалён"); closePanel(); render(); } return; }''')
rep('''    if(await save(openId, f)){ editing = false; toast("Данные сохранены"); } }''',
    '''    editing = false; if(await save(openId, f)) toast("Данные сохранены"); }''')
rep('''document.addEventListener("keydown",''', '''document.addEventListener("change", async e => {
  if(e.target.id!=="importFile" && e.target.id!=="importFile0") return;
  const f = e.target.files && e.target.files[0]; e.target.value && null; if(!f) return;
  try {
    const data = JSON.parse(await f.text());
    const list = normalizeImport(Array.isArray(data) ? data : (data && data.clients) || []);
    if(!list.length) throw new Error("empty");
    pendingImport = list; pendingTasks = Array.isArray(data && data.tasks) ? data.tasks : null;
    if(!clients.length) applyImport("replace"); else { openId = "data"; renderPanel(); }
  } catch(_){ toast("Не удалось прочитать файл. Выберите резервную копию WAYTEKO (.json)"); }
  e.target.value = "";
});
document.addEventListener("keydown",''')

# ---------- запуск
start = s.index('// ---------- подключение к базе')
end = s.index('setInterval(() => { if(loaded && !openId) render(); }, 60000);')
s = s[:start] + '''// ---------- запуск
const stored = loadLocal();
loaded = true;
if(stored===null){ render(); view.innerHTML = `<div class="empty">Память для приложения недоступна. Откройте WAYTEKO с главного экрана или выключите «Частный доступ» в Safari.</div>`; }
else { clients = Array.isArray(stored) ? stored : []; if(!getPw()) syncState.needPw = true; render(); }
try { navigator.storage && navigator.storage.persist && navigator.storage.persist(); } catch(_){}
if("serviceWorker" in navigator) window.addEventListener("load", () => navigator.serviceWorker.register("./sw.js").catch(() => {}));
document.addEventListener("visibilitychange", () => {
  if(document.hidden){ if(isGuest()) beat("off"); return; }
  if(!openId) render(); syncNow(); if(isGuest()) beat("on"); else { checkGuest(); syncShared(); } });
applyRole();
if(stored!==null) syncNow();
if(isGuest()) startPresence(); else checkGuest();
setInterval(() => { if(!document.hidden && !isGuest() && activeGuests().length) checkGuest(); }, 30000);
''' + s[end:]
rep('''  if(e.target.id==="meetForm"){''', '''  if(e.target.id==="ghForm"){ const tok = (overlay.querySelector("#ghtok")?.value || "").trim(); if(!tok) return;
    if(!getPw()){ toast("Сначала войдите по паролю"); return; }
    try { const r = await fetch(`https://api.github.com/repos/${REPO}`, {headers: ghHeaders(tok), cache:"no-store"});
      if(!r.ok) throw 0; const j = await r.json(); if(j.permissions && !j.permissions.push) throw 0; }
    catch(_){ toast("Токен не подходит: нужен доступ к репозиторию wayteko на запись"); return; }
    setGh(tok); setMeta({upErr:"", upRev: -1}); renderPanel(); await uploadNow(true); return; }
  if(e.target.id==="guestForm"){ await guestAction("add"); return; }
  if(e.target.id==="taskForm"){
    const text = (view.querySelector("#tk_text")?.value || "").trim(), cn = (view.querySelector("#tk_client")?.value || "").trim(), owner = (view.querySelector("#tk_owner")?.value || "").trim();
    if(!text){ toast("Напишите задачу"); return; }
    const c = cn ? clients.find(x => x.name.trim().toLowerCase() === cn.toLowerCase()) : null, now = new Date().toISOString();
    const l = getTasks(); l.push({id: "t" + Date.now().toString(36) + Math.random().toString(36).slice(2, 5), d: taskDay, cid: c ? c.id : "", cname: c ? "" : cn, owner, prio: taskPrio, text, done: false, created: now, updated: now});
    if(saveTasks(l)){ setMeta({lastOwner: owner}); taskPrio = "normal"; view.querySelector("#tk_text").value = ""; view.querySelector("#tk_client").value = ""; renderTasks(true); renderTasksBadge(); toast("Задача добавлена"); }
    return; }
  if(e.target.id==="pwForm"){ const p = (document.querySelector("#pw")?.value || "").trim(); if(p) await syncNow(p, true); return; }
  if(e.target.id==="meetForm"){''')
assert "db.collection" not in s and "window.claude" not in s
os.makedirs(OUT, exist_ok=True)
open(f"{OUT}/index.html", "w", encoding="utf-8").write(s)

manifest = {"name": "WAYTEKO CRM", "short_name": "WAYTEKO", "description": "CRM дилерской сети Вайтек Премиум",
            "start_url": "./", "scope": "./", "display": "standalone", "orientation": "portrait",
            "background_color": "#ecc844", "theme_color": "#1f4e78", "lang": "ru",
            "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                      {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
                      {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
json.dump(manifest, open(f"{OUT}/manifest.webmanifest", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

open(f"{OUT}/sw.js", "w").write("""const CACHE = "wayteko-v13";
const FILES = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png", "./icon-maskable-512.png", "./apple-touch-icon.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES))); self.skipWaiting(); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))); self.clients.claim(); });
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin || u.pathname.includes("/data/")) return;
  e.respondWith(fetch(e.request).then(r => { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return r; })
    .catch(() => caches.match(e.request).then(r => r || caches.match("./index.html"))));
});
""")

# ---------- иконки
from PIL import Image, ImageDraw, ImageFont
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def icon(size, path, pad=0.0):
    im = Image.new("RGB", (size, size), (31, 78, 120)); d = ImageDraw.Draw(im)
    inner = size * (1 - 2 * pad)
    f = ImageFont.truetype(FONT, int(inner * 0.62))
    bb = d.textbbox((0, 0), "W", font=f); w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((size - w) / 2 - bb[0], (size - h) / 2 - bb[1] - inner * 0.06), "W", font=f, fill=(255, 255, 255))
    f2 = ImageFont.truetype(FONT, max(10, int(inner * 0.11)))
    bb2 = d.textbbox((0, 0), "WAYTEKO", font=f2); w2 = bb2[2] - bb2[0]
    d.text(((size - w2) / 2 - bb2[0], size / 2 + inner * 0.27), "WAYTEKO", font=f2, fill=(255, 210, 0))
    im.save(path)
import shutil
for n in ["icon-512.png", "icon-192.png", "apple-touch-icon.png", "icon-maskable-512.png"]: (os.path.exists(f"{SP}/logo/{n}") and shutil.copy(f"{SP}/logo/{n}", f"{OUT}/{n}"))  # логотип WAYTEKO
print("OK", len(s), "bytes")
