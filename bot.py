import re
import logging
import os
import signal
import sys
import json
import random
from datetime import datetime, date

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
BOT_TOKEN = "8539880271:AAH1Dc_K378k11osJYw12oVbMqBj_IFH_N8"           # ← обязательно замени
ADMIN_CHAT_ID = 1165444045                   # ← ID админа

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

# ================= КАТАЛОГ ТОВАРОВ =================
PRODUCTS = {
    "choco": {
        "name": "🍓 Клубника в шоколаде",
        "photo": "http://fruttosmile.su/wp-content/uploads/2026/02/image-23-02-26-11-11-2.jpeg",
        "steps": [
            {
                "title": "Выберите размер:",
                "options": [
                    {"id": "4",  "label": "4 ягоды — 890₽",  "price": 890},
                    {"id": "9",  "label": "9 ягод — 1990₽",  "price": 1990},
                    {"id": "12", "label": "12 ягод — 2590₽", "price": 2590},
                    {"id": "15", "label": "15 ягод — 3190₽", "price": 3190},
                    {"id": "16", "label": "16 ягод — 3390₽", "price": 3390},
                    {"id": "20", "label": "20 ягод — 4190₽", "price": 4190},
                ]
            },
            {
                "title": "Выберите декор (1–4):",
                "options": [
                    {"id": "1", "label": "1 — Простой"},
                    {"id": "2", "label": "2 — Посыпка"},
                    {"id": "3", "label": "3 — Декор №1"},
                    {"id": "4", "label": "4 — Как на фото"},
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
                    {"id": "17", "label": "17–19 ягод — 3790₽", "price": 3790},
                    {"id": "20", "label": "20–23 ягоды — 4390₽", "price": 4390},
                    {"id": "25", "label": "25–27 ягод — 5590₽", "price": 5590},
                    {"id": "30", "label": "30–33 ягоды — 5790₽", "price": 5790},
                    {"id": "35", "label": "35–37 ягод — 6790₽", "price": 6790},
                ]
            },
            {
                "title": "Выберите декор (1–4):",
                "options": [
                    {"id": "1", "label": "1 — Простой"},
                    {"id": "2", "label": "2 — Посыпка"},
                    {"id": "3", "label": "3 — Декор №1"},
                    {"id": "4", "label": "4 — Как на фото"},
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
                    {"id": "12", "label": "12 ягод — 2490₽", "price": 2490},
                    {"id": "16", "label": "16 ягод — 2990₽", "price": 2990},
                    {"id": "20", "label": "20 ягод — 3990₽", "price": 3990},
                    {"id": "25", "label": "25 ягод — 4990₽", "price": 4990},
                ]
            },
            {
                "title": "Выберите декор (1–4):",
                "options": [
                    {"id": "1", "label": "1 — Простой"},
                    {"id": "2", "label": "2 — Посыпка"},
                    {"id": "3", "label": "3 — Декор №1"},
                    {"id": "4", "label": "4 — Как на фото"},
                ]
            }
        ]
    }
}

# ==================== ЛОГИКА ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text("Не удалось получить контакт. Попробуйте нажать кнопку ещё раз.")
        return

    name = contact.first_name or contact.last_name or "Клиент"
    phone = contact.phone_number

    context.user_data['name'] = name
    context.user_data['phone'] = phone

    await update.message.reply_text(
        f"Спасибо, {name}! Вы зарегистрированы в программе лояльности ✅\n"
        "Теперь можете выбирать товары и оформлять заказы мгновенно.",
        reply_markup=ReplyKeyboardRemove()
    )

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
        await update.callback_query.message.edit_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

async def product_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product_key = query.data.replace("prod_", "")
    product = PRODUCTS.get(product_key)

    if not product:
        await query.message.reply_text("Товар не найден.")
        return

    name = context.user_data.get("name")
    phone = context.user_data.get("phone")

    context.user_data.clear()

    if name:
        context.user_data["name"] = name
    if phone:
        context.user_data["phone"] = phone

    context.user_data["product_key"] = product_key
    context.user_data["product_photo"] = product["photo"]
    context.user_data["step_index"] = 0

    await show_step(query, context, product)

