import re
import logging
import signal
import sys
import random
import requests
from datetime import datetime, date, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import gspread
from google.oauth2.service_account import Credentials

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "8539880271:AAHlIoQUbX5Mz-HW3jxKzSWlr7iXX5YgYF8"           
ADMIN_CHAT_ID = 1165444045        

RETAILCRM_URL = "https://xtv17101986.retailcrm.ru"
RETAILCRM_API_KEY = "6ipmvADZaxUSe3usdKOauTFZjjGMOlf7"

TWOGIS_REVIEW_URL = "https://2gis.ru/irkutsk/firm/1548641653278292/104.353179%2C52.259892"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= GOOGLE TABLES =================
users_sheet = None
orders_sheet = None
birthdays_sheet = None

try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open("Fruttosmile Bonus CRM")

    print("✅ Успешно подключились к Google Таблице: Fruttosmile Bonus CRM")
    print("📋 Доступные листы:", [ws.title for ws in spreadsheet.worksheets()])

    # Подключаем каждый лист отдельно — чтобы один неисправный не ломал всё
    try:
        users_sheet = spreadsheet.worksheet("users")
        print("✅ Лист 'users' подключён")
    except Exception as e:
        logging.error(f"❌ Лист 'users' не найден: {e}")

    try:
        orders_sheet = spreadsheet.worksheet("orders")
        print("✅ Лист 'orders' подключён")
    except Exception as e:
        logging.error(f"❌ Лист 'orders' не найден: {e}")

    try:
        birthdays_sheet = spreadsheet.worksheet("birthdays")
        print("✅ Лист 'birthdays' подключён")
    except Exception as e:
        logging.error(f"❌ Лист 'birthdays' не найден: {e}")

except Exception as e:
    logging.error(f"❌ Критическая ошибка подключения к Google Sheets: {e}")


# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================
def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    if digits.startswith("7") and len(digits) == 11:
        return "+" + digits
    return "+" + digits if digits else ""


def create_customer_if_not_exists(name: str, phone: str):
    if not RETAILCRM_URL or not RETAILCRM_API_KEY:
        return
    normalized = normalize_phone(phone)
    if not normalized:
        return
    phone_no_plus = normalized.replace("+", "")
    headers = {"X-API-KEY": RETAILCRM_API_KEY}
    try:
        resp = requests.get(f"{RETAILCRM_URL}/api/v5/customers", 
                           headers=headers, 
                           params={"filter[phone]": phone_no_plus}, 
                           timeout=10)
        if resp.status_code == 200 and resp.json().get("customers"):
            return
        payload = {"customer": {"firstName": name or "Клиент", "phones": [{"number": phone_no_plus}]}}
        requests.post(f"{RETAILCRM_URL}/api/v5/customers/create", headers=headers, json=payload, timeout=10)
    except:
        pass


def clear_order_data(context):
    keys_to_keep = ["name", "phone"]
    new_data = {k: v for k, v in context.user_data.items() if k in keys_to_keep}
    context.user_data.clear()
    context.user_data.update(new_data)
    context.user_data.pop("order_created", None)
    context.user_data.pop("custom_steps", None)
    context.user_data.pop("confirm_clicked", None)
    context.user_data.pop("rated", None)


# ================= GRACEFUL SHUTDOWN =================
def shutdown(signum, frame):
    print("Получен сигнал остановки. Завершаем бота...")
    sys.exit(0)


# ================= АВТО ПРОВЕРКА ДНЕЙ РОЖДЕНИЯ =================
async def check_birthdays(context: ContextTypes.DEFAULT_TYPE):
    if not birthdays_sheet or not users_sheet:
        return
    today = datetime.now().date()
    current_year = str(today.year)
    user_rows = users_sheet.get_all_values()
    records = birthdays_sheet.get_all_records()

    for idx, r in enumerate(records):
        try:
            bday_str = r.get("date") or r.get("Date")
            if not bday_str: 
                continue
            bday = datetime.strptime(bday_str, "%d.%m")
            target = bday.replace(year=today.year)
            if target.date() < today:
                target = target.replace(year=today.year + 1)
            diff = (target.date() - today).days
            notified_year = str(r.get("notified") or "")

            if diff in [3, 7] and notified_year != current_year:
                phone = r.get("phone") or r.get("Phone")
                name = r.get("name") or r.get("Name")
                for row in user_rows[1:]:
                    if len(row) > 3 and row[3] == phone:
                        chat_id = row[0]
                        if chat_id:
                            await context.bot.send_message(
                                chat_id=int(chat_id),
                                text=f"🎉 Скоро день рождения {name}!\n\n"
                                     f"Осталось всего {diff} дня 💝\n\n"
                                     f"🎁 Пора выбрать подарок — закажите заранее",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("🍓 Клубника", callback_data="prod_choco")],
                                    [InlineKeyboardButton("🎩 Шляпные", callback_data="prod_hat")],
                                    [InlineKeyboardButton("❤️ Сердце", callback_data="prod_heart")]
                                ])
                            )
                            birthdays_sheet.update_cell(idx + 2, 4, current_year)
                            break
        except Exception as e:
            logging.error(f"Ошибка при проверке ДР: {e}")


