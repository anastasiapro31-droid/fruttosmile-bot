import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import gspread

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
import os
import json


# Scope для доступа к Google Sheets и Drive (оставь как было)
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Читаем ключ из переменной окружения (на Render)
GOOGLE_KEY_JSON = os.getenv("GOOGLE_KEY_JSON")

# Проверяем, что переменная вообще существует и не пустая
if GOOGLE_KEY_JSON is None or GOOGLE_KEY_JSON.strip() == "":
    raise ValueError("GOOGLE_KEY_JSON not set or empty in environment variables")

# Преобразуем строку в словарь (JSON)
creds_dict = json.loads(GOOGLE_KEY_JSON)

# Создаём credentials из словаря (без файла!)
from google.oauth2.service_account import Credentials
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
# Дальше всё как было
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

# ================= ВЫБОР ТОВАРА =================
async def product_selected(update, context):
    query = update.callback_query
    await query.answer()
 
    data = query.data
 
    if data.startswith("select_"):
        # Извлекаем техническое название товара из callback_data
        product_name = data.replace("select_", "") 
        
        # СОХРАНЯЕМ ДАННЫЕ В КОНТЕКСТ
        context.user_data['product'] = product_name      
        context.user_data['step'] = 'qty'                
        
        await query.message.reply_text("Товар выбран! Введите количество:")

# ================= ОФОРМЛЕНИЕ ЗАКАЗА =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, выбрал ли пользователь товар перед вводом текста
    if 'product' not in context.user_data:
        await update.message.reply_text("Что-то пошло не так. Начните заказ заново: /start")
        context.user_data.clear()
        return
 
    step = context.user_data.get("step", "qty")
 
    if step == "qty":
        qty_text = update.message.text.strip()
        
        # Валидация числа
        if not qty_text.isdigit() or int(qty_text) <= 0:
            await update.message.reply_text("Пожалуйста, введите положительное число (количество):")
            return
 
        context.user_data["qty"] = int(qty_text)
 
        # Формируем текст для пользователя
        order_text = (
            f"✅ Проверьте ваш заказ:\n\n"
            f"Товар: {context.user_data.get('product', '-')}\n"
            f"Количество: {context.user_data.get('qty', '-')}\n"
        )
        await update.message.reply_text(order_text)
 
        # Запись в Google Sheets
        try:
            # Убедитесь, что переменная 'sheet' и 'datetime' определены выше в коде
            sheet.append_row([
                datetime.now().strftime("%d.%m.%Y %H:%M"),
                context.user_data.get('product', '-'),
                context.user_data.get('variant', '-'), # Если используется
                context.user_data.get('qty', '-'),
                context.user_data.get('name', '-'),
                context.user_data.get('phone', '-'),
                context.user_data.get('address', '-')
            ])
            print("Заказ успешно записан в Google Sheets")
            await update.message.reply_text("Заказ успешно оформлен! Мы свяжемся с вами скоро ❤️")
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"Ошибка записи в Google Sheets:\n{error_msg}")
            # Убедитесь, что ADMIN_CHAT_ID определен в начале файла
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Ошибка записи заказа:\n{error_msg}")
            await update.message.reply_text("Произошла ошибка при сохранении. Но мы уже получили уведомление!")
 
        # Очищаем данные после успешного завершения
        context.user_data.clear()
    else:
        await update.message.reply_text("Пожалуйста, начните сначала: /start")
        context.user_data.clear()
 
# ================= ОСНОВНАЯ ЧАСТЬ (MAIN) =================
def main():
    # Используем ApplicationBuilder для создания приложения
    app = ApplicationBuilder().token(BOT_TOKEN).build()
 
    # Регистрация команд
    app.add_handler(CommandHandler("start", start))
    
    # Регистрация переходов "Назад"
    app.add_handler(CallbackQueryHandler(go_back, pattern="^back_main$"))
 
    # Категории и цены
    app.add_handler(CallbackQueryHandler(boxes_category, pattern="^cat_boxes$"))
    app.add_handler(CallbackQueryHandler(boxes_price, pattern="^box_(0_3000|3000_5000|5000_plus)$"))
 
    app.add_handler(CallbackQueryHandler(flowers_category, pattern="^cat_flowers$"))
 
    app.add_handler(CallbackQueryHandler(meat_category, pattern="^cat_meat$"))
 
    app.add_handler(CallbackQueryHandler(sweet_category, pattern="^cat_sweet$"))
    app.add_handler(CallbackQueryHandler(sweet_price, pattern="^sweet_(0_3000|3000_5000|5000_plus)$"))
 
    # Обработка нажатия кнопки "Выбрать"
    app.add_handler(CallbackQueryHandler(product_selected, pattern="^select_"))
 
    # Обработка ввода количества (любой текст, который не команда)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
 
    print("Бот запущен и готов к работе...")
    app.run_polling()
 
if __name__ == "__main__":
    main()