async def show_step(query, context, product):
    step_index = context.user_data["step_index"]
    step = product["steps"][step_index]

    buttons = []
    for opt in step["options"]:
        buttons.append([InlineKeyboardButton(opt["label"], callback_data=f"opt_{opt['id']}")])

    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])

    try:
        await query.message.delete()
    except:
        pass

    await query.message.chat.send_photo(
        photo=product["photo"],
        caption=f"{product['name']}\n\n{step['title']}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def option_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product_key = context.user_data.get("product_key")
    product = PRODUCTS.get(product_key)
    step_index = context.user_data.get("step_index", 0)

    if not product or step_index >= len(product["steps"]):
        await query.message.reply_text("Ошибка выбора. Начните заново.")
        await show_main_menu(update, context)
        return

    selected_id = query.data.replace("opt_", "")
    step = product["steps"][step_index]

    try:
        selected_option = next(o for o in step["options"] if o["id"] == selected_id)
    except StopIteration:
        await query.message.reply_text("Вариант не найден.")
        return

    if step_index == 0:
        context.user_data["size"] = selected_option["label"]
    elif step_index == 1:
        context.user_data["decor"] = selected_option["label"]
    else:
        context.user_data[f"step_{step_index}"] = selected_option["label"]

    if "price" in selected_option:
        context.user_data["price"] = selected_option["price"]

    context.user_data["step_index"] += 1

    if context.user_data["step_index"] < len(product["steps"]):
        await show_step(query, context, product)
    else:
        context.user_data["product"] = product["name"]
        context.user_data["qty"] = 1
        context.user_data["state"] = "WAIT_METHOD"

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚚 Доставка", callback_data="method_delivery")],
            [InlineKeyboardButton("🏠 Самовывоз", callback_data="method_pickup")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ])

        await query.message.reply_text("Выберите способ получения:", reply_markup=kb)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_delete(update.message)

    state = context.user_data.get('state')
    if not state:
        return

    text = update.message.text.strip()

    if state == 'WAIT_QTY':
        try:
            qty = int(re.sub(r'\D', '', text))
            if qty < 1:
                raise ValueError
            context.user_data['qty'] = qty

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚚 Доставка", callback_data="method_delivery")],
                [InlineKeyboardButton("🏠 Самовывоз", callback_data="method_pickup")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
            ])
            await update.message.reply_text("Выберите способ получения:", reply_markup=kb)
            context.user_data['state'] = 'WAIT_METHOD'
        except:
            await update.message.reply_text("Пожалуйста, укажите количество цифрами (минимум 1).")

    elif state == 'WAIT_ADDRESS':
        context.user_data['address'] = text
        context.user_data['state'] = 'WAIT_DATE'
        await update.message.reply_text("📅 Укажите дату доставки в формате ДД.ММ.ГГГГ\nПример: 25.12.2025")

    elif state == 'WAIT_DATE':
        try:
            dt = datetime.strptime(text, "%d.%m.%Y")
            if dt.date() < date.today():
                await update.message.reply_text("Дата не может быть в прошлом.\nУкажите дату начиная с сегодняшнего дня.")
                return

            context.user_data['date'] = text
            context.user_data['state'] = 'WAIT_TIME'

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("9:00–12:00", callback_data="time_9_12")],
                [InlineKeyboardButton("12:00–16:00", callback_data="time_12_16")],
                [InlineKeyboardButton("16:00–20:00", callback_data="time_16_20")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_address")]
            ])

            await update.message.reply_text("⏰ Выберите интервал доставки:", reply_markup=kb)

        except ValueError:
            await update.message.reply_text("Введите дату в формате ДД.ММ.ГГГГ")

    elif state == 'WAIT_COMMENT':
        context.user_data['comment'] = text
        context.user_data['state'] = 'WAIT_CONFIRM'
        await show_order_preview(update, context)

async def show_order_preview(update, context):
    d = context.user_data
    total = d.get('price', 0) * d.get('qty', 0) + d.get('delivery_fee', 0)

    product_text = d.get('product', 'Не указано')
    if d.get("size"):
        product_text += f"\nРазмер: {d.get('size')}"
    if d.get("decor"):
        product_text += f"\nДекор: {d.get('decor')}"

    text_order = (
        "📋 **Проверьте ваш заказ:**\n\n"
        f"📦 Товар: {product_text}\n"
        f"🔢 Кол-во: {d.get('qty')}\n"
        f"💰 Сумма: {total} ₽\n"
        f"🚛 Способ получения: {d.get('method')}\n"
        f"🏠 Адрес: {d.get('address', '-')}\n"
        f"📅 Дата: {d.get('date', '-')}\n"
        f"⏰ Время: {d.get('delivery_time', '-')}\n"
        f"💬 Комментарий: {d.get('comment') or '—'}"
    )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Подтвердить заказ", callback_data="confirm_order")],
        [InlineKeyboardButton("🔄 Изменить заказ", callback_data="restart_order")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ])

    msg = update.message or update.callback_query.message
    await msg.reply_text(text_order, reply_markup=kb, parse_mode="Markdown")