# ================= КАТАЛОГ ТОВАРОВ =================
PRODUCTS = {
    "choco": {
        "name": "🍓 Клубника в шоколаде",
        "steps": [
            {"title": "Выберите коробку:", "options": [
                {"id": "square", "label": "⬜ Квадратная коробка"},
                {"id": "round",  "label": "⭕ Круглая коробка"}
            ]}
        ]
    },
    "hat": {
        "name": "🎩 Шляпные коробки",
        "photo": "http://fruttosmile.su/wp-content/uploads/2026/02/image-23-02-26-11-11.jpeg",
        "steps": [
            {"title": "Выберите размер:", "options": [
                {"id": "15", "label": "15–16 ягод — 3990₽", "price": 3990},
                {"id": "20", "label": "20–23 ягоды — 4990₽", "price": 4990},
                {"id": "25", "label": "25–27 ягод — 5990₽", "price": 5990},
                {"id": "30", "label": "30–35 ягоды — 6990₽", "price": 6990},
            ]},
            {"title": "Выберите дизайн:", "options": [
                {"id": "1", "label": "Дизайн №1 (с ажурами)"},
                {"id": "2", "label": "Дизайн №2 (с посыпками и свежей ягодой)"},
                {"id": "3", "label": "Дизайн №3 (с ажурами и голубикой)"},
                {"id": "4", "label": "Дизайн №4 (с голубикой)"},
            ]}
        ]
    },
    "heart": {
        "name": "❤️ Коробочки «Сердце»",
        "photo": "http://fruttosmile.su/wp-content/uploads/2026/02/image-23-02-26-11-11-1.jpeg",
        "steps": [
            {"title": "Выберите размер:", "options": [
                {"id": "10", "label": "9-10 ягод — 3090₽", "price": 3190},
                {"id": "16", "label": "15-17 ягод — 4490₽", "price": 4490},
                {"id": "20", "label": "18-20 ягод — 4990₽", "price": 4990},
                {"id": "25", "label": "23-25 ягод — 5990₽", "price": 5990},
                {"id": "35", "label": "33-35 ягод — 7490₽", "price": 7490},
            ]},
            {"title": "Выберите дизайн:", "options": [
                {"id": "1", "label": "Дизайн №1 (с полосками и сердечками)"},
                {"id": "2", "label": "Дизайн №2 (с полосками)"},
                {"id": "3", "label": "Дизайн №3 (с посыпками/полосками и ягодами)"},
                {"id": "4", "label": "Дизайн №4 (с ажурами и декором)"},
            ]}
        ]
    }
}


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("phone"):
        kb = ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Поделиться номером", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await update.message.reply_text(
            "📱 Для начала работы отправьте номер телефона",
            reply_markup=kb
        )
        return

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🍓 Клубника", callback_data="prod_choco")],
        [InlineKeyboardButton("🎩 Шляпные", callback_data="prod_hat")],
        [InlineKeyboardButton("❤️ Сердце", callback_data="prod_heart")],
        [InlineKeyboardButton("⚙️ Админка", callback_data="admin_menu")]
    ])

    await update.message.reply_text(
        "Добро пожаловать в Fruttosmile! 🍓\n\nВыберите категорию:",
        reply_markup=kb
    )


# ================= КОНТАКТ =================
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone = normalize_phone(contact.phone_number)

    context.user_data["phone"] = phone
    context.user_data["name"] = contact.first_name or "Клиент"

    if users_sheet:
        try:
            cell = users_sheet.find(str(update.effective_user.id), in_column=1)
            if cell:
                users_sheet.update_cell(cell.row, 4, phone)
                print(f"Обновлён телефон для пользователя {update.effective_user.id}")
            else:
                users_sheet.append_row([
                    update.effective_user.id, 
                    contact.first_name or "", 
                    "", 
                    phone, 
                    "", "", "", "", ""
                ])
                print(f"Добавлен новый пользователь {update.effective_user.id}")
        except Exception as e:
            logging.error(f"Ошибка сохранения пользователя: {e}")

    await update.message.reply_text("Спасибо! Вы зарегистрированы ✅")


