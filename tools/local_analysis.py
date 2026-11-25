"""Generate rule-based recommendations; no external services."""
import json, sys, datetime as dt
def analyze(c, today):
    touches = c.get("touches") or []
    last = touches[-1] if touches else {}
    raw = str(last.get("t") or c.get("intro") or "")
    try:
        age = max(0, (today - dt.date.fromisoformat(str(last.get("d"))[:10])).days)
    except ValueError:
        age = None
    overdue = str(c.get("next_call") or "")[:10]
    late = bool(overdue and overdue < today.isoformat())
    score = max(0, min(100, 30 + min(len(touches), 5)*6 - (15 if late else 0) - (15 if age is not None and age > 30 else 0)))
    step = "Уточните текущий статус и согласуйте следующий шаг."
    obstacle = "Причина задержки не подтверждена."
    role = "sales"
    if late:
        step = "Свяжитесь с клиентом и согласуйте новую дату решения."
    return {"r": role, "t": step, "analysis": {
        "score": score, "trend": "Недостаточно данных для оценки динамики",
        "risk": "Повышенный" if late or (age is not None and age > 30) else "Не определён",
        "situation": ("Последнее касание: " + raw)[:300] if raw else "Нет описания касания.",
        "obstacle": obstacle, "step": step, "goal": "Согласовать конкретный следующий шаг.",
        "question": "Что необходимо для следующего решения?",
        "avoid": "Не считать интерес подтверждённым без ответа клиента.",
        "when": "Сегодня" if late else "По согласованному графику"}}
if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    today = dt.date.fromisoformat(data["today"])
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump({c["id"]: analyze(c, today) for c in data["clients"]}, f, ensure_ascii=False)
