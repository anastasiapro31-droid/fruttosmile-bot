import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "8539880271:AAH_ViAH5n3MdnATanMMDaoETHl2WGLYmn4"  # ← здесь твой токен от BotFather
ADMIN_CHAT_ID = 1165444045  # ← твой Telegram ID

SPREADSHEET_NAME = "Заказы Fruttosmile"
SHEET_NAME = "Лист1"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("fruttosmile_key.json", scope)
gc = gspread.authorize(creds)
sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

logging.basicConfig(level=logging.INFO)

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
            # добавь сюда остальные товары до 3000 ₽
        ],
        "3000_5000": [
            {"name": "Новогоднее сердце с клубникой", "price": "от 3490 ₽", "desc": "С голубикой и декором", "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png", "variants": [("Малое — 3490", "3490"), ("Среднее — 4490", "4490"), ("Большое — 5490", "5490")]},
            {"name": "Набор клубники и малины", "price": "2990 ₽", "desc": "7 клубник + 8–10 малины", "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/malinki-takie-vecerinki.jpg", "variants": None},
            {"name": "Набор с финиками и черешней/малиной", "price": "от 2390 ₽", "desc": "С орехами в шоколаде", "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/ceresenki.jpg", "variants": [("С черешней — 2390", "2390"), ("С малиной — 2990", "2990")]},
            # добавь сюда остальные товары 3000–5000 ₽
        ],
        "5000_plus": [
            {"name": "Бокс «Ассорти»", "price": "6990 ₽", "desc": "Шоколад + клубника + орехи", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/900-1080-piks.-880-1080-piks.-860-1080-piks.-840-1080-piks.-830-1080-piks.-820-1080-piks.png", "variants": None},
            # добавь сюда остальные товары от 5000 ₽
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
            # Добавь сюда остальные товары от 5000 ₽
        ]
    }
}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📦 Боксы", callback_data="cat_boxes")],
        [InlineKeyboardButton("💐 Свежие букеты", callback_data="cat_flowers")],
        [InlineKeyboardButton("🍖 Мясные букеты", callback_data="cat_meat")],
        [InlineKeyboardButton("🍬 Сладкие букеты", callback_data="cat_sweet")],
    ]
    await update.message.reply_text(
        "Добро пожаловать в Fruttosmile 💝\nВыберите категорию:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= НАЗАД =================
async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("📦 Боксы", callback_data="cat_boxes")],
        [InlineKeyboardButton("💐 Свежие букеты", callback_data="cat_flowers")],
        [InlineKeyboardButton("🍖 Мясные букеты", callback_data="cat_meat")],
        [InlineKeyboardButton("🍬 Сладкие букеты", callback_data="cat_sweet")],
    ]
    await query.edit_message_text(
        "Вернулись назад. Выберите категорию:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= БОКСЫ =================
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

    key = query.data.split("_", 1)[1]
    context.user_data["box_key"] = key

    products = PRODUCTS["boxes"][key]
    print(f"Боксы {key}: {len(products)} товаров")

    for product in products:
        keyboard = [[InlineKeyboardButton("Выбрать", callback_data=f"select_box_{id(product)}")]]
        await query.message.reply_photo(
            photo=product["photo"],
            caption=f"🎁 {product['name']}\n{product['price']}\n\n{product['desc']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    keyboard_back = [[InlineKeyboardButton("← Назад в категории", callback_data="cat_boxes")]]
    await query.message.reply_text("Вернуться:", reply_markup=InlineKeyboardMarkup(keyboard_back))

# ================= СВЕЖИЕ БУКЕТЫ =================
async def flowers_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    products = PRODUCTS["flowers"]
    print(f"Свежие букеты: {len(products)} товаров")

    for product in products:
        keyboard = [[InlineKeyboardButton("Выбрать", callback_data=f"select_flower_{id(product)}")]]
        await query.message.reply_photo(
            photo=product["photo"],
            caption=f"💐 {product['name']}\n{product['price']}\n\n{product['desc']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    keyboard_back = [[InlineKeyboardButton("← Назад в меню", callback_data="back_main")]]
    await query.message.reply_text("Вернуться:", reply_markup=InlineKeyboardMarkup(keyboard_back))

# ================= МЯСНЫЕ БУКЕТЫ =================
async def meat_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    products = PRODUCTS["meat"]
    print(f"Мясные букеты: {len(products)} товаров")

    for product in products:
        keyboard = [[InlineKeyboardButton("Выбрать", callback_data=f"select_meat_{id(product)}")]]
        await query.message.reply_photo(
            photo=product["photo"],
            caption=f"🍖 {product['name']}\n{product['price']}\n\n{product['desc']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    keyboard_back = [[InlineKeyboardButton("← Назад в меню", callback_data="back_main")]]
    await query.message.reply_text("Вернуться:", reply_markup=InlineKeyboardMarkup(keyboard_back))

# ================= СЛАДКИЕ БУКЕТЫ =================
async def sweet_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("До 3000 ₽", callback_data="sweet_0_3000")],
        [InlineKeyboardButton("3000–5000 ₽", callback_data="sweet_3000_5000")],
        [InlineKeyboardButton("5000+ ₽", callback_data="sweet_5000_plus")],
        [InlineKeyboardButton("← Назад", callback_data="back_main")],
    ]
    await query.edit_message_text("Выберите ценовую категорию сладких букетов:", reply_markup=InlineKeyboardMarkup(keyboard))

async def sweet_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    key = query.data.split("_", 1)[1]
    context.user_data["sweet_key"] = key

    products = PRODUCTS["sweet"][key]
    print(f"Сладкие букеты {key}: {len(products)} товаров")

    for product in products:
        keyboard = [[InlineKeyboardButton("Выбрать", callback_data=f"select_sweet_{id(product)}")]]
        await query.message.reply_photo(
            photo=product["photo"],
            caption=f"🍬 {product['name']}\n{product['price']}\n\n{product['desc']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    keyboard_back = [[InlineKeyboardButton("← Назад в категории", callback_data="cat_sweet")]]
    await query.message.reply_text("Вернуться:", reply_markup=InlineKeyboardMarkup(keyboard_back))

# ================= ВЫБОР ТОВАРА =================
async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("select_"):
        # Здесь можно сохранять выбранный товар в user_data
        # Пока просто подтверждаем
        await query.message.reply_text("Товар выбран! Введите количество:")

# ================= ОФОРМЛЕНИЕ ЗАКАЗА =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'product' not in context.user_data:
        await update.message.reply_text("Что-то пошло не так. Начните заказ заново: /start")
        context.user_data.clear()
        return

    step = context.user_data.get("step", "qty")

    if step == "qty":
        context.user_data["qty"] = update.message.text
        context.user_data["step"] = "name"
        await update.message.reply_text("Введите имя:")

    elif step == "name":
        context.user_data["name"] = update.message.text
        context.user_data["step"] = "phone"
        await update.message.reply_text("Введите телефон:")

    elif step == "phone":
        context.user_data["phone"] = update.message.text
        context.user_data["step"] = "address"
        await update.message.reply_text("Введите адрес доставки:")

    elif step == "address":
        context.user_data["address"] = update.message.text

        order_text = (
            f"🧾 Новый заказ\n\n"
            f"Товар: {context.user_data.get('product', {}).get('name', '—')}\n"
            f"Цена: {context.user_data.get('variant', '—')}\n"
            f"Количество: {context.user_data.get('qty', '—')}\n"
            f"Имя: {context.user_data.get('name', '—')}\n"
            f"Телефон: {context.user_data.get('phone', '—')}\n"
            f"Адрес: {context.user_data.get('address', '—')}"
        )

        await update.message.reply_text(order_text)
        await context.bot.send_message(ADMIN_CHAT_ID, order_text)

        try:
            sheet.append_row([
                datetime.now().strftime("%d.%m.%Y %H:%M"),
                context.user_data.get('product', {}).get('name', '—'),
                context.user_data.get('variant', '—'),
                context.user_data.get('qty', '—'),
                context.user_data.get('name', '—'),
                context.user_data.get('phone', '—'),
                context.user_data.get('address', '—')
            ])
        except Exception as e:
            print(f"Ошибка записи в Google Sheets: {e}")
            await context.bot.send_message(ADMIN_CHAT_ID, f"Ошибка записи заказа в таблицу: {e}")

        await update.message.reply_text("✅ Заказ принят! Мы скоро свяжемся 💖")
        context.user_data.clear()

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(go_back, pattern="^back_main$"))

    app.add_handler(CallbackQueryHandler(boxes_category, pattern="^cat_boxes$"))
    app.add_handler(CallbackQueryHandler(boxes_price, pattern="^box_(0_3000|3000_5000|5000_plus)$"))

    app.add_handler(CallbackQueryHandler(flowers_category, pattern="^cat_flowers$"))

    app.add_handler(CallbackQueryHandler(meat_category, pattern="^cat_meat$"))

    app.add_handler(CallbackQueryHandler(sweet_category, pattern="^cat_sweet$"))
    app.add_handler(CallbackQueryHandler(sweet_price, pattern="^sweet_(0_3000|3000_5000|5000_plus)$"))

    app.add_handler(CallbackQueryHandler(product_selected, pattern="^select_"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
