import os
import requests
import html
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, который выполнится при старте
    polling_task = asyncio.create_task(telegram_polling())
    yield
    # Код, который выполнится при остановке
    polling_task.cancel()

app = FastAPI(lifespan=lifespan)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Чтение конфигурации
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Читаем ID и превращаем в список (поддерживаем один ID или несколько через запятую)
raw_chat_ids = os.getenv("TELEGRAM_CHAT_ID", "")
AUTHORIZED_IDS = [id.strip() for id in raw_chat_ids.split(",") if id.strip()]
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")

# --- ССЫЛКИ ДЛЯ МЕНЮ (Вставьте свои) ---
WEBSITE_URL = "https://domio.ugo.si/"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1CCSdqINQ_0fzc1Yd_fDPFIFwxt0_8L7W0zWq5QyhKaU/edit?gid=0#gid=0"

def get_recent_clients():
    """Запрашивает список клиентов из Google Script (через doGet)"""
    try:
        response = requests.get(GOOGLE_SCRIPT_URL, timeout=15)
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                print(f"Ошибка: Google Script вернул не JSON. Ответ сервера: {response.text[:200]}")
        else:
            print(f"Ошибка: Google Script вернул статус {response.status_code}")
    except Exception as e:
        print(f"Ошибка при запросе к Google Script: {e}")
    return []

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

async def telegram_polling():
    """Простой лонг-поллинг для обработки команды /menu"""
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"offset": offset, "timeout": 30}
            # Используем session для эффективности, если нужно, но пока просто requests
            response = requests.get(url, params=params, timeout=35)
            
            if response.status_code == 200:
                updates = response.json().get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    message = update.get("message")
                    if message and "text" in message:
                        text = message["text"]
                        chat_id = message["chat"]["id"]
                        
                        if text == "/menu":
                            # Проверка авторизации (проверяем наличие в списке)
                            if str(chat_id) not in AUTHORIZED_IDS:
                                send_telegram_message(chat_id, "❌ <b>Доступ запрещен.</b>\nВы не авторизованы для использования этой команды.")
                                continue

                            clients = get_recent_clients()
                            
                            clients_text = "<b>Последние 10 клиентов:</b>\n"
                            if not clients or not isinstance(clients, list):
                                clients_text += "<i>Данные пока отсутствуют или ошибка GAS</i>"
                            else:
                                for c in clients:
                                    # Безопасное получение данных
                                    name = c.get('name', '???')
                                    contact = c.get('contact', '???')
                                    price = c.get('price', '0')
                                    clients_text += f"• {name} ({contact}) — {price}\n"
                            
                            menu_msg = (
                                f"<b>🏠 Меню управления</b>\n\n"
                                f"🌐 <a href='{WEBSITE_URL}'>Открыть сайт</a>\n"
                                f"📊 <a href='{SPREADSHEET_URL}'>Открыть таблицу</a>\n\n"
                                f"{clients_text}"
                            )
                            send_telegram_message(chat_id, menu_msg)
                            
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Ошибка поллинга: {e}")
        await asyncio.sleep(1)

@app.post("/api/booking")
async def create_booking(
    name: str = Form(...),
    contact: str = Form(...),
    services: str = Form(...),
    total_price: str = Form(...),
    info: str = Form(None)
):
    """
    Эндпоинт для приема заявок с сайта.
    Отправляет уведомление в Telegram и дублирует данные в Google Sheets через Apps Script.
    """
    
    # Экранируем спецсимволы, чтобы не сломать HTML-разметку Telegram
    safe_name = html.escape(name)
    safe_contact = html.escape(contact)
    safe_services = html.escape(services)
    safe_price = html.escape(total_price)
    safe_info = html.escape(info) if info else "—"

    # --- Шаг 1. Формирование и отправка сообщения в Telegram ---
    message = (
        f"<b>🔔 Новая заявка с сайта</b>\n\n"
        f"👤 <b>Имя:</b> {safe_name}\n"
        f"📞 <b>Контакт:</b> {safe_contact}\n"
        f"💅 <b>Услуги:</b> {safe_services}\n"
        f"💰 <b>Сумма:</b> {safe_price}\n"
        f"📝 <b>Комментарий:</b> {safe_info}"
    )
    
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    tg_payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        tg_response = requests.post(tg_url, json=tg_payload, timeout=10)
        if tg_response.status_code != 200:
            print(f"Ошибка Telegram (Status {tg_response.status_code}): {tg_response.text}")
        tg_response.raise_for_status()
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

    # --- Шаг 2. Пересылка данных в Google Apps Script ---
    gs_payload = {
        "name": name,
        "contact": contact,
        "services": services,
        "total_price": total_price,
        "info": info if info else ""
    }
    
    try:
        # Google Script ожидает данные в формате Form (x-www-form-urlencoded)
        gs_response = requests.post(GOOGLE_SCRIPT_URL, data=gs_payload, timeout=10)
        gs_response.raise_for_status()
    except Exception as e:
        print(f"Ошибка отправки в Google Script: {e}")

    # --- Ответ фронтенду ---
    return {"result": "success"}

if __name__ == "__main__":
    import uvicorn
    # Запуск сервера на порту 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
