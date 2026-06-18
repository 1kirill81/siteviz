import os
import requests
import html
import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()

SERVICES_FILE = "services.json"

def load_services():
    if os.path.exists(SERVICES_FILE):
        with open(SERVICES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_services(services):
    with open(SERVICES_FILE, "w", encoding="utf-8") as f:
        json.dump(services, f, ensure_ascii=False, indent=4)

user_states = {}
temp_data = {}

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
raw_chat_ids = os.getenv("TELEGRAM_CHAT_ID", "")
AUTHORIZED_IDS = [id.strip() for id in raw_chat_ids.split(",") if id.strip()]
TELEGRAM_CHAT_ID = AUTHORIZED_IDS[0] if AUTHORIZED_IDS else None
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")

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

def send_telegram_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

def answer_callback_query(callback_query_id, text=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка ответа на callback query: {e}")

async def telegram_polling():
    """Безопасный асинхронный лонг-поллинг с поддержкой управления услугами"""
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"offset": offset, "timeout": 30}
            
            response = await asyncio.to_thread(requests.get, url, params=params, timeout=35)
            
            if response.status_code == 200:
                updates = response.json().get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    
                    # ОБРАБОТКА CALLBACK QUERIES
                    if "callback_query" in update:
                        cb = update["callback_query"]
                        chat_id = cb["message"]["chat"]["id"]
                        data = cb["data"]
                        cb_id = cb["id"]
                        
                        if str(chat_id) not in AUTHORIZED_IDS:
                            await asyncio.to_thread(answer_callback_query, cb_id, "Нет доступа")
                            continue

                        if data == "services_list":
                            services = load_services()
                            text = "<b>🛠 Управление услугами</b>\nВыберите услугу для редактирования:"
                            buttons = []
                            for s in services:
                                buttons.append([{"text": f"✏️ {s['name']}", "callback_data": f"edit_{s['id']}"}])
                            buttons.append([{"text": "➕ Добавить новую услугу", "callback_data": "add_service"}])
                            buttons.append([{"text": "🏠 В главное меню", "callback_data": "back_to_menu"}])
                            
                            markup = {"inline_keyboard": buttons}
                            await asyncio.to_thread(send_telegram_message, chat_id, text, markup)
                            await asyncio.to_thread(answer_callback_query, cb_id)

                        elif data == "add_service":
                            user_states[chat_id] = "WAIT_ADD_NAME"
                            await asyncio.to_thread(send_telegram_message, chat_id, "📝 Введите <b>название</b> новой услуги:")
                            await asyncio.to_thread(answer_callback_query, cb_id)

                        elif data.startswith("edit_"):
                            s_id = int(data.split("_")[1])
                            services = load_services()
                            service = next((s for s in services if s["id"] == s_id), None)
                            if service:
                                text = (f"<b>Редактирование: {service['name']}</b>\n\n"
                                        f"💰 <b>Цена:</b> {service['price']}\n"
                                        f"📄 <b>Мини-описание:</b> {service['description']}\n"
                                        f"📖 <b>Полное:</b> {service['fullDescription'][:100]}...")
                                buttons = [
                                    [{"text": "🏷 Имя", "callback_data": f"set_name_{s_id}"}, {"text": "💰 Цена", "callback_data": f"set_price_{s_id}"}],
                                    [{"text": "📄 Мини-описание", "callback_data": f"set_desc_{s_id}"}],
                                    [{"text": "📖 Полное описание", "callback_data": f"set_full_{s_id}"}],
                                    [{"text": "🗑 Удалить услугу", "callback_data": f"del_conf_{s_id}"}],
                                    [{"text": "🔙 К списку", "callback_data": "services_list"}]
                                ]
                                markup = {"inline_keyboard": buttons}
                                await asyncio.to_thread(send_telegram_message, chat_id, text, markup)
                            await asyncio.to_thread(answer_callback_query, cb_id)

                        elif data.startswith("set_"):
                            _, field, s_id = data.split("_")
                            user_states[chat_id] = f"WAIT_EDIT_{field.upper()}"
                            temp_data[chat_id] = {"id": int(s_id)}
                            prompt = {
                                "name": "название", "price": "стоимость",
                                "desc": "мини-описание", "full": "полное описание"
                            }.get(field, "значение")
                            await asyncio.to_thread(send_telegram_message, chat_id, f"Введите новое <b>{prompt}</b>:")
                            await asyncio.to_thread(answer_callback_query, cb_id)

                        elif data.startswith("del_conf_"):
                            s_id = int(data.split("_")[2])
                            buttons = [
                                [{"text": "✅ Да, удалить", "callback_data": f"del_yes_{s_id}"}],
                                [{"text": "❌ Отмена", "callback_data": f"edit_{s_id}"}]
                            ]
                            await asyncio.to_thread(send_telegram_message, chat_id, "⚠️ Вы уверены, что хотите <b>УДАЛИТЬ</b> эту услугу?", {"inline_keyboard": buttons})
                            await asyncio.to_thread(answer_callback_query, cb_id)

                        elif data.startswith("del_yes_"):
                            s_id = int(data.split("_")[2])
                            services = [s for s in load_services() if s["id"] != s_id]
                            save_services(services)
                            await asyncio.to_thread(send_telegram_message, chat_id, "✅ Услуга успешно удалена.")
                            # Возврат к списку
                            services = load_services()
                            buttons = [[{"text": f"✏️ {s['name']}", "callback_data": f"edit_{s['id']}"}] for s in services]
                            buttons.append([{"text": "➕ Добавить новую услугу", "callback_data": "add_service"}])
                            await asyncio.to_thread(send_telegram_message, chat_id, "Обновленный список:", {"inline_keyboard": buttons})
                            await asyncio.to_thread(answer_callback_query, cb_id)

                        elif data == "back_to_menu":
                            user_states[chat_id] = None
                            await asyncio.to_thread(send_telegram_message, chat_id, "Возвращаемся...")
                            # Имитируем команду /menu
                            await handle_menu_command(chat_id)
                            await asyncio.to_thread(answer_callback_query, cb_id)
                        
                        continue

                    # ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ
                    message = update.get("message")
                    if message and "text" in message:
                        text = message["text"]
                        chat_id = message["chat"]["id"]
                        
                        if str(chat_id) not in AUTHORIZED_IDS:
                            continue
                        
                        # Команда /cancel для сброса состояния
                        if text == "/cancel":
                            user_states[chat_id] = None
                            await asyncio.to_thread(send_telegram_message, chat_id, "Действие отменено.")
                            continue

                        if text == "/menu" or text == "/start":
                            await handle_menu_command(chat_id)
                            continue

                        # ОБРАБОТКА СОСТОЯНИЙ (STATE MACHINE)
                        state = user_states.get(chat_id)
                        if state:
                            if state == "WAIT_ADD_NAME":
                                temp_data[chat_id] = {"name": text}
                                user_states[chat_id] = "WAIT_ADD_DESC"
                                await asyncio.to_thread(send_telegram_message, chat_id, "Введите <b>краткое описание</b>:")
                            elif state == "WAIT_ADD_DESC":
                                temp_data[chat_id]["description"] = text
                                user_states[chat_id] = "WAIT_ADD_FULL"
                                await asyncio.to_thread(send_telegram_message, chat_id, "Введите <b>полное описание</b>:")
                            elif state == "WAIT_ADD_FULL":
                                temp_data[chat_id]["fullDescription"] = text
                                user_states[chat_id] = "WAIT_ADD_PRICE"
                                await asyncio.to_thread(send_telegram_message, chat_id, "Введите <b>стоимость</b> (например, 1500 ₽):")
                            elif state == "WAIT_ADD_PRICE":
                                services = load_services()
                                new_id = max([s["id"] for s in services] + [0]) + 1
                                
                                # Автоматически добавляем ₽, если пользователь ввел просто число
                                price_text = text.strip()
                                if "₽" not in price_text:
                                    price_text += " ₽"

                                new_service = {
                                    "id": new_id,
                                    "name": temp_data[chat_id]["name"],
                                    "description": temp_data[chat_id]["description"],
                                    "fullDescription": temp_data[chat_id]["fullDescription"],
                                    "price": price_text
                                }
                                services.append(new_service)
                                save_services(services)
                                user_states[chat_id] = None
                                await asyncio.to_thread(send_telegram_message, chat_id, f"✅ Услуга <b>{new_service['name']}</b> добавлена!")
                            
                            elif state.startswith("WAIT_EDIT_"):
                                field = state.replace("WAIT_EDIT_", "").lower()
                                s_id = temp_data[chat_id]["id"]
                                services = load_services()
                                for s in services:
                                    if s["id"] == s_id:
                                        if field == "name": s["name"] = text
                                        elif field == "price": 
                                            # Автоматически добавляем ₽
                                            price_text = text.strip()
                                            if "₽" not in price_text:
                                                price_text += " ₽"
                                            s["price"] = price_text
                                        elif field == "desc": s["description"] = text
                                        elif field == "full": s["fullDescription"] = text
                                        break
                                save_services(services)
                                user_states[chat_id] = None
                                await asyncio.to_thread(send_telegram_message, chat_id, "✅ Изменения сохранены!")

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Ошибка поллинга: {e}")
        await asyncio.sleep(1)

async def handle_menu_command(chat_id):
    """Вспомогательная функция для вывода главного меню"""
    clients = await asyncio.to_thread(get_recent_clients)
    clients_text = "<b>Последние 10 клиентов:</b>\n"
    if not clients or not isinstance(clients, list):
        clients_text += "<i>Данные пока отсутствуют или ошибка GAS</i>"
    else:
        for c in clients:
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
    markup = {
        "inline_keyboard": [
            [{"text": "🛠 Управление услугами", "callback_data": "services_list"}],
            [{"text": "🔄 Обновить список клиентов", "callback_data": "back_to_menu"}]
        ]
    }
    await asyncio.to_thread(send_telegram_message, chat_id, menu_msg, markup)

@app.get("/api/services")
async def get_services_endpoint():
    return load_services()

@app.post("/api/booking")
async def create_booking(
    name: str = Form(...),
    contact: str = Form(...),
    services: str = Form(...),
    total_price: str = Form(...),
    info: str = Form(None)
):
    """Эндпоинт для мгновенного приема заявок без ожидания ответа внешних API"""
    safe_name = html.escape(name)
    safe_contact = html.escape(contact)
    safe_services = html.escape(services)
    safe_price = html.escape(total_price)
    safe_info = html.escape(info) if info else "—"

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
    
    # ИСПРАВЛЕНИЕ: Отправляем уведомление в ТГ в фоновом потоке
    try:
        await asyncio.to_thread(requests.post, tg_url, json=tg_payload, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

    gs_payload = {
        "name": name,
        "contact": contact,
        "services": services,
        "total_price": total_price,
        "info": info if info else ""
    }
    
    # ИСПРАВЛЕНИЕ: Отправляем запись в Google Таблицу в фоновом потоке
    try:
        await asyncio.to_thread(requests.post, GOOGLE_SCRIPT_URL, data=gs_payload, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки в Google Script: {e}")

    return {"result": "success"}

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

@app.get("/")
async def read_index():
    return FileResponse("index.html")

@app.get("/gallery.html")
async def read_gallery():
    return FileResponse("gallery.html")

@app.get("/style.css")
async def read_style():
    return FileResponse("style.css", media_type="text/css")

@app.get("/app.js")
async def read_app_js():
    return FileResponse("app.js", media_type="application/javascript")

@app.get("/car.png")
async def read_car():
    return FileResponse("car.png")

@app.get("/master.jpg")
async def read_master():
    return FileResponse("master.jpg")

@app.get("/sup.jpg")
async def read_sup():
    return FileResponse("sup.jpg")

if os.path.exists("examples"):
    app.mount("/examples", StaticFiles(directory="examples"), name="examples")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)