import logging
import os
import json
import re
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "8539880271:AAH9lzZw5XvDmnvGI1T460up-ZJ3_SxPB1s"
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

            {"name": "Бенто-торт из клубники в шоколаде (8 ягод)", "price": "2490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/07/photoeditorsdk-export4.png"},

            {"name": "Стаканчик с клубникой в шоколаде", "price": "1790", "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export69-660x800-1.png"},

            {"name": "Набор с клубникой, финиками и черешней", "price": "2390", "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/ceresenki.jpg"},

            {"name": "Набор клубники и малины в шоколаде", "price": "2990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/malinki-takie-vecerinki.jpg"},

            {"name": "Конфеты ручной работы", "price": "1390", "photo": "http://fruttosmile.su/wp-content/uploads/2025/04/unnamed-file.jpg"},

            {"name": "Бананы в шоколаде мини коробочка", "price": "1390", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/banany-11.jpg"},

            {"name": "Бананы с орехами", "price": "1990", "photo": "http://fruttosmile.su/wp-content/uploads/2014/08/jguy.png"},

            {"name": "Клубника в шоколаде 12 ягод", "price": "2590", "photo": "http://fruttosmile.su/wp-content/uploads/2014/03/photo_5449855732875908292_y.jpg"},

            {"name": "Сердечко «Клубника и бананы в шоколаде»", "price": "2490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/serdechko-klubnika-i-banany-v-shokolade.png"},

            {"name": "Круглая коробка Бананы и клубника в шоколаде", "price": "2290", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/kruglaya-korobka-banany-i-klubnika-v-shokolade.jpg"},

            {"name": "Набор «Бананы и клубника в шоколаде» 20*20", "price": "2990", "photo": "http://fruttosmile.su/wp-content/uploads/2023/02/photo_2024-02-24_19-13-37.jpg"},

            {"name": "Набор с клубникой, финиками и малиной", "price": "2990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/06/ceresenki.jpg"}

        ],

        "3000_5000": [

            {"name": "Новогоднее сердце с клубникой в шоколаде Маленькое", "price": "3490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png"},

            {"name": "Новогоднее сердце с клубникой в шоколаде Среднее", "price": "4490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png"},

            {"name": "Подарочный набор «Ягодный микс»", "price": "4990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photoeditorsdk-export67.png"},

            {"name": "Клубника в шоколаде 16 ягод", "price": "3390", "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/16-miks-posypki.jpg"},

            {"name": "Коробочка с цветами и макаронсами «Солнечная»", "price": "3490", "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/photoeditorsdk-export248.png"},

            {"name": "Круглая коробочка с клубникой", "price": "3490", "photo": "http://fruttosmile.su/wp-content/uploads/2024/02/photo_5388599668054814722_y.jpg"},

            {"name": "Набор «Клубничные джентльмены» Малый", "price": "2190", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-04-05_17-43-47.jpg"},

            {"name": "Набор «Клубничные джентльмены» Средний", "price": "2790", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-04-05_17-43-47.jpg"},

            {"name": "Набор «Клубничные джентльмены» Большой", "price": "4390", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-04-05_17-43-47.jpg"},

            {"name": "Набор «Экзотический»", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/fdgecx_660x800_481x582.png"},

            {"name": "Набор из ягод » Шоколатье»", "price": "4490", "photo": "http://fruttosmile.su/wp-content/uploads/2016/12/img_3983.jpg"},

            {"name": "Набор клубники и шоколада «Мужской»", "price": "3990", "photo": "http://fruttosmile.su/wp-content/uploads/2020/05/photo_2024-08-08_16-13-32.jpg"},

            {"name": "Набор фруктов в шоколаде «Ассорти»", "price": "4990", "photo": "http://fruttosmile.su/wp-content/uploads/2017/08/photo_2024-05-10_17-28-111.jpg"},

            {"name": "Набор-комплимент с цветами и клубникой", "price": "3490", "photo": "http://fruttosmile.su/wp-content/uploads/2024/01/photo_2024-01-27_11-11-33.jpg"},

            {"name": "Новогодняя коробочка с клубникой Малый", "price": "3490", "photo": "http://fruttosmile.su/wp-content/uploads/2024/12/photoeditorsdk-export61.png"},

            {"name": "Новогодняя коробочка с клубникой Средний", "price": "3890", "photo": "http://fruttosmile.su/wp-content/uploads/2024/12/photoeditorsdk-export61.png"},

            {"name": "Новогодняя коробочка с клубникой Большой", "price": "4490", "photo": "http://fruttosmile.su/wp-content/uploads/2024/12/photoeditorsdk-export61.png"},

            {"name": "Подарочный бокс «Райское наслаждение»", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2017/06/ld.png"},

            {"name": "Сердце с клубникой в шоколаде с декором", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photo_2022_12_09_15_57_12_481x582.jpg"},

            {"name": "Торт из клубники в шоколаде", "price": "7490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photo_2025_02_25_16_20_32_481x582.jpg"},

            {"name": "Клубника в шоколаде «Зверята»", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2023/07/photo_2024-08-08_16-12-56.jpg"},

            {"name": "Бокс «С надписью» Малый", "price": "5490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/boks-s-nadpisyu.jpg"},

            {"name": "Бокс «С надписью» Средний", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/boks-s-nadpisyu.jpg"},

            {"name": "Бокс «С надписью» Большой", "price": "6990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/boks-s-nadpisyu.jpg"},

            {"name": "Бокс «Двойной шоколад» Малый", "price": "5490", "photo": "http://fruttosmile.su/wp-content/uploads/2024/08/20240809_155003.jpg"},

            {"name": "Бокс «Двойной шоколад» Большой", "price": "6990", "photo": "http://fruttosmile.su/wp-content/uploads/2024/08/20240809_155003.jpg"},

            {"name": "Бокс подарочный «Для мужчин»", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2018/09/photo_2024-08-08_16-18-29.jpg"},

            {"name": "Бокс с цветами, клубникой и шампанским « Элеганс»", "price": "6590", "photo": "http://fruttosmile.su/wp-content/uploads/2017/05/lngi.png"},

            {"name": "Двойное сердце с цветами и клубникой в шоколаде", "price": "6990", "photo": "http://fruttosmile.su/wp-content/uploads/2020/11/photo_5327822311698586102_y.jpg"}

        ],

        "5000_plus": [

            {"name": "Бокс «Ассорти»", "price": "6990", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/900-1080-piks.-880-1080-piks.-860-1080-piks.-840-1080-piks.-830-1080-piks.-820-1080-piks.png"},

            {"name": "Корзина клубники в шоколаде L", "price": "11990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-klubniki-v-shokolade-l.jpeg"},

            {"name": "Корзина клубники в шоколаде S", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-klubniki-v-shokolade-s.jpeg"},

            {"name": "Корзина клубники в шоколаде XXL", "price": "25000", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-klubniki-v-shokolade-xxl.jpeg"},

            {"name": "Корзина фруктов «Заморская»", "price": "9990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/korzina-fruktov-zamorskaya.jpg"},

            {"name": "Мужская корзина «Брутал»", "price": "12990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/whatsapp202023_10_1620v2014.38.08_14f00b4d_481x582.jpg"},

            {"name": "Фруктовая корзина", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/05/photo_2025-05-24_17-21-00-fruktii.jpg"},

            {"name": "Новогоднее сердце с клубникой в шоколаде Большое", "price": "5490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/image-17-12-25-06-50-2.png"}

        ]

    },

    "flowers": [

        {"name": "Букет «Альстромерия»", "price": "3990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-alstromeriya.jpg"},

        {"name": "Букет «Зефирка»", "price": "4490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photoeditorsdk_export_37__481x582.png"},

        {"name": "Букет «Первый снег»", "price": "11490", "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/r1w7h3k2q2e1vg1badull79xa3ttaryb.jpg"},

        {"name": "Букет «Розовая нежность»", "price": "5490", "photo": "http://fruttosmile.su/wp-content/uploads/2024/09/photoeditorsdk-export40.png"},

        {"name": "Букет «Яркое настроение»", "price": "3990", "photo": "http://fruttosmile.su/wp-content/uploads/2024/09/photoeditorsdk-export39.png"},

        {"name": "Букет из гипсофилы в шляпной коробке", "price": "3290", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photoeditorsdk_export_12__481x582.png"},

        {"name": "Букет из нежнейшей эустомы", "price": "3990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-nezhnejshej-eustomy.jpg"},

        {"name": "Букет из роз «Танец страсти»", "price": "5490", "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/img_3182-0x800.jpg"},

        {"name": "Букет из роз и эустомы", "price": "3490", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-roz-i-eustomy.jpg"},

        {"name": "Букет из хризантем «Облако»", "price": "3500", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-iz-hrizantem-oblako.png"},

        {"name": "Букет Микс", "price": "4000", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-miks.png"},

        {"name": "Моно букет «Диантусы»", "price": "2690", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/mono-buket-diantusy.png"},

        {"name": "Моно букет из нежной кустовой розочки", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/mono-buket-iz-nezhnoj-kustovoj-rozochki.png"}

    ],

    "meat": [

        {"name": "Букет «Мясной» VIP", "price": "7990", "photo": "http://fruttosmile.su/wp-content/uploads/2016/08/photo_2024-04-05_17-41-51-660x800.jpg"},

        {"name": "Букет «Мясной» стандарт", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photo_2024-08-08_16-52-24.jpg"},

        {"name": "Букет из королевских креветок и клешней краба", "price": "9990", "photo": "http://fruttosmile.su/wp-content/uploads/2018/08/photo_2022-12-09_18-05-36-2.jpg"},

        {"name": "Букет из раков 2кг", "price": "10990", "photo": "http://fruttosmile.su/wp-content/uploads/2018/08/photo_2022-12-09_18-05-41.jpg"},

        {"name": "Букет из раков 1кг", "price": "6990", "photo": "http://fruttosmile.su/wp-content/uploads/2018/08/photo_2022-12-09_18-05-41.jpg"}

    ],

    "sweet": {

        "0_3000": [

            {"name": "Букет Мандариновое настроение", "price": "2990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/12/nastroenie.jpg"}

        ],

        "3000_5000": [

            {"name": "Букет «Брутальный зефир»", "price": "3490", "photo": "http://fruttosmile.su/wp-content/uploads/2018/01/photoeditorsdk-export86.png"},

            {"name": "Букет клубничный «С росписью»", "price": "4490", "photo": "http://fruttosmile.su/wp-content/uploads/2016/07/photo_2024-04-05_17-37-48.jpg"},

            {"name": "Букет из фруктов с цветами «Алая роскошь»", "price": "4990", "photo": "http://fruttosmile.su/wp-content/uploads/2016/10/photoeditorsdk-export203-660x800.png"},

            {"name": "Букет из цельных фруктов » С любовью»", "price": "3990", "photo": "http://fruttosmile.su/wp-content/uploads/2016/04/photo_2022-12-09_15-56-56.jpg"},

            {"name": "Букет из сладостей «Зефирный»", "price": "2990", "photo": "http://fruttosmile.su/wp-content/uploads/2017/01/photoeditorsdk-export192.png"},

            {"name": "Букет клубничный M Ажурный", "price": "4990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/03/photo_2024_08_11_18_53_18_481x582.jpg"},

            {"name": "Букет клубничный S Ажурный", "price": "3990", "photo": "http://fruttosmile.su/wp-content/uploads/2025/02/buket-klubnichnyj-s-azhurnyj-1.jpg"},

            {"name": "Букет клубничный с хризантемами", "price": "6990", "photo": "http://fruttosmile.su/wp-content/uploads/2016/07/photoeditorsdk-export213.png"}

        ],

        "5000_plus": [

            {"name": "Букет «Клубничная принцесса»", "price": "6990", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/photoeditorsdk-export135.png"},

            {"name": "Букет «Ягодное ассорти»", "price": "6490", "photo": "http://fruttosmile.su/wp-content/uploads/2016/12/photo_2024-04-05_17-55-09.jpg"},

            {"name": "Букет в шляпной коробке «с макаронсами»", "price": "6990", "photo": "http://fruttosmile.su/wp-content/uploads/2017/04/photo_2024-08-08_15-59-41.jpg"},

            {"name": "Букет из 101 клубники", "price": "16990", "photo": "http://fruttosmile.su/wp-content/uploads/2017/02/1649107507_70474509.jpg"},

            {"name": "Букет из сухофруктов и орехов «Для здоровья»", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2017/09/img_20240811_152040_726.jpg"},

            {"name": "Букет клубничный L Ажурный", "price": "5990", "photo": "http://fruttosmile.su/wp-content/uploads/2016/06/ghjj.png"},

            {"name": "Букет клубничный «Диадема» Стандарт", "price": "9990", "photo": "http://fruttosmile.su/wp-content/uploads/2017/03/photoeditorsdk-export21.png"},

            {"name": "Букет клубничный «Диадема» Премиум", "price": "14990", "photo": "http://fruttosmile.su/wp-content/uploads/2017/03/photoeditorsdk-export21.png"},

            {"name": "Букет клубничный с розами » Розовая нежность»", "price": "6990", "photo": "http://fruttosmile.su/wp-content/uploads/2016/09/photo_2024-08-08_16-33-40.jpg"}

        ]

    }

}

# ================= ЛОГИКА =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # всегда чистим при /start, чтобы не было старых данных

    # Если телефон уже сохранён — сразу меню
    if context.user_data.get('phone'):
        await show_main_menu(update, context)
        return

    # Просим поделиться номером
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Зарегистрироваться в программе лояльности", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.message.reply_text(
        "Добро пожаловать в Fruttosmile! 💝\n\n"
        "Чтобы сделать заказ и участвовать в программе лояльности, "
        "подтвердите ваш номер телефона (это займёт 1 секунду):",
        reply_markup=keyboard
    )
    # state не нужен, т.к. контакт ловим отдельным хэндлером


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if contact:
        phone = contact.phone_number
        name = contact.first_name or contact.last_name or "Клиент"

        context.user_data['name'] = name
        context.user_data['phone'] = phone

        await update.message.reply_text(
            f"Спасибо, {name}! Ваш номер {phone} сохранён ✅\n"
            "Теперь можете выбирать товары и оформлять заказы мгновенно.",
            reply_markup=ReplyKeyboardRemove()  # убираем кнопку с клавиатуры
        )

        await show_main_menu(update, context)
    else:
        await update.message.reply_text(
            "Не удалось получить номер. Попробуйте нажать кнопку ещё раз.",
            reply_markup=ReplyKeyboardRemove()
        )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Если сообщение — не текст (например, стикер, голосовое и т.д.) — игнорируем
    if not update.message.text:
        return

    state = context.user_data.get('state')
    if not state:
        return

    text = update.message.text

    if state == 'WAIT_QTY':
        try:
            qty = int(re.sub(r'\D', '', text))
            if qty < 1:
                raise ValueError
            context.user_data['qty'] = qty

            # Сразу к выбору способа получения (имя и телефон уже есть!)
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚚 Доставка (+400 ₽)", callback_data="method_delivery")],
                [InlineKeyboardButton("🏠 Самовывоз", callback_data="method_pickup")]
            ])
            await update.message.reply_text("Выберите способ получения:", reply_markup=kb)
            context.user_data['state'] = 'WAIT_METHOD'
        except:
            await update.message.reply_text("Пожалуйста, введите количество цифрами (минимум 1).")

    elif state == 'WAIT_ADDRESS':
        context.user_data['address'] = text
        context.user_data['state'] = 'WAIT_DATE'
        await update.message.reply_text("📅 Укажите дату и время доставки (например: 15.02 в 14:00):")

    elif state == 'WAIT_DATE':
        context.user_data['delivery_time'] = text
        context.user_data['state'] = 'WAIT_COMMENT'
        await update.message.reply_text("💬 Пожелания по оформлению (открытка, упаковка и т.д.):")

    elif state == 'WAIT_COMMENT':
        context.user_data['comment'] = text
        context.user_data['state'] = 'WAIT_CONFIRM'
        await show_order_preview(update, context)


# В main() замени/добавь хэндлеры так:

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Основные обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(cat_handler, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(subcat_handler, pattern="^sub_"))
    app.add_handler(CallbackQueryHandler(product_selected, pattern="^sel_"))
    app.add_handler(CallbackQueryHandler(delivery_method_handler, pattern="^method_"))
    app.add_handler(CallbackQueryHandler(payment_handler, pattern="^pay_"))
    app.add_handler(CallbackQueryHandler(confirm_handler, pattern="^(confirm_order|restart_order)$"))

    # Важно: отдельный хэндлер для контакта — выше всех текстовых
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    # Текстовые сообщения (заказ) — после контакта
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
