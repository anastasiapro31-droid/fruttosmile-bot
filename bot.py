import logging
import os
import json
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ================= НАСТРОЙКИ =================
# ВСТАВЬТЕ СЮДА ВАШ САМЫЙ НОВЫЙ ТОКЕН ОТ BOTFATHER
BOT_TOKEN = "8539880271:AAH9lzZw5XvDmnvGI1T460up-ZJ3_SxPB1s"
ADMIN_CHAT_ID = 1165444045 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= КАТАЛОГ ТОВАРОВ (ВСЕ СОХРАНЕНО) =================
PRODUCTS = {
    "boxes": {
        "0_3000": [
            {"name": "Бенто-торт из клубники (8 ягод)", "price": 2490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/07/photoeditorsdk-export4.png"},
            {"name": "Набор клубники и малины", "price": 2990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/malinki-takie-vecerinki.jpg"},
            {"name": "Набор с клубникой и финиками (с черешней)", "price": 2390, "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/ceresenki.jpg"},
            {"name": "Стаканчик с клубникой", "price": 1790, "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export69-660x800-1.png"},
            {"name": "Конфеты ручной работы", "price": 1390, "photo": "http://fruttosmile.su/wp-content/uploads/2025/04/unnamed-file.jpg"},
            {"name": "Бананы в шоколаде мини", "price": 1390, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/banany-11.jpg"},
            {"name": "Бананы с орехами", "price": 1990, "photo": "http://fruttosmile.su/wp-content/uploads/2014/08/jguy.png"},
            {"name": "Клубника в шоколаде (12 ягод)", "price": 2590, "photo": "http://fruttosmile.su/wp-content/uploads/2014/03/photo_5449855732875908292_y.jpg"},
            {"name": "Сердечко Клубника и бананы", "price": 2490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/serdechko-klubnika-i-banany-v-shokolade.png"}
        ],
        "3000_5000": [
            {"name": "Новогоднее сердце (9-10 ягод)", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png"},
            {"name": "Новогоднее сердце (16-18 ягод)", "price": 4490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png"},
            {"name": "Подарочный набор «Ягодный микс»", "price": 4990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export67.png"},
            {"name": "Клубника в шоколаде (16 ягод)", "price": 3390, "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/16-miks-posypki.jpg"},
            {"name": "Круглая коробка клубника (Малая)", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/02/photo_5388599668054814722_y.jpg"},
            {"name": "Круглая коробка клубника (Средняя)", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2024/02/photo_5388599668054814722_y.jpg"},
            {"name": "Набор «Клубничные джентльмены» (12 ягод)", "price": 2790, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-04-05_17-43-47.jpg"},
            {"name": "Набор-комплимент цветы и клубника", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/01/photo_2024-01-27_11-11-33.jpg"}
        ],
        "5000_plus": [
            {"name": "Бокс «Ассорти»", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/900-1080-piks.-880-1080-piks.-860-1080-piks.-840-1080-piks.-830-1080-piks.-820-1080-piks.png"},
            {"name": "Бокс «С надписью»", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/boks-s-nadpisyu.jpg"},
            {"name": "Торт из клубники в шоколаде", "price": 7490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photo_2025_02_25_16_20_32_481x582.jpg"}
        ]
    },
    "flowers": {
        "0_4000": [
            {"name": "Букет «Альстромерия»", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-alstromeriya.jpg"},
            {"name": "Букет «Яркое настроение»", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2024/09/photoeditorsdk-export39.png"},
            {"name": "Моно букет «Диантусы»", "price": 2690, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/mono-buket-diantusy.png"}
        ],
        "4000_plus": [
            {"name": "Букет «Розовая нежность»", "price": 5490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/09/photoeditorsdk-export40.png"},
            {"name": "Букет «Первый снег»", "price": 11490, "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/r1w7h3k2q2e1vg1badull79xa3ttaryb.jpg"}
        ]
    },
    "sweet": {
        "0_5000": [
            {"name": "Букет «Зефирный»", "price": 2990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/photoeditorsdk-export192.png"},
            {"name": "Букет Мандариновое настроение", "price": 2990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/nastroenie.jpg"}
        ],
        "5000_plus": [
            {"name": "Букет из 101 клубники", "price": 16990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/1649107507_70474509.jpg"},
            {"name": "Корзина клубники L", "price": 11990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-klubniki-v-shokolade-l.jpeg"}
        ]
    },
    "meat": [
        {"name": "Мясной конверт", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-26.jpg"},
        {"name": "Мясной стандарт", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-24.jpg"},
        {"name": "Мясной ящик", "price": 7500, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-27.jpg"},
        {"name": "Мясной Гигант", "price": 8500, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-25.jpg"}
    ]
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
    
    # ИСПРАВЛЕНО: Для мяса выводим сразу, для остальных - подкатегории
    if cat == "meat":
        for p in PRODUCTS["meat"]:
            kb = [[InlineKeyboardButton("🛍 Заказать", callback_data=f"sel_{p['name'][:20]}")]]
           await query.message.reply_photo(p["photo"], caption=f"{p['name']}\nЦена: {p['price']} ₽", reply_markup=InlineKeyboardMarkup(kb))
    else:
        ranges = {
            "boxes": [("До 3000", "0_3000"), ("3000-5000", "3000_5000"), ("Более 5000", "5000_plus")],
            "flowers": [("До 4000", "0_4000"), ("Более 4000", "4000_plus")],
            "sweet": [("До 5000", "0_5000"), ("Более 5000", "5000_plus")]
        }
        kb = [[InlineKeyboardButton(r[0], callback_data=f"sub_{cat}_{r[1]}")] for r in ranges[cat]]
        kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
        await query.edit_message_text("Выберите ценовой диапазон:", reply_markup=InlineKeyboardMarkup(kb))

async def subcat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    cat, r_key = data[1], "_".join(data[2:])
    for p in PRODUCTS[cat][r_key]:
        kb = [[InlineKeyboardButton("🛍 Заказать", callback_data=f"sel_{p['name'][:20]}")]]
        await query.message.reply_photo(p["photo"], caption=f"{p['name']}\nЦена: {p['price']} ₽", reply_markup=InlineKeyboardMarkup(kb))

async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    p_name_part = query.data.replace("sel_", "")
    
    found = None
    for cat_key, cat_val in PRODUCTS.items():
        if isinstance(cat_val, list):
            for p in cat_val:
                if p['name'].startswith(p_name_part): found = p; break
        else:
            for r_list in cat_val.values():
                for p in r_list:
                    if p['name'].startswith(p_name_part): found = p; break
        if found: break

    if found:
        context.user_data.update({'product': found['name'], 'price': found['price'], 'photo': found['photo'], 'state': 'WAIT_QTY'})
        await query.message.reply_text(f"✅ Вы выбрали: {found['name']}\n\n1️⃣ Укажите количество (цифрами):")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    
    if not state and (update.message.photo or update.message.document):
        client = context.user_data.get('name', 'Клиент')
        caption = f"📄 ЧЕК ОБ ОПЛАТЕ от {client}"
        if update.message.photo:
            await context.bot.send_photo(ADMIN_CHAT_ID, update.message.photo[-1].file_id, caption=caption)
        else:
            await context.bot.send_document(ADMIN_CHAT_ID, update.message.document.file_id, caption=caption)
        await update.message.reply_text("Спасибо! Менеджер скоро свяжется с вами. ✨")
        return

    if not state: return
    text = update.message.text

    if state == 'WAIT_QTY':
        try:
            qty = int(re.sub(r'\D', '', text))
            context.user_data.update({'qty': qty, 'state': 'WAIT_NAME'})
            await update.message.reply_text("2️⃣ Как вас зовут?")
        except: await update.message.reply_text("Введите число.")
    elif state == 'WAIT_NAME':
        context.user_data.update({'name': text, 'state': 'WAIT_PHONE'})
        await update.message.reply_text("3️⃣ Ваш номер телефона:")
    elif state == 'WAIT_PHONE':
        context.user_data.update({'phone': text, 'state': 'WAIT_METHOD'})
        kb = [[InlineKeyboardButton("🚚 Доставка (+400₽)", callback_data="method_delivery"), 
               InlineKeyboardButton("🏠 Самовывоз", callback_data="method_pickup")]]
        await update.message.reply_text("4️⃣ Способ получения:", reply_markup=InlineKeyboardMarkup(kb))
    elif state == 'WAIT_ADDRESS':
        context.user_data.update({'address': text, 'state': 'WAIT_DATE'})
        await update.message.reply_text("5️⃣ Дата и время доставки:")
    elif state == 'WAIT_DATE':
        context.user_data.update({'delivery_time': text, 'state': 'WAIT_COMMENT'})
        await update.message.reply_text("6️⃣ Пожелания (текст открытки):")
    elif state == 'WAIT_COMMENT':
        context.user_data['comment'] = text
        await finish_order(update, context)

async def delivery_method_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "method_delivery":
        context.user_data.update({'method': "Доставка", 'fee': 400, 'state': 'WAIT_ADDRESS'})
        await query.edit_message_text("📍 Укажите адрес доставки:")
    else:
        context.user_data.update({'method': "Самовывоз", 'fee': 0, 'address': "—", 'state': 'WAIT_DATE'})
        await query.edit_message_text("🏠 Когда планируете забрать заказ?")

async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data
    total = (d['price'] * d['qty']) + d['fee']
    summary = (f"🔔 НОВЫЙ ЗАКАЗ!\n"
               f"📦 Товар: {d['product']}\n🔢 Кол-во: {d['qty']}\n💰 ИТОГО: {total} ₽\n"
               f"👤 Клиент: {d['name']}\n📞 Тел: {d['phone']}\n🚛 Способ: {d['method']}\n"
               f"🏠 Адрес: {d['address']}\n⏰ Время: {d['delivery_time']}\n💬 Коммент: {d['comment']}")
    await context.bot.send_photo(ADMIN_CHAT_ID, d['photo'], caption=summary)
    payment_text = (f"✅ Заказ оформлен!\n\n💵 К оплате: {total} ₽\n\nОплата по QR: [Нажмите здесь](https://qr.nspk.ru/BS1A0054EC7LHJ358M29KSAKOJJ638N1?type=01&bank=100000000284&crc=F07F)\n\nПришлите скриншот чека сюда.")
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(payment_text, parse_mode='Markdown')
    context.user_data['state'] = None

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(cat_handler, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(subcat_handler, pattern="^sub_"))
    app.add_handler(CallbackQueryHandler(product_selected, pattern="^sel_"))
    app.add_handler(CallbackQueryHandler(delivery_method_handler, pattern="^method_"))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
