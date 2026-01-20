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

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ================= GOOGLE TABLES =================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

GOOGLE_KEY_JSON = os.getenv("GOOGLE_KEY_JSON")

if GOOGLE_KEY_JSON is None or GOOGLE_KEY_JSON.strip() == "":
    # Если вы запускаете локально для теста, можно временно заменить на путь к файлу
    # Но для Render переменная GOOGLE_KEY_JSON обязательна
    print("ВНИМАНИЕ: GOOGLE_KEY_JSON не найдена. Бот может не записать данные в таблицу.")
    sheet = None
else:
    try:
        creds_dict = json.loads(GOOGLE_KEY_JSON)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        gc = gspread.authorize(creds)
        sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)
    except Exception as e:
        print(f"Ошибка подключения к Google Sheets: {e}")
        sheet = None

# ================= ТОВАРЫ ====================
PRODUCTS = {
    "boxes": {
        "0_3000": [
            {"name": "Бенто-торт из клубники", "price": "2490 ₽", "desc": "8 ягод в шоколаде", "photo": "http://fruttosmile.su/wp-content/uploads/2025/07/photoeditorsdk-export4.png", "variants": None},
            {"name": "Стаканчик с клубникой", "price": "1790 ₽", "desc": "7–9 ягод + декор", "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export69-660x800-1.png", "variants": None},
            {"name": "Конфеты ручной работы", "price": "1390 ₽", "desc": "Байкал / Дубай / фундук", "photo": "http://fruttosmile.su/wp-content/uploads/2025/04/unnamed-file.jpg", "variants": None},
            {"name": "Бананы мини", "price": "1390 ₽", "desc": "8 шт на палочках", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/banany-11.jpg", "variants": None},
            {"name": "Бананы с орехами", "price": "1990 ₽", "desc": "22–25 шт", "photo": "http://fruttosmile.su/wp-content/uploads/2014/08/jguy.png", "variants": None},
            {"name": "Клубника 12 ягод", "price": "2590 ₽", "desc": "В бельгийском шоколаде", "photo": "http://fruttosmile.su/wp-content/uploads/2014/03/photo_5449855732875908292_y.jpg", "variants": None},
            {"name": "Круглая коробка бананы+клубника", "price": "2290 ₽", "desc": "Микс в коробке", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/kruglaya-korobka-banany-i-klubnika-v-shokolade.jpg", "variants": None},
            {"name": "Сердечко клубника+бананы", "price": "2490 ₽", "desc": "Мини-сердце", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/serdechko-klubnika-i-banany-v-shokolade.png", "variants": None},
        ],
        "3000_5000": [
            {"name": "Новогоднее сердце с клубникой", "price": "от 3490 ₽", "desc": "С голубикой и декором", "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png", "variants": [("Малое — 3490", "3490"), ("Среднее — 4490", "4490"), ("Большое — 5490", "5490")]},
            {"name": "Набор клубники и малины", "price": "2990 ₽", "desc": "7 клубник + 8–10 малины", "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/malinki-takie-vecerinki.jpg", "variants": None},
            {"name": "Набор с финиками и черешней/малиной", "price": "от 2390 ₽", "desc": "С орехами в шоколаде", "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/ceresenki.jpg", "variants": [("С черешней — 2390", "2390"), ("С малиной — 2990", "2990")]},
        ],
        "5000_plus": [
            {"name": "Бокс «Ассорти»", "price": "6990 ₽", "desc": "Шоколад + клубника + орехи", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/900-1080-piks.-880-1080-piks.-860-1080-piks.-840-1080-piks.-830-1080-piks.-820-1080-piks.png", "variants": None},
        ]
    },
    "flowers": [
        {"name": "Моно букет «Диантусы»", "price": "2690 ₽", "desc": "Моно-букет", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/mono-buket-diantusy.png", "variants": None},
        {"name": "Букет из гипсофилы в шляпной коробке", "price": "3290 ₽", "desc": "Воздушная гипсофила", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photoeditorsdk_export_12__481x582.png", "variants": None},
        {"name": "Букет из роз и эустомы", "price": "3490 ₽", "desc": "Розы + эустома", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-roz-i-eustomy.jpg", "variants": None},
        {"name": "Букет из хризантем «Облако»", "price": "3500 ₽", "desc": "Пушистые хризантемы", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-hrizantem-oblako.png", "variants": None},
        {"name": "Букет «Альстромерия»", "price": "3990 ₽", "desc": "11 весенних альстромерий", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-alstromeriya.jpg", "variants": None},
        {"name": "Букет «Яркое настроение»", "price": "3990 ₽", "desc": "Яркий букет", "photo": "http://fruttosmile.su/wp-content/uploads/2024/09/photoeditorsdk-export39.png", "variants": None},
        {"name": "Букет из нежнейшей эустомы", "price": "3990 ₽", "desc": "Нежная эустома", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-nezhnejshej-eustomy.jpg", "variants": None},
        {"name": "Букет Микс", "price": "4000 ₽", "desc": "Микс цветов", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-miks.png", "variants": None},
        {"name": "Букет «Зефирка»", "price": "4490 ₽", "desc": "Воздушный букет", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photoeditorsdk_export_37__481x582.png", "variants": None},
        {"name": "Букет «Розовая нежность»", "price": "5490 ₽", "desc": "Розовые тона", "photo": "http://fruttosmile.su/wp-content/uploads/2024/09/photoeditorsdk-export40.png", "variants": None},
        {"name": "Букет из роз «Танец страсти»", "price": "5490 ₽", "desc": "Красные розы", "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/img_3182-0x800.jpg", "variants": None},
        {"name": "Моно букет из кустовой розочки", "price": "5990 ₽", "desc": "Нежные кустовые розы", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/mono-buket-iz-nezhnoj-kustovoj-rozochki.png", "variants": None},
        {"name": "Букет «Первый снег»", "price": "11490 ₽", "desc": "Зимний роскошный букет", "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/r1w7h3k2q2e1vg1badull79xa3ttaryb.jpg", "variants": None},
    ],
    "meat": [
        {"name": "Букет «Мясной» стандарт", "price": "5990 ₽", "desc": "Мини 1,5 кг / Стандарт 2–2,1 кг", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-24.jpg", "variants": None},
        {"name": "Букет «Мясной» VIP", "price": "7990 ₽", "desc": "Вес ~3 кг", "photo": "http://fruttosmile.su/wp-content/uploads/2016/08/photo_2024-04-05_17-41-51-660x800.jpg", "variants": None},
        {"name": "Букет из раков", "price": "от 6990 ₽", "desc": "1 кг — 6990 / 2 кг — 10990", "photo": "http://fruttosmile.su/wp-content/uploads/2018/08/photo_2022-12-09_18-05-41.jpg", "variants": [("1 кг — 6990", "6990"), ("2 кг — 10990", "10990")]},
        {"name": "Букет из креветок и краба", "price": "9990 ₽", "desc": "Королевские креветки + клешни краба", "photo": "http://fruttosmile.su/wp-content/uploads/2018/08/photo_2022-12-09_18-05-36-2.jpg", "variants": None},
    ],
    "sweet": {
        "0_3000": [
            {"name": "Букет из сладостей «Зефирный»", "price": "2990 ₽", "desc": "Зефирный букет", "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/photoeditorsdk-export192.png", "variants": None},
            {"name": "Букет Мандариновое настроение", "price": "2990 ₽", "desc": "12–14 мандарин + декор", "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/nastroenie.jpg", "variants": None},
        ],
        "3000_5000": [
            {"name": "Букет «Брутальный зефир»", "price": "3490 ₽", "desc": "Шоколадные оттенки + золотое напыление", "photo": "http://fruttosmile.su/wp-content/uploads/2018/01/photoeditorsdk-export86.png", "variants": None},
            {"name": "Букет из цельных фруктов «С любовью»", "price": "3990 ₽", "desc": "Цельные фрукты", "photo": "http://fruttosmile.su/wp-content/uploads/2016/04/photo_2022-12-09_15-56-56.jpg", "variants": None},
            {"name": "Букет клубничный S Ажурный", "price": "3990 ₽", "desc": "20–25 ягод", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-klubnichnyj-s-azhurnyj-1.jpg", "variants": [("Малый", "3990"), ("Средний", "4990"), ("Большой", "5990")]},
            {"name": "Букет из фруктов «Алая роскошь»", "price": "4990 ₽", "desc": "Фрукты + цветы", "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/photoeditorsdk-export203-660x800.png", "variants": None},
            {"name": "Букет клубничный M Ажурный", "price": "4990 ₽", "desc": "30–35 ягод", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photo_2024_08_11_18_53_18_481x582.jpg", "variants": None},
            {"name": "Букет клубничный «С росписью»", "price": "4490 ₽", "desc": "35–40 ягод", "photo": "http://fruttosmile.su/wp-content/uploads/2016/07/photo_2024-04-05_17-37-48.jpg", "variants": None},
        ],
        "5000_plus": [
            {"name": "Букет «Ягодное ассорти»", "price": "6490 ₽", "desc": "35–40 клубник + другие ягоды", "photo": "http://fruttosmile.su/wp-content/uploads/2016/12/photo_2024-04-05_17-55-09.jpg", "variants": None},
            {"name": "Букет в шляпной коробке с макаронсами", "price": "6990 ₽", "desc": "С макаронсами", "photo": "http://fruttosmile.su/wp-content/uploads/2017/04/photo_2024-08-08_15-59-41.jpg", "variants": None},
            {"name": "Букет клубничный с хризантемами", "price": "6990 ₽", "desc": "Хризантемы + 0,8–0,9 кг клубники", "photo": "http://fruttosmile.su/wp-content/uploads/2016/07/photoeditorsdk-export213.png", "variants": None},
            {"name": "Букет «Клубничная принцесса»", "price": "от 6990 ₽", "desc": "Ягоды + цветы", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photoeditorsdk-export135.png", "variants": [("Малый — 6990", "6990"), ("Средний — 7990", "7990"), ("Большой — 9990", "9990")]},
        ]
    }
}

# ================= ВСЕ ОБРАБОТЧИКИ (HANDLERS) =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📦 Боксы", callback_data="cat_boxes")],
        [InlineKeyboardButton("💐 Свежие букеты", callback_data="cat_flowers")],
        [InlineKeyboardButton("🍖 Мясные букеты", callback_data="cat_meat")],
        [InlineKeyboardButton("🍬 Сладкие букеты", callback_data="cat_sweet")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text("Выберите категорию:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Добро пожаловать в Fruttosmile 💝\nВыберите категорию:", reply_markup=reply_markup)

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def boxes_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("До 3000 ₽", callback_data="box_0_3000")],
        [InlineKeyboardButton("3000–5000 ₽", callback_data="box_3000_5000")],
        [InlineKeyboardButton("5000+ ₽", callback_data="box_5000_plus")],
        [InlineKeyboardButton("← Назад", callback_data="back_main")],
    ]
    await query.edit_message_text("Выберите ценовую категорию боксов:", reply_markup=InlineKeyboardMarkup(keyboard))

async def boxes_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("box_", "")
    products = PRODUCTS["boxes"].get(key, [])
    for p in products:
        kb = [[InlineKeyboardButton("Выбрать", callback_data=f"select_{p['name'][:30]}")]]
        await query.message.reply_photo(photo=p["photo"], caption=f"🎁 {p['name']}\n{p['price']}\n\n{p['desc']}", reply_markup=InlineKeyboardMarkup(kb))
    await query.message.reply_text("Вернуться:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="cat_boxes")]]))

async def flowers_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    for p in PRODUCTS["flowers"]:
        kb = [[InlineKeyboardButton("Выбрать", callback_data=f"select_{p['name'][:30]}")]]
        await query.message.reply_photo(photo=p["photo"], caption=f"💐 {p['name']}\n{p['price']}\n\n{p['desc']}", reply_markup=InlineKeyboardMarkup(kb))
    await query.message.reply_text("Вернуться:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="back_main")]]))

async def meat_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    for p in PRODUCTS["meat"]:
        kb = [[InlineKeyboardButton("Выбрать", callback_data=f"select_{p['name'][:30]}")]]
        await query.message.reply_photo(photo=p["photo"], caption=f"🍖 {p['name']}\n{p['price']}\n\n{p['desc']}", reply_markup=InlineKeyboardMarkup(kb))
    await query.message.reply_text("Вернуться:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="back_main")]]))

async def sweet_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("До 3000 ₽", callback_data="sweet_0_3000")],
        [InlineKeyboardButton("3000–5000 ₽", callback_data="sweet_3000_5000")],
        [InlineKeyboardButton("5000+ ₽", callback_data="sweet_5000_plus")],
        [InlineKeyboardButton("← Назад", callback_data="back_main")],
    ]
    await query.edit_message_text("Выберите категорию сладких букетов:", reply_markup=InlineKeyboardMarkup(keyboard))

async def sweet_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("sweet_", "")
    products = PRODUCTS["sweet"].get(key, [])
    for p in products:
        kb = [[InlineKeyboardButton("Выбрать", callback_data=f"select_{p['name'][:30]}")]]
        await query.message.reply_photo(photo=p["photo"], caption=f"🍬 {p['name']}\n{p['price']}\n\n{p['desc']}", reply_markup=InlineKeyboardMarkup(kb))
    await query.message.reply_text("Вернуться:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="cat_sweet")]]))

async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_name = query.data.replace("select_", "")
    context.user_data['product'] = product_name
    context.user_data['step'] = 'qty'
    await query.message.reply_text(f"Вы выбрали: {product_name}\nВведите количество:")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'product' not in context.user_data:
        await update.message.reply_text("Что-то пошло не так. Начните заказ заново: /start")
        return

    step = context.user_data.get("step", "qty")
    if step == "qty":
        text = update.message.text.strip()
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text("Введите число (количество):")
            return
        
        context.user_data["qty"] = int(text)
        product = context.user_data.get('product')
        qty = context.user_data.get('qty')
        
        # Попытка записи в таблицу
        if sheet:
            try:
                sheet.append_row([datetime.now().strftime("%d.%m.%Y %H:%M"), product, "", qty, update.effective_user.full_name, "", ""])
                await update.message.reply_text(f"✅ Заказ принят!\nТовар: {product}\nКоличество: {qty}\nМы свяжемся с вами ❤️")
            except Exception as e:
                logging.error(f"Таблица ошибка: {e}")
                await update.message.reply_text("Заказ принят, но не записан в таблицу (ошибка сервера).")
        else:
            await update.message.reply_text(f"Заказ принят локально (Таблица не подключена).\nТовар: {product}, Кол-во: {qty}")
        
        context.user_data.clear()

# ================= MAIN (ЗАПУСК) =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(go_back, pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(boxes_category, pattern="^cat_boxes$"))
    app.add_handler(CallbackQueryHandler(boxes_price, pattern="^box_"))
    app.add_handler(CallbackQueryHandler(flowers_category, pattern="^cat_flowers$"))
    app.add_handler(CallbackQueryHandler(meat_category, pattern="^cat_meat$"))
    app.add_handler(CallbackQueryHandler(sweet_category, pattern="^cat_sweet$"))
    app.add_handler(CallbackQueryHandler(sweet_price, pattern="^sweet_"))
    app.add_handler(CallbackQueryHandler(product_selected, pattern="^select_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
