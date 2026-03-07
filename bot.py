import re
import logging
import os
import signal
import sys
import json
import random
import requests
from datetime import datetime, date, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
BOT_TOKEN = "8539880271:AAHlIoQUbX5Mz-HW3jxKzSWlr7iXX5YgYF8"           # ← обязательно замени
ADMIN_CHAT_ID = 1165444045        # ← ID админа

RETAILCRM_URL = "https://xtv17101986.retailcrm.ru"  # ← замени
RETAILCRM_API_KEY = "6ipmvADZaxUSe3usdKOauTFZjjGMOlf7"                      # ← вставь реальный ключ

TWOGIS_REVIEW_URL = "https://2gis.ru/irkutsk/firm/1548641653278292/104.353179%2C52.259892"  # ← замени на реальную

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= GOOGLE TABLES =================
users_sheet = None
orders_sheet = None
bonus_logs_sheet = None

try:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=scope
    )

    gc = gspread.authorize(creds)
    spreadsheet = gc.open("Fruttosmile Bonus CRM")

    users_sheet = spreadsheet.worksheet("users")
    orders_sheet = spreadsheet.worksheet("orders")
    bonus_logs_sheet = spreadsheet.worksheet("logs")

    print("Google Sheets подключён успешно")
except Exception as e:
    logging.error(f"Ошибка Google Sheets: {e}")

# ================= УДАЛЕНИЕ СООБЩЕНИЙ =================
async def safe_delete(message):
    try:
        await message.delete()
    except:
        pass

# ================= НОРМАЛИЗАЦИЯ ТЕЛЕФОНА =================
def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    if digits.startswith("7") and len(digits) == 11:
        return "+" + digits
    return "+" + digits

# ================= СОЗДАНИЕ КЛИЕНТА В RETAILCRM =================
def create_customer_if_not_exists(name: str, phone: str):
    if not RETAILCRM_URL or not RETAILCRM_API_KEY:
        logging.warning("RetailCRM URL или API-ключ не указаны")
        return

    normalized = normalize_phone(phone)
    phone_no_plus = normalized.replace("+", "")

    headers = {"X-API-KEY": RETAILCRM_API_KEY}

    try:
        response = requests.get(
            f"{RETAILCRM_URL}/api/v5/customers",
            headers=headers,
            params={"filter[phone]": phone_no_plus},
            timeout=10
        )

        if response.status_code == 200 and response.json().get("customers"):
            logging.info(f"Клиент {phone_no_plus} уже существует")
            return

        payload = {
            "customer": {
                "firstName": name or "Клиент",
                "phones": [{"number": phone_no_plus}]
            }
        }

        create_response = requests.post(
            f"{RETAILCRM_URL}/api/v5/customers/create",
            headers=headers,
            json=payload,
            timeout=10
        )

        if create_response.status_code in (200, 201):
            logging.info(f"Клиент {name} ({phone_no_plus}) создан")
        else:
            logging.error(f"Ошибка создания: {create_response.text}")

    except Exception as e:
        logging.error(f"Ошибка связи с RetailCRM: {e}")

# ================= КАТАЛОГ ТОВАРОВ =================
PRODUCTS = {
    "choco": {
        "name": "🍓 Клубника в шоколаде",
        "steps": [
            {
                "title": "Выберите коробку:",
                "options": [
                    {"id": "square", "label": "⬜ Квадратная коробка"},
                    {"id": "round",  "label": "⭕ Круглая коробка"}
                ]
            }
        ]
    },
    "hat": {
        "name": "🎩 Шляпные коробки",
        "photo": "http://fruttosmile.su/wp-content/uploads/2026/02/image-23-02-26-11-11.jpeg",
        "steps": [
            {
                "title": "Выберите размер:",
                "options": [
                    {"id": "15", "label": "15–16 ягод — 3990₽", "price": 3990},
                    {"id": "20", "label": "20–23 ягоды — 4990₽", "price": 4990},
                    {"id": "25", "label": "25–27 ягод — 5990₽", "price": 5990},
                    {"id": "30", "label": "30–35 ягоды — 6990₽", "price": 6990},
                ]
            },
            {
                "title": "Выберите дизайн:",
                "options": [
                    {"id": "1", "label": "Дизайн №1 (с ажурами)"},
                    {"id": "2", "label": "Дизайн №2 (с посыпками и свежей ягодой)"},
                    {"id": "3", "label": "Дизайн №3 (с ажурами и голубикой)"},
                    {"id": "4", "label": "Дизайн №4 (с голубикой)"},
                ]
            }
        ]
    },
    "heart": {
        "name": "❤️ Коробочки «Сердце»",
        "photo": "http://fruttosmile.su/wp-content/uploads/2026/02/image-23-02-26-11-11-1.jpeg",
        "steps": [
            {
                "title": "Выберите размер:",
                "options": [
                    {"id": "10", "label": "9-10 (мелкая до 12шт)  ягод — 3090₽", "price": 3190},
                    {"id": "16", "label": "15-17 ягод — 4490₽", "price": 4490},
                    {"id": "20", "label": "18-20 ягод — 4990₽", "price": 4990},
                    {"id": "25", "label": "23-25 ягод — 5990₽", "price": 5990},
                    {"id": "35", "label": "33-35 ягод — 7490₽", "price": 7490},
                ]
            },
            {
                "title": "Выберите дизайн:",
                "options": [
                    {"id": "1", "label": "Дизайн №1 (с полосками и сердечками)"},
                    {"id": "2", "label": "Дизайн №2 (с полосками)"},
                    {"id": "3", "label": "Дизайн №3 (с посыпками/полосками и ягодами)"},
                    {"id": "4", "label": "Дизайн №4 (с ажурами и декором)"},
                ]
            }
        ]
    }
}

# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================

def clear_order_data(context):
    keys_to_keep = ["name", "phone"]
    new_data = {k: v for k, v in context.user_data.items() if k in keys_to_keep}
    context.user_data.clear()
    context.user_data.update(new_data)
    context.user_data.pop("order_created", None)
    context.user_data.pop("custom_steps", None)
    context.user_data.pop("confirm_clicked", None)   # сброс защиты от двойного клика

# ================= GRACEFUL SHUTDOWN =================
def shutdown(signum, frame):
    print("Получен сигнал остановки. Завершаем бота...")
    sys.exit(0)

# ================= ОБРАБОТЧИКИ =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if users_sheet:
        try:
            cell = users_sheet.find(str(user_id), in_column=1)
            if cell:
                row = cell.row
                name_cell = users_sheet.cell(row, 3)
                phone_cell = users_sheet.cell(row, 4)
                context.user_data["name"]  = name_cell.value.strip() if name_cell.value else None
                context.user_data["phone"] = phone_cell.value.strip() if phone_cell.value else None
        except Exception as e:
            logging.error(f"Ошибка поиска пользователя в таблице: {e}")

    if context.user_data.get('phone'):
        await show_main_menu(update, context)
        return

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Поделиться номером для регистрации", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await update.message.reply_text(
        "Добро пожаловать в Fruttosmile! 💝\n\n"
        "Чтобы сделать заказ и участвовать в программе лояльности, "
        "поделитесь своим номером телефона (это займёт 1 секунду):",
        reply_markup=keyboard
    )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if not contact:
        await update.message.reply_text("Не удалось получить контакт. Попробуйте ещё раз.")
        return

    name = contact.first_name or contact.last_name or "Клиент"
    phone = normalize_phone(contact.phone_number)

    context.user_data['name'] = name
    context.user_data['phone'] = phone

    if users_sheet:
        try:
            users_sheet.append_row([
                update.effective_user.id,
                update.effective_user.username or "",
                name,
                phone,
                0,
                datetime.now().strftime("%d.%m.%Y %H:%M"),
                "",
                "false"
            ])
        except Exception as e:
            logging.error(f"Ошибка записи пользователя: {e}")

    await update.message.reply_text(
        f"Спасибо, {name}! Вы зарегистрированы ✅\n"
        "Теперь можете выбирать товары.",
        reply_markup=ReplyKeyboardRemove()
    )

    create_customer_if_not_exists(name, phone)
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🍓 Клубника в шоколаде", callback_data="prod_choco")],
        [InlineKeyboardButton("🎩 Шляпные коробки", callback_data="prod_hat")],
        [InlineKeyboardButton("❤️ Коробочки «Сердце»", callback_data="prod_heart")],
        [InlineKeyboardButton("📞 Связь с магазином", url="https://t.me/fruttosmile")]
    ])

    text = "Выберите товар:"

    if update.callback_query:
        try: await update.callback_query.message.delete()
        except: pass
        await update.callback_query.message.chat.send_message(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

async def product_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not context.user_data.get("phone"):
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Поделиться номером для регистрации", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await query.message.reply_text(
            "📱 Для оформления заказа сначала отправьте номер телефона.",
            reply_markup=keyboard
        )
        return

    saved_name = context.user_data.get("name")
    saved_phone = context.user_data.get("phone")

    product_key = query.data.replace("prod_", "")
    product = PRODUCTS.get(product_key)

    if not product:
        await query.message.reply_text("Товар не найден.")
        return

    clear_order_data(context)

    if saved_name:
        context.user_data["name"] = saved_name
    if saved_phone:
        context.user_data["phone"] = saved_phone

    context.user_data.update({
        "product_key": product_key,
        "step_index": 0
    })
    context.user_data["product"] = product["name"]

    if product_key == "choco":
        context.user_data["product_photo"] = None
    else:
        context.user_data["product_photo"] = product.get("photo")

    await show_step(query, context, product)

