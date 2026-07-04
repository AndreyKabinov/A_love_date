import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Загружаем переменные из .env (если есть)
load_dotenv()

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Конфигурация SMTP из переменных окружения ---
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")          # ваша почта (отправитель)
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # пароль или app‑password
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", SMTP_USER)  # куда отправлять

# Проверяем обязательные переменные
if not SMTP_USER or not SMTP_PASSWORD:
    logger.warning("SMTP_USER или SMTP_PASSWORD не заданы! Письма не будут отправляться.")

# --- Схема данных от фронтенда ---
class DateRequest(BaseModel):
    date: str = Field(..., description="Дата в формате YYYY-MM-DD")
    comment: str = Field("", description="Комментарий пользователя")

# --- Создаём приложение FastAPI ---
app = FastAPI(
    title="Приглашение на свидание — бэкенд",
    description="Принимает дату и комментарий, отправляет письмо на почту",
    version="1.0.0"
)

# --- Разрешаем CORS для фронтенда (GitHub Pages и локальной разработки) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ваш-username.github.io",  # замените на свой GitHub Pages адрес
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "*"  # для тестирования (в продакшене лучше указать конкретные домены)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Эндпоинт для проверки здоровья ---
@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "Сервер работает"}

# --- Основной эндпоинт ---
@app.post("/send-email", status_code=status.HTTP_200_OK)
async def send_email(request: DateRequest):
    """
    Принимает JSON с полями date и comment,
    формирует письмо и отправляет через SMTP.
    """
    date = request.date
    comment = request.comment

    # Проверяем, что конфигурация почты задана
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.error("SMTP-учётные данные не настроены.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Почтовый сервис не настроен на сервере."
        )

    # --- Формируем письмо ---
    subject = "💕 Новое приглашение на свидание!"
    body = f"""
Здравствуйте!

Пользователь ответил на ваше приглашение:

📅 Дата: {date}
💬 Комментарий: {comment if comment else "❤️ (без комментария)"}

С наилучшими пожеланиями,
Ваш романтичный бот 💖
    """

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # --- Отправка через SMTP ---
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()  # защищённое соединение
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Письмо успешно отправлено на {RECIPIENT_EMAIL}")
        return {
            "success": True,
            "message": "Письмо отправлено! 💌",
            "recipient": RECIPIENT_EMAIL
        }
    except smtplib.SMTPAuthenticationError:
        logger.error("Ошибка аутентификации SMTP. Проверьте логин/пароль.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учётные данные почтового ящика."
        )
    except smtplib.SMTPException as e:
        logger.error(f"SMTP ошибка: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Не удалось отправить письмо: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера."
        )

# --- Точка входа для локального запуска ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )