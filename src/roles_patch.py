# Выполняется внутри make_app.py (переменные s и rep оттуда).
# Имя при входе, ответственный за каждое действие, доступ «Редактор» (правит клиентов, но не видит задачи
# и не удаляет клиентов). Владелец (главный пароль) может всё.

# ---------- стили
rep('.guest .temps button{pointer-events:none}', '''.editor .ubanner,.editor .box:has(> [data-askdel]),.editor .box:has(> .confirm){display:none!important}
.upill{display:inline-block;margin-left:8px;padding:1px 8px;border-radius:999px;font-size:12px;font-weight:600;background:var(--surface-2);color:var(--muted);border:1px solid var(--line)}
.upill.ed{background:#fff1bf;color:#8a6400;border-color:#f1d38a}
.guest .temps button{pointer-events:none}''')

# ---------- шапка: кто вошёл
rep('<span id="guestPill" class="gpill" hidden></span>', '<span id="userPill" class="upill" hidden></span><span id="guestPill" class="gpill" hidden></span>')

# ---------- кто вносит изменения (имя при входе)
rep('function whoAmI(){ return "Интернет-версия"; }', '''const USERKEY = "wayteko.user.v1";
function getUser(){ try { return (localStorage.getItem(USERKEY) || "").trim(); } catch(e){ return ""; } }
function setUser(n){ try { n ? localStorage.setItem(USERKEY, n) : localStorage.removeItem(USERKEY); } catch(e){} }
function whoAmI(){ return getUser() || (isEditor() ? "Редактор" : isGuest() ? "Гость" : "Владелец"); }
const validName = n => n.trim().split(/\\s+/).filter(w => w.length > 1).length >= 2;''')

# сохранение и создание клиента — с ответственным и журналом
rep('''  const prev = clients[i]; clients[i] = {...prev, ...patch, updated: new Date().toISOString()};''',
    '''  const prev = clients[i]; clients[i] = {...prev, ...attrib(prev, patch), updated: new Date().toISOString()};''')
rep('''  clients.push({...data, id, touches:[], created:now, updated:now});''',
    '''  const who = whoAmI();
  clients.push({...data, id, touches:[], created:now, updated:now, createdBy: who, updatedBy: who, hist:[{at: now, by: who, a: "завёл клиента"}]});''')
rep('''function removeClient(id){ if(isGuest()){ toast(GUEST_MSG); return false; }''',
    '''function removeClient(id){ if(isGuest()){ toast(GUEST_MSG); return false; } if(isEditor()){ toast("Удалять клиентов может только владелец"); return false; }''')

# объединение версий при сверке устройств: касания и журнал не теряются
rep('''    const r = remote.get(c.id);
    if(r && (r.updated || "") > (c.updated || "")){ out.push(r); changed++; }
    else { out.push(c); if(!r || (c.updated || "") > (r.updated || "")) localAhead = true; }''',
    '''    const r = remote.get(c.id);
    if(!r){ out.push(c); localAhead = true; }
    else { const m = mergeClient(c, r); out.push(m); if(JSON.stringify(m) !== JSON.stringify(c)) changed++; if(JSON.stringify(m) !== JSON.stringify(r)) localAhead = true; }''')
rep('''    if(!l){ byId.set(r.id, r); added++; }
    else if((r.updated||"") > (l.updated||"")){ byId.set(r.id, r); changed++; } }''',
    '''    if(!l){ byId.set(r.id, r); added++; }
    else { const m = mergeClient(l, r); if(JSON.stringify(m) !== JSON.stringify(l)){ byId.set(r.id, m); changed++; } } }''')

# редакторы в общей копии владельца
rep('''      const body = JSON.stringify({updated: stampUp, clients, deleted: getMeta().deleted || [], guests: getGuests(), tasks: getTasks(), gh: tok});''',
    '''      if(await pullEditors().catch(() => 0)){ saveLocalOnly(); render(); }
      const body = JSON.stringify({updated: stampUp, clients, deleted: getMeta().deleted || [], guests: getGuests(), editors: getEditors(), tasks: getTasks(), gh: tok});''')
rep('''    if(activeGuests().length) await putGuestCopies(tok).catch(() => {});''',
    '''    if(activeGuests().length) await putGuestCopies(tok).catch(() => {});
    if(activeEditors().length) await putEditorCopies(tok).catch(() => {});''')
rep('''  if(tch){ setTasks([...ltm.values()]); changed++; }''',
    '''  if(tch){ setTasks([...ltm.values()]); changed++; }
  const re = Array.isArray(sh.editors) ? sh.editors : [];
  const lem = new Map(getEditors().map(x => [x.id, x])); let ech = false;
  for(const r of re){ if(!r || !r.id) continue; const l = lem.get(r.id);
    if(!l || (r.updated || "") > (l.updated || "")){ lem.set(r.id, r); ech = true; }
    else if((l.updated || "") > (r.updated || "")) localAhead = true; }
  for(const id of lem.keys()) if(!re.some(r => r && r.id === id)) localAhead = true;
  if(ech){ setEditors([...lem.values()]); changed++; }''')
# периодическая сверка владельца забирает правки редакторов
rep('''    const sh = await fetchShared();
    if(!sh){ if(manual) toast("Других устройств пока нет"); return; }''',
    '''    const ed = await pullEditors().catch(() => 0);
    if(ed){ saveLocalOnly(); setMeta({rev: (getMeta().rev || 0) + 1}); scheduleUpload(); render(); toast(`Изменения от редакторов: ${ed}`); }
    const sh = await fetchShared();
    if(!sh){ if(manual) toast("Других устройств пока нет"); return; }''')

# ---------- роли: владелец / редактор / гость
rep('''function isGuest(){ return getRole() === "guest"; }
function applyRole(){ document.documentElement.classList.toggle("guest", isGuest()); }''',
    '''function isGuest(){ return getRole() === "guest"; }
function isEditor(){ return getRole() === "editor"; }
const isOwner = () => !isGuest() && !isEditor();
function applyRole(){ document.documentElement.classList.toggle("guest", isGuest()); document.documentElement.classList.toggle("editor", isEditor()); }''')
rep('''    if(isGuest() && !pwTry){ await guestSync(getPw(), manual, false); return; }''',
    '''    if(isGuest() && !pwTry){ await guestSync(getPw(), manual, false); return; }
    if(isEditor() && !pwTry){ await editorSync(getPw(), manual, false); return; }''')
rep('''catch(e){ if(pwTry && await guestSync(pwTry, manual, true)) return;''',
    '''catch(e){ if(pwTry && (await guestSync(pwTry, manual, true) || await editorSync(pwTry, manual, true))) return;''')
rep('''    setPw(pw); syncState.needPw = false; syncState.updated = snap.updated; syncState.status = "ok";''',
    '''    if(getRole()){ setRole(""); clients = []; setTasks([]); saveLocalOnly(); setMeta({lastSync: null, sharedSeen: null}); }
    setPw(pw); syncState.needPw = false; syncState.updated = snap.updated; syncState.status = "ok";''')
rep('''if(!isGuest() && getPw()){ syncShared(); startShare(); syncAdvice(); } }''',
    '''if(isOwner() && getPw()){ syncShared(); startShare(); syncAdvice(); } if(isEditor() && getPw()) startEditor(); }''')
rep('''async function uploadNow(manual){
  const tok = getGh(), pw = getPw();''', '''async function uploadNow(manual){
  if(isEditor()) return editorUpload(manual);
  const tok = getGh(), pw = getPw();''')
rep('''  if(isGuest() || !getPw() || shareBusy || upBusy) return;''', '''  if(!isOwner() || !getPw() || shareBusy || upBusy) return;''')
rep('''function loadAdvice(){ if(isGuest()){''', '''function loadAdvice(){ if(!isOwner()){''')
rep('''  if(isGuest() || !getPw() || advBusy) return; advBusy = true;''', '''  if(!isOwner() || !getPw() || advBusy) return; advBusy = true;''')
rep('''  if(shareTimer || isGuest()) return;''', '''  if(shareTimer || !isOwner()) return;''')
rep('''  const list = activeGuests(); if(!list.length || isGuest()){ guestSeen = {}; renderGuestPill(); return; }''',
    '''  const list = activeGuests(); if(!list.length || !isOwner()){ guestSeen = {}; renderGuestPill(); return; }''')
rep('''  if(openId==="data"){ overlay.hidden = false; overlay.innerHTML = isGuest() ? guestDataPanel() : renderDataPanel(); return; }''',
    '''  if(openId==="data"){ overlay.hidden = false; overlay.innerHTML = isGuest() ? guestDataPanel() : isEditor() ? editorDataPanel() : renderDataPanel(); return; }''')
