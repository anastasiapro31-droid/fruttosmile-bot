import logging
import os
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "8539880271:AAH_ViAH5n3MdnATanMMDaoETHl2WGLYmn4"
ADMIN_CHAT_ID = 1165444045 
SPREADSHEET_NAME = "Заказы Fruttosmile"
SHEET_NAME = "Лист1"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= GOOGLE TABLES =================
GOOGLE_KEY_JSON = os.getenv("GOOGLE_KEY_JSON")
sheet = None
if GOOGLE_KEY_JSON:
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = json.loads(GOOGLE_KEY_JSON)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        gc = gspread.authorize(creds)
        sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)
    except Exception as e:
        logging.error(f"Ошибка Google Sheets: {e}")

# ================= ПОЛНЫЙ КАТАЛОГ ТОВАРОВ =================
PRODUCTS = {
    "boxes": {
        "0_3000": [
            {"name": "Бенто-торт из клубники", "price": "2490 ₽", "photo": "http://fruttosmile.su/wp-content/uploads/2025/07/photoeditorsdk-export4.png"},
            {"name": "Стаканчик с клубникой", "price": "1790 ₽", "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export69-660x800-1.png"},
            {"name": "Набор с финиками", "price": "2390 ₽", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-11-20_12-25-34.jpg"}
        ],
        "3000_5000": [
            {"name": "Набор клубники и малины", "price": "2990 ₽", "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/malinki-takie-vecerinki.jpg"},
            {"name": "Ягодное ассорти", "price": "3490 ₽", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/yagodnoe-assorti.jpg"}
        ],
        "5000_plus": [
            {"name": "Бокс «Ассорти»", "price": "6990 ₽", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/900-1080-piks.-880-1080-piks.-860-1080-piks.-840-1080-piks.-830-1080-piks.-820-1080-piks.png"}
        ]
    },
    "flowers": [
        {"name": "Моно букет «Диантусы»", "price": "2690 ₽", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/mono-buket-diantusy.png"},
        {"name": "Букет «Розовая нежность»", "price": "3490 ₽", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-roz-i-eustomy.jpg"},
        {"name": "Букет «Яркое настроение»", "price": "4290 ₽", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/yarkoe-nastroenie.jpg"}
    ],
    "meat": [
        {"name": "Мясной стандарт", "price": "5990 ₽", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-24.jpg"},
        {"name": "Мясной Гигант", "price": "8500 ₽", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-25.jpg"}
    ],
    "sweet": {
        "0_3000": [
            {"name": "Мандариновое настроение", "price": "2990 ₽", "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/nastroenie.jpg"}
        ]
    }
}

# ================= ЛОГИКА =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("📦 Боксы", callback_data="cat_boxes")],
        [InlineKeyboardButton("💐 Свежие букеты", callback_data="cat_flowers")],
        [InlineKeyboardButton("🍖 Мясные букеты", callback_data="cat_meat")],
        [InlineKeyboardButton("🍬 Сладкие букеты", callback_data="cat_sweet")],
    ]
    text = "Добро пожаловать в Fruttosmile 💝\nВыберите категорию:"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def cat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data.replace("cat_", "")
    if cat in ["boxes", "sweet"]:
        kb = [[InlineKeyboardButton("До 3000", callback_data=f"sub_{cat}_0_3000")],
              [InlineKeyboardButton("3000-5000", callback_data=f"sub_{cat}_3000_5000")],
              [InlineKeyboardButton("5000+", callback_data=f"sub_{cat}_5000_plus")],
              [InlineKeyboardButton("⬅️ Назад", callback_data="back")]]
        await query.edit_message_text("Выберите бюджет:", reply_markup=InlineKeyboardMarkup(kb))
    else:
        for p in PRODUCTS.get(cat, []):
            kb = [[InlineKeyboardButton("🛍 Выбрать этот товар", callback_data=f"sel_{p['name'][:20]}")]]
            await query.message.reply_photo(p["photo"], caption=f"{p['name']}\nЦена: {p['price']}", reply_markup=InlineKeyboardMarkup(kb))

async def subcat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    items = PRODUCTS.get(data[1], {}).get("_".join(data[2:]), [])
    for p in items:
        kb = [[InlineKeyboardButton("🛍 Выбрать этот товар", callback_data=f"sel_{p['name'][:20]}")]]
        await query.message.reply_photo(p["photo"], caption=f"{p['name']}\nЦена: {p['price']}", reply_markup=InlineKeyboardMarkup(kb))

async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    p_name = query.data.replace("sel_", "")
    context.user_data['product'] = p_name
    # Ищем фото для админа
    for cat in PRODUCTS.values():
        items = cat if isinstance(cat, list) else [i for sub in cat.values() for i in sub]
        for p in items:
            if p['name'].startswith(p_name):
                context.user_data['product_photo'] = p['photo']
                break
    context.user_data['state'] = 'WAIT_QTY'
    await query.message.reply_text(f"✅ Вы выбрали: {p_name}\n\n1️⃣ Укажите нужное количество (только цифры):")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'state' not in context.user_data: return
    state = context.user_data.get('state')
    text = update.message.text
    if state == 'WAIT_QTY':
        context.user_data['qty'] = text
        context.user_data['state'] = 'WAIT_NAME'
        await update.message.reply_text("2️⃣ Как вас зовут? (Имя)")
    elif state == 'WAIT_NAME':
        context.user_data['name'] = text
        context.user_data['state'] = 'WAIT_PHONE'
        await update.message.reply_text("3️⃣ Введите ваш номер телефона для связи:")
    elif state == 'WAIT_PHONE':
        context.user_data['phone'] = text
        context.user_data['state'] = 'WAIT_METHOD'
        kb = [[InlineKeyboardButton("🚚 Доставка", callback_data="method_delivery"), 
               InlineKeyboardButton("🏠 Самовывоз", callback_data="method_pickup")]]
        await update.message.reply_text("4️⃣ Выберите способ получения:", reply_markup=InlineKeyboardMarkup(kb))
    elif state == 'WAIT_ADDRESS':
        context.user_data['address'] = text
        context.user_data['state'] = 'WAIT_DATE'
        await update.message.reply_text("5️⃣ Укажите желаемую дату и время доставки:")
    elif state == 'WAIT_DATE':
        context.user_data['delivery_time'] = text
        context.user_data['state'] = 'WAIT_COMMENT'
        await update.message.reply_text("6️⃣ Напишите пожелания по оформлению или текст для открытки:")
    elif state == 'WAIT_COMMENT':
        context.user_data['comment'] = text
        await finish_order(update, context)

async def delivery_method_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "method_delivery":
        context.user_data['method'] = "Доставка"
        context.user_data['state'] = 'WAIT_ADDRESS'
        await query.edit_message_text("📍 Укажите адрес доставки:")
    else:
        context.user_data['method'] = "Самовывоз"
        context.user_data['address'] = "— (Самовывоз)"
        context.user_data['state'] = 'WAIT_DATE'
        await query.edit_message_text("🏠 Выбран самовывоз.\n5️⃣ Укажите дату и время, когда планируете забрать заказ:")

async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data
    summary = (
        f"🔔 НОВЫЙ ЗАКАЗ!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📦 Товар: {d.get('product')}\n"
        f"🔢 Кол-во: {d.get('qty')}\n"
        f"👤 Клиент: {d.get('name')}\n"
        f"📞 Тел: {d.get('phone')}\n"
        f"🚛 Способ: {d.get('method')}\n"
        f"🏠 Адрес: {d.get('address')}\n"
        f"⏰ Время: {d.get('delivery_time')}\n"
        f"💬 Коммент: {d.get('comment')}\n"
        f"━━━━━━━━━━━━━━━"
    )
    try:
        if d.get('product_photo'):
            await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=d.get('product_photo'), caption=summary)
        else:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary)
    except Exception as e:
        logging.error(f"Ошибка уведомления админа: {e}")
    if sheet:
        try:
            sheet.append_row([datetime.now().strftime("%d.%m.%Y %H:%M"), d.get('product'), d.get('qty'), d.get('name'), d.get('phone'), d.get('method'), d.get('address'), d.get('delivery_time'), d.get('comment')])
        except: pass
    payment_text = (
        "Порядок оплаты:\n"
        "• Сохраните картинку с QR.\n"
        "• В приложении банка: Платежи → Сканировать QR → загрузите картинку и внесите сумму.\n\n"
        "Также можно воспользоваться [ссылкой на QR](https://qr.nspk.ru/BS1A0054EC7LHJ358M29KSAKOJJ638N1?type=01&bank=100000000284&crc=F07F), чтобы сразу перейти к оплате. ☺️\n\n"
        "После оплаты отправьте, пожалуйста, чек или скриншот. 😇🫶"
    )
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(payment_text, parse_mode='Markdown')
    context.user_data.clear()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(cat_handler, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(subcat_handler, pattern="^sub_"))
    app.add_handler(CallbackQueryHandler(product_selected, pattern="^sel_"))
    app.add_handler(CallbackQueryHandler(delivery_method_handler, pattern="^method_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
