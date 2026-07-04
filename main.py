import os
import logging
import requests
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Конфигурация VK ---
VK_ACCESS_TOKEN = os.getenv("VK_ACCESS_TOKEN")
VK_USER_ID = os.getenv("VK_USER_ID")  # ваш ID ВКонтакте
VK_API_VERSION = "5.199"  # актуальная версия API

if not VK_ACCESS_TOKEN or not VK_USER_ID:
    logger.warning("VK_ACCESS_TOKEN или VK_USER_ID не заданы!")

# --- Схема данных ---
class DateRequest(BaseModel):
    date: str
    comment: str = ""

# --- FastAPI ---
app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://ваш-username.github.io",  # замените на свой
        "*"  # для теста
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Проверка ---
@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "VK бот работает!"}

# --- Отправка в VK ---
@app.post("/send-email", status_code=status.HTTP_200_OK)
async def send_to_vk(request: DateRequest):
    date = request.date
    comment = request.comment

    if not VK_ACCESS_TOKEN or not VK_USER_ID:
        raise HTTPException(
            status_code=500,
            detail="VK не настроен на сервере."
        )

    # Формируем текст сообщения
    text = f"""💕 Новое приглашение на свидание!

📅 Дата: {date}
💬 Комментарий: {comment if comment else "❤️ (без комментария)"}
    """

    url = "https://api.vk.com/method/messages.send"
    params = {
        "user_id": VK_USER_ID,
        "random_id": 0,  # обязательно для избежания дублей
        "message": text,
        "access_token": VK_ACCESS_TOKEN,
        "v": VK_API_VERSION
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Проверяем на ошибки VK
        if "error" in data:
            error_msg = data["error"].get("error_msg", "Неизвестная ошибка")
            logger.error(f"Ошибка VK: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"VK вернул ошибку: {error_msg}"
            )

        logger.info(f"Сообщение отправлено в VK пользователю {VK_USER_ID}")
        return {"success": True, "message": "Сообщение отправлено в VK!"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса к VK: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка отправки в VK: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )

# --- Точка входа ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)