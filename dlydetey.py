from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

from dotenv import load_dotenv
import os

# 🔐 Загружаем переменные из .env
load_dotenv()
print("Файлы в папке:", os.listdir("."))
print("Переменные окружения:", dict(os.environ))

# ✅ Получаем токен ПО ИМЕНИ переменной
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("❌ Не задан BOT_TOKEN. Проверь файл .env")
# 🟢 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋 Я бот-помощник для учеников.\nВыбери нужное действие:",
        reply_markup=get_keyboard()
    )

# 📱 Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📚 Моя домашка":
        await update.message.reply_text("🔗 Ссылка на домашку")
    elif text == "📅 Следующее занятие":
        await update.message.reply_text("📅 Следующее занятие: пятница, 19 апреля")
    else:
        await update.message.reply_text("Не понял команду.")

# 🚀 Основная функция
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен...")
    app.run_polling()  # ← Эта строка важна!

if __name__ == '__main__':
    main()

# 🌐 Имя Google Таблицы
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "автоматизация домашки_пробное")

# 🧪 Для проверки — увидим в консоли
print(f"✅ BOT_TOKEN успешно загружен: {TOKEN[:10]}...")  # Покажет первые 10 символов

# 🌐 Настройки
TOKEN = os.getenv("8236782787:AAHlUH0GXzvEQ5YrFXTwXyEkAUxVj_wY51I")  # Устанавливай в Replit Secrets или Render
GOOGLE_SHEET_NAME = os.getenv("автоматизация домашки_пробное")
SHEET_PAGE_NAME = "Лист1"  # или другое имя листа, если нужно

# 🕒 Таймзона Москвы
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

# 🧠 Подключение к Google Таблице
def connect_google_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open(GOOGLE_SHEET_NAME).worksheet(SHEET_PAGE_NAME)
        return sheet
    except Exception as e:
        print(f"❌ Ошибка подключения к Google Таблице: {e}")
        return None

# 🔍 Получение данных из таблицы по username или телефону
def get_student_data(sheet, username: str = None, phone: str = None):
    try:
        data = sheet.get_all_records()
    except Exception as e:
        print(f"Ошибка чтения таблицы: {e}")
        return None, None, None

    for row in data:
        tg = str(row.get("ТГ ученика", "")).strip().lower().lstrip("@")
        phone_cell = str(row.get("Телефон ученика", "")).strip()

        if (username and username.lower() == tg) or (phone and phone == phone_cell):
            return (
                row.get("Ссылка на домашку"),
                row.get("Дедлайн домашки"),
                row.get("Следующее занятие", "").strip()
            )
    return None, None, None

# ✅ Клавиатура
def get_keyboard():
    keyboard = [
        [KeyboardButton("📚 Моя домашка")],
        [KeyboardButton("📅 Следующее занятие")],
        [KeyboardButton("ℹ️ Полезная информация")],
        [KeyboardButton("📢 Написать учителю")],
        [KeyboardButton("❓ Частые вопросы")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# 🟢 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋 Я бот-помощник для учеников.\nВыбери нужное действие:",
        reply_markup=get_keyboard()
    )

# 📱 Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    sheet = context.bot_data.get("sheet")  # Получаем таблицу из bot_data

    if not sheet:
        await update.message.reply_text("❌ Система временно недоступна. Попробуй позже.")
        return

    if text == "📚 Моя домашка":
        username = user.username
        phone = None

        # Проверим, не сохранили ли контакт ранее
        if "phone" in context.user_data:
            phone = context.user_data["phone"]

        link, deadline, _ = get_student_data(sheet, username, phone)

        if not link and not deadline:
            await update.message.reply_text(
                "❌ Не удалось найти твою домашку. "
                "Убедись, что твой username или телефон указаны в таблице."
            )
            return

        message = "📚 Вот твоя домашняя работа:\n"
        if link:
            message += f"🔗 [Открыть задание]({link})\n"
        if deadline:
            message += f"⏰ Сдать до: *{deadline}*"

        await update.message.reply_text(message, parse_mode="Markdown")

    elif text == "📅 Следующее занятие":
        username = user.username
        lesson_str = None

        if "phone" in context.user_data:
            _, _, lesson_str = get_student_data(sheet, "", context.user_data["phone"])
        if not lesson_str:
            _, _, lesson_str = get_student_data(sheet, username, "")

        if lesson_str:
            await update.message.reply_text(f"*{lesson_str}*", parse_mode="Markdown")
        else:
            await update.message.reply_text("📅 Информация о следующем занятии пока не доступна.")

    elif text == "ℹ️ Полезная информация":
        info = (
            "📌 *Полезная информация:*\n\n"
            "• Занятия проходят по пятницам\n"
            "• Домашка сдаётся до 18:00\n"
            "• Обратная связь — в личные сообщения"
        )
        await update.message.reply_text(info, parse_mode="Markdown")

    elif text == "📢 Написать учителю":
        await update.message.reply_text("📩 Напиши сюда сообщение — я передам учителю.")

    elif text == "❓ Частые вопросы":
        faq = (
            "❓ *Частые вопросы:*\n\n"
            "1. *Когда следующее занятие?* — Проверь в разделе «Следующее занятие».\n"
            "2. *Как сдать домашку?* — Выполни задание и отправь учителю.\n"
            "3. *Не приходит домашка?* — Убедись, что твой username указан в таблице."
        )
        await update.message.reply_text(faq, parse_mode="Markdown")

    else:
        await update.message.reply_text("Не понял команду. Используй кнопки ниже.")

# 📱 Обработка контакта
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone_number = contact.phone_number
    context.user_data["phone"] = phone_number
    await update.message.reply_text(f"✅ Твой номер {phone_number} сохранён!")

# 🚀 Основная функция
def main():
    # Проверяем, есть ли токен
    if not TOKEN:
        print("❌ Не задан BOT_TOKEN. Установи переменную окружения BOT_TOKEN")
        return

    # Создаём приложение
    app = Application.builder().token(TOKEN).build()

    # Подключаемся к Google Таблице
    sheet = connect_google_sheets()
    if not sheet:
        print("❌ Не удалось подключиться к Google Таблице. Бот не запущен.")
        return

    # Сохраняем таблицу в bot_data, чтобы использовать в обработчиках
    app.bot_data["sheet"] = sheet

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))  # Обработка контакта

    # Запуск
    print("✅ Бот запущен и готов к работе...")
    app.run_polling()

if __name__ == '__main__':
    main()