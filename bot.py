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

# ================= ПОЛНЫЙ КАТАЛОГ ТОВАРОВ ====================
PRODUCTS = {
    "boxes": {
        "0_3000": [
            {"name": "Бенто-торт из клубники", "price": "2490 ₽", "desc": "8 ягод в шоколаде", "photo": "http://fruttosmile.su/wp-content/uploads/2025/07/photoeditorsdk-export4.png"},
            {"name": "Стаканчик с клубникой", "price": "1790 ₽", "desc": "7–9 ягод + декор", "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export69-660x800-1.png"},
            {"name": "Конфеты ручной работы", "price": "1390 ₽", "desc": "Байкал / Дубай / фундук", "photo": "http://fruttosmile.su/wp-content/uploads/2025/04/unnamed-file.jpg"},
            {"name": "Бананы мини", "price": "1390 ₽", "desc": "8 шт на палочках", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/banany-11.jpg"},
            {"name": "Бананы с орехами", "price": "1990 ₽", "desc": "22–25 шт", "photo": "http://fruttosmile.su/wp-content/uploads/2014/08/jguy.png"},
            {"name": "Клубника 12 ягод", "price": "2590 ₽", "desc": "В бельгийском шоколаде", "photo": "http://fruttosmile.su/wp-content/uploads/2014/03/photo_5449855732875908292_y.jpg"},
            {"name": "Круглая коробка микс", "price": "2290 ₽", "desc": "Бананы и клубника", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/kruglaya-korobka-banany-i-klubnika-v-shokolade.jpg"},
            {"name": "Сердечко клубника+бананы", "price": "2490 ₽", "desc": "Мини-сердце", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/serdechko-klubnika-i-banany-v-shokolade.png"},
        ],
        "3000_5000": [
            {"name": "Новогоднее сердце", "price": "3490 ₽", "desc": "С голубикой и декором", "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png"},
            {"name": "Набор клубники и малины", "price": "2990 ₽", "desc": "7 клубник + 8–10 малины", "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/malinki-takie-vecerinki.jpg"},
            {"name": "Набор с финиками", "price": "2390 ₽", "desc": "С орехами в шоколаде", "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/ceresenki.jpg"},
        ],
        "5000_plus": [
            {"name": "Бокс «Ассорти»", "price": "6990 ₽", "desc": "Шоколад + клубника + орехи", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/900-1080-piks.-880-1080-piks.-860-1080-piks.-840-1080-piks.-830-1080-piks.-820-1080-piks.png"},
        ]
    },
    "flowers": [
        {"name": "Моно букет «Диантусы»", "price": "2690 ₽", "desc": "Нежные гвоздики", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/mono-buket-diantusy.png"},
        {"name": "Букет из гипсофилы", "price": "3290 ₽", "desc": "В шляпной коробке", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photoeditorsdk_export_12__481x582.png"},
        {"name": "Букет из роз и эустомы", "price": "3490 ₽", "desc": "Романтичный микс", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-roz-i-eustomy.jpg"},
        {"name": "Букет «Облако»", "price": "3500 ₽", "desc": "Белые хризантемы", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-hrizantem-oblako.png"},
        {"name": "Букет «Яркое настроение»", "price": "3990 ₽", "desc": "Цветочный микс", "photo": "http://fruttosmile.su/wp-content/uploads/2024/09/photoeditorsdk-export39.png"},
        {"name": "Букет «Первый снег»", "price": "11490 ₽", "desc": "Премиум букет", "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/r1w7h3k2q2e1vg1badull79xa3ttaryb.jpg"},
    ],
    "meat": [
        {"name": "Мясной стандарт", "price": "5990 ₽", "desc": "Вес ~2 кг", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-24.jpg"},
        {"name": "Мясной VIP", "price": "7990 ₽", "desc": "Вес ~3 кг", "photo": "http://fruttosmile.su/wp-content/uploads/2016/08/photo_2024-04-05_17-41-51-660x800.jpg"},
        {"name": "Букет из раков", "price": "6990 ₽", "desc": "От 1 кг свежих раков", "photo": "http://fruttosmile.su/wp-content/uploads/2018/08/photo_2022-12-09_18-05-41.jpg"},
        {"name": "Креветки и краб", "price": "9990 ₽", "desc": "Деликатесный набор", "photo": "http://fruttosmile.su/wp-content/uploads/2018/08/photo_2022-12-09_18-05-36-2.jpg"},
    ],
    "sweet": {
        "0_3000": [
            {"name": "Зефирный букет", "price": "2990 ₽", "desc": "Воздушный зефир", "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/photoeditorsdk-export192.png"},
            {"name": "Мандариновое настроение", "price": "2990 ₽", "desc": "Свежие мандарины", "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/nastroenie.jpg"},
        ],
        "3000_5000": [
            {"name": "Брутальный зефир", "price": "3490 ₽", "desc": "С золотым декором", "photo": "http://fruttosmile.su/wp-content/uploads/2018/01/photoeditorsdk-export86.png"},
            {"name": "Букет клубничный S", "price": "3990 ₽", "desc": "20–25 ягод", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-klubnichnyj-s-azhurnyj-1.jpg"},
        ],
        "5000_plus": [
            {"name": "Ягодное ассорти", "price": "6490 ₽", "desc": "35–40 ягод", "photo": "http://fruttosmile.su/wp-content/uploads/2016/12/photo_2024-04-05_17-55-09.jpg"},
        ]
    }
}

# ================= ЛОГИКА ОПРОСА =================

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
    
    if query.data in ["cat_boxes", "cat_sweet"]:
        cat_key = query.data.replace("cat_", "")
        kb = [
            [InlineKeyboardButton("До 3000", callback_data=f"sub_{cat_key}_0_3000")],
            [InlineKeyboardButton("3000-5000", callback_data=f"sub_{cat_key}_3000_5000")],
            [InlineKeyboardButton("5000+", callback_data=f"sub_{cat_key}_5000_plus")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
        ]
        await query.edit_message_text("Выберите ценовой диапазон:", reply_markup=InlineKeyboardMarkup(kb))
    else:
        cat_key = query.data.replace("cat_", "")
        for p in PRODUCTS.get(cat_key, []):
            kb = [[InlineKeyboardButton("🛍 Выбрать этот товар", callback_data=f"sel_{p['name'][:20]}")]]
            await query.message.reply_photo(p["photo"], caption=f"✨ {p['name']}\n💰 Цена: {p['price']}\n📝 {p['desc']}", reply_markup=InlineKeyboardMarkup(kb))

async def subcat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    items = PRODUCTS.get(data[1], {}).get("_".join(data[2:]), [])
    for p in items:
        kb = [[InlineKeyboardButton("🛍 Выбрать этот товар", callback_data=f"sel_{p['name'][:20]}")]]
        await query.message.reply_photo(p["photo"], caption=f"✨ {p['name']}\n💰 Цена: {p['price']}\n📝 {p['desc']}", reply_markup=InlineKeyboardMarkup(kb))

async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['product'] = query.data.replace("sel_", "")
    context.user_data['state'] = 'WAIT_QTY'
    await query.message.reply_text(f"✅ Вы выбрали: {context.user_data['product']}\n\n1️⃣ Укажите нужное количество (только цифры):")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    text = update.message.text

    if state == 'WAIT_QTY':
        if not text.isdigit():
            await update.message.reply_text("❌ Пожалуйста, введите количество цифрами:")
            return
        context.user_data['qty'] = text
        context.user_data['state'] = 'WAIT_NAME'
        await update.message.reply_text("2️⃣ Как вас зовут? (Имя)")

    elif state == 'WAIT_NAME':
        context.user_data['name'] = text
        context.user_data['state'] = 'WAIT_PHONE'
        await update.message.reply_text("3️⃣ Введите ваш номер телефона для связи:")

    elif state == 'WAIT_PHONE':
        context.user_data['phone'] = text
        context.user_data['state'] = 'WAIT_ADDRESS'
        await update.message.reply_text("4️⃣ Укажите адрес доставки:")

    elif state == 'WAIT_ADDRESS':
        context.user_data['address'] = text
        await finish_order(update, context)

async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data
    summary = (
        f"🔔 НОВЫЙ ЗАКАЗ!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📦 Товар: {d['product']}\n"
        f"🔢 Кол-во: {d['qty']}\n"
        f"👤 Клиент: {d['name']}\n"
        f"📞 Телефон: {d['phone']}\n"
        f"🏠 Адрес: {d['address']}\n"
        f"━━━━━━━━━━━━━━━"
    )

    # 1. Уведомление вам
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary)
    except Exception as e:
        logging.error(f"Ошибка уведомления: {e}")

    # 2. Запись в таблицу
    if sheet:
        try:
            sheet.append_row([datetime.now().strftime("%d.%m.%Y %H:%M"), d['product'], d['qty'], d['name'], d['phone'], d['address']])
        except:
            pass

    await update.message.reply_text("🎉 Заказ успешно оформлен! Мы свяжемся с вами в ближайшее время для подтверждения. Спасибо, что выбрали Fruttosmile! ❤️")
    context.user_data.clear()

# ================= ЗАПУСК =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(cat_handler, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(subcat_handler, pattern="^sub_"))
    app.add_handler(CallbackQueryHandler(product_selected, pattern="^sel_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
