import os, json, base64, hashlib, datetime as dt, io, ssl, smtplib
from pathlib import Path
from email.message import EmailMessage
from xml.sax.saxutils import escape
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4, landscape

from semantic_analysis import analyze

def main():
    box=json.loads(Path("data/app.enc.json").read_text())
    b=base64.b64decode
    key=hashlib.pbkdf2_hmac("sha256",os.environ["WAYTEKO_PW"].encode(),b(box["salt"]),box["iter"],32)
    app=json.loads(AESGCM(key).decrypt(b(box["iv"]),b(box["ct"]),None))
    day=dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).date()
    schedule=os.environ.get("SCHEDULE","")
    modes=["week","month"] if not schedule else (["week"] if schedule=="0 16 * * 5" else ["month"] if (day+dt.timedelta(days=1)).month!=day.month else [])
    if not modes: return
    advice_box=json.loads(Path("data/advice.enc.json").read_text())
    advice_key=hashlib.pbkdf2_hmac("sha256",os.environ["WAYTEKO_PW"].encode(),b(advice_box["salt"]),advice_box["iter"],32)
    items=json.loads(AESGCM(advice_key).decrypt(b(advice_box["iv"]),b(advice_box["ct"]),None)).get("items",{})
    analyses={}
    reused=0
    refreshed=0
    for c in app["clients"]:
        if c.get("id") in (app.get("deleted") or []): continue
        if not any(t and t.get("t") for t in (c.get("touches") or [])): continue
        data = {"status": c.get("temp"), "intro": c.get("intro"), "next_call": c.get("next"), "plan": c.get("plan"), "touches": [x for x in (c.get("touches") or []) if x and x.get("t")], "meets": c.get("meets") or [], "contract": c.get("contract")}
        fingerprint=hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        cached=items.get(c["id"]) or {}
        a=cached.get("analysis") or {}
        if cached.get("source")=="qwen" and cached.get("fingerprint")==fingerprint and cached.get("day")==day.isoformat() and all(isinstance(a.get(k),str) and a[k].strip() for k in ("situation","trend","goal","obstacle")):
            analyses[c["id"]]=a
            reused+=1
            continue
        for attempt in range(3):
            try:
                analyses[c["id"]]=analyze(data,day.isoformat())["analysis"]
                refreshed+=1
                break
            except Exception:
                if attempt==2: raise RuntimeError("Client analysis failed after retries; report not sent") from None
    print("Verified cached analyses:",reused,"Refreshed:",refreshed)
    for mode in modes:
        start=day-dt.timedelta(days=day.weekday()) if mode=="week" else day.replace(day=1)
        end=min(day,start+dt.timedelta(days=4)) if mode=="week" else day
        pdf=render(app,start,end,analyses)
        msg=EmailMessage()
        msg["From"]="e.zakharov1222@gmail.com"
        msg["To"]="zaharov@wayteko.ru"
        msg["Cc"]="ezakharov1222@gmail.com"
        msg["Subject"]="WAYTEKO — "+("Недельный" if mode=="week" else "Месячный")+" PDF "+str(end)
        msg.set_content("Отчёт по фактическим касаниям за "+str(start)+" — "+str(end))
        msg.add_attachment(pdf,maintype="application",subtype="pdf",filename="WAYTEKO-"+mode+"-"+str(end)+".pdf")
        with smtplib.SMTP_SSL("smtp.gmail.com",465,context=ssl.create_default_context(),timeout=60) as smtp:
            smtp.login(msg["From"],os.environ["WAYTEKO_SMTP_PASSWORD"].replace(" ",""))
            if smtp.send_message(msg): raise RuntimeError("Recipient refused")
        print("PDF sent:",mode)

