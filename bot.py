import logging
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
 
# --- НАСТРОЙКИ ---
TOKEN = "8539880271:AAH9lzZw5XvDmnvGI1T460up-ZJ3_SxPB1s"
ADMIN_CHAT_ID = 5664273200 # ЗАМЕНИТЕ НА ВАШ ID ИЗ @userinfobot
 
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
 
# ПОЛНЫЙ КАТАЛОГ ТОВАРОВ
PRODUCTS = {
    "boxes": {
        "0_3000": [
            {"name": "Бенто-торт из клубники", "price": 2490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/07/photoeditorsdk-export4.png"},
            {"name": "Набор клубники и малины", "price": 2990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/malinki-takie-vecerinki.jpg"},
            {"name": "Стаканчик с клубникой", "price": 1790, "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export69-660x800-1.png"},
            {"name": "Конфеты ручной работы", "price": 1390, "photo": "http://fruttosmile.su/wp-content/uploads/2025/04/unnamed-file.jpg"},
            {"name": "Бананы в шоколаде мини", "price": 1390, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/banany-11.jpg"},
            {"name": "Бананы с орехами", "price": 1990, "photo": "http://fruttosmile.su/wp-content/uploads/2014/08/jguy.png"},
            {"name": "Клубника в шоколаде 12 ягод", "price": 2590, "photo": "http://fruttosmile.su/wp-content/uploads/2014/03/photo_5449855732875908292_y.jpg"},
            {"name": "Сердечко клубника/бананы", "price": 2490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/serdechko-klubnika-i-banany-v-shokolade.png"}
        ],
        "3000_6000": [
            {"name": "Новогоднее сердце", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png"},
            {"name": "Подарочный набор Ягодный микс", "price": 4990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export67.png"},
            {"name": "Бокс С надписью", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/boks-s-nadpisyu.jpg"},
            {"name": "Бокс Двойной шоколад", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2024/08/20240809_155003.jpg"},
            {"name": "Набор Шоколатье", "price": 4490, "photo": "http://fruttosmile.su/wp-content/uploads/2016/12/img_3983.jpg"},
            {"name": "Круглая коробочка клубники", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/02/photo_5388599668054814722_y.jpg"}
        ],
        "6000_plus": [
            {"name": "Бокс Ассорти", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/900-1080-piks.-880-1080-piks.-860-1080-piks.-840-1080-piks.-830-1080-piks.-820-1080-piks.png"},
            {"name": "Бокс Элеганс", "price": 6590, "photo": "http://fruttosmile.su/wp-content/uploads/2017/05/lngi.png"},
            {"name": "Торт из клубники", "price": 7490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photo_2025_02_25_16_20_32_481x582.jpg"}
        ]
    },
    "flowers": {
        "0_4000": [
            {"name": "Букет Альстромерия", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-alstromeriya.jpg"},
            {"name": "Букет Яркое настроение", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2024/09/photoeditorsdk-export39.png"},
            {"name": "Букет роз и эустомы", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-roz-i-eustomy.jpg"}
        ],
        "4000_plus": [
            {"name": "Букет Зефирка", "price": 4490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photoeditorsdk_export_37__481x582.png"},
            {"name": "Букет Розовая нежность", "price": 5490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/09/photoeditorsdk-export40.png"},
            {"name": "Букет Танец страсти", "price": 5490, "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/img_3182-0x800.jpg"}
        ]
    },
    "meat": [
        {"name": "Мясной VIP", "price": 7990, "photo": "http://fruttosmile.su/wp-content/uploads/2016/08/photo_2024-04-05_17-41-51-660x800.jpg"},
        {"name": "Мясной стандарт", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-24.jpg"},
        {"name": "Букет Креветки и Краб", "price": 9990, "photo": "http://fruttosmile.su/wp-content/uploads/2018/08/photo_2022-12-09_18-05-36-2.jpg"}
    ],
    "sweet": {
        "0_4500": [
            {"name": "Брутальный зефир", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2018/01/photoeditorsdk-export86.png"},
            {"name": "Клубничный с росписью", "price": 4490, "photo": "http://fruttosmile.su/wp-content/uploads/2016/07/photo_2024-04-05_17-37-48.jpg"}
        ],
        "4500_plus": [
            {"name": "Клубничная принцесса", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photoeditorsdk-export135.png"},
            {"name": "Букет 101 клубника", "price": 16990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/1649107507_70474509.jpg"}
        ]
    }
}
 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("📦 Боксы и Наборы", callback_data="cat_boxes")],
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
            kb = [[InlineKeyboardButton("🛍 Выбрать этот товар", callback_data=f"sel_{p['name'][:20]}")]]
            await query.message.reply_photo(photo=p["photo"], caption=f"{p['name']}\nЦена: {p['price']} ₽", reply_markup=InlineKeyboardMarkup(kb))
    else:
        ranges = {
            "boxes": [("До 3000 ₽", "0_3000"), ("3000-6000 ₽", "3000_6000"), ("6000+ ₽", "6000_plus")],
            "flowers": [("До 4000 ₽", "0_4000"), ("4000+ ₽", "4000_plus")],
            "sweet": [("До 4500 ₽", "0_4500"), ("4500+ ₽", "4500_plus")]
        }
        kb = [[InlineKeyboardButton(r[0], callback_data=f"sub_{cat}_{r[1]}")] for r in ranges[cat]]
        kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
        await query.edit_message_text("Выберите бюджет:", reply_markup=InlineKeyboardMarkup(kb))
 
async def subcat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    items = PRODUCTS.get(data[1], {}).get("_".join(data[2:]), [])
    for p in items:
        kb = [[InlineKeyboardButton("🛍 Выбрать этот товар", callback_data=f"sel_{p['name'][:20]}")]]
        await query.message.reply_photo(p["photo"], caption=f"{p['name']}\nЦена: {p['price']} ₽", reply_markup=InlineKeyboardMarkup(kb))
 
async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    p_name = query.data.replace("sel_", "")
    found = False
    for cat in PRODUCTS.values():
        items = cat if isinstance(cat, list) else [i for sub in cat.values() for i in sub]
        for p in items:
            if p['name'].startswith(p_name):
                context.user_data['product'] = p['name']
                context.user_data['price'] = int(p['price'])
                context.user_data['product_photo'] = p['photo']
                found = True
                break
        if found: break
    context.user_data['state'] = 'WAIT_QTY'
    await query.message.reply_text(f"✅ Вы выбрали: {context.user_data.get('product')}\n\n1️⃣ Укажите количество (цифрами):")

async def delivery_method_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "method_delivery":
        context.user_data['method'] = "Доставка"
        context.user_data['delivery_fee'] = 400
        context.user_data['state'] = 'WAIT_ADDRESS'
        await query.edit_message_text("📍 Укажите адрес:")
    else:
        context.user_data['method'] = "Самовывоз"
        context.user_data['delivery_fee'] = 0
        context.user_data['address'] = "—"
        context.user_data['state'] = 'WAIT_DATE'
        await query.edit_message_text("🏠 Когда заберете?")
 
async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data
    total_items = d.get('price', 0) * d.get('qty', 1)
    total_final = total_items + d.get('delivery_fee', 0)
    
    summary = (
        f"🔔 НОВЫЙ ЗАКАЗ!\n"
        f"📦 {d.get('product')}\n"
        f"🔢 Кол-во: {d.get('qty')}\n"
        f"💰 ИТОГО: {total_final} ₽ (включая доставку {d.get('delivery_fee',0)} ₽)\n"
        f"👤 {d.get('name')}\n"
        f"📞 {d.get('phone')}\n"
        f"🚛 {d.get('method')}\n"
        f"🏠 {d.get('address')}\n"
        f"⏰ {d.get('delivery_time')}\n"
        f"💬 {d.get('comment') or '—'}"
    )
 
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary)
        if 'order_photo' in d:
            if d.get('order_photo_type') == 'photo':
                await context.bot.send_photo(
                    chat_id=ADMIN_CHAT_ID,
                    photo=d['order_photo'],
                    caption="Фото заказа от клиента"
                )
            else:
                await context.bot.send_document(
                    chat_id=ADMIN_CHAT_ID,
                    document=d['order_photo'],
                    caption="Фото/файл заказа от клиента"
                )
    except Exception as e:
        logging.error(f"Ошибка отправки админу: {e}")
 
    context.user_data['state'] = 'WAIT_ORDER_PHOTO'
    target = update.message if update.message else (update.callback_query.message if update.callback_query else None)
    if target:
        await target.reply_text(
            "📸 Пожалуйста, пришлите фото того, что хотите заказать (надпись, оформление, конкретный вариант и т.д.)\n\n"
            "После этого мы выставим точный счёт и реквизиты."
        )

async def media_or_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')

    if update.message.photo or update.message.document:
        file_id = None
        file_type = None

        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            file_type = 'photo'
        elif update.message.document:
            file_id = update.message.document.file_id
            file_type = 'document'

        client_name = context.user_data.get('name', 'Клиент')

        if state == 'WAIT_ORDER_PHOTO':
            context.user_data['order_photo'] = file_id
            context.user_data['order_photo_type'] = file_type
            context.user_data['state'] = None

            total = context.user_data.get('price', 0) * context.user_data.get('qty', 1) + context.user_data.get('delivery_fee', 0)

            await update.message.reply_text(
                f"Фото получено! Спасибо ❤️\n\n"
                f"К оплате: **{total} ₽**\n\n"
                f"Оплатите, пожалуйста, по ссылке:\n"
                f"https://qr.nspk.ru/BS1A0054EC7LHJ358M29KSAKOJJ638N1?type=01&bank=100000000284&crc=F07F\n\n"
                "После оплаты пришлите скрин чека — и мы сразу начнём готовить ваш заказ!"
            )

            try:
                if file_type == 'photo':
                    await context.bot.send_photo(ADMIN_CHAT_ID, file_id, caption=f"Фото заказа от {client_name}")
                else:
                    await context.bot.send_document(ADMIN_CHAT_ID, file_id, caption=f"Файл заказа от {client_name}")
            except Exception as e:
                logging.error(f"Не удалось переслать фото заказа: {e}")

        elif state is None:  # чек после оформления
            await context.bot.send_message(ADMIN_CHAT_ID, f"💳 Чек от {client_name}")
            if file_type == 'photo':
                await context.bot.send_photo(ADMIN_CHAT_ID, file_id)
            else:
                await context.bot.send_document(ADMIN_CHAT_ID, file_id)
            await update.message.reply_text("Чек получен! Мы уже готовим ваш заказ ✨")

        return

    if update.message and update.message.text:
        text = update.message.text.strip()

        if state == 'WAIT_QTY':
            qty_digits = re.sub(r'\D', '', text)
            if qty_digits:
                context.user_data['qty'] = int(qty_digits)
                context.user_data['state'] = 'WAIT_NAME'
                await update.message.reply_text("2️⃣ Как вас зовут?")
            else:
                await update.message.reply_text("Пожалуйста, введите количество числом (например: 1).")

        elif state == 'WAIT_NAME':
            context.user_data['name'] = text
            context.user_data['state'] = 'WAIT_PHONE'
            await update.message.reply_text("3️⃣ Ваш номер телефона:")

        elif state == 'WAIT_PHONE':
            context.user_data['phone'] = text
            context.user_data['state'] = 'WAIT_METHOD'
            kb = [
                [InlineKeyboardButton("🚚 Доставка (+400₽)", callback_data="method_delivery")],
                [InlineKeyboardButton("🏠 Самовывоз", callback_data="method_pickup")]
            ]
            await update.message.reply_text("4️⃣ Способ получения:", reply_markup=InlineKeyboardMarkup(kb))

        elif state == 'WAIT_ADDRESS':
            context.user_data['address'] = text
            context.user_data['state'] = 'WAIT_DATE'
            await update.message.reply_text("5️⃣ Дата и время доставки:")

        elif state == 'WAIT_DATE':
            context.user_data['delivery_time'] = text
            context.user_data['state'] = 'WAIT_COMMENT'
            await update.message.reply_text("6️⃣ Пожелания (текст открытки и т.д.):")

        elif state == 'WAIT_COMMENT':
            context.user_data['comment'] = text
            await finish_order(update, context)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(cat_handler, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(subcat_handler, pattern="^sub_"))
    app.add_handler(CallbackQueryHandler(product_selected, pattern="^sel_"))
    app.add_handler(CallbackQueryHandler(delivery_method_handler, pattern="^method_"))

    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL, media_or_text_handler))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
