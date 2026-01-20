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
        print(f"Ошибка Google Sheets: {e}")

# ================= ТОВАРЫ ====================
PRODUCTS = {
    "boxes": {
        "0_3000": [{"name": "Бенто-торт из клубники", "price": "2490 ₽", "desc": "8 ягод", "photo": "http://fruttosmile.su/wp-content/uploads/2025/07/photoeditorsdk-export4.png"}],
        "3000_5000": [{"name": "Набор клубники и малины", "price": "2990 ₽", "desc": "7 клубник + малина", "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/malinki-takie-vecerinki.jpg"}],
        "5000_plus": [{"name": "Бокс «Ассорти»", "price": "6990 ₽", "desc": "Шоколад + клубника", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/900-1080-piks.-880-1080-piks.-860-1080-piks.-840-1080-piks.-830-1080-piks.-820-1080-piks.png"}]
    },
    "flowers": [{"name": "Моно букет «Диантусы»", "price": "2690 ₽", "desc": "Моно-букет", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/mono-buket-diantusy.png"}],
    "meat": [{"name": "Букет «Мясной» стандарт", "price": "5990 ₽", "desc": "Вес 2 кг", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-24.jpg"}],
    "sweet": {
        "0_3000": [{"name": "Мандариновое настроение", "price": "2990 ₽", "desc": "12-14 мандарин", "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/nastroenie.jpg"}],
        "3000_5000": [{"name": "Букет «Брутальный зефир»", "price": "3490 ₽", "desc": "Зефир в шоколаде", "photo": "http://fruttosmile.su/wp-content/uploads/2018/01/photoeditorsdk-export86.png"}],
        "5000_plus": [{"name": "Букет «Ягодное ассорти»", "price": "6490 ₽", "desc": "35-40 клубник", "photo": "http://fruttosmile.su/wp-content/uploads/2016/12/photo_2024-04-05_17-55-09.jpg"}]
    }
}

# ================= ОБРАБОТЧИКИ =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📦 Боксы", callback_data="cat_boxes")],
        [InlineKeyboardButton("💐 Свежие букеты", callback_data="cat_flowers")],
        [InlineKeyboardButton("🍖 Мясные букеты", callback_data="cat_meat")],
        [InlineKeyboardButton("🍬 Сладкие букеты", callback_data="cat_sweet")],
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text("Выберите категорию:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("Добро пожаловать в Fruttosmile 💝\nВыберите категорию:", reply_markup=InlineKeyboardMarkup(keyboard))

async def cat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cat_boxes":
        kb = [[InlineKeyboardButton("До 3000", callback_data="sub_box_0_3000")], [InlineKeyboardButton("3000-5000", callback_data="sub_box_3000_5000")], [InlineKeyboardButton("Назад", callback_data="back")]]
        await query.edit_message_text("Цена боксов:", reply_markup=InlineKeyboardMarkup(kb))
    elif query.data == "cat_sweet":
        kb = [[InlineKeyboardButton("До 3000", callback_data="sub_sweet_0_3000")], [InlineKeyboardButton("Назад", callback_data="back")]]
        await query.edit_message_text("Цена сладких букетов:", reply_markup=InlineKeyboardMarkup(kb))
    elif query.data == "cat_flowers":
        for p in PRODUCTS["flowers"]:
            await query.message.reply_photo(p["photo"], caption=f"{p['name']}\n{p['price']}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Выбрать", callback_data=f"sel_{p['name'][:20]}")]]))
    elif query.data == "cat_meat":
        for p in PRODUCTS["meat"]:
            await query.message.reply_photo(p["photo"], caption=f"{p['name']}\n{p['price']}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Выбрать", callback_data=f"sel_{p['name'][:20]}")]]))

async def subcat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_") # sub_box_0_3000
    cat = data[1]
    price_range = "_".join(data[2:])
    
    items = PRODUCTS.get(cat, {}).get(price_range, [])
    for p in items:
        await query.message.reply_photo(p["photo"], caption=f"{p['name']}\n{p['price']}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Выбрать", callback_data=f"sel_{p['name'][:20]}")]]))

async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    p_name = query.data.replace("sel_", "")
    context.user_data['product'] = p_name
    await query.message.reply_text(f"Вы выбрали: {p_name}\nВведите количество:")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'product' not in context.user_data:
        await update.message.reply_text("Начните с команды /start")
        return

    qty = update.message.text
    if not qty.isdigit():
        await update.message.reply_text("Введите число (количество):")
        return

    product = context.user_data['product']
    user = update.effective_user.full_name
    
    if sheet:
        try:
            sheet.append_row([datetime.now().strftime("%d.%m.%Y %H:%M"), product, qty, user])
            await update.message.reply_text(f"✅ Заказ принят!\nТовар: {product}\nКол-во: {qty}\nМы свяжемся с вами!")
        except:
            await update.message.reply_text("Ошибка записи в таблицу, но мы увидели ваш заказ!")
    else:
        await update.message.reply_text(f"Заказ: {product} ({qty} шт.). Таблица не настроена.")
    
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
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