# ================= АДМИНКА =================
async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "admin_menu":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Тест рассылки", callback_data="admin_test")],
            [InlineKeyboardButton("📢 Сделать рассылку", callback_data="admin_send")],
            [InlineKeyboardButton("📅 Запросить ДР", callback_data="admin_bday")]
        ])
        await query.message.reply_text("Админ-панель:", reply_markup=kb)

    elif query.data == "admin_test":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить", callback_data="bday_add")],
            [InlineKeyboardButton("❌ Не хочу", callback_data="bday_skip")]
        ])
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text="🧪 ТЕСТ ДР\n\n🎉 Добавьте дни рождения близких\n\nМы напомним вам заранее, чтобы вы успели заказать подарок 🎁",
            reply_markup=kb
        )
        await query.message.reply_text("✅ Тест отправлен администратору")

    elif query.data == "admin_send":
        if not users_sheet:
            await query.message.reply_text("❌ Таблица пользователей не подключена")
            return
        users = users_sheet.get_all_values()
        count = 0
        for row in users[1:]:
            try:
                chat_id = int(row[0])
                if chat_id:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="🎁 У нас для вас есть кое-что вкусное!\n\n🍓 Закажите клубнику в шоколаде прямо сейчас 💝"
                    )
                    count += 1
            except Exception as e:
                print(f"Ошибка отправки рассылки: {e}")
                continue
        await query.message.reply_text(f"✅ Рассылка отправлена: {count} чел.")

    elif query.data == "admin_bday":
        if not users_sheet:
            await query.message.reply_text("❌ Таблица пользователей не подключена")
            return
        users = users_sheet.get_all_values()
        count = 0
        for row in users[1:]:
            try:
                chat_id = int(row[0])
                if len(row) > 8 and row[8] in ["added", "declined"]:
                    continue
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Добавить", callback_data="bday_add")],
                    [InlineKeyboardButton("❌ Не хочу", callback_data="bday_skip")]
                ])
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="🎉 Добавьте дни рождения близких\n\nМы напомним вам заранее, чтобы вы успели заказать подарок 🎁",
                    reply_markup=kb
                )
                count += 1
            except Exception as e:
                print(f"Ошибка отправки запроса ДР: {e}")
                continue
        await query.message.reply_text(f"✅ Запрос ДР отправлен: {count} чел.")


# ================= SHOW MAIN MENU =================
async def show_main_menu(update, context):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🍓 Клубника", callback_data="prod_choco")],
        [InlineKeyboardButton("🎩 Шляпные", callback_data="prod_hat")],
        [InlineKeyboardButton("❤️ Сердце", callback_data="prod_heart")],
        [InlineKeyboardButton("⚙️ Админка", callback_data="admin_menu")]
    ])
    text = "Выберите категорию:"
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=kb)
    else:
        await update.message.reply_text(text, reply_markup=kb)


# ================= ЗАКАЗЫ =================
async def product_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not context.user_data.get("phone"):
        kb = ReplyKeyboardMarkup([[KeyboardButton("📱 Поделиться номером для регистрации", request_contact=True)]],
                                 resize_keyboard=True, one_time_keyboard=True)
        await query.message.reply_text("📱 Для оформления заказа сначала отправьте номер телефона.", reply_markup=kb)
        return

    product_key = query.data.replace("prod_", "")
    product = PRODUCTS.get(product_key)
    if not product:
        await query.message.reply_text("Товар не найден.")
        return

    clear_order_data(context)
    context.user_data.update({
        "product_key": product_key,
        "step_index": 0,
        "product": product["name"],
        "product_photo": product.get("photo") if product_key != "choco" else None
    })
    await show_step(query, context, product)


