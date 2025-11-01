from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import uvicorn

# ------------------------
# Настройка FastAPI
# ------------------------
app = FastAPI()

# Статика и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Загрузка вопросов
with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)


# ------------------------
# Роуты
# ------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/test", response_class=HTMLResponse)
async def test(request: Request):
    return templates.TemplateResponse("test.html", {"request": request, "questions": questions})

@app.post("/submit", response_class=HTMLResponse)
async def submit(request: Request):
    form_data = await request.form()
    answers = dict(form_data)

    score = 0
    for q in questions:
        if answers.get(q["question"]) == q["answer"]:
            score += 1

    return templates.TemplateResponse(
        "result.html",
        {"request": request, "score": score, "total": len(questions)}
    )


# ------------------------
# Автозапуск локального сервера
# ------------------------
if __name__ == "__main__":
    print("Сервер запущен локально на http://127.0.0.1:8000")
    print("Для остановки сервера нажмите Ctrl+C")
    uvicorn.run(app, host="0.0.0.0", port=8000)