async def show_step(query, context, product):
    step_index = context.user_data["step_index"]

    custom_steps = context.user_data.get("custom_steps")
    if custom_steps:
        step = custom_steps[step_index]
    else:
        step = product["steps"][step_index]

    buttons = []
    for opt in step["options"]:
        buttons.append([InlineKeyboardButton(opt["label"], callback_data=f"opt_{opt['id']}")])

    caption = product['name']
    box = context.user_data.get("box_type", "")
    size = context.user_data.get("size", "")

    if box:
        caption += f"\nКоробка: {box}"
    if size:
        caption += f"\nРазмер: {size}"
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
        await query.message.chat.send_photo(
            photo=photo,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await query.message.chat.send_message(
            caption,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

async def option_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not context.user_data.get("product_key"):
        await query.message.reply_text("Пожалуйста, начните заказ заново.")
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
                        {"id": "4",  "label": "4 ягод — 990₽",  "price": 990},
                        {"id": "9",  "label": "9 ягод — 2090₽",  "price": 2090},
                        {"id": "12", "label": "12 ягод — 2790₽", "price": 2790},
                        {"id": "15", "label": "15 ягод — 3390₽", "price": 3390},
                        {"id": "16", "label": "16 ягод — 3590₽", "price": 3590},
                        {"id": "20", "label": "20 ягод — 4390₽", "price": 4390},
                    ]},
                    {"title": "Выберите дизайн:", "options": [
                        {"id": "1", "label": "Дизайн №1 (Полоски / посыпки)"},
                        {"id": "2", "label": "Дизайн №2 (Полоски в тон)"},
                        {"id": "3", "label": "Дизайн №3 (Посыпки)"},
                        {"id": "4", "label": "Дизайн №4 (Полоски / посыпки)"},
                    ]}
                ]
            else:
                context.user_data["product_photo"] = "http://fruttosmile.su/wp-content/uploads/2026/02/image-27-02-26-08-49-1.jpeg"
                context.user_data["box_type"] = "Круглая"
                custom_steps = [
                    {"title": "Выберите размер:", "options": [
                        {"id": "14",   "label": "12–14 ягод — 3690₽", "price": 3690},
                        {"id": "16",   "label": "15–16 ягод — 4190₽", "price": 4190},
                        {"id": "20",   "label": "18–20 ягод — 4790₽", "price": 4790},
                        {"id": "berry","label": "Бокс из свежих ягод — 4390₽", "price": 4390},
                    ]},
                    {"title": "Выберите дизайн:", "options": [
                        {"id": "1", "label": "Дизайн 1 (С полосками/посыпками/шоколадками)"},
                        {"id": "2", "label": "Дизайн 2 (С полосками/посыпками)"},
                        {"id": "3", "label": "Дизайн 3 (С полосками и голубикой)"},
                        {"id": "4", "label": "Бокс «Ягодная поляна» (без шоколада)"},
                    ]}
                ]

            context.user_data["custom_steps"] = custom_steps
            context.user_data["step_index"] = 0
            context.user_data.pop("size", None)
            context.user_data.pop("decor", None)
            context.user_data["product"] = f"{product['name']} ({context.user_data['box_type']})"

            await show_step(query, context, product)
            return

    custom_steps = context.user_data.get("custom_steps")
    if custom_steps:
        step = custom_steps[step_index]
    else:
        step = product["steps"][step_index]

    valid_ids = [str(o["id"]) for o in step["options"]]
    if str(selected_id) not in valid_ids:
        await query.answer("Кнопка устарела, выберите заново", show_alert=False)
        return

    try:
        selected_option = next(o for o in step["options"] if o["id"] == selected_id)
    except StopIteration:
        await query.message.reply_text("Вариант не найден.")
        return

    if "price" in selected_option:
        context.user_data["price"] = selected_option["price"]

    if step_index == 0:
        context.user_data["size"] = selected_option["label"]
    elif step_index == 1:
        context.user_data["decor"] = selected_option["label"]

    context.user_data["step_index"] += 1

    steps = context.user_data.get("custom_steps")
    if not steps:
        steps = product["steps"]

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

    if query.data == "back_to_box":
        context.user_data["step_index"] = 0
        context.user_data.pop("custom_steps", None)
        context.user_data["product_photo"] = None
        context.user_data.pop("box_type", None)
        context.user_data.pop("product", None)

        product = PRODUCTS["choco"]
        await show_step(query, context, product)
        return

    if query.data.startswith("back_"):
        if query.data == "back_to_method":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚚 Доставка", callback_data="method_delivery")],
                [InlineKeyboardButton("🏠 Самовывоз", callback_data="method_pickup")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
            ])
            try: await query.message.delete()
            except: pass
            await query.message.chat.send_message("Выберите способ получения:", reply_markup=kb)
            context.user_data['state'] = 'WAIT_METHOD'

        elif query.data == "back_to_district":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Октябрьский — 350₽", callback_data="district_350")],
                [InlineKeyboardButton("Кировский — 400₽", callback_data="district_400")],
                [InlineKeyboardButton("Свердловский — 450₽", callback_data="district_450")],
                [InlineKeyboardButton("Ленинский — 550₽", callback_data="district_550")],
                [InlineKeyboardButton("Индивидуальный тариф", callback_data="district_custom")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_method")]
            ])
            try: await query.message.delete()
            except: pass
            await query.message.chat.send_message("Выберите район доставки:", reply_markup=kb)
            context.user_data['state'] = 'WAIT_DISTRICT'

        elif query.data == "back_to_address":
            context.user_data['state'] = 'WAIT_ADDRESS'
            try: await query.message.delete()
            except: pass
            await query.message.chat.send_message("📍 Введите полный адрес доставки:")

        elif query.data == "back_to_date":
            context.user_data['state'] = 'WAIT_DATE'
            try: await query.message.delete()
            except: pass
            await query.message.chat.send_message("📅 Укажите дату доставки в формате ДД.ММ.ГГГГ\nПример: 25.01.2026")

    elif query.data == "main_menu":
        context.user_data.pop("product", None)
        context.user_data.pop("price", None)
        context.user_data.pop("size", None)
        context.user_data.pop("decor", None)
        context.user_data.pop("box_type", None)
        context.user_data.pop("product_photo", None)
        await show_main_menu(update, context)

    elif query.data == "step_back":
        current_step = context.user_data.get("step_index", 0)
        if current_step > 0:
            context.user_data["step_index"] = current_step - 1
            product_key = context.user_data.get("product_key")
            product = PRODUCTS.get(product_key)
            if product:
                try: await query.message.delete()
                except: pass
                await show_step(query, context, product)
        else:
            await show_main_menu(update, context)