async def show_step(query, context, product):
    step_index = context.user_data["step_index"]
    custom_steps = context.user_data.get("custom_steps")
    step = custom_steps[step_index] if custom_steps else product["steps"][step_index]

    buttons = [[InlineKeyboardButton(opt["label"], callback_data=f"opt_{opt['id']}")] for opt in step["options"]]

    caption = product['name']
    if context.user_data.get("box_type"):
        caption += f"\nКоробка: {context.user_data['box_type']}"
    if context.user_data.get("size"):
        caption += f"\nРазмер: {context.user_data['size']}"
    caption += f"\n\n{step['title']}"

    if custom_steps:
        if step_index == 0:
            buttons.append([InlineKeyboardButton("⬅️ Назад к коробкам", callback_data="back_to_box")])
        elif step_index == 1:
            buttons.append([InlineKeyboardButton("⬅️ Назад к размеру", callback_data="step_back")])
    else:
        if step_index > 0:
            buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="step_back")])
        else:
            buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])

    try:
        await query.message.delete()
    except:
        pass

    photo = context.user_data.get("product_photo")
    if photo:
        await query.message.chat.send_photo(photo=photo, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await query.message.chat.send_message(caption, reply_markup=InlineKeyboardMarkup(buttons))


async def option_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not context.user_data.get("product_key"):
        await show_main_menu(update, context)
        return

    product_key = context.user_data.get("product_key")
    product = PRODUCTS.get(product_key)
    step_index = context.user_data.get("step_index", 0)
    selected_id = query.data.replace("opt_", "")

    if product_key == "choco" and step_index == 0:
        if selected_id in ("square", "round"):
            if selected_id == "square":
                context.user_data["product_photo"] = "http://fruttosmile.su/wp-content/uploads/2026/02/image-27-02-26-08-49.jpeg"
                context.user_data["box_type"] = "Квадратная"
                custom_steps = [
                    {"title": "Выберите размер:", "options": [
                        {"id": "4", "label": "4 ягод — 990₽", "price": 990},
                        {"id": "9", "label": "9 ягод — 2090₽", "price": 2090},
                        {"id": "12", "label": "12 ягод — 2790₽", "price": 2790},
                        {"id": "15", "label": "15 ягод — 3390₽", "price": 3390},
                        {"id": "16", "label": "16 ягод — 3590₽", "price": 3590},
                        {"id": "20", "label": "20 ягод — 4390₽", "price": 4390}
                    ]},
                    {"title": "Выберите дизайн:", "options": [
                        {"id": "1", "label": "Дизайн №1"},
                        {"id": "2", "label": "Дизайн №2"},
                        {"id": "3", "label": "Дизайн №3"},
                        {"id": "4", "label": "Дизайн №4"}
                    ]}
                ]
            else:
                context.user_data["product_photo"] = "http://fruttosmile.su/wp-content/uploads/2026/02/image-27-02-26-08-49-1.jpeg"
                context.user_data["box_type"] = "Круглая"
                custom_steps = [
                    {"title": "Выберите размер:", "options": [
                        {"id": "14", "label": "12–14 ягод — 3690₽", "price": 3690},
                        {"id": "16", "label": "15–16 ягод — 4190₽", "price": 4190},
                        {"id": "20", "label": "18–20 ягод — 4790₽", "price": 4790},
                        {"id": "berry", "label": "Бокс из свежих ягод — 4390₽", "price": 4390}
                    ]},
                    {"title": "Выберите дизайн:", "options": [
                        {"id": "1", "label": "Дизайн 1"},
                        {"id": "2", "label": "Дизайн 2"},
                        {"id": "3", "label": "Дизайн 3"},
                        {"id": "4", "label": "Бокс «Ягодная поляна»"}
                    ]}
                ]

            context.user_data["custom_steps"] = custom_steps
            context.user_data["step_index"] = 0
            context.user_data["product"] = f"{product['name']} ({context.user_data['box_type']})"
            await show_step(query, context, product)
            return

    custom_steps = context.user_data.get("custom_steps")
    step = custom_steps[step_index] if custom_steps else product["steps"][step_index]

    try:
        selected_option = next(o for o in step["options"] if o["id"] == selected_id)
    except StopIteration:
        return

    if "price" in selected_option:
        context.user_data["price"] = selected_option["price"]

    if step_index == 0:
        context.user_data["size"] = selected_option["label"]
    elif step_index == 1:
        context.user_data["decor"] = selected_option["label"]

    context.user_data["step_index"] += 1
    steps = context.user_data.get("custom_steps") or product["steps"]

    if context.user_data["step_index"] < len(steps):
        await show_step(query, context, product)
    else:
        context.user_data["qty"] = 1
        context.user_data["state"] = "WAIT_METHOD"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚚 Доставка", callback_data="method_delivery")],
            [InlineKeyboardButton("🏠 Самовывоз", callback_data="method_pickup")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ])
        await query.message.reply_text("Выберите способ получения:", reply_markup=kb)