rep('''  if(!openId) render(); syncNow(); if(isGuest()) beat("on"); else { checkGuest(); syncShared(); syncAdvice(); } });''',
    '''  if(!openId) render(); syncNow(); if(isGuest()) beat("on"); else if(isOwner()){ checkGuest(); syncShared(); syncAdvice(); } });''')
rep('''if(!isGuest() && getPw()) syncAdvice();''', '''if(isOwner() && getPw()) syncAdvice();''')
rep('''if(isGuest()) startPresence(); else checkGuest();''', '''if(isGuest()) startPresence(); else if(isOwner()) checkGuest();''')
rep('''  if(t.dataset.act==="logout"){ if(isGuest()){ beat("off"); setRole(""); clients = []; saveLocalOnly(); setMeta({lastSync: null}); }
    setPw(""); syncState.needPw = true; closePanel(); render(); return; }''',
    '''  if(t.dataset.act==="logout"){ if(!isOwner()){ if(isGuest()) beat("off"); setRole(""); setGh(""); clients = []; saveLocalOnly(); setMeta({lastSync: null, deleted: [], rev: 0, upRev: 0}); }
    setPw(""); setUser(""); syncState.needPw = true; closePanel(); render(); return; }
  if(t.dataset.act==="e-share" || t.dataset.act==="e-copy"){ const x = activeEditors().find(y => y.id === t.dataset.eid); if(!x) return; const txt = editorMessage(x);
    if(t.dataset.act==="e-share" && navigator.share){ try { await navigator.share({text: txt}); } catch(_){} return; }
    try { await navigator.clipboard.writeText(txt); toast("Скопировано — вставьте в сообщение"); } catch(_){ toast(x.pw); } return; }
  if(t.dataset.act==="e-new"){ await editorAction("new", t.dataset.eid); return; }
  if(t.dataset.act==="e-off"){ await editorAction("off", t.dataset.eid); return; }''')

# ---------- вход: пароль + имя и фамилия
rep('''function pwHtml(){
  return `<form class="welcome" id="pwForm"><h2>Вход в WAYTEKO</h2>
    <div>Введите пароль — основной или гостевой. Он нужен один раз: приложение запомнит его на этом устройстве и само будет подтягивать свежую базу.</div>
    <label class="f">Пароль<input id="pw" type="password" autocomplete="current-password" autocapitalize="off" spellcheck="false" required></label>''',
    '''function nameHtml(){
  return `<form class="welcome" id="nameForm"><h2>Кто работает в приложении?</h2>
    <div>Укажите имя и фамилию. Они будут стоять ответственным у каждого касания, нового клиента и изменения, которые вы внесёте.</div>
    <label class="f">Имя и фамилия<input id="uname" type="text" autocomplete="name" autocapitalize="words" maxlength="60" placeholder="Например: Иван Петров" required value="${esc(getUser())}"></label>
    <div class="actions"><button class="btn primary" type="submit">Продолжить</button></div></form>`;
}
function pwHtml(){
  return `<form class="welcome" id="pwForm"><h2>Вход в WAYTEKO</h2>
    <div>Введите пароль, который вам выдали. Имя и фамилия закреплены за паролем — их назначает владелец, менять их не нужно. Приложение запомнит вход на этом устройстве.</div>
    <label class="f">Пароль<input id="pw" type="password" autocomplete="current-password" autocapitalize="off" spellcheck="false" required></label>''')
rep('''  if(e.target.id==="pwForm"){ const p = (document.querySelector("#pw")?.value || "").trim(); if(p) await syncNow(p, true); return; }''',
    '''  if(e.target.id==="pwForm"){ const p = (document.querySelector("#pw")?.value || "").trim(); if(p) await syncNow(p, true); return; }
  if(e.target.id==="nameForm"){ const n = (document.querySelector("#uname")?.value || "").trim().replace(/\\s+/g, " ");
    if(!validName(n)){ toast("Укажите имя и фамилию"); return; }
    setUser(n); toast(`Здравствуйте, ${n.split(" ")[0]}!`); render(); return; }
  if(e.target.id==="editorForm"){ await editorAction("add"); return; }''')