async def delivery_method_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.pop('date', None)
    context.user_data.pop('delivery_time', None)
    context.user_data.pop('comment', None)
    context.user_data.pop('address', None)

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

        try:
            await query.message.delete()
        except:
            pass

        await query.message.chat.send_message("Выберите район доставки:", reply_markup=kb)

    elif query.data == "method_pickup":
        context.user_data['method'] = "Самовывоз"
        context.user_data['delivery_fee'] = 0
        context.user_data['address'] = "Самовывоз"
        context.user_data['state'] = 'WAIT_DATE'

        try:
            await query.message.delete()
        except:
            pass

        await query.message.chat.send_message(
            "📅 Укажите дату самовывоза в формате ДД.ММ.ГГГГ\nПример: 25.12.2025"
        )

async def district_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "district_custom":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Связь с менеджером", url="https://t.me/fruttosmile")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_method")]
        ])
        try:
            await query.message.delete()
        except:
            pass
        await query.message.chat.send_message(
            "Менеджер рассчитает стоимость доставки индивидуально:",
            reply_markup=kb
        )
        return

    price_str = query.data.split("_")[1]
    try:
        price = int(price_str)
    except:
        price = 0

    context.user_data['delivery_fee'] = price

    product_price = context.user_data.get('price', 0)
    qty = context.user_data.get('qty', 1)
    subtotal = product_price * qty
    total = subtotal + price

    text = (
        f"Стоимость доставки в выбранный район: **{price} ₽**\n\n"
        f"Товар: {subtotal} ₽\n"
        f"**Итого с доставкой: {total} ₽**\n\n"
        "Продолжить оформление?"
    )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, продолжить", callback_data="confirm_district")],
        [InlineKeyboardButton("⬅️ Выбрать другой район", callback_data="back_to_district")]
    ])

    try:
        await query.message.delete()
    except:
        pass

    await query.message.chat.send_message(text, reply_markup=kb, parse_mode="Markdown")

async def confirm_district_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['state'] = 'WAIT_ADDRESS'

    try:
        await query.message.delete()
    except:
        pass

    await query.message.chat.send_message("📍 Введите полный адрес доставки (улица, дом, квартира):")

async def time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if context.user_data.get("state") != "WAIT_TIME":
        return

    time_map = {
        "time_13_17": "13:00–17:00",
        "time_17_21": "17:00–21:00"
    }

    selected_time = time_map.get(query.data)

    if not selected_time:
        return

    context.user_data['delivery_time'] = selected_time
    context.user_data['state'] = 'WAIT_COMMENT'

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Без комментария", callback_data="no_comment")]
    ])

    try:
        await query.message.delete()
    except:
        pass

    await query.message.chat.send_message(
        "💬 Напишите пожелания к заказу (надпись на открытке, особые просьбы и т.д.):",
        reply_markup=kb
    )

async def no_comment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data['comment'] = "—"
    context.user_data['state'] = 'WAIT_CONFIRM'

    try:
        await query.message.delete()
    except:
        pass

    await show_order_preview(update, context)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    if not state:
        return

    text = update.message.text.strip()

    if state == 'WAIT_ADDRESS':
        context.user_data['address'] = text
        context.user_data['state'] = 'WAIT_DATE'
        await update.message.reply_text("📅 Укажите дату доставки/самовывоза в формате ДД.ММ.ГГГГ\nПример: 25.01.2026")

    elif state == 'WAIT_DATE':
        try:
            dt = datetime.strptime(text, "%d.%m.%Y")
            if dt.date() < date.today():
                await update.message.reply_text("Дата не может быть в прошлом.\nУкажите дату начиная с сегодняшнего дня.")
                return

            context.user_data['date'] = text
            context.user_data['state'] = 'WAIT_TIME'

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("13:00–17:00", callback_data="time_13_17")],
                [InlineKeyboardButton("17:00–21:00", callback_data="time_17_21")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_address")]
            ])

            await update.message.reply_text("⏰ Выберите интервал:", reply_markup=kb)

        except ValueError:
            await update.message.reply_text("Введите дату в формате ДД.ММ.ГГГГ\nПример: 25.01.2026")

    elif state == 'WAIT_COMMENT':
        context.user_data['comment'] = text
        context.user_data['state'] = 'WAIT_CONFIRM'
        await show_order_preview(update, context)

    elif state == "WAIT_FEEDBACK_TEXT":
        feedback = text
        rating = context.user_data.get("last_rating")
        name = context.user_data.get("name")
        phone = context.user_data.get("phone")

        message = (
            f"⚠️ Негативный отзыв\n\n"
            f"Имя: {name}\n"
            f"Телефон: {phone}\n"
            f"Оценка: {rating}\n\n"
            f"Комментарий:\n{feedback}"
        )

        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)

        await update.message.reply_text(
            "Спасибо за обратную связь 🙏\n"
            "Наш менеджер свяжется с вами."
        )

        context.user_data.pop("state", None)
        context.user_data.pop("last_rating", None)