async def show_payment_options(update, context):
    method = context.user_data.get("method")

    if method == "Самовывоз":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Оплатить сейчас", callback_data="pay_online")],
            [InlineKeyboardButton("🏪 Оплатить при получении", callback_data="pay_pickup")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_method")]
        ])
    else:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Оплатить сейчас", callback_data="pay_online")],
            [InlineKeyboardButton("💵 Оплатить курьеру (наличные)", callback_data="pay_courier")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_method")]
        ])

    msg = update.message or update.callback_query.message
    await msg.reply_text("💳 Выберите способ оплаты:", reply_markup=kb)

async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "pay_online":
        context.user_data["payment_method"] = "QR-оплата"

        d = context.user_data
        total_items = d.get('price', 0) * d.get('qty', 0)
        total_final = total_items + d.get('delivery_fee', 0)

        product_text = d.get('product', 'Не указано')
        if d.get("size"):
            product_text += f"\nРазмер: {d.get('size')}"
        if d.get("decor"):
            product_text += f"\nДекор: {d.get('decor')}"

        payment_text = (
            f"✅ **Заказ оформлен!**\n\n"
            f"💵 **Итоговая сумма: {total_final} ₽**\n"
            f"({total_items} ₽ за товар + {d.get('delivery_fee', 0)} ₽ доставка)\n\n"
            f"**Оплата:**\n"
            f"• Оплатите по [ссылке на QR](https://qr.nspk.ru/BS1A0054EC7LHJ358M29KSAKOJJ638N1)\n\n"
            f"📸 После оплаты отправьте сюда скриншот чека."
        )

        await query.message.reply_text(payment_text, parse_mode="Markdown", disable_web_page_preview=True)

        confirm_text = (
            f"🆔 Заказ успешно принят!\n\n"
            f"Товар: {product_text}\n"
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
        context.user_data["payment_method"] = "Оплата курьеру (наличные)"
        await query.message.reply_text(
            "💵 Оплата курьеру наличными.\nПожалуйста, подготовьте сумму без сдачи."
        )
        await finish_order(update, context)

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

        await query.edit_message_text("Выберите район доставки:", reply_markup=kb)

    elif query.data == "method_pickup":
        context.user_data['method'] = "Самовывоз"
        context.user_data['delivery_fee'] = 0
        context.user_data['address'] = "Самовывоз"
        context.user_data['delivery_time'] = "По договоренности"
        context.user_data['state'] = 'WAIT_COMMENT'

        await query.edit_message_text(
            "💬 Напишите пожелания к заказу\n"
            "(номер получателя, надпись на открытке, особые просьбы и т.д.)\n"
            "Или напишите 'Нет':"
        )

async def district_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "district_custom":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Связь с менеджером", url="https://t.me/fruttosmile")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_method")]
        ])
        await query.edit_message_text(
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

    await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

async def confirm_district_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['state'] = 'WAIT_ADDRESS'
    await query.edit_message_text("📍 Введите полный адрес доставки (улица, дом, квартира):")

async def time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    time_map = {
        "time_9_12": ("9:00–12:00", 9),
        "time_12_16": ("12:00–16:00", 12),
        "time_16_20": ("16:00–20:00", 16)
    }

    selected_time, start_hour = time_map.get(query.data, (None, None))

    if not selected_time:
        return

    order_date_str = context.user_data.get("date")

    if order_date_str:
        order_date = datetime.strptime(order_date_str, "%d.%m.%Y").date()

        if order_date == date.today():
            current_hour = datetime.now().hour
            if current_hour >= start_hour:
                await query.edit_message_text(
                    "⛔ Этот интервал уже недоступен.\nВыберите более позднее время."
                )
                return

    context.user_data['delivery_time'] = selected_time
    context.user_data['state'] = 'WAIT_COMMENT'

    await query.edit_message_text(
        "💬 Напишите пожелания к заказу\n"
        "(номер получателя, надпись на открытке, особые просьбы и т.д.):"
    )

async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("back_"):
        # Обработка всех back_*
        if query.data == "back_to_method":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚚 Доставка", callback_data="method_delivery")],
                [InlineKeyboardButton("🏠 Самовывоз", callback_data="method_pickup")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
            ])
            await query.edit_message_text("Выберите способ получения:", reply_markup=kb)
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
            await query.edit_message_text("Выберите район доставки:", reply_markup=kb)
            context.user_data['state'] = 'WAIT_DISTRICT'

        elif query.data == "back_to_address":
            context.user_data['state'] = 'WAIT_ADDRESS'
            await query.edit_message_text("📍 Введите полный адрес доставки:")

        elif query.data == "back_to_date":
            context.user_data['state'] = 'WAIT_DATE'
            await query.edit_message_text("📅 Укажите дату доставки в формате ДД.ММ.ГГГГ\nПример: 25.12.2025")

    elif query.data == "main_menu":
        name = context.user_data.get("name")
        phone = context.user_data.get("phone")

        context.user_data.clear()

        if name:
            context.user_data["name"] = name
        if phone:
            context.user_data["phone"] = phone

        await show_main_menu(update, context)