rep('''  document.documentElement.classList.toggle("locked", !!syncState.needPw);
  if(syncState.needPw){ bn.hidden = true; if(!view.querySelector("#pwForm")) view.innerHTML = pwHtml(); }''',
    '''  const needName = !syncState.needPw && isOwner() && !getUser();
  document.documentElement.classList.toggle("locked", !!syncState.needPw || needName);
  if(syncState.needPw){ bn.hidden = true; if(!view.querySelector("#pwForm")) view.innerHTML = pwHtml(); }
  else if(needName){ bn.hidden = true; if(!view.querySelector("#nameForm")) view.innerHTML = nameHtml(); }''')
rep('''function renderGuestPill(){
  const el = document.getElementById("guestPill"); if(!el) return;''', '''function renderGuestPill(){
  const up = document.getElementById("userPill");
  if(up){ const u = getUser(); up.hidden = !u || isGuest() || !!syncState.needPw; up.className = isEditor() ? "upill ed" : "upill"; up.textContent = isEditor() ? `✏️ ${u} · редактор` : `👤 ${u}`; }
  const el = document.getElementById("guestPill"); if(!el) return;''')

# ---------- доступ «Редактор»: панель владельца, копии, синхронизация
rep('''    ${guestBox()}''', '''    ${editorBox()}
    ${guestBox()}''')
rep('''    <div class="box"><button class="btn ghost small" data-act="logout" type="button">Сменить пароль на этом устройстве</button></div>''',
    '''    <div class="box"><div class="note">Вы вошли как <b>${esc(getUser())}</b> (владелец).</div><button class="btn ghost small" data-act="logout" type="button">Выйти / сменить пользователя</button></div>''')