async def show_order_preview(update, context):
    d = context.user_data
    total = d.get('price', 0) * d.get('qty', 1) + d.get('delivery_fee', 0)

    product_text = d.get('product', 'Не указано')
    box_type = d.get('box_type', '')
    size = d.get('size', '')
    decor = d.get('decor', '')

    full_text = product_text
    if box_type: full_text += f"\nКоробка: {box_type}"
    if size: full_text += f"\nРазмер: {size}"
    if decor: full_text += f"\nДизайн: {decor}"

    text_order = (
        "📋 **Проверьте ваш заказ:**\n\n"
        f"📦 **Товар:**\n{full_text}\n"
        f"🔢 Кол-во: {d.get('qty', 1)}\n"
        f"💰 Сумма: {total} ₽\n"
        f"🚛 Способ получения: {d.get('method')}\n"
        f"🏠 Адрес: {d.get('address', '-')}\n"
        f"📅 Дата: {d.get('date') or 'не указана'}\n"
        f"⏰ Время: {d.get('delivery_time') or 'не указано'}\n"
        f"💬 Комментарий: {d.get('comment') or '—'}"
    )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Подтвердить заказ", callback_data="confirm_order")],
        [InlineKeyboardButton("🔄 Изменить заказ", callback_data="restart_order")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ])

    msg = update.effective_message
    await msg.reply_text(text_order, reply_markup=kb, parse_mode="Markdown")

async def show_payment_options(update, context):
    method = context.user_data.get("method")

    if method == "Самовывоз":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Оплатить по QR", callback_data="pay_online")],
            [InlineKeyboardButton("🏪 Оплатить при получении", callback_data="pay_pickup")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_method")]
        ])
    else:  # Доставка
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Оплатить по QR", callback_data="pay_online")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_method")]
        ])

    msg = update.effective_message
    await msg.reply_text("💳 Выберите способ оплаты:", reply_markup=kb)

async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "pay_online":
        context.user_data["payment_method"] = "QR-оплата"

        d = context.user_data
        total_items = d.get('price', 0) * d.get('qty', 1)
        total_final = total_items + d.get('delivery_fee', 0)

        product_text = d.get('product', 'Не указано')
        box_type = d.get('box_type', '')
        size = d.get('size', '')
        decor = d.get('decor', '')

        full_text = product_text
        if box_type: full_text += f"\nКоробка: {box_type}"
        if size: full_text += f"\nРазмер: {size}"
        if decor: full_text += f"\nДизайн: {decor}"

        payment_text = (
            f"✅ **Заказ оформлен!**\n\n"
            f"💵 **Итоговая сумма: {total_final} ₽**\n"
            f"({total_items} ₽ за товар + {d.get('delivery_fee', 0)} ₽ доставка)\n\n"
            f"**Оплата:**\n"
            f"• Оплатите по [ссылке на QR](https://pay.alfabank.ru/sc/syXfcnoxVCDYcYsx)\n\n"
            f"📸 После оплаты отправьте сюда скриншот чека."
        )

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛍 Сделать ещё заказ", callback_data="main_menu")]
        ])

        await query.message.reply_text(payment_text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=reply_markup)

        confirm_text = (
            f"🆔 Заказ успешно принят!\n\n"
            f"Товар:\n{full_text}\n"
            f"Сумма к оплате: **{total_final} ₽**\n"
            "Ожидаем подтверждение оплаты от менеджера (обычно 5–15 минут)."
        )
        await query.message.reply_text(confirm_text, parse_mode="Markdown")

        await finish_order(update, context, status="Ожидает оплаты", skip_client_message=True)

    elif query.data == "pay_pickup":
        context.user_data["payment_method"] = "Оплата при получении"
        await query.message.reply_text(
            "🏪 Вы выбрали оплату при получении.\nМенеджер свяжется с вами для подтверждения."
        )
        await finish_order(update, context)

    elif query.data == "pay_courier":
        # Эта ветка больше не используется, но оставляем на всякий случай
        context.user_data["payment_method"] = "Оплата курьеру (наличные)"
        await query.message.reply_text(
            "💵 Оплата курьеру наличными.\nПожалуйста, подготовьте сумму без сдачи."
        )
        await finish_order(update, context)