async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "main_menu":
        clear_order_data(context)
        await show_main_menu(update, context)

    elif query.data == "step_back":
        current = context.user_data.get("step_index", 0)
        if current > 0:
            context.user_data["step_index"] = current - 1
            product = PRODUCTS.get(context.user_data.get("product_key"))
            if product:
                await show_step(query, context, product)
        else:
            await show_main_menu(update, context)

    elif query.data == "back_to_box":
        context.user_data["step_index"] = 0
        context.user_data.pop("custom_steps", None)
        context.user_data.pop("box_type", None)
        product = PRODUCTS["choco"]
        await show_step(query, context, product)

    elif query.data == "back_to_method":
        context.user_data['state'] = 'WAIT_METHOD'
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚚 Доставка", callback_data="method_delivery")],
            [InlineKeyboardButton("🏠 Самовывоз", callback_data="method_pickup")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ])
        await query.message.reply_text("Выберите способ получения:", reply_markup=kb)
        
    elif query.data == "back_to_district":
        context.user_data['state'] = 'WAIT_DISTRICT'
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Октябрьский — 350₽", callback_data="district_350")],
            [InlineKeyboardButton("Кировский — 400₽", callback_data="district_400")],
            [InlineKeyboardButton("Свердловский — 450₽", callback_data="district_450")],
            [InlineKeyboardButton("Ленинский — 550₽", callback_data="district_550")],
            [InlineKeyboardButton("Индивидуальный тариф", callback_data="district_custom")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ])
        await query.message.reply_text("Выберите район доставки:", reply_markup=kb)


# ================= ДОСТАВКА И ОФОРМЛЕНИЕ =================
async def delivery_method_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "method_delivery":
        context.user_data['method'] = "Доставка"
        context.user_data['state'] = 'WAIT_DISTRICT'
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Октябрьский — 350₽", callback_data="district_350")],
            [InlineKeyboardButton("Кировский — 400₽", callback_data="district_400")],
            [InlineKeyboardButton("Свердловский — 450₽", callback_data="district_450")],
            [InlineKeyboardButton("Ленинский — 550₽", callback_data="district_550")],
            [InlineKeyboardButton("Индивидуальный тариф", callback_data="district_custom")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ])
        await query.message.chat.send_message("Выберите район доставки:", reply_markup=kb)
    elif query.data == "method_pickup":
        context.user_data['method'] = "Самовывоз"
        context.user_data['delivery_fee'] = 0
        context.user_data['address'] = "Самовывоз"
        context.user_data['state'] = 'WAIT_DATE'
        await query.message.chat.send_message("📅 Укажите дату самовывоза в формате ДД.ММ.ГГГГ")


async def district_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "district_custom":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📞 Связь с менеджером", url="https://t.me/fruttosmile")],
                                   [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_method")]])
        await query.message.chat.send_message("Менеджер рассчитает стоимость доставки индивидуально:", reply_markup=kb)
        return
    price = int(query.data.split("_")[1])
    context.user_data['delivery_fee'] = price
    total = context.user_data.get('price', 0) * context.user_data.get('qty', 1) + price
    text = f"Стоимость доставки: **{price} ₽**\n\nИтого: **{total} ₽**"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, продолжить", callback_data="confirm_district")],
        [InlineKeyboardButton("⬅️ Выбрать другой район", callback_data="back_to_district")]
    ])
    await query.message.chat.send_message(text, reply_markup=kb, parse_mode="Markdown")


async def confirm_district_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['state'] = 'WAIT_ADDRESS'
    await query.message.chat.send_message("📍 Введите полный адрес доставки:")


async def time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    time_map = {"time_9_13": "9:00–13:00", "time_13_17": "13:00–17:00", "time_17_21": "17:00–21:00"}
    context.user_data['delivery_time'] = time_map.get(query.data)
    context.user_data['state'] = 'WAIT_COMMENT'
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Без комментария", callback_data="no_comment")]])
    await query.message.chat.send_message("💬 Напишите пожелания к заказу:", reply_markup=kb)


async def no_comment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['comment'] = "—"
    context.user_data['state'] = 'WAIT_CONFIRM'
    await show_order_preview(update, context)


