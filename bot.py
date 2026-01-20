import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# 1. НАСТРОЙКИ ЛОГИРОВАНИЯ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 2. ПОЛНЫЙ СПИСОК ТОВАРОВ
PRODUCTS = {
    "boxes": {
        "0_3000": [
            {"name": "Бокс S (Мини)", "price": 2500, "photo": "https://img.freepik.com/premium-photo/gift-box-with-flowers-inside_1025754-15.jpg"},
            {"name": "Сладкий Бокс Мини", "price": 2800, "photo": "https://img.freepik.com/free-photo/sweet-gift-box_23-2149053730.jpg"}
        ],
        "3000_5000": [
            {"name": "Бокс M (Средний)", "price": 4500, "photo": "https://img.freepik.com/free-photo/beautiful-flowers-bouquet_23-2149053702.jpg"},
            {"name": "Фруктовый Бокс", "price": 3800, "photo": "https://img.freepik.com/free-photo/fruit-basket-gift_23-2149053710.jpg"}
        ],
        "5000_plus": [
            {"name": "Бокс Premium XL", "price": 7000, "photo": "https://img.freepik.com/free-photo/luxury-flower-arrangement_23-2149053715.jpg"},
            {"name": "VIP Бокс 'Голд'", "price": 9500, "photo": "https://img.freepik.com/free-photo/luxury-gift-box-with-flowers_23-2149053720.jpg"}
        ]
    },
    "flowers": {
        "0_4000": [
            {"name": "Букет 'Нежность'", "price": 3500, "photo": "https://img.freepik.com/free-photo/close-up-tender-flowers_23-2149053780.jpg"},
            {"name": "Весенний микс", "price": 3200, "photo": "https://img.freepik.com/free-photo/spring-flowers-bouquet_23-2149053790.jpg"}
        ],
        "4000_plus": [
            {"name": "Букет 'Роскошь'", "price": 5500, "photo": "https://img.freepik.com/free-photo/gorgeous-bouquet-roses_23-2149053801.jpg"},
            {"name": "101 Роза (Красные)", "price": 15000, "photo": "https://img.freepik.com/free-photo/huge-bouquet-red-roses_23-2149053810.jpg"},
            {"name": "101 Роза (Микс)", "price": 16500, "photo": "https://img.freepik.com/free-photo/big-bouquet-colorful-roses_23-2149053815.jpg"}
        ]
    },
    "meat": [
        {"name": "Мясной конверт S", "price": 3000, "photo": "https://basket-10.wbcontent.net/vol1454/part145464/145464730/images/big/1.jpg"},
        {"name": "Мясной Стандарт M", "price": 4500, "photo": "https://i.pinimg.com/736x/8a/5a/61/8a5a6104f98a287e07671759f2a24f11.jpg"},
        {"name": "Мясной Ящик L", "price": 6000, "photo": "https://i.pinimg.com/736x/01/9b/8e/019b8e8b83569769395f17d7f780e55b.jpg"},
        {"name": "Мясной Гигант XL", "price": 8500, "photo": "https://img2.gorod.lv/images/news/321855/big/6.jpg"},
        {"name": "Мужской набор 'Пивной'", "price": 5000, "photo": "https://i.pinimg.com/736x/2b/4c/3d/2b4c3d4e5f6a7b8c9d0e1f2a3b4c5d6e.jpg"}
    ],
    "sweet": {
        "0_5000": [
            {"name": "Сладкий набор S", "price": 3000, "photo": "https://img.freepik.com/free-photo/delicious-sweet-composition_23-2149053740.jpg"},
            {"name": "Зефирный букет", "price": 3500, "photo": "https://img.freepik.com/free-photo/marshmallow-bouquet_23-2149053745.jpg"}
        ],
        "5000_plus": [
            {"name": "Сладкий набор XL", "price": 6500, "photo": "https://img.freepik.com/free-photo/luxury-sweet-gift_23-2149053755.jpg"},
            {"name": "Шоколадный взрыв", "price": 7500, "photo": "https://img.freepik.com/free-photo/chocolate-gift-set_23-2149053760.jpg"}
        ]
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📦 Боксы", callback_data="cat_boxes")],
        [InlineKeyboardButton("💐 Свежие букеты", callback_data="cat_flowers")],
        [InlineKeyboardButton("🍖 Мясные букеты", callback_data="cat_meat")],
        [InlineKeyboardButton("🍬 Сладкие букеты", callback_data="cat_sweet")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Добро пожаловать в Fruttosmile ❤️\nВыберите категорию:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def cat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data.replace("cat_", "")

    if cat == "meat":
        for p in PRODUCTS["meat"]:
            kb = [[InlineKeyboardButton("🛒 Заказать", callback_data=f"sel_{p['name'][:20]}")]]
            await query.message.reply_photo(
                photo=p["photo"], 
                caption=f"**{p['name']}**\nЦена: {p['price']} ₽", 
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(kb)
            )
    else:
        ranges = {
            "boxes": [("До 3000 ₽", "0_3000"), ("3000-5000 ₽", "3000_5000"), ("Более 5000 ₽", "5000_plus")],
            "flowers": [("До 4000 ₽", "0_4000"), ("Более 4000 ₽", "4000_plus")],
            "sweet": [("До 5000 ₽", "0_5000"), ("Более 5000 ₽", "5000_plus")]
        }
        kb = [[InlineKeyboardButton(r[0], callback_data=f"sub_{cat}_{r[1]}")] for r in ranges[cat]]
        kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
        await query.edit_message_text("Выберите ценовой диапазон:", reply_markup=InlineKeyboardMarkup(kb))

async def subcat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    cat = parts[1]
    r_key = "_".join(parts[2:])
    
    for p in PRODUCTS[cat][r_key]:
        kb = [[InlineKeyboardButton("🛒 Заказать", callback_data=f"sel_{p['name'][:20]}")]]
        await query.message.reply_photo(
            photo=p["photo"], 
            caption=f"**{p['name']}**\nЦена: {p['price']} ₽",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )

def main():
    # Ваш текущий токен
    TOKEN = "8053988271:AAH9IzZw5XvDmnvGI1T468up-ZJ3_SxPB1s"
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="back"))
    app.add_handler(CallbackQueryHandler(cat_handler, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(subcat_handler, pattern="^sub_"))
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