async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE, status="Создан", skip_client_message=False):
    d = context.user_data

    if d.get("order_created"):
        return
    d["order_created"] = True

    if not d.get("price"):
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text="⚠️ Ошибка: заказ без цены. Пользователь не выбрал товар корректно."
        )
        msg = update.effective_message
        if msg:
            await msg.reply_text("⚠️ Произошла ошибка оформления заказа.\nПожалуйста оформите заказ заново.")
        return

    logging.info(f"ORDER DATA: {d}")

    if orders_sheet:
        try:
            col = orders_sheet.col_values(1)
            last_number = 0
            for v in reversed(col):
                if v.startswith("FS-"):
                    try:
                        last_number = int(v.replace("FS-", ""))
                        break
                    except:
                        pass
            new_number = last_number + 1
        except Exception as e:
            logging.error(f"Ошибка при генерации ID: {e}")
            new_number = random.randint(10000, 99999)
    else:
        new_number = random.randint(1, 99999)

    order_id = f"FS-{str(new_number).zfill(5)}"
    context.user_data["order_id"] = order_id

    client_id = update.effective_user.id
    context.user_data["client_id"] = client_id

    username = update.effective_user.username
    context.user_data["username"] = username

    price = d.get('price', 0)
    qty = d.get('qty', 1)
    total_items = price * qty
    total_final = total_items + d.get('delivery_fee', 0)

    product_name = d.get("product") or "Не указано"
    box_type = d.get("box_type")
    size = d.get("size")
    decor = d.get("decor")

    parts = [product_name]
    if box_type: parts.append(f"Коробка: {box_type}")
    if size:     parts.append(f"Размер: {size}")
    if decor:    parts.append(f"Дизайн: {decor}")

    full_product_text = "\n".join(parts)

    client_name = d.get("name")
    client_phone = d.get("phone")

    if not client_name or not client_phone:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text="⚠️ Заказ без данных клиента. Проверьте регистрацию."
        )
        return

    summary = (
        f"🔔 НОВЫЙ ЗАКАЗ!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 ID заказа: {order_id}\n"
        f"📦 Товар:\n{full_product_text}\n"
        f"🔢 Кол-во: {qty}\n"
        f"💰 ИТОГО: {total_final} ₽\n"
        f"👤 Клиент: {client_name}\n"
        f"📞 Тел: {client_phone}\n"
        f"🚚 Способ: {d.get('method', 'Не указан')}\n"
        f"🏠 Адрес: {d.get('address', '-')}\n"
        f"📅 Дата: {d.get('date') or 'не указана'}\n"
        f"⏰ Время: {d.get('delivery_time') or 'не указано'}\n"
        f"💬 Комментарий: {d.get('comment') or '—'}\n"
        f"📌 Статус: {status}\n"
        f"━━━━━━━━━━━━━━━"
    )

    contact_button = [[InlineKeyboardButton("💬 Открыть профиль", url=f"tg://user?id={client_id}")]]

    method = d.get("method", "").strip()

    if status == "Ожидает оплаты":
        admin_kb = InlineKeyboardMarkup(
            contact_button + [
                [InlineKeyboardButton("💳 Подтвердить оплату", callback_data=f"paid_{order_id}")]
            ]
        )

    elif status == "Создан":
        admin_kb = InlineKeyboardMarkup(
            contact_button + [
                [InlineKeyboardButton("✅ Принять заказ", callback_data=f"accept_{order_id}")]
            ]
        )

    elif method == "Самовывоз":
        admin_kb = InlineKeyboardMarkup(
            contact_button + [
                [InlineKeyboardButton("🍳 Заказ готов", callback_data=f"ready_{order_id}")],
                [InlineKeyboardButton("✅ Выдан клиенту", callback_data=f"picked_{order_id}")]
            ]
        )

    else:
        admin_kb = InlineKeyboardMarkup(
            contact_button + [
                [InlineKeyboardButton("🍳 Заказ готов", callback_data=f"ready_{order_id}")],
                [InlineKeyboardButton("🚚 Передан курьеру", callback_data=f"sent_{order_id}")],
                [InlineKeyboardButton("✅ Доставлен", callback_data=f"done_{order_id}")]
            ]
        )

    photo = d.get('product_photo')

    try:
        if photo:
            await context.bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=photo,
                caption=summary,
                reply_markup=admin_kb
            )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=summary,
                reply_markup=admin_kb
            )
    except Exception as e:
        logging.error(f"Ошибка отправки админу: {e}")
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=summary,
            reply_markup=admin_kb
        )

    if orders_sheet:
        success = False

        for i in range(3):
            try:
                orders_sheet.append_row([
                    order_id,
                    datetime.now().strftime("%d.%m.%Y %H:%M"),
                    client_id,
                    d.get('name', ''),
                    d.get('phone', ''),
                    full_product_text,
                    d.get('qty', 1),
                    total_final,
                    d.get('method'),
                    d.get('address', '-'),
                    f"{d.get('date', '-')} {d.get('delivery_time', '-')}",
                    status
                ])

                print(f"Заказ {order_id} записан в таблицу")
                success = True
                break

            except Exception as e:
                logging.error(f"Ошибка записи заказа (попытка {i+1}): {e}")

        if not success:
            try:
                backup_order = {
                    "order_id": order_id,
                    "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "client_id": client_id,
                    "name": d.get('name'),
                    "phone": d.get('phone'),
                    "product": full_product_text,
                    "qty": d.get('qty', 1),
                    "total": total_final,
                    "method": d.get('method'),
                    "address": d.get('address'),
                    "delivery": f"{d.get('date')} {d.get('delivery_time')}",
                    "status": status
                }

                with open("orders_backup.json", "a", encoding="utf-8") as f:
                    f.write(json.dumps(backup_order, ensure_ascii=False) + "\n")

            except Exception as e:
                logging.error(f"Ошибка резервного сохранения: {e}")

            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"❌ Google Sheets не ответил.\nЗаказ {order_id} сохранён в orders_backup.json"
            )

    payment_text = (
        f"✨ **Заказ оформлен успешно!** ✨\n\n"
        f"🆔 **ID заказа:** {order_id}\n\n"
        f"📦 **Товар:**\n{full_product_text}\n"
        f"🔢 Количество: {d.get('qty', 1)}\n"
        f"🚛 Способ: {d.get('method', 'Не указан')}\n"
        f"📅 Дата: {d.get('date') or 'не указана'}\n"
        f"⏰ Время: {d.get('delivery_time') or 'не указано'}\n\n"
        f"💰 **Итого к оплате: {total_final} ₽**\n\n"
        f"Спасибо, что выбрали Fruttosmile 💝"
    )

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 Сделать ещё заказ", callback_data="main_menu")]
    ])

    msg = update.effective_message
    if not skip_client_message and msg:
        await msg.reply_text(payment_text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=reply_markup)

