import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# 1. НАСТРОЙКИ ЛОГИРОВАНИЯ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 2. ПОЛНЫЙ КАТАЛОГ ТОВАРОВ
PRODUCTS = {
    "boxes": {
        "0_3000": [
            {"name": "Бенто-торт из клубники (8 ягод)", "price": 2490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/07/photoeditorsdk-export4.png"},
            {"name": "Набор клубники и малины", "price": 2990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/malinki-takie-vecerinki.jpg"},
            {"name": "Стаканчик с клубникой", "price": 1790, "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export69-660x800-1.png"},
            {"name": "Конфеты ручной работы", "price": 1390, "photo": "http://fruttosmile.su/wp-content/uploads/2025/04/unnamed-file.jpg"},
            {"name": "Бананы в шоколаде мини", "price": 1390, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/banany-11.jpg"},
            {"name": "Бананы с орехами", "price": 1990, "photo": "http://fruttosmile.su/wp-content/uploads/2014/08/jguy.png"},
            {"name": "Клубника в шоколаде (12 ягод)", "price": 2590, "photo": "http://fruttosmile.su/wp-content/uploads/2014/03/photo_5449855732875908292_y.jpg"},
            {"name": "Круглая коробка Бананы/Клубника", "price": 2290, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/kruglaya-korobka-banany-i-klubnika-v-shokolade.jpg"},
            {"name": "Набор Бананы/Клубника 20*20", "price": 2990, "photo": "http://fruttosmile.su/wp-content/uploads/2023/02/photo_2024-02-24_19-13-37.jpg"},
            {"name": "Сердечко Клубника/Бананы", "price": 2490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/serdechko-klubnika-i-banany-v-shokolade.png"}
        ],
        "3000_6000": [
            {"name": "Новогоднее сердце", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png"},
            {"name": "Подарочный набор 'Ягодный микс'", "price": 4990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export67.png"},
            {"name": "Бокс 'С надписью'", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/boks-s-nadpisyu.jpg"},
            {"name": "Бокс 'Двойной шоколад'", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2024/08/20240809_155003.jpg"},
            {"name": "Бокс 'Для мужчин'", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2018/09/photo_2024-08-08_16-18-29.jpg"},
            {"name": "Клубника в шоколаде 'Зверята'", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2023/07/photo_2024-08-08_16-12-56.jpg"},
            {"name": "Клубника в шоколаде (16 ягод)", "price": 3390, "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/16-miks-posypki.jpg"},
            {"name": "Коробочка 'Солнечная'", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/photoeditorsdk-export248.png"},
            {"name": "Круглая коробочка клубники", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/02/photo_5388599668054814722_y.jpg"},
            {"name": "Набор 'Клубничные джентльмены'", "price": 4390, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-04-05_17-43-47.jpg"},
            {"name": "Набор 'Экзотический'", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/fdgecx_660x800_481x582.png"},
            {"name": "Набор из ягод 'Шоколатье'", "price": 4490, "photo": "http://fruttosmile.su/wp-content/uploads/2016/12/img_3983.jpg"},
            {"name": "Набор клубники 'Мужской'", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2020/05/photo_2024-08-08_16-13-32.jpg"},
            {"name": "Набор фруктов 'Ассорти'", "price": 4990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/08/photo_2024-05-10_17-28-111.jpg"},
            {"name": "Набор-комплимент с цветами", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/01/photo_2024-01-27_11-11-33.jpg"},
            {"name": "Новогодняя коробочка", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/12/photoeditorsdk-export61.png"},
            {"name": "Бокс 'Райское наслаждение'", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/06/ld.png"},
            {"name": "Сердце с клубникой декор", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photo_2022_12_09_15_57_12_481x582.jpg"}
        ],
        "6000_plus": [
            {"name": "Бокс 'Ассорти'", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/900-1080-piks.-880-1080-piks.-860-1080-piks.-840-1080-piks.-830-1080-piks.-820-1080-piks.png"},
            {"name": "Бокс 'Элеганс'", "price": 6590, "photo": "http://fruttosmile.su/wp-content/uploads/2017/05/lngi.png"},
            {"name": "Двойное сердце цветы/клубника", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2020/11/photo_5327822311698586102_y.jpg"},
            {"name": "Торт из клубники в шоколаде", "price": 7490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photo_2025_02_25_16_20_32_481x582.jpg"}
        ]
    },
    "flowers": {
        "0_4000": [
            {"name": "Букет 'Альстромерия'", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-alstromeriya.jpg"},
            {"name": "Букет 'Яркое настроение'", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2024/09/photoeditorsdk-export39.png"},
            {"name": "Гипсофила в коробке", "price": 3290, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photoeditorsdk_export_12__481x582.png"},
            {"name": "Букет из эустомы", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-nezhnejshej-eustomy.jpg"},
            {"name": "Букет из роз и эустомы", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-roz-i-eustomy.jpg"},
            {"name": "Букет 'Облако' (хризантемы)", "price": 3500, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-hrizantem-oblako.png"},
            {"name": "Букет Микс", "price": 4000, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-miks.png"},
            {"name": "Моно букет 'Диантусы'", "price": 2690, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/mono-buket-diantusy.png"}
        ],
        "4000_plus": [
            {"name": "Букет 'Зефирка'", "price": 4490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photoeditorsdk_export_37__481x582.png"},
            {"name": "Букет 'Первый снег'", "price": 11490, "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/r1w7h3k2q2e1vg1badull79xa3ttaryb.jpg"},
            {"name": "Букет 'Розовая нежность'", "price": 5490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/09/photoeditorsdk-export40.png"},
            {"name": "Букет 'Танец страсти'", "price": 5490, "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/img_3182-0x800.jpg"},
            {"name": "Моно букет из кустовой розы", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/mono-buket-iz-nezhnoj-kustovoj-rozochki.png"}
        ]
    },
    "meat": [
        {"name": "Букет 'Мясной' VIP", "price": 7990, "photo": "http://fruttosmile.su/wp-content/uploads/2016/08/photo_2024-04-05_17-41-51-660x800.jpg"},
        {"name": "Букет 'Мясной' стандарт", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-24.jpg"},
        {"name": "Букет Креветки и Краб", "price": 9990, "photo": "http://fruttosmile.su/wp-content/uploads/2018/08/photo_2022-12-09_18-05-36-2.jpg"},
        {"name": "Букет из раков (2кг)", "price": 10990, "photo": "http://fruttosmile.su/wp-content/uploads/2018/08/photo_2022-12-09_18-05-41.jpg"}
    ],
    "sweet": {
        "0_4500": [
            {"name": "Букет 'Брутальный зефир'", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2018/01/photoeditorsdk-export86.png"},
            {"name": "Букет 'Зефирный'", "price": 2990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/photoeditorsdk-export192.png"},
            {"name": "Букет фруктов 'С любовью'", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2016/04/photo_2022-12-09_15-56-56.jpg"},
            {"name": "Букет клубничный 'С росписью'", "price": 4490, "photo": "http://fruttosmile.su/wp-content/uploads/2016/07/photo_2024-04-05_17-37-48.jpg"},
            {"name": "Букет клубничный S Ажурный", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-klubnichnyj-s-azhurnyj-1.jpg"},
            {"name": "Букет 'Мандариновое настроение'", "price": 2990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/nastroenie.jpg"}
        ],
        "4500_plus": [
            {"name": "Букет 'Клубничная принцесса'", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photoeditorsdk-export135.png"},
            {"name": "Букет 'Ягодное ассорти'", "price": 6490, "photo": "http://fruttosmile.su/wp-content/uploads/2016/12/photo_2024-04-05_17-55-09.jpg"},
            {"name": "Шляпная коробка макаронс", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/04/photo_2024-08-08_15-59-41.jpg"},
            {"name": "Букет из 101 клубники", "price": 16990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/1649107507_70474509.jpg"},
            {"name": "Букет 'Для здоровья'", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/09/img_20240811_152040_726.jpg"},
            {"name": "Фрукты 'Алая роскошь'", "price": 4990, "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/photoeditorsdk-export203-660x800.png"},
            {"name": "Букет клубничный L Ажурный", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2016/06/ghjj.png"},
            {"name": "Букет клубничный M Ажурный", "price": 4990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photo_2024_08_11_18_53_18_481x582.jpg"},
            {"name": "Букет клубничный с хризантемами", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2016/07/photoeditorsdk-export213.png"},
            {"name": "Клубничный букет 'Диадема'", "price": 9990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/03/photoeditorsdk-export21.png"},
            {"name": "Букет розы 'Розовая нежность'", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2016/09/photo_2024-08-08_16-33-40.jpg"},
            {"name": "Корзина клубники в шоколаде L", "price": 11990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-klubniki-v-shokolade-l.jpeg"},
            {"name": "Корзина клубники в шоколаде S", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-klubniki-v-shokolade-s.jpeg"},
            {"name": "Корзина клубники XXL", "price": 25000, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-klubniki-v-shokolade-xxl.jpeg"},
            {"name": "Корзина фруктов 'Заморская'", "price": 9990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-fruktov-zamorskaya.jpg"},
            {"name": "Мужская корзина 'Брутал'", "price": 12990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/whatsapp202023_10_1620v2014.38.08_14f00b4d_481x582.jpg"},
            {"name": "Фруктовая корзина", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photo_2025-05-24_17-21-00-fruktii.jpg"}
        ]
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📦 Боксы и Наборы", callback_data="cat_boxes")],
        [InlineKeyboardButton("💐 Свежие букеты", callback_data="cat_flowers")],
        [InlineKeyboardButton("🍖 Мясные букеты", callback_data="cat_meat")],
        [InlineKeyboardButton("🍬 Сладкие букеты", callback_data="cat_sweet")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Добро пожаловать в Fruttosmile ❤️\nВыберите интересующую категорию:"
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
            await query.message.reply_photo(photo=p["photo"], caption=f"**{p['name']}**\nЦена: {p['price']} ₽", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    else:
        ranges = {
            "boxes": [("До 3000 ₽", "0_3000"), ("3000 - 6000 ₽", "3000_6000"), ("Более 6000 ₽", "6000_plus")],
            "flowers": [("До 4000 ₽", "0_4000"), ("Более 4000 ₽", "4000_plus")],
            "sweet": [("До 4500 ₽", "0_4500"), ("Более 4500 ₽", "4500_plus")]
        }
        kb = [[InlineKeyboardButton(r[0], callback_data=f"sub_{cat}_{r[1]}")] for r in ranges[cat]]
        kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
        await query.edit_message_text("Выберите ценовой диапазон:", reply_markup=InlineKeyboardMarkup(kb))

async def subcat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    cat, r_key = parts[1], "_".join(parts[2:])
    
    for p in PRODUCTS[cat][r_key]:
        kb = [[InlineKeyboardButton("🛒 Заказать", callback_data=f"sel_{p['name'][:20]}")]]
        await query.message.reply_photo(photo=p["photo"], caption=f"**{p['name']}**\nЦена: {p['price']} ₽", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

def main():
    TOKEN = "8539880271:AAH9lzZw5XvDmnvGI1T460up-ZJ3_SxPB1s"
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="back"))
    app.add_handler(CallbackQueryHandler(cat_handler, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(subcat_handler, pattern="^sub_"))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
