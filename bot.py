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
BOT_TOKEN = "8539880271:AAH1Dc_K378k11osJYw12oVbMqBj_IFH_N8"
ADMIN_CHAT_ID = 1165444045
SPREADSHEET_NAME = "Fruttosmile Bonus CRM"
SHEET_NAME = "users"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= GOOGLE TABLES =================
GOOGLE_KEY_JSON = os.getenv("GOOGLE_KEY_JSON")
users_sheet = None
orders_sheet = None
bonus_logs_sheet = None
if GOOGLE_KEY_JSON:
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = json.loads(GOOGLE_KEY_JSON)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
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

# ================= ПОЛНЫЙ КАТАЛОГ ТОВАРОВ =================
PRODUCTS = {
    "boxes": {
        "0_3000": [
            {"name": "Бенто-торт из клубники в шоколаде (8 ягод)", "price": "2490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/07/photoeditorsdk-export4.png"},
            {"name": "Стаканчик с клубникой в шоколаде", "price": "1790", "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export69-660x800-1.png"},
            {"name": "Набор с клубникой, финиками и черешней", "price": "2390", "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/ceresenki.jpg"},
            {"name": "Набор клубники и малины в шоколаде", "price": "2990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/malinki-takie-vecerinki.jpg"},
            {"name": "Конфеты ручной работы", "price": "1390", "photo": "http://fruttosmile.su/wp-content/uploads/2025/04/unnamed-file.jpg"},
            {"name": "Бананы в шоколаде мини коробочка", "price": "1390", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/banany-11.jpg"},
            {"name": "Бананы с орехами", "price": "1990", "photo": "http://fruttosmile.su/wp-content/uploads/2014/08/jguy.png"},
            {"name": "Клубника в шоколаде 12 ягод", "price": "2590", "photo": "http://fruttosmile.su/wp-content/uploads/2014/03/photo_5449855732875908292_y.jpg"},
            {"name": "Сердечко «Клубника и бананы в шоколаде»", "price": "2490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/serdechko-klubnika-i-banany-v-shokolade.png"},
            {"name": "Круглая коробка Бананы и клубника в шоколаде", "price": "2290", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/kruglaya-korobka-banany-i-klubnika-v-shokolade.jpg"},
            {"name": "Набор «Бананы и клубника в шоколаде» 20*20", "price": "2990", "photo": "http://fruttosmile.su/wp-content/uploads/2023/02/photo_2024-02-24_19-13-37.jpg"},
            {"name": "Набор с клубникой, финиками и малиной", "price": "2990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/ceresenki.jpg"}
        ],
        "3000_5000": [
            {"name": "Новогоднее сердце с клубникой в шоколаде Маленькое", "price": "3490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png"},
            {"name": "Новогоднее сердце с клубникой в шоколаде Среднее", "price": "4490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png"},
            {"name": "Подарочный набор «Ягодный микс»", "price": "4990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export67.png"},
            {"name": "Клубника в шоколаде 16 ягод", "price": "3390", "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/16-miks-posypki.jpg"},
            {"name": "Коробочка с цветами и макаронсами «Солнечная»", "price": "3490", "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/photoeditorsdk-export248.png"},
            {"name": "Круглая коробочка с клубникой", "price": "3490", "photo": "http://fruttosmile.su/wp-content/uploads/2024/02/photo_5388599668054814722_y.jpg"},
            {"name": "Набор «Клубничные джентльмены» Малый", "price": "2190", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-04-05_17-43-47.jpg"},
            {"name": "Набор «Клубничные джентльмены» Средний", "price": "2790", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-04-05_17-43-47.jpg"},
            {"name": "Набор «Клубничные джентльмены» Большой", "price": "4390", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-04-05_17-43-47.jpg"},
            {"name": "Набор «Экзотический»", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/fdgecx_660x800_481x582.png"},
            {"name": "Набор из ягод » Шоколатье»", "price": "4490", "photo": "http://fruttosmile.su/wp-content/uploads/2016/12/img_3983.jpg"},
            {"name": "Набор клубники и шоколада «Мужской»", "price": "3990", "photo": "http://fruttosmile.su/wp-content/uploads/2020/05/photo_2024-08-08_16-13-32.jpg"},
            {"name": "Набор фруктов в шоколаде «Ассорти»", "price": "4990", "photo": "http://fruttosmile.su/wp-content/uploads/2017/08/photo_2024-05-10_17-28-111.jpg"},
            {"name": "Набор-комплимент с цветами и клубникой", "price": "3490", "photo": "http://fruttosmile.su/wp-content/uploads/2024/01/photo_2024-01-27_11-11-33.jpg"},
            {"name": "Новогодняя коробочка с клубникой Малый", "price": "3490", "photo": "http://fruttosmile.su/wp-content/uploads/2024/12/photoeditorsdk-export61.png"},
            {"name": "Новогодняя коробочка с клубникой Средний", "price": "3890", "photo": "http://fruttosmile.su/wp-content/uploads/2024/12/photoeditorsdk-export61.png"},
            {"name": "Новогодняя коробочка с клубникой Большой", "price": "4490", "photo": "http://fruttosmile.su/wp-content/uploads/2024/12/photoeditorsdk-export61.png"},
            {"name": "Подарочный бокс «Райское наслаждение»", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2017/06/ld.png"},
            {"name": "Сердце с клубникой в шоколаде с декором", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photo_2022_12_09_15_57_12_481x582.jpg"},
            {"name": "Торт из клубники в шоколаде", "price": "7490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photo_2025_02_25_16_20_32_481x582.jpg"},
            {"name": "Клубника в шоколаде «Зверята»", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2023/07/photo_2024-08-08_16-12-56.jpg"},
            {"name": "Бокс «С надписью» Малый", "price": "5490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/boks-s-nadpisyu.jpg"},
            {"name": "Бокс «С надписью» Средний", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/boks-s-nadpisyu.jpg"},
            {"name": "Бокс «С надписью» Большой", "price": "6990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/boks-s-nadpisyu.jpg"},
            {"name": "Бокс «Двойной шоколад» Малый", "price": "5490", "photo": "http://fruttosmile.su/wp-content/uploads/2024/08/20240809_155003.jpg"},
            {"name": "Бокс «Двойной шоколад» Большой", "price": "6990", "photo": "http://fruttosmile.su/wp-content/uploads/2024/08/20240809_155003.jpg"},
            {"name": "Бокс подарочный «Для мужчин»", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2018/09/photo_2024-08-08_16-18-29.jpg"},
            {"name": "Бокс с цветами, клубникой и шампанским « Элеганс»", "price": "6590", "photo": "http://fruttosmile.su/wp-content/uploads/2017/05/lngi.png"},
            {"name": "Двойное сердце с цветами и клубникой в шоколаде", "price": "6990", "photo": "http://fruttosmile.su/wp-content/uploads/2020/11/photo_5327822311698586102_y.jpg"}
        ],
        "5000_plus": [
            {"name": "Бокс «Ассорти»", "price": "6990", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/900-1080-piks.-880-1080-piks.-860-1080-piks.-840-1080-piks.-830-1080-piks.-820-1080-piks.png"},
            {"name": "Корзина клубники в шоколаде L", "price": "11990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-klubniki-v-shokolade-l.jpeg"},
            {"name": "Корзина клубники в шоколаде S", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-klubniki-v-shokolade-s.jpeg"},
            {"name": "Корзина клубники в шоколаде XXL", "price": "25000", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-klubniki-v-shokolade-xxl.jpeg"},
            {"name": "Корзина фруктов «Заморская»", "price": "9990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-fruktov-zamorskaya.jpg"},
            {"name": "Мужская корзина «Брутал»", "price": "12990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/whatsapp202023_10_1620v2014.38.08_14f00b4d_481x582.jpg"},
            {"name": "Фруктовая корзина", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photo_2025-05-24_17-21-00-fruktii.jpg"},
            {"name": "Новогоднее сердце с клубникой в шоколаде Большое", "price": "5490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png"}
        ]
    },
    # Остальные категории (flowers, meat, sweet) — если нужно, добавь их аналогично предыдущим версиям
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
        [InlineKeyboardButton("📦 Боксы", callback_data="cat_boxes")],
        [InlineKeyboardButton("💐 Свежие букеты", callback_data="cat_flowers")],
        [InlineKeyboardButton("🍖 Мясные букеты", callback_data="cat_meat")],
        [InlineKeyboardButton("🍬 Сладкие букеты", callback_data="cat_sweet")],
        [InlineKeyboardButton("📞 Связь с магазином", url="https://t.me/fruttosmile")]
    ])
    text = "Выберите категорию:"

    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

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
                [InlineKeyboardButton("🏠 Самовывоз", callback_data="method_pickup")]
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
            await update.message.reply_text("Неверный формат. Укажите дату как ДД.ММ.ГГГГ\nПример: 25.12.2025")

    elif state == 'WAIT_COMMENT':
        context.user_data['comment'] = text
        context.user_data['state'] = 'WAIT_CONFIRM'
        await show_order_preview(update, context)

async def show_order_preview(update, context):
    d = context.user_data
    total = int(d.get('price', 0)) * int(d.get('qty', 0)) + d.get('delivery_fee', 0)

    text_order = (
        "📋 **Проверьте ваш заказ:**\n\n"
        f"📦 Товар: {d.get('product')}\n"
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
        [InlineKeyboardButton("📞 Связь с магазином", url="https://t.me/fruttosmile")]
    ])

    msg = update.message or update.callback_query.message
    await msg.reply_text(text_order, reply_markup=kb, parse_mode="Markdown")

async def show_payment_options(update, context):
    method = context.user_data.get("method")

    if method == "Самовывоз":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Оплатить сейчас", callback_data="pay_online")],
            [InlineKeyboardButton("🏪 Оплатить при получении", callback_data="pay_pickup")]
        ])
    else:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Оплатить сейчас", callback_data="pay_online")],
            [InlineKeyboardButton("💵 Оплатить курьеру (наличные)", callback_data="pay_courier")]
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

        payment_text = (
            f"✅ **Заказ оформлен!**\n\n"
            f"💵 **Итоговая сумма: {total_final} ₽**\n"
            f"({total_items} ₽ за товар + {d.get('delivery_fee', 0)} ₽ доставка)\n\n"
            f"**Оплата:**\n"
            f"• Оплатите по [ссылке на QR](https://qr.nspk.ru/BS1A0054EC7LHJ358M29KSAKOJJ638N1)\n\n"
            f"📸 После оплаты отправьте сюда скриншот чека."
        )

        await query.message.reply_text(payment_text, parse_mode="Markdown", disable_web_page_preview=True)

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
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_method")]
        ])

        await query.edit_message_text("Выберите район доставки:", reply_markup=kb)

    elif query.data == "method_pickup":
        context.user_data['method'] = "Самовывоз"
        context.user_data['delivery_fee'] = 0
        context.user_data['address'] = "-"
        context.user_data['state'] = 'WAIT_DATE'
        await query.edit_message_text("🕒 Укажите дату, когда планируете забрать заказ (ДД.ММ.ГГГГ):")

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

    selected_time, start_hour = time_map.get(query.data, ("Не указано", 0))

    order_date_str = context.user_data.get("date")
    if order_date_str:
        order_date = datetime.strptime(order_date_str, "%d.%m.%Y").date()
        if order_date == date.today():
            if datetime.now().hour >= start_hour:
                await query.edit_message_text(
                    "⛔ Этот интервал уже недоступен.\nВыберите более позднее время."
                )
                return

    context.user_data['delivery_time'] = selected_time
    context.user_data['state'] = 'WAIT_COMMENT'

    await query.edit_message_text(
        "💬 Напишите пожелания к заказу (надпись на открытке, особые просьбы и т.д.):"
    )

async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_method":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚚 Доставка", callback_data="method_delivery")],
            [InlineKeyboardButton("🏠 Самовывоз", callback_data="method_pickup")]
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

async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE, status="Создан", skip_client_message=False):
    d = context.user_data

    order_id = f"FS-{random.randint(10000, 99999)}"
    context.user_data["order_id"] = order_id

    client_id = update.effective_user.id
    context.user_data["client_id"] = client_id

    total_items = d.get('price', 0) * d.get('qty', 0)
    total_final = total_items + d.get('delivery_fee', 0)

    summary = (
        f"🔔 НОВЫЙ ЗАКАЗ!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 ID заказа: {order_id}\n"
        f"📦 Товар: {d.get('product')}\n"
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

    admin_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Подтвердить оплату", callback_data=f"paid_{order_id}")],
        [InlineKeyboardButton("✅ Принять", callback_data=f"accept_{order_id}")],
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
                d.get('product'),
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
        f"📦 {d.get('product')}\n"
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

    context.user_data.clear()

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
    await query.edit_message_reply_markup(reply_markup=None)  # Удаляем все кнопки после нажатия

async def handle_payment_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"📸 Клиент {user.full_name} отправил чек.\nTelegram ID: {user.id}"
    )

    await context.bot.forward_message(
        chat_id=ADMIN_CHAT_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )

    await update.message.reply_text("✅ Чек отправлен менеджеру. Ожидайте подтверждения.")

async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_order":
        await show_payment_options(update, context)

    elif query.data == "restart_order":
        context.user_data.clear()
        await query.message.reply_text("🔄 Заказ сброшен. Начнём заново.")
        await start(update, context)

    elif query.data == "confirm_district":
        await confirm_district_handler(update, context)

async def cat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.replace("cat_", "")
    context.user_data['current_cat'] = category

    data = PRODUCTS.get(category)

    if isinstance(data, dict):
        keyboard = [
            [InlineKeyboardButton("До 3000 ₽", callback_data=f"sub_{category}_0_3000")],
            [InlineKeyboardButton("3000 — 5000 ₽", callback_data=f"sub_{category}_3000_5000")],
            [InlineKeyboardButton("От 5000 ₽", callback_data=f"sub_{category}_5000_plus")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ]
        await query.edit_message_text("Выберите ценовой диапазон:", reply_markup=InlineKeyboardMarkup(keyboard))

    else:
        await show_products_list(query, data)

async def show_products_list(query, products):
    await query.message.delete()

    for i, p in enumerate(products):
        caption = f"<b>{p['name']}</b>\n\n💰 Цена: {p['price']}₽"
        keyboard = [[InlineKeyboardButton(f"🛍 Купить {p['name']}", callback_data=f"sel_{i}")]]

        if p.get('photo'):
            try:
                await query.message.chat.send_photo(
                    photo=p['photo'],
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                await query.message.chat.send_message(f"⚠️ Ошибка фото: {caption}", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.message.chat.send_message(caption, reply_markup=InlineKeyboardMarkup(keyboard))

    back_kb = [[InlineKeyboardButton("⬅️ Назад в меню", callback_data="main_menu")]]
    await query.message.chat.send_message("Выберите понравившийся товар выше 👆", reply_markup=InlineKeyboardMarkup(back_kb))

async def subcat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, cat, sub = query.data.split('_', 2)
    products = PRODUCTS[cat][sub]
    await show_products_list(query, products)

async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        idx = int(query.data.replace("sel_", ""))
    except:
        await query.message.reply_text("Ошибка выбора товара. Попробуйте заново.")
        return

    cat = context.user_data.get('current_cat')
    data = PRODUCTS.get(cat)

    if isinstance(data, dict):
        all_products = []
        for sublist in data.values():
            all_products.extend(sublist)
    else:
        all_products = data

    if idx < 0 or idx >= len(all_products):
        await query.message.reply_text("Товар не найден. Попробуйте выбрать заново.")
        return

    product = all_products[idx]

    context.user_data.update({
        'product': product['name'],
        'price': int(product['price']),
        'product_photo': product.get('photo'),
        'state': 'WAIT_QTY'
    })

    await query.message.reply_text(
        f"🍓 Вы выбрали: {product['name']}\n"
        f"💰 Цена: {product['price']}₽\n\n"
        "Сколько штук хотите заказать? Пришлите цифру:"
    )

# ==================== GRACEFUL SHUTDOWN ДЛЯ RENDER ====================
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

    app.add_handler(CallbackQueryHandler(cat_handler, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(subcat_handler, pattern="^sub_"))
    app.add_handler(CallbackQueryHandler(product_selected, pattern="^sel_"))

    app.add_handler(CallbackQueryHandler(delivery_method_handler, pattern="^method_"))
    app.add_handler(CallbackQueryHandler(district_handler, pattern="^district_"))
    app.add_handler(CallbackQueryHandler(time_handler, pattern="^time_"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="^back_"))
    app.add_handler(CallbackQueryHandler(payment_handler, pattern="^pay_"))
    app.add_handler(CallbackQueryHandler(confirm_handler, pattern="^(confirm_order|restart_order|confirm_district)$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.add_handler(CallbackQueryHandler(order_status_handler, pattern="^(paid|accept|ready|sent|done)_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_payment_screenshot))

    app.run_polling()

if __name__ == "__main__":
    main()