async def show_order_preview(update, context):
    d = context.user_data
    total = d.get('price', 0) * d.get('qty', 1) + d.get('delivery_fee', 0)
    text = f"📋 **Проверьте заказ:**\n\nТовар: {d.get('product')}\nКол-во: {d.get('qty', 1)}\nИтого: {total} ₽"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Подтвердить заказ", callback_data="confirm_order")],
        [InlineKeyboardButton("🔄 Изменить", callback_data="restart_order")]
    ])
    await update.effective_message.reply_text(text, reply_markup=kb, parse_mode="Markdown")


async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if context.user_data.get("confirm_clicked"):
        await query.answer("⏳ Уже обрабатывается...")
        return

    context.user_data["confirm_clicked"] = True

    if query.data == "confirm_order":
        if context.user_data.get("state") != "WAIT_CONFIRM":
            await query.message.reply_text("❗ Сначала завершите оформление заказа.")
            return
        if not context.user_data.get("date") or not context.user_data.get("delivery_time"):
            await query.message.reply_text("❗ Укажите дату и время.")
            return

        await finish_order(update, context, status="Создан")
        await show_payment_options(update, context)

    elif query.data == "restart_order":
        clear_order_data(context)
        await query.message.reply_text("🔄 Заказ сброшен. Начнём заново.")
        await show_main_menu(update, context)


async def show_payment_options(update, context):
    method = context.user_data.get("method")
    if method == "Самовывоз":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Оплатить по QR", callback_data="pay_online")],
            [InlineKeyboardButton("🏪 Оплатить при получении", callback_data="pay_pickup")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_method")]
        ])
    else:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Оплатить по QR", callback_data="pay_online")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_method")]
        ])
    await update.effective_message.reply_text("💳 Выберите способ оплаты:", reply_markup=kb)


async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "pay_online":
        total = context.user_data.get('price', 0) * context.user_data.get('qty', 1) + context.user_data.get('delivery_fee', 0)
        await query.message.reply_text(
            f"✅ Заказ оформлен! Итого: {total} ₽\nОплатите по QR и пришлите скриншот.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
            ])
        )
        await finish_order(update, context, status="Ожидает оплаты")


async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE, status="Создан"):
    d = context.user_data

    if not d.get("name") or not d.get("phone"):
        await update.effective_message.reply_text("❌ Ошибка: не найдено имя или телефон. Нажмите /start")
        return

    if d.get("order_created"):
        return
    d["order_created"] = True

    order_id = f"FS-{random.randint(10000, 99999)}"
    total = d.get('price', 0) * d.get('qty', 1) + d.get('delivery_fee', 0)

    if orders_sheet:
        try:
            orders_sheet.append_row([
                order_id, d.get("name"), d.get("phone"), d.get("product"),
                total, d.get("date"), d.get("delivery_time"), d.get("method"),
                d.get("address", "-"), datetime.now().strftime("%d.%m.%Y %H:%M")
            ])
        except Exception as e:
            logging.error(f"Ошибка записи заказа: {e}")

    summary = f"🔔 НОВЫЙ ЗАКАЗ!\nID: {order_id}\nТовар: {d.get('product')}\nСумма: {total} ₽\nКлиент: {d.get('name')}\nТел: {d.get('phone')}\nАдрес: {d.get('address', '-')}"
    try:
        await context.bot.send_message(ADMIN_CHAT_ID, summary)
    except Exception as e:
        logging.error(f"Ошибка отправки админу: {e}")

    await update.effective_message.reply_text(f"✅ Заказ {order_id} оформлен! Спасибо!")

    context.application.job_queue.run_once(
        send_review_request,
        when=10,
        data={
            "chat_id": update.effective_user.id,
            "name": d.get("name"),
            "phone": d.get("phone"),
            "order_id": order_id
        },
        name=f"review_{order_id}"
    )

    clear_order_data(context)


# ================= РЕЙТИНГ =================
async def send_review_request(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    data = job.data
    chat_id = data["chat_id"]

    context.application.bot_data[chat_id] = {
        "name": data.get("name"),
        "phone": data.get("phone"),
        "order_id": data.get("order_id")
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐1", callback_data="rate_1"),
         InlineKeyboardButton("⭐2", callback_data="rate_2"),
         InlineKeyboardButton("⭐3", callback_data="rate_3"),
         InlineKeyboardButton("⭐4", callback_data="rate_4"),
         InlineKeyboardButton("⭐5", callback_data="rate_5")]
    ])

    await context.bot.send_message(
        chat_id=chat_id,
        text="✨ Оцените ваш заказ от 1 до 5:",
        reply_markup=keyboard
    )


