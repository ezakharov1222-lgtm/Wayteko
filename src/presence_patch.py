# Выполняется внутри make_app.py после roles_patch.py.
# «В сети» для редакторов и гостей: последний вход, всплывающее уведомление владельцу при входе
# (висит, пока не закроет), системное уведомление на компьютере. Видит только владелец.

# ---------- редакторы тоже отмечаются «в сети»
rep('''async function beat(state){
  if(!isGuest() || !getPw()) return;''', '''async function beat(state){
  if(!(isGuest() || isEditor()) || !getPw()) return;''')
rep('''  if(presTimer || !isGuest()) return;
  beat("on");
  presTimer = setInterval(() => { if(!document.hidden && isGuest()){ beat("on"); syncNow(); } }, 120000);''',
    '''  if(presTimer || !(isGuest() || isEditor())) return;
  beat("on");
  presTimer = setInterval(() => { if(!document.hidden && (isGuest() || isEditor())){ beat("on"); if(isGuest()) syncNow(); } }, 110000);''')
rep('''function startEditor(){ if(edTimer || !isEditor()) return;''', '''function startEditor(){ startPresence(); if(edTimer || !isEditor()) return;''')
rep('''  if(!openId) render(); syncNow(); if(isGuest()) beat("on"); else if(isOwner()){''', '''  if(!openId) render(); syncNow(); if(isGuest() || isEditor()) beat("on"); else if(isOwner()){''')

# ---------- владелец следит за гостями и редакторами
rep('''  const list = activeGuests(); if(!list.length || !isOwner()){ guestSeen = {}; renderGuestPill(); return; }''',
    '''  const list = [...activeGuests(), ...activeEditors()]; if(!list.length || !isOwner()){ guestSeen = {}; renderGuestPill(); return; }''')
rep('''  list.forEach((g, i) => { next[g.id] = res.at(i); }); guestSeen = next;
  renderGuestPill();''', '''  list.forEach((g, i) => { next[g.id] = res.at(i); }); guestSeen = next;
  presenceNotify(list);
  renderGuestPill();''')
rep('''setInterval(() => { if(!document.hidden && !isGuest() && activeGuests().length) checkGuest(); }, 30000);''',
    '''setInterval(() => { if(isOwner() && getPw() && (activeGuests().length || activeEditors().length)) checkGuest(); }, 30000);
renderNotices();''')
rep('''  const on = activeGuests().filter(g => guestSeen[g.id] && guestSeen[g.id].online).map(g => g.name || "Гость");''',
    '''  const on = [...activeEditors(), ...activeGuests()].filter(g => guestSeen[g.id] && guestSeen[g.id].online).map(g => g.name || "Гость");''')
rep('''function guestStatus(gs){
  return !gs ? "проверяю…" : gs.online ? `🟢 в сети${gs.tab && TABNAME[gs.tab] ? " · смотрит «" + TABNAME[gs.tab] + "»" : ""}`
    : gs.at ? `был в сети ${esc(fmtStamp(new Date(gs.at).toISOString()))}` : gs.err ? "статус недоступен" : "ещё не заходил";
}''', '''function seenOf(id){
  const gs = guestSeen[id], st = getSeen()[id];
  if(!gs && !st) return null;
  const at = Math.max((gs && gs.at) || 0, (st && st.at) || 0) || null;
  return {...(gs || {online: false}), at};
}
function guestStatus(gs){
  return !gs ? "проверяю…" : gs.online ? `🟢 в сети${gs.tab && TABNAME[gs.tab] ? " · смотрит «" + TABNAME[gs.tab] + "»" : ""}`
    : gs.at ? `последний раз в сети: ${esc(fmtStamp(new Date(gs.at).toISOString()))}` : gs.err ? "статус недоступен" : "ещё не заходил(а)";
}''')
rep('''      <div><b>${esc(g.name || "Гость")}</b> · ${guestStatus(guestSeen[g.id])}</div>''',
    '''      <div><b>${esc(g.name || "Гость")}</b> · ${guestStatus(seenOf(g.id))}</div>''')
rep('''      <div><b>${esc(x.name || "Редактор")}</b></div>''', '''      <div><b>${esc(x.name || "Редактор")}</b> · ${guestStatus(seenOf(x.id))}</div>''')
# кнопка системных уведомлений — в блоке редакторов у владельца
rep('''    ${list.length ? `<div class="note">Изменения редактора приходят к вам в течение минуты''',
    '''    ${notifyBtn()}
    ${list.length ? `<div class="note">Изменения редактора приходят к вам в течение минуты''')
# «последний раз в сети» — общее для всех устройств владельца
rep('''editorTasks: getEdTasks()});''', '''editorTasks: getEdTasks(), seen: seenForShare()});''')
rep('''  if(!getUser() && sh.ownerName){ setUser(sh.ownerName); changed++; }''', '''  if(!getUser() && sh.ownerName){ setUser(sh.ownerName); changed++; }
  mergeSeen(sh.seen);''')