async def order_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if context.user_data.get("last_action") == data:
        await query.answer("Статус уже установлен", show_alert=True)
        return

    context.user_data["last_action"] = data

    if data == "completed":
        await query.answer("Статус уже установлен", show_alert=True)
        return

    if "_" not in data:
        return

    action, order_id = data.split("_", 1)

    status_map = {
        "paid": "Оплачен",
        "accept": "Принят",
        "ready": "Готов",
        "sent": "Передан курьеру",
        "done": "Доставлен",
        "picked": "Выдан клиенту"
    }

    new_status = status_map.get(action)

    client_id = None
    order_method = None
    row_index = None

    if orders_sheet:
        try:
            cell = orders_sheet.find(order_id, in_column=1)
            if cell:
                row_index = cell.row
                row = orders_sheet.row_values(row_index)
                current_status = row[11] if len(row) > 11 else ""

                if current_status.strip() == new_status:
                    await query.answer("Этот статус уже установлен", show_alert=True)
                    return

                client_id_raw = row[2] if len(row) > 2 else None
                if client_id_raw:
                    try:
                        client_id = int(float(client_id_raw))
                    except:
                        pass

                order_method = row[8] if len(row) > 8 else ""

                orders_sheet.update_cell(row_index, 12, new_status)

        except Exception as e:
            logging.error(f"Ошибка работы с таблицей в order_status_handler: {e}")

    if client_id:
        if action == "accept":
            await context.bot.send_message(
                chat_id=client_id,
                text="✅ Ваш заказ принят!\n\n🍓 Мы начали готовить ваш заказ.\nОжидайте уведомление о готовности 💝"
            )
        elif action == "ready":
            await context.bot.send_message(
                chat_id=client_id,
                text="🍓 Ваш заказ готов!\n\nМожно забирать или ожидать курьера 💝"
            )
        elif action == "sent":
            await context.bot.send_message(
                chat_id=client_id,
                text="🚚 Ваш заказ передан курьеру!\nОжидайте доставку 💝"
            )
        elif action in ["done", "picked"]:
            await context.bot.send_message(
                chat_id=client_id,
                text="💖 Спасибо за заказ!\n\nБудем рады видеть вас снова 💝",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛍 Сделать ещё заказ", callback_data="main_menu")]
                ])
            )

    if action in ["done", "picked"] and client_id:
        delay = 24 + random.randint(0, 6)
        context.application.job_queue.run_once(
            send_review_request,
            when=timedelta(hours=delay),
            data={"chat_id": client_id},
            name=f"review_{order_id}"
        )
        logging.info(f"Запланирован запрос оценки через {delay} часов для {client_id} (заказ {order_id})")

    if action == "paid":
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Принять заказ", callback_data=f"accept_{order_id}")]
        ]))

    elif action == "accept":
        if order_method == "Самовывоз":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🍳 Заказ готов", callback_data=f"ready_{order_id}")],
                [InlineKeyboardButton("✅ Выдан клиенту", callback_data=f"picked_{order_id}")]
            ])
        else:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🍳 Заказ готов", callback_data=f"ready_{order_id}")],
                [InlineKeyboardButton("🚚 Передан курьеру", callback_data=f"sent_{order_id}")],
                [InlineKeyboardButton("✅ Доставлен", callback_data=f"done_{order_id}")]
            ])
        await query.edit_message_reply_markup(reply_markup=kb)

    elif action == "ready":
        if order_method == "Самовывоз":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Выдан клиенту", callback_data=f"picked_{order_id}")]
            ])
        else:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚚 Передан курьеру", callback_data=f"sent_{order_id}")],
                [InlineKeyboardButton("✅ Доставлен", callback_data=f"done_{order_id}")]
            ])
        await query.edit_message_reply_markup(reply_markup=kb)

    elif action == "sent":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Доставлен", callback_data=f"done_{order_id}")]
        ])
        await query.edit_message_reply_markup(reply_markup=kb)

    elif action in ["done", "picked"]:
        final_text = "✅ Заказ выдан клиенту" if action == "picked" else "✅ Заказ доставлен"

        try:
            if query.message.caption:
                await query.edit_message_caption(
                    caption=f"{query.message.caption}\n\n{final_text}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(final_text, callback_data="completed")]
                    ])
                )
            else:
                await query.edit_message_text(
                    text=f"{query.message.text}\n\n{final_text}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(final_text, callback_data="completed")]
                    ])
                )
        except Exception as e:
            logging.error(f"Ошибка редактирования сообщения: {e}")
            await query.edit_message_reply_markup(reply_markup=None)

    context.user_data.pop("state", None)