async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE, status="Создан", skip_client_message=False):
    d = context.user_data

    order_id = f"FS-{random.randint(10000, 99999)}"
    context.user_data["order_id"] = order_id

    client_id = update.effective_user.id
    context.user_data["client_id"] = client_id

    total_items = d.get('price', 0) * d.get('qty', 0)
    total_final = total_items + d.get('delivery_fee', 0)

    product_text = d.get('product', 'Не указано')
    if d.get("size"):
        product_text += f"\nРазмер: {d.get('size')}"
    if d.get("decor"):
        product_text += f"\nДекор: {d.get('decor')}"

    summary = (
        f"🔔 НОВЫЙ ЗАКАЗ!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 ID заказа: {order_id}\n"
        f"📦 Товар: {product_text}\n"
        f"🔢 Кол-во: {d.get('qty')}\n"
        f"💰 ИТОГО: {total_final} ₽\n"
        f"👤 Клиент: {d.get('name')}\n"
        f"📞 Тел: {d.get('phone')}\n"
        f"🚛 Способ: {d.get('method')}\n"
        f"🏠 Адрес: {d.get('address', '-')}\n"
        f"📅 Дата: {d.get('date', '-')}\n"
        f"⏰ Время: {d.get('delivery_time', '-')}\n"
        f"💬 Комментарий: {d.get('comment', '-')}\n"
        f"📌 Статус: {status}\n"
        f"━━━━━━━━━━━━━━━"
    )

    if status == "Ожидает оплаты":
        admin_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Подтвердить оплату", callback_data=f"paid_{order_id}")]
        ])
    elif status == "Оплачен":
        admin_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Принять заказ", callback_data=f"accept_{order_id}")]
        ])
    else:
        admin_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🍳 Заказ готов", callback_data=f"ready_{order_id}")],
            [InlineKeyboardButton("🚚 Передан курьеру", callback_data=f"sent_{order_id}")],
            [InlineKeyboardButton("✅ Доставлен", callback_data=f"done_{order_id}")]
        ])

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=d.get('product_photo', ''),
            caption=summary,
            reply_markup=admin_kb
        )
    except:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=summary,
            reply_markup=admin_kb
        )

    if orders_sheet:
        try:
            orders_sheet.append_row([
                order_id,
                datetime.now().strftime("%d.%m.%Y %H:%M"),
                update.effective_user.id,
                d.get('name'),
                d.get('phone'),
                product_text,
                d.get('qty'),
                total_final,
                d.get('method'),
                d.get('address', '-'),
                f"{d.get('date', '-')} {d.get('delivery_time', '-')}",
                status
            ])
        except Exception as e:
            logging.error(f"Ошибка записи заказа: {e}")

    payment_text = (
        f"✨ **Заказ оформлен успешно!** ✨\n\n"
        f"🆔 **ID заказа:** {order_id}\n\n"
        f"📦 {product_text}\n"
        f"🔢 Количество: {d.get('qty')}\n"
        f"🚛 Способ: {d.get('method')}\n"
        f"📅 Дата: {d.get('date')}\n"
        f"⏰ Время: {d.get('delivery_time')}\n\n"
        f"💰 **Итого к оплате: {total_final} ₽**\n\n"
        f"Спасибо, что выбрали Fruttosmile 💝"
    )

    if not skip_client_message:
        msg = update.callback_query.message if update.callback_query else update.message
        await msg.reply_text(payment_text, parse_mode="Markdown", disable_web_page_preview=True)

