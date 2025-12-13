from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import uvicorn
from fastapi.responses import FileResponse
import os
from fastapi import APIRouter
from database import SessionLocal, init_db, TestResult



# =========================
# ИНИЦИАЛИЗАЦИЯ
# =========================

init_db()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Загружаем вопросы
with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# =========================
# ГЛАВНАЯ СТРАНИЦА
# =========================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# =========================
# СТРАНИЦА ТЕСТА
# =========================

@app.get("/test", response_class=HTMLResponse)
async def test(request: Request):
    user = {
        "firstname": request.query_params.get("firstname", ""),
        "lastname": request.query_params.get("lastname", ""),
        "middlename": request.query_params.get("middlename", ""),
        "age": request.query_params.get("age", 0)
    }

    if not user["firstname"] or not user["lastname"]:
        return RedirectResponse(url="/")

    return templates.TemplateResponse(
        "test.html",
        {"request": request, "questions": questions, "user": user}
    )

# =========================
# СОХРАНЕНИЕ РЕЗУЛЬТАТА
# =========================

def save_result(user, score, total):
    db = SessionLocal()
    result = TestResult(
        lastname=user.get("lastname", ""),
        firstname=user.get("firstname", ""),
        middlename=user.get("middlename", ""),
        age=int(user.get("age", 0)),
        score=score,
        total=total
    )
    db.add(result)
    db.commit()
    db.close()

# =========================
# ОТПРАВКА ТЕСТА
# =========================

@app.post("/submit")
async def submit(request: Request):
    """
    Поддержка JSON и form-data
    """
    try:
        data = await request.json()
        user = data.get("user", {})
        answers = data.get("answers", {})
    except:
        form_data = await request.form()
        # Вытаскиваем user из формы
        user = {
            "firstname": form_data.get("firstname", ""),
            "lastname": form_data.get("lastname", ""),
            "middlename": form_data.get("middlename", ""),
            "age": form_data.get("age", 0)
        }
        # Остальные поля — ответы
        answers = {k: v for k, v in form_data.items() if k not in user and k != "time_elapsed"}

    # Подсчет баллов
    score = 0
    for q in questions:
        your_answer = answers.get(q["question"], "")
        if your_answer == q["answer"]:
            score += 1

    save_result(user, score, len(questions))

    # Если JSON-запрос
    if request.headers.get("accept") == "application/json" or "application/json" in request.headers.get("content-type", ""):
        return JSONResponse({"score": score, "total": len(questions), "user": user})

    # Иначе HTML
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "score": score,
            "total": len(questions),
            "user": user
        }
    )

# =========================
# ВСЕ РЕЗУЛЬТАТЫ
# =========================

@app.get("/results", response_class=HTMLResponse)
async def results(request: Request):
    db = SessionLocal()
    # Сортируем по времени прохождения теста, сначала идут первые
    all_results = db.query(TestResult).order_by(TestResult.timestamp.asc()).all()
    db.close()

    # Добавляем поле rank (порядок прохождения)
    for idx, r in enumerate(all_results, start=1):
        r.rank = idx

    return templates.TemplateResponse(
        "results.html",
        {"request": request, "results": all_results}
    )

@app.delete("/admin/clear-db")
async def clear_db():
    db = SessionLocal()
    db.query(TestResult).delete()
    db.commit()
    db.close()
    return {"status": "database cleared"}


@app.get("/download_db")
async def download_db():
    db = SessionLocal()
    all_results = db.query(TestResult).order_by(TestResult.id).all()
    db.close()

    filename = "test_results.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("ID | ФИО | Возраст | Баллы | Всего вопросов | Дата и время\n")
        f.write("="*70 + "\n")
        for r in all_results:
            fio = f"{r.lastname} {r.firstname} {r.middlename}".strip()
            timestamp = r.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            line = f"{r.id} | {fio} | {r.age} | {r.score} | {r.total} | {timestamp}\n"
            f.write(line)

    # Отправляем файл пользователю
    return FileResponse(filename, media_type="text/plain", filename=filename)
# =========================
# ЗАПУСК
# =========================

#if __name__ == "__main__":
 #   print("Сервер запущен на http://127.0.0.1:8000")
  #  uvicorn.run(app, host="0.0.0.0", port=8000)
