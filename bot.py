import logging
import os
import json
import re
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

# ================= КАТАЛОГ ТОВАРОВ =================
PRODUCTS = {
    "boxes": {
        "0_3000": [
            {"name": "Бенто-торт из клубники (8 ягод)", "price": 2490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/07/photoeditorsdk-export4.png"},
            {"name": "Набор клубники и малины", "price": 2990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/malinki-takie-vecerinki.jpg"},
            {"name": "Набор с клубникой и финиками (с черешней)", "price": 2390, "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/ceresenki.jpg"},
            {"name": "Набор с клубникой и финиками (с малиной)", "price": 2990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/ceresenki.jpg"},
            {"name": "Стаканчик с клубникой", "price": 1790, "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export69-660x800-1.png"},
            {"name": "Конфеты ручной работы", "price": 1390, "photo": "http://fruttosmile.su/wp-content/uploads/2025/04/unnamed-file.jpg"},
            {"name": "Бананы в шоколаде мини", "price": 1390, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/banany-11.jpg"},
            {"name": "Бананы с орехами", "price": 1990, "photo": "http://fruttosmile.su/wp-content/uploads/2014/08/jguy.png"},
            {"name": "Клубника в шоколаде (12 ягод)", "price": 2590, "photo": "http://fruttosmile.su/wp-content/uploads/2014/03/photo_5449855732875908292_y.jpg"},
            {"name": "Круглая коробка Бананы и клубника", "price": 2290, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/kruglaya-korobka-banany-i-klubnika-v-shokolade.jpg"},
            {"name": "Набор Бананы и клубника (20*20)", "price": 2990, "photo": "http://fruttosmile.su/wp-content/uploads/2023/02/photo_2024-02-24_19-13-37.jpg"},
            {"name": "Сердечко Клубника и бананы", "price": 2490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/serdechko-klubnika-i-banany-v-shokolade.png"}
        ],
        "3000_5000": [
            {"name": "Новогоднее сердце (9-10 ягод)", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png"},
            {"name": "Новогоднее сердце (16-18 ягод)", "price": 4490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png"},
            {"name": "Подарочный набор «Ягодный микс»", "price": 4990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export67.png"},
            {"name": "Клубника в шоколаде (16 ягод)", "price": 3390, "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/16-miks-posypki.jpg"},
            {"name": "Коробочка цветы и макаронс Солнечная", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/photoeditorsdk-export248.png"},
            {"name": "Круглая коробка клубника (Малая 12-14)", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/02/photo_5388599668054814722_y.jpg"},
            {"name": "Круглая коробка клубника (Средняя 15-16)", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2024/02/photo_5388599668054814722_y.jpg"},
            {"name": "Круглая коробка клубника (Большая 18-20)", "price": 4590, "photo": "http://fruttosmile.su/wp-content/uploads/2024/02/photo_5388599668054814722_y.jpg"},
            {"name": "Набор «Клубничные джентльмены» (9 ягод)", "price": 2190, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-04-05_17-43-47.jpg"},
            {"name": "Набор «Клубничные джентльмены» (12 ягод)", "price": 2790, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-04-05_17-43-47.jpg"},
            {"name": "Набор «Клубничные джентльмены» (20 ягод)", "price": 4390, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-04-05_17-43-47.jpg"},
            {"name": "Набор из ягод «Шоколатье»", "price": 4490, "photo": "http://fruttosmile.su/wp-content/uploads/2016/12/img_3983.jpg"},
            {"name": "Набор клубники «Мужской»", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2020/05/photo_2024-08-08_16-13-32.jpg"},
            {"name": "Набор-комплимент цветы и клубника", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/01/photo_2024-01-27_11-11-33.jpg"},
            {"name": "Новогодняя коробочка (12-14 ягод)", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/12/photoeditorsdk-export61.png"},
            {"name": "Новогодняя коробочка (15-17 ягод)", "price": 3890, "photo": "http://fruttosmile.su/wp-content/uploads/2024/12/photoeditorsdk-export61.png"},
            {"name": "Новогодняя коробочка (18-22 ягоды)", "price": 4490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/12/photoeditorsdk-export61.png"}
        ],
        "5000_plus": [
            {"name": "Новогоднее сердце (20-23 ягоды)", "price": 5490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png"},
            {"name": "Бокс «Ассорти» (Бельгийский шоколад)", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/900-1080-piks.-880-1080-piks.-860-1080-piks.-840-1080-piks.-830-1080-piks.-820-1080-piks.png"},
            {"name": "Бокс «С надписью» (Малый)", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/boks-s-nadpisyu.jpg"},
            {"name": "Бокс «Двойной шоколад» (Малый)", "price": 5490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/08/20240809_155003.jpg"},
            {"name": "Бокс «Двойной шоколад» (Большой)", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2024/08/20240809_155003.jpg"},
            {"name": "Бокс «Для мужчин»", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2018/09/photo_2024-08-08_16-18-29.jpg"},
            {"name": "Бокс «Элеганс» (с цветами)", "price": 6590, "photo": "http://fruttosmile.su/wp-content/uploads/2017/05/lngi.png"},
            {"name": "Двойное сердце цветы и клубника", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2020/11/photo_5327822311698586102_y.jpg"},
            {"name": "Клубника в шоколаде «Зверята»", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2023/07/photo_2024-08-08_16-12-56.jpg"},
            {"name": "Набор «Экзотический»", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/fdgecx_660x800_481x582.png"},
            {"name": "Набор фруктов «Ассорти»", "price": 4990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/08/photo_2024-05-10_17-28-111.jpg"},
            {"name": "Бокс «Райское наслаждение»", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/06/ld.png"},
            {"name": "Сердце с декором", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photo_2022_12_09_15_57_12_481x582.jpg"},
            {"name": "Торт из клубники в шоколаде", "price": 7490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photo_2025_02_25_16_20_32_481x582.jpg"}
        ]
    },
    "flowers": {
        "0_4000": [
            {"name": "Букет «Альстромерия»", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-alstromeriya.jpg"},
            {"name": "Букет «Яркое настроение»", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2024/09/photoeditorsdk-export39.png"},
            {"name": "Букет из гипсофилы в коробке", "price": 3290, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photoeditorsdk_export_12__481x582.png"},
            {"name": "Букет из эустомы", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-nezhnejshej-eustomy.jpg"},
            {"name": "Букет из роз и эустомы", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-roz-i-eustomy.jpg"},
            {"name": "Букет из хризантем «Облако»", "price": 3500, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-hrizantem-oblako.png"},
            {"name": "Букет Микс", "price": 4000, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-miks.png"},
            {"name": "Моно букет «Диантусы»", "price": 2690, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/mono-buket-diantusy.png"}
        ],
        "4000_plus": [
            {"name": "Букет «Зефирка»", "price": 4490, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photoeditorsdk_export_37__481x582.png"},
            {"name": "Букет «Первый снег»", "price": 11490, "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/r1w7h3k2q2e1vg1badull79xa3ttaryb.jpg"},
            {"name": "Букет «Розовая нежность»", "price": 5490, "photo": "http://fruttosmile.su/wp-content/uploads/2024/09/photoeditorsdk-export40.png"},
            {"name": "Букет из роз «Танец страсти»", "price": 5490, "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/img_3182-0x800.jpg"},
            {"name": "Моно букет из кустовой розочки", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/mono-buket-iz-nezhnoj-kustovoj-rozochki.png"}
        ]
    },
    "sweet": {
        "0_5000": [
            {"name": "Букет «Брутальный зефир»", "price": 3490, "photo": "http://fruttosmile.su/wp-content/uploads/2018/01/photoeditorsdk-export86.png"},
            {"name": "Букет из сладостей «Зефирный»", "price": 2990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/photoeditorsdk-export192.png"},
            {"name": "Букет из цельных фруктов", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2016/04/photo_2022-12-09_15-56-56.jpg"},
            {"name": "Букет клубничный «С росписью»", "price": 4490, "photo": "http://fruttosmile.su/wp-content/uploads/2016/07/photo_2024-04-05_17-37-48.jpg"},
            {"name": "Букет клубничный S Ажурный", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-klubnichnyj-s-azhurnyj-1.jpg"},
            {"name": "Букет клубничный M Ажурный", "price": 4990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photo_2024_08_11_18_53_18_481x582.jpg"},
            {"name": "Букет Мандариновое настроение", "price": 2990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/nastroenie.jpg"}
        ],
        "5000_plus": [
            {"name": "Букет «Клубничная принцесса» (Малый)", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photoeditorsdk-export135.png"},
            {"name": "Букет «Ягодное ассорти»", "price": 6490, "photo": "http://fruttosmile.su/wp-content/uploads/2016/12/photo_2024-04-05_17-55-09.jpg"},
            {"name": "Букет в шляпной коробке", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/04/photo_2024-08-08_15-59-41.jpg"},
            {"name": "Букет из 101 клубники", "price": 16990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/1649107507_70474509.jpg"},
            {"name": "Букет из сухофруктов «Для здоровья»", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/09/img_20240811_152040_726.jpg"},
            {"name": "Букет «Алая роскошь»", "price": 4990, "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/photoeditorsdk-export203-660x800.png"},
            {"name": "Букет клубничный L Ажурный", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2016/06/ghjj.png"},
            {"name": "Букет клубничный с хризантемами", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2016/07/photoeditorsdk-export213.png"},
            {"name": "Букет «Диадема»", "price": 9990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/03/photoeditorsdk-export21.png"},
            {"name": "Букет «Розовая нежность»", "price": 6990, "photo": "http://fruttosmile.su/wp-content/uploads/2016/09/photo_2024-08-08_16-33-40.jpg"},
            {"name": "Корзина клубники L", "price": 11990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-klubniki-v-shokolade-l.jpeg"},
            {"name": "Корзина клубники S", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-klubniki-v-shokolade-s.jpeg"},
            {"name": "Корзина клубники XXL", "price": 25000, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-klubniki-v-shokolade-xxl.jpeg"},
            {"name": "Корзина «Заморская»", "price": 9990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-fruktov-zamorskaya.jpg"},
            {"name": "Корзина «Брутал»", "price": 12990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/whatsapp202023_10_1620v2014.38.08_14f00b4d_481x582.jpg"},
            {"name": "Фруктовая корзина", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photo_2025-05-24_17-21-00-fruktii.jpg"}
        ]
    },
    "meat": [
        {"name": "Мясной конверт", "price": 3990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-26.jpg"},
        {"name": "Мясной стандарт", "price": 5990, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-24.jpg"},
        {"name": "Мясной ящик", "price": 7500, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-27.jpg"},
        {"name": "Мясной Гигант", "price": 8500, "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-25.jpg"}
    ]
}

# ================= ЛОГИКА БОТА =================

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
    
    if cat == "meat":
        # Мясные просто списком
        for p in PRODUCTS["meat"]:
            kb = [[InlineKeyboardButton("🛍 Заказать", callback_data=f"sel_{p['name'][:20]}")]]
            await query.message.reply_photo(p["photo"], caption=f"{p['name']}\nЦена: {p['price']} ₽", reply_markup=InlineKeyboardMarkup(kb))
    else:
        # Для остальных категорий - выбор бюджета
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
    data = query.data.split("_") # sub_cat_range
    cat = data[1]
    range_key = "_".join(data[2:])
    
    items = PRODUCTS[cat][range_key]
    for p in items:
        kb = [[InlineKeyboardButton("🛍 Заказать", callback_data=f"sel_{p['name'][:20]}")]]
        await query.message.reply_photo(p["photo"], caption=f"{p['name']}\nЦена: {p['price']} ₽", reply_markup=InlineKeyboardMarkup(kb))

async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    p_name_part = query.data.replace("sel_", "")
    
    # Ищем товар во всем каталоге
    found = False
    for cat_data in PRODUCTS.values():
        if isinstance(cat_data, list): # Мясные
            for p in cat_data:
                if p['name'].startswith(p_name_part):
                    context.user_data.update({'product': p['name'], 'price': p['price'], 'photo': p['photo']})
                    found = True; break
        else: # Словари по ценам
            for range_list in cat_data.values():
                for p in range_list:
                    if p['name'].startswith(p_name_part):
                        context.user_data.update({'product': p['name'], 'price': p['price'], 'photo': p['photo']})
                        found = True; break
        if found: break

    context.user_data['state'] = 'WAIT_QTY'
    await query.message.reply_text(f"✅ Вы выбрали: {context.user_data['product']}\n\n1️⃣ Укажите количество (цифрами):")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    
    # Обработка чека
    if not state and (update.message.photo or update.message.document):
        client = context.user_data.get('name', 'Клиент')
        caption = f"📄 ЧЕК ОБ ОПЛАТЕ от {client}"
        if update.message.photo:
            await context.bot.send_photo(ADMIN_CHAT_ID, update.message.photo[-1].file_id, caption=caption)
        else:
            await context.bot.send_document(ADMIN_CHAT_ID, update.message.document.file_id, caption=caption)
        await update.message.reply_text("Спасибо! Менеджер проверит оплату и свяжется с вами. ✨")
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
        await update.message.reply_text("6️⃣ Пожелания по оформлению (текст открытки):")
        
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
    total_prod = d['price'] * d['qty']
    total = total_prod + d['fee']
    
    summary = (
        f"🔔 НОВЫЙ ЗАКАЗ!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📦 Товар: {d['product']}\n"
        f"🔢 Кол-во: {d['qty']}\n"
        f"💰 ИТОГО: {total} ₽\n"
        f"👤 Клиент: {d['name']}\n"
        f"📞 Тел: {d['phone']}\n"
        f"🚛 Способ: {d['method']}\n"
        f"🏠 Адрес: {d['address']}\n"
        f"⏰ Время: {d['delivery_time']}\n"
        f"💬 Коммент: {d['comment']}\n"
        f"━━━━━━━━━━━━━━━"
    )

    await context.bot.send_photo(ADMIN_CHAT_ID, d['photo'], caption=summary)
    
    payment_text = (
        f"✅ **Заказ оформлен!**\n\n"
        f"💵 **К оплате: {total} ₽**\n"
        f"({total_prod} ₽ + {d['fee']} ₽ доставка)\n\n"
        f"**Оплата по QR:**\n"
        f"• [Нажмите здесь](https://qr.nspk.ru/BS1A0054EC7LHJ358M29KSAKOJJ638N1?type=01&bank=100000000284&crc=F07F)\n\n"
        f"📸 Пришлите сюда скриншот чека после оплаты."
    )
    
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