async def order_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    action, order_id = data.split("_", 1)

    status_map = {
        "paid": "Оплачен",
        "accept": "Принят",
        "ready": "Готов",
        "sent": "Передан курьеру",
        "done": "Доставлен"
    }

    status_text_map = {
        "paid": f"💳 Ваш заказ {order_id} успешно оплачен! Мы приступаем к его обработке.",
        "accept": f"✅ Ваш заказ {order_id} принят в работу!",
        "ready": f"🍳 Ваш заказ {order_id} готов!",
        "sent": f"🚚 Ваш заказ {order_id} передан курьеру!",
        "done": f"🎉 Ваш заказ {order_id} успешно доставлен!"
    }

    new_status = status_map.get(action)

    client_id = None

    if orders_sheet:
        try:
            records = orders_sheet.get_all_records()
            for i, row in enumerate(records):
                if row.get("ID заказа") == order_id:
                    orders_sheet.update_cell(i + 2, 12, new_status)
                    client_id = row.get("Telegram ID")
                    break
        except Exception as e:
            logging.error(f"Ошибка обновления статуса: {e}")

    if client_id:
        await context.bot.send_message(
            chat_id=client_id,
            text=status_text_map.get(action, f"Статус изменён: {new_status}")
        )

    await query.answer(f"Статус: {new_status}")

    if action == "paid":
        new_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Принять заказ", callback_data=f"accept_{order_id}")]
        ])
        await query.edit_message_reply_markup(reply_markup=new_kb)

    elif action == "accept":
        new_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🍳 Заказ готов", callback_data=f"ready_{order_id}")],
            [InlineKeyboardButton("🚚 Передан курьеру", callback_data=f"sent_{order_id}")],
            [InlineKeyboardButton("✅ Доставлен", callback_data=f"done_{order_id}")]
        ])
        await query.edit_message_reply_markup(reply_markup=new_kb)

    elif action in ["ready", "sent"]:
        remaining = []
        if action != "ready":
            remaining.append([InlineKeyboardButton("🍳 Заказ готов", callback_data=f"ready_{order_id}")])
        if action != "sent":
            remaining.append([InlineKeyboardButton("🚚 Передан курьеру", callback_data=f"sent_{order_id}")])
        remaining.append([InlineKeyboardButton("✅ Доставлен", callback_data=f"done_{order_id}")])
        if remaining:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(remaining))

    elif action == "done":
        await query.edit_message_reply_markup(reply_markup=None)

        if client_id:
            review_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔁 Повторить заказ", callback_data=f"repeat_{order_id}")],
                [InlineKeyboardButton("🛍 Сделать новый заказ", callback_data="main_menu")],
                [InlineKeyboardButton("⭐ Оставить отзыв + бонус", url="https://t.me/fruttosmile_bonus_bot")]
            ])

            await context.bot.send_message(
                chat_id=client_id,
                text="🎉 Спасибо за заказ!\n\nБудем рады видеть вас снова 💝",
                reply_markup=review_keyboard
            )

        context.user_data.clear()

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
            except (ValueError, TypeError, ZeroDivisionError):
                qty = 1
                price = 0

            context.user_data.update({
                "product": row.get("Товар"),
                "qty": qty,
                "price": price,
                "state": "WAIT_METHOD"
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
        await show_payment_options(update, context)

    elif query.data == "restart_order":
        context.user_data.clear()
        await query.message.reply_text("🔄 Заказ сброшен. Начнём заново.")
        await show_main_menu(update, context)

async def handle_payment_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"📸 Клиент {user.full_name} отправил чек.\nTelegram ID: {user.id}"
    )

    await context.bot.forward_message(
        chat_id=ADMIN_CHAT_ID,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id
    )

    await update.message.reply_text("✅ Чек отправлен менеджеру. Ожидайте подтверждения.")

# ==================== GRACEFUL SHUTDOWN ====================
def shutdown(signum, frame):
    print("Получен сигнал остановки, завершаем polling...")
    sys.exit(0)

# ==================== MAIN ====================
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
    app.add_handler(CallbackQueryHandler(back_handler, pattern="^(back_|main_menu)"))  # исправленный pattern

    app.add_handler(CallbackQueryHandler(payment_handler, pattern="^pay_"))

    app.add_handler(CallbackQueryHandler(confirm_handler, pattern="^(confirm_order|restart_order)$"))
    app.add_handler(CallbackQueryHandler(confirm_district_handler, pattern="^confirm_district$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(CallbackQueryHandler(order_status_handler, pattern="^(paid|accept|ready|sent|done)_"))
    app.add_handler(CallbackQueryHandler(repeat_handler, pattern="^repeat_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_payment_screenshot))

    app.run_polling()

if __name__ == "__main__":
    main()