# ---------- стили и код уведомлений
rep('.guest .temps button{pointer-events:none}', '''.notices{position:fixed;bottom:calc(env(safe-area-inset-bottom,0px) + 64px);left:max(10px,env(safe-area-inset-left,0px));z-index:60;display:grid;gap:8px;width:min(360px,calc(100vw - 20px))}
.notice{background:var(--surface);border:1px solid var(--line);border-left:5px solid var(--green);border-radius:10px;box-shadow:0 8px 28px rgba(0,0,0,.18);padding:10px 12px;display:flex;gap:10px;align-items:flex-start;font-size:14px}
.notice b{display:block}.notice .muted{font-size:12px}.notice button{margin-left:auto;flex:0 0 auto}
.guest .temps button{pointer-events:none}''')
rep('''<div class="toast" id="toast" hidden></div>''', '''<div class="toast" id="toast" hidden></div>
<div class="notices" id="notices" hidden></div>''')
rep('''// ---------- доступ с редактированием (до 4 человек''', '''// ---------- «в сети»: последний вход и уведомления о входе (видит только владелец)
const SEENKEY = "wayteko.seen.v1", NOTKEY = "wayteko.notices.v1";
function getSeen(){ try { const v = JSON.parse(localStorage.getItem(SEENKEY) || "{}"); return v && typeof v === "object" ? v : {}; } catch(e){ return {}; } }
function setSeen(v){ try { localStorage.setItem(SEENKEY, JSON.stringify(v)); } catch(e){} }
function seenForShare(){ const s = getSeen(), o = {}; for(const [k, v] of Object.entries(s)) if(v && v.at) o[k] = v.at; return o; }
function mergeSeen(o){ if(!o || typeof o !== "object") return; const s = getSeen(); let ch = false;
  for(const [k, at] of Object.entries(o)){ if(+at > ((s[k] || {}).at || 0)){ s[k] = {...(s[k] || {}), at: +at}; ch = true; } } if(ch) setSeen(s); }
function getNotices(){ try { const v = JSON.parse(localStorage.getItem(NOTKEY) || "[]"); return Array.isArray(v) ? v : []; } catch(e){ return []; } }
function setNotices(l){ try { localStorage.setItem(NOTKEY, JSON.stringify(l.slice(-20))); } catch(e){} }
function presenceNotify(list){
  if(!isOwner()) return;
  const s = getSeen(), add = [];
  for(const p of list){
    const r = guestSeen[p.id]; if(!r || r.err) continue;
    const prev = s[p.id] || {};
    if(r.online && !prev.online) add.push({id: p.id, name: p.name || (p.id[0] === "e" ? "Редактор" : "Гость"), kind: p.id[0] === "e" ? "редактор" : "гость", at: r.at || Date.now()});
    s[p.id] = {online: !!r.online, at: Math.max(prev.at || 0, r.at || 0) || null};
  }
  setSeen(s);
  if(!add.length) return;
  setNotices([...getNotices(), ...add]); renderNotices();
  if("Notification" in window && Notification.permission === "granted")
    add.forEach(n => { try { new Notification("WAYTEKO: " + n.name + " в сети", {body: `${n.kind === "редактор" ? "Редактор" : "Гость"} зашёл в приложение · ${new Date(n.at).toLocaleTimeString("ru-RU", {hour: "2-digit", minute: "2-digit"})}`, tag: n.id + n.at, requireInteraction: true, icon: "icon-192.png"}); } catch(e){} });
}
function renderNotices(){
  const el = document.getElementById("notices"); if(!el) return;
  const l = isOwner() && getPw() ? getNotices() : [];
  el.hidden = !l.length; if(!l.length){ el.innerHTML = ""; return; }
  el.innerHTML = l.map((n, i) => `<div class="notice" role="status"><span>🟢</span><div><b>${esc(n.name)} — в сети</b><div class="muted">${n.kind === "редактор" ? "Редактор" : "Гость"} зашёл в приложение · ${esc(fmtStamp(new Date(n.at).toISOString()))}</div></div>
    <button class="btn ghost small" data-ndel="${i}" type="button" aria-label="Закрыть уведомление">✕</button></div>`).join("")
    + (l.length > 1 ? `<div style="text-align:right"><button class="btn small" data-ndel="all" type="button">Закрыть все</button></div>` : "");
}
function notifyBtn(){
  if(!("Notification" in window)) return "";
  if(Notification.permission === "granted") return `<div class="note">🔔 Уведомления о входе на этом устройстве включены — и в приложении, и системные.</div>`;
  if(Notification.permission === "denied") return `<div class="note">🔔 Системные уведомления запрещены в настройках браузера — уведомления о входе показываются внутри приложения.</div>`;
  return `<div class="actions"><button class="btn small" data-act="notify-on" type="button">🔔 Включить системные уведомления на этом устройстве</button></div>`;
}
document.addEventListener("click", async e => {
  const b = e.target.closest("[data-ndel],[data-act='notify-on']"); if(!b) return;
  if(b.dataset.act === "notify-on"){ try { await Notification.requestPermission(); } catch(_){} renderPanel(); return; }
  const v = b.dataset.ndel, l = getNotices(); setNotices(v === "all" ? [] : l.filter((_, i) => String(i) !== v)); renderNotices();
});
window.addEventListener("pagehide", () => { if(isGuest() || isEditor()) beat("off"); });

// ---------- доступ с редактированием (до 4 человек''')
