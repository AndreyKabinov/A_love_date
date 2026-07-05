import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# --- Схема данных ---
class DateRequest(BaseModel):
    date: str
    comment: str = ""

# --- Создаём приложение ---
app = FastAPI()

# --- Разрешаем CORS для всех источников (для ngrok и GitHub Pages) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # можно указать конкретные домены позже
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Файл для сохранения ---
LOG_FILE = "responses.txt"

# --- Проверка ---
@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "Сервер на FastAPI работает!"}

# --- Основной эндпоинт ---
@app.post("/send-email")
async def save_data(request: DateRequest):
    date = request.date
    comment = request.comment

    # Записываем в файл с временной меткой
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] Дата: {date} | Комментарий: {comment}\n")

    # Выводим в консоль, чтобы видеть в реальном времени
    print(f"✅ Получено: {date} - {comment}")

    return {"success": True, "message": "Данные сохранены!"}

# --- Запуск (если файл запущен напрямую) ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)