def render(app,start,end,analyses):
    for name,file in [("Regular","DejaVuSans.ttf"),("Bold","DejaVuSans-Bold.ttf")]:
        pdfmetrics.registerFont(TTFont(name,"/usr/share/fonts/truetype/dejavu/"+file))
    navy=colors.HexColor("#18365b")
    normal=ParagraphStyle("normal",fontName="Regular",fontSize=9,leading=12)
    bold=ParagraphStyle("bold",parent=normal,fontName="Bold")
    heading=ParagraphStyle("heading",parent=bold,fontSize=12,leading=16,textColor=navy)
    def p(v,style=normal): return Paragraph(escape(str(v if v is not None and v != "" else "—")),style)
    groups={}
    count=0
    signing=0
    interested=0
    overdue=0
    turnover={}
    def revenue(c):
        try: return float(str(c.get("revenue")).replace(" ","").replace(",","."))
        except (ValueError,TypeError): return None
    def money(v): return (f"{v/1000:,.1f} млрд ₽" if v>=1000 else f"{v:,.1f} млн ₽").replace(","," ").replace(".",",")
    for c in app["clients"]:
        if c.get("id") in (app.get("deleted") or []): continue
        history=sorted([t for t in (c.get("touches") or []) if t and t.get("t")],key=lambda t:str(t.get("d") or ""))
        period=[t for t in history if str(start)<=str(t.get("d",""))[:10]<=str(end)]
        count+=len(period)
        status=c.get("temp")
        a=analyses.get(c.get("id"),{})
        contract=c.get("contract")
        pending=contract in (True,"work")
        signed=contract=="signed"
        # Require positive evidence in the latest relevant recorded contact.
        import re
        positive=r"(запросил[аи]?|попросил[аи]?|запросили|интересует|заинтересован[аы]?|подтвердил[аи]? интерес|хотят.{0,30}дилер|получил.{0,25}заказ|согласовали.{0,30}условия|договорились о работе)"
        negative=r"(не заинтересован|не интересует|отказал|отказались|интерес потерян|не актуально|неактуально)"
        intent=False
        for touch in reversed(history):
            t=str(touch.get("t","")).lower()
            if re.search(negative,t): break
            if re.search(positive,t): intent=True; break
        if not history:
            t=str(c.get("intro") or "").lower()
            intent=bool(re.search(positive,t) and not re.search(negative,t))
        special={"branch":"ФИЛИАЛЫ","dealer":"ДЕЙСТВУЮЩИЕ ДИЛЕРЫ","refused":"ОТКАЗЫ"}
        if status not in special:
            overdue+=int(bool(c.get("next") and str(c["next"])[:10]<str(end)))
            signing+=int(pending)
            interested+=int(intent or pending or signed)
        group=special.get(status) or ("ПРИОРИТЕТ A — ДОГОВОР В РАБОТЕ" if pending else "ДЕЙСТВУЮЩИЕ ДИЛЕРЫ" if signed else "ПРИОРИТЕТ B — ПОДТВЕРЖДЁННЫЙ ИНТЕРЕС" if intent else "ПРИОРИТЕТ C — ПЕРВИЧНАЯ ПРОРАБОТКА")
        v=revenue(c)
        if v is not None: turnover[group]=turnover.get(group,0)+v
        stage=a.get("situation") or "Первичная стадия переговоров"
        if pending: stage="Договор в работе. "+stage
        elif signed: stage="Договор подписан. "+stage
        prospect=(" ".join(a[k] for k in ("trend","goal","obstacle") if a.get(k))) or "Первичная проработка: возможность сотрудничества предстоит уточнить."
        groups.setdefault(group,[]).append([p(" / ".join(str(c.get(k) or "") for k in ("name","region")).strip(" /"),bold),p(len(period)),p(money(v) if v is not None else "Нет данных"),p(stage),p(prospect)])
    n=sum(map(len,groups.values()))
    a_total=sum(v for g,v in turnover.items() if g.startswith("ПРИОРИТЕТ A"))
    b_total=sum(v for g,v in turnover.items() if g.startswith("ПРИОРИТЕТ B"))
    story=[p("Сергей Алексеевич, добрый день!",bold),p("Ниже — состояние работы с потенциальными дилерами за "+str(start)+" — "+str(end)),Spacer(1,12),p("ГЛАВНОЕ",heading),p(f"— {n} компаний в отчёте, {count} касаний за период. Просроченных контактов: {overdue}."),p(f"— {signing} компаний на стадии подписания: договор в работе."),p(f"— {interested} компаний подтвердили заинтересованность или перешли к договору."),p(f"— Известный суммарный оборот: приоритет А — {money(a_total)}, приоритет Б — {money(b_total)}. Компании без данных о выручке не включены в суммы."),Spacer(1,10)]
    kpi=Table([[p(n,heading),p(count,heading),p(signing,heading),p(interested,heading)],[p("компаний в работе"),p("касаний отработано"),p("на подписании"),p("подтвердили намерение")]],colWidths=[187]*4)
    kpi.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#edf1f6")),("BOX",(0,0),(-1,-1),0.5,navy),("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.extend([kpi,Spacer(1,16)])
    for group,rows in sorted(groups.items(),key=lambda x: next((i for i,k in enumerate(("ПРИОРИТЕТ A","ПРИОРИТЕТ B","ПРИОРИТЕТ C","ДЕЙСТВУЮЩИЕ","ФИЛИАЛЫ","ОТКАЗЫ")) if x[0].startswith(k)),99)):
        story.append(p(group,heading))
        story.append(p(f"Компаний: {len(rows)}. Известный суммарный оборот: {money(turnover.get(group,0))}."))
        table=Table([[p(x,ParagraphStyle("th",parent=bold,textColor=colors.white)) for x in ["Компания, регион","Кас.","Выручка 2025","Стадия","Перспектива"]]]+rows,colWidths=[155,45,95,235,218],repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),navy),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#fce9df"),colors.HexColor("#fff4ed")] if group.startswith("ПРИОРИТЕТ A") else [colors.white,colors.HexColor("#f2f3f5")]),("VALIGN",(0,0),(-1,-1),"TOP"),("LINEBELOW",(0,0),(-1,0),1,navy)]))
        story.extend([table,Spacer(1,12)])
    out=io.BytesIO()
    SimpleDocTemplate(out,pagesize=landscape(A4),leftMargin=45,rightMargin=45,topMargin=35,bottomMargin=35).build(story)
    return out.getvalue()

if __name__=="__main__":
    main()