async def send_review_request(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.data["chat_id"]

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⭐1", callback_data="rate_1"),
            InlineKeyboardButton("⭐2", callback_data="rate_2"),
            InlineKeyboardButton("⭐3", callback_data="rate_3"),
            InlineKeyboardButton("⭐4", callback_data="rate_4"),
            InlineKeyboardButton("⭐5", callback_data="rate_5"),
        ]
    ])

    await context.bot.send_message(
        chat_id=chat_id,
        text="✨ Оцените ваш заказ от 1 до 5:",
        reply_markup=keyboard
    )

async def rating_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_reply_markup(reply_markup=None)

    rating = int(query.data.replace("rate_", ""))
    context.user_data["last_rating"] = rating

    if rating == 5:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Оставить отзыв в 2ГИС ⭐", url=TWOGIS_REVIEW_URL)]
        ])

        await query.message.reply_text(
            "Спасибо за высокую оценку! ❤️\n\n"
            "Нам будет очень приятно, если вы оставите отзыв в 2ГИС:",
            reply_markup=keyboard
        )
    else:
        context.user_data["state"] = "WAIT_FEEDBACK_TEXT"
        await query.message.reply_text(
            "Нам очень жаль, что что-то не понравилось 🙏\n"
            "Пожалуйста, опишите проблему."
        )

async def repeat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = query.data.replace("repeat_", "")

    if not orders_sheet:
        await query.message.reply_text("Ошибка повторного заказа.")
        return

    records = orders_sheet.get_all_records()

    for row in records:
        if row.get("ID заказа") == order_id:
            try:
                qty = int(row.get("Кол-во") or 1)
                total = int(row.get("Сумма") or 0)
                price = total // qty if qty > 0 else total
            except:
                qty = 1
                price = 0

            clear_order_data(context)

            context.user_data.update({
                "product": row.get("Товар"),
                "qty": qty,
                "price": price,
                "state": "WAIT_METHOD",
                "name": row.get("Имя"),
                "phone": row.get("Телефон")
            })

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚚 Доставка", callback_data="method_delivery")],
                [InlineKeyboardButton("🏠 Самовывоз", callback_data="method_pickup")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
            ])

            await query.message.reply_text(
                f"🔁 Повторяем заказ:\n\n"
                f"Товар: {row.get('Товар')}\n"
                f"Количество: {qty}\n\n"
                "Выберите способ получения:",
                reply_markup=kb
            )
            return

    await query.message.reply_text("Не удалось найти заказ для повторения.")

async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_order":
        if context.user_data.get("state") != "WAIT_CONFIRM":
            await query.message.reply_text("❗ Сначала завершите оформление заказа.")
            return

        if not context.user_data.get("date"):
            await query.message.reply_text("❗ Пожалуйста, укажите дату.")
            return

        if not context.user_data.get("delivery_time"):
            await query.message.reply_text("❗ Пожалуйста, выберите время.")
            return

        await show_payment_options(update, context)
        context.user_data["state"] = "WAIT_PAYMENT"

    elif query.data == "restart_order":
        clear_order_data(context)
        await query.message.reply_text("🔄 Заказ сброшен. Начнём заново.")
        await show_main_menu(update, context)

async def handle_payment_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"📸 Клиент {user.full_name} отправил чек.\nTelegram: @{user.username or 'нет'}\nID: {user.id}"
    )

    await context.bot.forward_message(
        chat_id=ADMIN_CHAT_ID,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id
    )

    await update.message.reply_text("✅ Чек отправлен менеджеру. Ожидайте подтверждения.")

# ================= MAIN =================
def main():
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    app.add_handler(CallbackQueryHandler(product_entry, pattern="^prod_"))
    app.add_handler(CallbackQueryHandler(option_handler, pattern="^opt_"))

    app.add_handler(CallbackQueryHandler(delivery_method_handler, pattern="^method_"))
    app.add_handler(CallbackQueryHandler(district_handler, pattern="^district_"))
    app.add_handler(CallbackQueryHandler(time_handler, pattern="^time_"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="^(back_.*|main_menu|step_back|back_to_box)$"))
    app.add_handler(CallbackQueryHandler(no_comment_handler, pattern="^no_comment$"))

    app.add_handler(CallbackQueryHandler(payment_handler, pattern="^pay_"))
    app.add_handler(CallbackQueryHandler(rating_handler, pattern="^rate_"))
    app.add_handler(CallbackQueryHandler(confirm_handler, pattern="^(confirm_order|restart_order)$"))
    app.add_handler(CallbackQueryHandler(confirm_district_handler, pattern="^confirm_district$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(CallbackQueryHandler(order_status_handler, pattern="^(paid|accept|ready|sent|done|picked)_|^completed$"))
    app.add_handler(CallbackQueryHandler(repeat_handler, pattern="^repeat_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_payment_screenshot))

    app.run_polling()

if __name__ == "__main__":
    main()