async def rating_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if context.user_data.get("rated"):
        await query.answer("Вы уже оценили заказ ❤️")
        return

    context.user_data["rated"] = True
    await query.edit_message_reply_markup(reply_markup=None)

    rating = int(query.data.replace("rate_", ""))

    user_data = context.application.bot_data.get(update.effective_user.id, {})
    name = user_data.get("name", "Неизвестно")
    phone = user_data.get("phone", "Нет телефона")
    order_id = user_data.get("order_id", "—")

    if rating == 5:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ Оставить отзыв в 2ГИС", url=TWOGIS_REVIEW_URL)]
        ])

        await query.message.reply_text(
            "💖 Спасибо большое за высокую оценку!\n\n"
            "Нам будет очень приятно, если вы оставите отзыв ❤️",
            reply_markup=kb
        )

        await context.bot.send_message(
            ADMIN_CHAT_ID,
            f"🌟 Отличный отзыв!\n\n"
            f"Заказ: {order_id}\n"
            f"Оценка: {rating}\n"
            f"Имя: {name}\n"
            f"Телефон: {phone}\n"
            f"ID: {update.effective_user.id}"
        )

        context.application.bot_data.pop(update.effective_user.id, None)

    else:
        context.user_data["state"] = "WAIT_FEEDBACK_TEXT"
        context.user_data["last_rating"] = rating
        await query.message.reply_text(
            "Нам очень жаль, что что-то не понравилось 🙏\n"
            "Пожалуйста, опишите проблему."
        )


# ================= TEXT HANDLER =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    state = context.user_data.get('state')
    text = update.message.text.strip()

    if state == "WAIT_FEEDBACK_TEXT":
        feedback = text
        rating = context.user_data.get("last_rating")
        user_data = context.application.bot_data.get(update.effective_user.id, {})
        name = user_data.get("name", "Неизвестно")
        phone = user_data.get("phone", "Нет телефона")
        order_id = user_data.get("order_id", "—")

        await context.bot.send_message(
            ADMIN_CHAT_ID,
            f"⚠️ Негативный отзыв\n\n"
            f"Заказ: {order_id}\n"
            f"Оценка: {rating}\n"
            f"Имя: {name}\n"
            f"Телефон: {phone}\n"
            f"ID: {update.effective_user.id}\n\n"
            f"Комментарий:\n{feedback}"
        )

        await update.message.reply_text("Спасибо за обратную связь 🙏\nНаш менеджер свяжется с вами.")

        context.user_data.pop("state", None)
        context.user_data.pop("last_rating", None)
        context.application.bot_data.pop(update.effective_user.id, None)
        return

    if state == 'WAIT_ADDRESS':
        context.user_data['address'] = text
        context.user_data['state'] = 'WAIT_DATE'
        await update.message.reply_text("📅 Введите дату в формате ДД.ММ.ГГГГ")

    elif state == 'WAIT_DATE':
        try:
            dt = datetime.strptime(text, "%d.%m.%Y")
            if dt.date() < date.today():
                await update.message.reply_text("Дата не может быть в прошлом.")
                return
            context.user_data['date'] = text
            context.user_data['state'] = 'WAIT_TIME'
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("9:00–13:00", callback_data="time_9_13")],
                [InlineKeyboardButton("13:00–17:00", callback_data="time_13_17")],
                [InlineKeyboardButton("17:00–21:00", callback_data="time_17_21")]
            ])
            await update.message.reply_text("⏰ Выберите время:", reply_markup=kb)
        except:
            await update.message.reply_text("Введите дату в формате ДД.ММ.ГГГГ")

    elif state == 'WAIT_COMMENT':
        context.user_data['comment'] = text
        context.user_data['state'] = 'WAIT_CONFIRM'
        await show_order_preview(update, context)

    elif state == "WAIT_BDAY_NAME":
        context.user_data["bday_name"] = text
        context.user_data["state"] = "WAIT_BDAY_DATE"
        await update.message.reply_text("Введите дату в формате ДД.ММ")
    elif state == "WAIT_BDAY_DATE":
        if not birthdays_sheet:
            await update.message.reply_text("⏳ Функция дней рождения временно недоступна.")
            context.user_data.pop("state", None)
            return
        try:
            datetime.strptime(text, "%d.%m")
        except:
            await update.message.reply_text("❌ Неверный формат. Введите ДД.ММ (например 05.09)")
            return

        name = context.user_data.get("bday_name")
        phone = context.user_data.get("phone")
        
        # если нет телефона в памяти — берём из users
        if not phone and users_sheet:
            try:
                cell = users_sheet.find(str(update.effective_user.id), in_column=1)
                if cell:
                    phone = users_sheet.cell(cell.row, 4).value
            except:
                pass
        
        # сохраняем обратно в память (ВАЖНО)
        context.user_data["phone"] = phone

