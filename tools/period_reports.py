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
    def p(v,style=normal): return Paragraph(escape(str(v or "—")),style)
    groups={}
    count=0
    for c in app["clients"]:
        if c.get("id") in (app.get("deleted") or []): continue
        history=sorted([t for t in (c.get("touches") or []) if t and t.get("t")],key=lambda t:str(t.get("d") or ""))
        period=[t for t in history if str(start)<=str(t.get("d",""))[:10]<=str(end)]
        count+=len(period)
        status=c.get("temp")
        group={"branch":"ФИЛИАЛЫ","dealer":"ДЕЙСТВУЮЩИЕ ДИЛЕРЫ","refused":"ОТКАЗЫ"}.get(status,"В ПРОРАБОТКЕ — СТАДИЯ НЕ ПОДТВЕРЖДЕНА")
        a=analyses.get(c.get("id"),{})
        stage=a.get("situation") or "Первичная стадия переговоров"
        prospect=(" ".join(a[k] for k in ("trend","goal","obstacle") if a.get(k))) or "Первичная проработка: возможность сотрудничества предстоит уточнить."
        groups.setdefault(group,[]).append([p(" / ".join(str(c.get(k) or "") for k in ("name","region")).strip(" /"),bold),p(len(period)),p(c.get("revenue") or "Нет подтверждённых данных"),p(stage),p(prospect)])
    n=sum(map(len,groups.values()))
    story=[p("Сергей Алексеевич, добрый день!",bold),p("Ниже — состояние работы с потенциальными дилерами за "+str(start)+" — "+str(end)),Spacer(1,12),p("ГЛАВНОЕ",heading),p(f"Компаний в отчёте: {n}. Касаний за период: {count}. Стадии подписания и намерения не подсчитаны без подтверждённых данных."),Spacer(1,10)]
    kpi=Table([[p(n,heading),p(count,heading),p("—",heading),p("—",heading)],[p("компаний в работе"),p("касаний отработано"),p("на подписании"),p("подтвердили намерение")]],colWidths=[187]*4)
    kpi.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#edf1f6")),("BOX",(0,0),(-1,-1),0.5,navy),("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.extend([kpi,Spacer(1,16)])
    for group,rows in groups.items():
        story.append(p(group,heading))
        table=Table([[p(x,bold) for x in ["Компания, регион","Кас.","Выручка 2025","Стадия","Перспектива"]]]+rows,colWidths=[155,45,95,235,218],repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#dce5ef")),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f2f3f5")]),("VALIGN",(0,0),(-1,-1),"TOP"),("LINEBELOW",(0,0),(-1,0),1,navy)]))
        story.extend([table,Spacer(1,12)])
    out=io.BytesIO()
    SimpleDocTemplate(out,pagesize=landscape(A4),leftMargin=45,rightMargin=45,topMargin=35,bottomMargin=35).build(story)
    return out.getvalue()

if __name__=="__main__":
    main()