rep('''function uploadBox(){''', '''// ---------- доступ с редактированием (до 4 человек; без задач и без удаления клиентов)
const EDKEY = "wayteko.editors.v1", MAXE = 4;
function getEditors(){ try { const v = JSON.parse(localStorage.getItem(EDKEY) || "[]"); return Array.isArray(v) ? v : []; } catch(e){ return []; } }
function setEditors(l){ try { localStorage.setItem(EDKEY, JSON.stringify(l)); } catch(e){} }
const activeEditors = () => getEditors().filter(x => x.pw && !x.off);
function genEditorPw(){ return "E" + genGuestPw().slice(1); }
const edPathFor = async pw => `data/e-${await hex16("wayteko-editor:" + pw)}.enc.json`;
async function fetchBoxAuth(path){
  const tok = getGh(), h = tok ? {...ghHeaders(tok), Accept: "application/vnd.github.raw"} : {Accept: "application/vnd.github.raw"};
  const r = await fetch(`https://api.github.com/repos/${REPO}/contents/${path}?ref=main&t=${Date.now()}`, {headers: h, cache: "no-store"});
  if(r.status === 404) return null;
  if(!r.ok) throw new Error("http");
  return await r.json();
}
function mergeClientList(list, del){ // в текущий список clients; возвращает число изменённых карточек
  const delS = new Set(del || []), byId = new Map(clients.map(c => [c.id, c])); let n = 0;
  for(const r of (list || [])){ if(!r || !r.id || delS.has(r.id)) continue;
    const l = byId.get(r.id), m = mergeClient(l, r);
    if(!l || JSON.stringify(m) !== JSON.stringify(l)){ byId.set(r.id, m); n++; } }
  for(const id of delS) if(byId.delete(id)) n++;
  clients = [...byId.values()]; return n;
}
// задачи редакторов: у владельца — только просмотр; свои задачи владельца редакторам не уходят
const EDTKEY = "wayteko.edtasks.v1";
function getEdTasks(){ try { const v = JSON.parse(localStorage.getItem(EDTKEY) || "{}"); return v && typeof v === "object" ? v : {}; } catch(e){ return {}; } }
function putEdTasks(x, list){
  if(!Array.isArray(list)) return false;
  const all = getEdTasks(), prev = JSON.stringify((all[x.id] || {}).tasks || []), next = JSON.stringify(list);
  if(prev === next && (all[x.id] || {}).name === (x.name || "")) return false;
  all[x.id] = {name: x.name || "", tasks: list};
  for(const id of Object.keys(all)) if(!activeEditors().some(y => y.id === id)) delete all[id];
  try { localStorage.setItem(EDTKEY, JSON.stringify(all)); } catch(e){} return true;
}
function mergeOwnTasks(list){ // устройство редактора: свои задачи из своей копии (новее — побеждает)
  if(!Array.isArray(list)) return 0;
  const m = new Map(getTasks().map(t => [t.id, t])); let n = 0;
  for(const r of list){ if(!r || !r.id) continue; const l = m.get(r.id); if(!l || (r.updated || "") > (l.updated || "")){ m.set(r.id, r); n++; } }
  if(n){ setTasks([...m.values()]); renderTasksBadge(); if(tab === "tasks" && !openId) renderTasks(); }
  return n;
}
function edTaskRow(t, old){
  const c = t.cid ? clients.find(x => x.id === t.cid) : null, p = prioOf(t);
  const who = c ? `<button class="name" data-open="${c.id}" type="button">${esc(c.name)}</button>` : (t.cname ? `<b>${esc(t.cname)}</b>` : "");
  return `<article class="card task prio-${p} ${t.done ? "done" : ""}"><div class="trow">
    <span class="tcheck" aria-label="${t.done ? "выполнена" : "не выполнена"}" style="display:inline-flex;align-items:center;justify-content:center">${t.done ? "✓" : ""}</span>
    <div class="tbody"><div><span class="pbadge p-${p}">${PRIO[p].l}</span></div>${who}<div class="ttext">${esc(t.text)}</div>
      ${t.owner ? `<div class="towner">👤 ${esc(t.owner)}</div>` : ""}${old ? `<div class="muted" style="font-size:12px">было на ${esc(fmtW(t.d))}</div>` : ""}</div></div></article>`;
}
function edTasksHtml(){
  if(!isOwner()) return "";
  const today = todayIso(), all = getEdTasks(), eds = activeEditors().filter(x => all[x.id]);
  if(!eds.length) return "";
  let h = `<h2 class="sec">✏️ Задачи редакторов <span class="n">только просмотр</span></h2>`;
  for(const x of eds){
    const list = (all[x.id].tasks || []).filter(t => t && !t.del);
    const day = list.filter(t => t.d === taskDay).sort(byPrio);
    const over = taskDay === today ? list.filter(t => !t.done && t.d < today).sort(byPrio) : [];
    h += `<div class="box" style="margin-top:8px"><h4>${esc(x.name || "Редактор")} · ${day.filter(t => !t.done).length} из ${day.length} осталось${over.length ? ` · хвостов ${over.length}` : ""}</h4>
      ${day.length ? `<div class="list">${day.map(t => edTaskRow(t, false)).join("")}</div>` : `<div class="muted">На этот день задач нет.</div>`}
      ${over.length ? `<div class="list" style="margin-top:6px">${over.map(t => edTaskRow(t, true)).join("")}</div>` : ""}</div>`;
  }
  return h;
}
async function pullEditors(){ // владелец забирает правки редакторов
  let n = 0;
  for(const x of activeEditors()){
    try { const box = await fetchBoxAuth(await edPathFor(x.pw)); if(!box) continue;
      const snap = JSON.parse(new TextDecoder().decode(await openBox(box, x.pw)));
      n += mergeClientList(normalizeImport(snap.clients || []), getMeta().deleted || []);
      if(putEdTasks(x, snap.tasks) && tab === "tasks" && !openId) renderTasks(); } catch(e){}
  }
  return n;
}
async function putOneEditor(tok, x){
  const path = await edPathFor(x.pw);
  for(let attempt = 0; attempt < 3; attempt++){
    let etasks = (getEdTasks()[x.id] || {}).tasks || [];
    try { const box = await fetchBoxAuth(path);
      if(box){ const snap = JSON.parse(new TextDecoder().decode(await openBox(box, x.pw))); if(mergeClientList(normalizeImport(snap.clients || []), getMeta().deleted || [])) saveLocalOnly();
        etasks = Array.isArray(snap.tasks) ? snap.tasks : etasks; putEdTasks(x, etasks); } } catch(e){}
    const body = JSON.stringify({updated: new Date().toISOString(), clients, deleted: getMeta().deleted || [], gh: tok, editor: {id: x.id, name: x.name || ""}, tasks: etasks});
    try { await putFile(tok, path, await sealBox(new TextEncoder().encode(body), x.pw), "Копия редактора [skip ci]"); return; }
    catch(e){ if(e && e.message === "conflict" && attempt < 2) continue; throw e; }
  }
}
async function putEditorCopies(tok){ for(const x of activeEditors()){ try { await putOneEditor(tok, x); } catch(e){} } }
function editorMessage(x){
  return `WAYTEKO — доступ с редактированием${x.name ? " для " + x.name : ""}\\nСсылка: ${APP_URL}\\nПароль: ${x.pw}\\n\\nОткройте ссылку в Safari, введите имя и фамилию и пароль. Можно добавлять клиентов, записывать касания и встречи. Чтобы поставить на экран: «Поделиться» → «На экран «Домой»», затем откройте значок и войдите ещё раз.`;
}
function editorBox(){
  const list = activeEditors();
  const rows = list.map(x => `<div class="mrow">
      <div><b>${esc(x.name || "Редактор")}</b></div>
      <div>Пароль: <b style="font-family:ui-monospace,Menlo,monospace;letter-spacing:.03em">${esc(x.pw)}</b></div>
      <div class="actions"><button class="btn primary small" data-act="e-share" data-eid="${esc(x.id)}" type="button">📤 Отправить</button>
        <button class="btn small" data-act="e-copy" data-eid="${esc(x.id)}" type="button">Скопировать</button>
        <button class="btn ghost small" data-act="e-new" data-eid="${esc(x.id)}" type="button">Сменить пароль</button>
        <button class="btn ghost small" data-act="e-off" data-eid="${esc(x.id)}" type="button" style="color:var(--red)">Удалить</button></div></div>`).join("");
  const add = list.length >= MAXE ? `<div class="note">Добавлено максимум — ${MAXE}. Чтобы добавить нового, удалите одного из списка.</div>`
    : getGh() ? `<form id="editorForm" style="display:grid;gap:8px;margin-top:4px"><label class="f">Имя и фамилия редактора (закрепляются за паролем)<input id="ename" type="text" autocapitalize="words" placeholder="Например: Анна Смирнова" required maxlength="60"></label>
      <button class="btn primary" type="submit">Добавить редактора</button></form>`
    : `<div class="note">Сначала подключите отправку в интернет-версию (блок выше).</div>`;
  return `<div class="box"><h4>Доступ с редактированием · ${list.length} из ${MAXE}</h4>
    <div class="note">Редактор может добавлять клиентов, записывать касания и встречи, менять статусы и данные, вести свои задачи. Ваши задачи он не видит, клиентов удалять не может. Его задачи видны вам во вкладке «Задачи». Каждое его действие подписывается его именем.</div>
    ${rows}${add}
    ${list.length ? `<div class="note">Изменения редактора приходят к вам в течение минуты, пока приложение открыто, и в течение часа — даже если ваши устройства выключены.</div>` : ""}</div>`;
}
async function editorAction(kind, eid){
  const tok = getGh(); if(!tok){ toast("Сначала подключите отправку"); return; }
  const before = getEditors(), list = before.map(x => ({...x})), now = new Date().toISOString();
  try {
    if(kind === "add"){
      const name = (overlay.querySelector("#ename")?.value || "").trim();
      if(!validName(name)){ toast("Укажите имя и фамилию редактора"); return; }
      if(activeEditors().length >= MAXE){ toast(`Не больше ${MAXE} редакторов`); return; }
      const x = {id: "e" + Date.now().toString(36) + Math.random().toString(36).slice(2, 5), name, pw: genEditorPw(), updated: now};
      list.push(x); setEditors(list); await putOneEditor(tok, x);
      toast(`Редактор «${name}» добавлен — отправьте ему пароль`);
    } else {
      const x = list.find(y => y.id === eid); if(!x || !x.pw) return;
      const oldPath = await edPathFor(x.pw);
      if(mergeClientList(await (async () => { try { const b = await fetchBoxAuth(oldPath); return b ? normalizeImport(JSON.parse(new TextDecoder().decode(await openBox(b, x.pw))).clients || []) : []; } catch(e){ return []; } })(), getMeta().deleted || [])) saveLocalOnly();
      if(kind === "new"){ x.pw = genEditorPw(); x.updated = now; setEditors(list); await putOneEditor(tok, x);
        await deleteFile(tok, oldPath, "Пароль редактора сменён [skip ci]").catch(() => {});
        toast(`Пароль для «${x.name || "редактора"}» сменён — старый больше не работает`); }
      else if(kind === "off"){ await deleteFile(tok, oldPath, "Доступ редактора удалён [skip ci]");
        x.off = true; delete x.pw; x.updated = now; setEditors(list); toast(`Доступ «${x.name || "редактора"}» удалён`); }
    }
    setMeta({rev: (getMeta().rev || 0) + 1}); scheduleUpload();
  } catch(e){ setEditors(before); toast(e && e.message === "token" ? "Токен не подходит — подключите отправку заново" : "Нет связи, попробуйте ещё раз"); }
  renderPanel();
}
// ---------- устройство редактора
let edTimer = null, edBusy = false;
function editorRevoked(){
  setPw(""); setRole(""); setGh(""); clients = []; saveLocalOnly(); setMeta({lastSync: null, deleted: [], rev: 0, upRev: 0});
  syncState.needPw = true; closePanel(); toast("Доступ изменён или отключён владельцем"); render();
}
async function editorSync(pw, manual, login){
  let box;
  try { box = await fetchBoxAuth(await edPathFor(pw)); }
  catch(e){ if(login) return false; syncState.status = "offline"; if(manual) toast("Нет связи — работаю с сохранёнными данными"); render(); return true; }
  if(!box){ if(!login) editorRevoked(); return false; }
  let snap;
  try { snap = JSON.parse(new TextDecoder().decode(await openBox(box, pw))); }
  catch(e){ if(!login) editorRevoked(); return false; }
  if(!isEditor()){ clients = []; setTasks([]); setMeta({rev: 0, upRev: 0}); }
  setPw(pw); setRole("editor"); ADVICE = {}; try { localStorage.removeItem(ADVLS); } catch(e){}
  if(snap.gh) setGh(snap.gh);
  const nm = ((snap.editor && snap.editor.name) || "").trim(); setUser(nm);
  syncState.needPw = false; syncState.status = "ok"; syncState.updated = snap.updated;
  mergeClientList(normalizeImport(snap.clients || []), snap.deleted || []); saveLocalOnly();
  mergeOwnTasks(snap.tasks);
  setMeta({lastSync: snap.updated, editorName: (snap.editor && snap.editor.name) || "", deleted: snap.deleted || []});
  if(login) toast(nm ? `Вы вошли как ${nm} · доступ с редактированием` : "Вход выполнен: доступ с редактированием"); else if(manual) toast("Данные обновлены");
  if(isDirty()) scheduleUpload();
  render(); startEditor(); return true;
}
function startEditor(){ if(edTimer || !isEditor()) return; edTimer = setInterval(() => { if(!document.hidden && isEditor() && !upBusy) syncNow(); }, 60000); }
async function editorUpload(manual){
  const tok = getGh(), pw = getPw(); if(!tok || !pw) return false;
  if(upBusy){ scheduleUpload(); return false; }
  upBusy = true; const rev = getMeta().rev || 0;
  try {
    const path = await edPathFor(pw);
    for(let attempt = 0; attempt < 3; attempt++){
      const box = await fetchBoxAuth(path); if(!box){ editorRevoked(); return false; }
      const snap = JSON.parse(new TextDecoder().decode(await openBox(box, pw)));
      mergeClientList(normalizeImport(snap.clients || []), snap.deleted || []); saveLocalOnly(); mergeOwnTasks(snap.tasks);
      const body = JSON.stringify({updated: new Date().toISOString(), clients, deleted: snap.deleted || [], gh: snap.gh || tok, editor: snap.editor || {}, tasks: getTasks()});
      try { await putFile(tok, path, await sealBox(new TextEncoder().encode(body), pw), "Изменения редактора [skip ci]"); break; }
      catch(e){ if(e && e.message === "conflict" && attempt < 2) continue; throw e; }
    }
    setMeta({upRev: rev, lastUpload: new Date().toISOString(), upErr: ""});
    if(manual) toast("Отправлено"); return true;
  } catch(e){ setMeta({upErr: "Нет связи — отправлю при следующем открытии"}); if(manual) toast(getMeta().upErr); return false; }
  finally { upBusy = false; if(openId==="data") renderPanel(); if(isDirty() && getMeta().upRev===rev && !getMeta().upErr) scheduleUpload(); }
}
function editorDataPanel(){
  const m = getMeta();
  return `<div class="scrim" data-close></div><aside class="panel" role="dialog" aria-label="Данные">
    <div class="head"><h2>Данные</h2><button class="btn ghost" data-close type="button" aria-label="Закрыть">✕</button></div>
    <div class="box"><h4>Доступ с редактированием${m.editorName ? " · " + esc(m.editorName) : ""}</h4>
      <div>Вы вошли как <b>${esc(getUser())}</b> — имя закреплено за вашим паролем владельцем. Ваши касания и изменения подписываются этим именем.</div>
      <div>Клиентов: <b>${clients.length}</b>. Данные от: <b>${m.lastSync ? esc(fmtStamp(m.lastSync)) : "—"}</b>${syncState.status==="offline" ? " · сейчас нет связи" : ""}.</div>
      <div>Последняя отправка: <b>${m.lastUpload ? esc(fmtStamp(m.lastUpload)) : "ещё не было"}</b>${isDirty() ? " · есть неотправленные изменения" : ""}</div>
      ${m.upErr ? `<div style="color:var(--red)">${esc(m.upErr)}</div>` : ""}
      <div class="note">Можно добавлять клиентов, записывать касания и встречи, вести свои задачи. Удалять клиентов может только владелец. Ваши задачи видит владелец.</div>
      <div class="actions"><button class="btn primary small" data-act="upload" type="button">⬆️ Отправить сейчас</button>
        <button class="btn small" data-act="sync" type="button">🔄 Обновить</button>
        <button class="btn small" data-act="csv" type="button">📊 Таблица (.csv)</button>
        <button class="btn ghost small" data-act="logout" type="button">Выйти</button></div></div>
  </aside>`;
}
function uploadBox(){''')