birthdays_sheet.append_row([phone, name, text, ""])
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить ещё", callback_data="bday_add")],
            [InlineKeyboardButton("📋 Мои даты", callback_data="my_birthdays")]
        ])
        await update.message.reply_text("✅ Дата сохранена!", reply_markup=kb)
        context.user_data.pop("state", None)


# ================= ДНИ РОЖДЕНИЯ =================
async def birthday_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "bday_add":
        context.user_data["state"] = "WAIT_BDAY_NAME"
        await query.message.reply_text("Введите имя (например: Мама)")
    elif query.data == "bday_skip":
        if users_sheet:
            try:
                cell = users_sheet.find(str(update.effective_user.id), in_column=1)
                if cell:
                    users_sheet.update_cell(cell.row, 9, "declined")
            except:
                pass
        await query.message.reply_text("Ок, больше не будем предлагать 👍")


async def my_bdays_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not birthdays_sheet:
        await query.message.reply_text("⏳ Функция дней рождения временно недоступна.")
        return
    phone = context.user_data.get("phone")
    records = birthdays_sheet.get_all_records()
    user_dates = [r for r in records if r.get("phone") == phone]
    if not user_dates:
        await query.message.reply_text("У вас пока нет дат")
        return
    text = "📅 Ваши даты:\n\n"
    buttons = []
    for i, r in enumerate(user_dates):
        text += f"{i+1}. {r.get('name')} — {r.get('date')}\n"
        buttons.append([InlineKeyboardButton(f"❌ Удалить {r.get('name')}", callback_data=f"delbday_{i}")])
    buttons.append([InlineKeyboardButton("➕ Добавить", callback_data="bday_add")])
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


async def delete_bday_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not birthdays_sheet:
        return
    index = int(query.data.split("_")[1])
    phone = context.user_data.get("phone")
    records = birthdays_sheet.get_all_records()
    user_rows = [(i+2, r) for i, r in enumerate(records) if r.get("phone") == phone]
    if index < len(user_rows):
        birthdays_sheet.delete_rows(user_rows[index][0])
    await query.message.reply_text("❌ Дата удалена")


# ================= MAIN =================
def main():
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    if app.job_queue is None:
        from telegram.ext import JobQueue
        job_queue = JobQueue()
        job_queue.set_application(app)
        app.job_queue = job_queue
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    app.add_handler(CallbackQueryHandler(product_entry, pattern="^prod_"))
    app.add_handler(CallbackQueryHandler(option_handler, pattern="^opt_"))
    app.add_handler(CallbackQueryHandler(delivery_method_handler, pattern="^method_"))
    app.add_handler(CallbackQueryHandler(district_handler, pattern="^district_"))
    app.add_handler(CallbackQueryHandler(confirm_district_handler, pattern="^confirm_district$"))
    app.add_handler(CallbackQueryHandler(time_handler, pattern="^time_"))
    app.add_handler(CallbackQueryHandler(no_comment_handler, pattern="^no_comment$"))
    app.add_handler(CallbackQueryHandler(payment_handler, pattern="^pay_"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="^(back_.*|main_menu|step_back|back_to_box|back_to_method)$"))
    app.add_handler(CallbackQueryHandler(confirm_handler, pattern="^(confirm_order|restart_order)$"))
    app.add_handler(CallbackQueryHandler(rating_handler, pattern="^rate_"))
    app.add_handler(CallbackQueryHandler(admin_handler, pattern="^admin_"))

    app.add_handler(CallbackQueryHandler(birthday_handler, pattern="^bday_"))
    app.add_handler(CallbackQueryHandler(my_bdays_handler, pattern="^my_birthdays$"))
    app.add_handler(CallbackQueryHandler(delete_bday_handler, pattern="^delbday_"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # Автопроверка дней рождения
    if birthdays_sheet and users_sheet:
        app.job_queue.run_repeating(check_birthdays, interval=86400, first=10)
        print("✅ Автопроверка дней рождения запущена")
    else:
        print("⚠️ Автопроверка ДР не запущена (отсутствует birthdays_sheet или users_sheet)")

    print("🤖 Бот успешно запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