# не перерисовывать открытую карточку, пока человек печатает (фоновые обновления)
rep('''  if(openId) renderPanel();
}''', '''  if(openId){ const a = document.activeElement; if(!(a && overlay.contains(a) && /INPUT|TEXTAREA|SELECT/.test(a.tagName))) renderPanel(); }
}''')

# гость: имя и фамилия тоже назначаются владельцем и закрепляются за паролем
rep('''  setMeta({lastSync: snap.updated, guestName: snap.guestName || ""});''',
    '''  setMeta({lastSync: snap.updated, guestName: snap.guestName || ""}); setUser((snap.guestName || "").trim());''')
rep('''<label class="f">Имя нового гостя (видно только вам)<input id="gname" type="text" placeholder="Например: Иван, директор" required maxlength="40"></label>''',
    '''<label class="f">Имя и фамилия гостя (закрепляются за паролем)<input id="gname" type="text" autocapitalize="words" placeholder="Например: Иван Петров" required maxlength="60"></label>''')
rep('''      if(!name){ toast("Укажите имя гостя"); return; }''', '''      if(!validName(name)){ toast("Укажите имя и фамилию гостя"); return; }''')
rep('''el.textContent = "👁 Гость · только просмотр"; return; }''', '''el.textContent = `👁 ${getUser() || "Гость"} · только просмотр`; return; }''')
rep('''  if(login) toast("Гостевой доступ: только просмотр");''', '''  if(login) toast(snap.guestName ? `Вы вошли как ${snap.guestName} · только просмотр` : "Гостевой доступ: только просмотр");''')

# имя владельца — общее для всех его устройств (вводится один раз)
rep('''editors: getEditors(), tasks: getTasks(), gh: tok});''', '''editors: getEditors(), tasks: getTasks(), gh: tok, ownerName: getUser(), editorTasks: getEdTasks()});''')
rep('''  if(!getGh() && sh.gh){''', '''  if(!getUser() && sh.ownerName){ setUser(sh.ownerName); changed++; }
  if(!getGh() && sh.gh){''')

# вкладка «Задачи»: у владельца — блок задач редакторов, у редактора — пояснение; автор задачи
rep("""    <p class="note" style="margin-top:14px">🔒 Задачи видите только вы — на всех своих устройствах. Гостям они не показываются и в их копии не попадают.</p>`;""",
    """    ${edTasksHtml()}
    <p class="note" style="margin-top:14px">${isEditor() ? "🔒 Это ваши задачи. Их видите вы и владелец; гостям они не показываются." : "🔒 Ваши задачи видите только вы — на всех своих устройствах. Редакторам и гостям они не показываются."}</p>`;""")
rep("""owner, prio: taskPrio, text, done: false, created: now, updated: now});""", """owner, prio: taskPrio, text, done: false, created: now, updated: now, by: whoAmI()});""")
