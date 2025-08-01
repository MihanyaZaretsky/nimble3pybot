import os
import logging
from flask import Flask, request, jsonify, render_template_string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
import asyncio
import threading

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)

# Получаем токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://nimble3tgbot.onrender.com')

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден в переменных окружения!")
    exit(1)

# Создаем приложение Telegram
telegram_app = Application.builder().token(BOT_TOKEN).build()

# HTML шаблон для Web App
WEBAPP_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nimble Roulette</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .container {
            text-align: center;
            max-width: 400px;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        h1 {
            margin-bottom: 20px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        .roulette-wheel {
            width: 200px;
            height: 200px;
            border: 8px solid #ffd700;
            border-radius: 50%;
            margin: 20px auto;
            background: conic-gradient(
                #ff0000 0deg 45deg,
                #000000 45deg 90deg,
                #ff0000 90deg 135deg,
                #000000 135deg 180deg,
                #ff0000 180deg 225deg,
                #000000 225deg 270deg,
                #ff0000 270deg 315deg,
                #000000 315deg 360deg
            );
            animation: spin 3s ease-out;
        }
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .placeholder-text {
            margin-top: 20px;
            font-size: 1.2em;
            opacity: 0.8;
        }
        .close-btn {
            background: #ff6b6b;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 20px;
            transition: background 0.3s;
        }
        .close-btn:hover {
            background: #ff5252;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎰 Nimble Roulette</h1>
        <div class="roulette-wheel"></div>
        <p class="placeholder-text">
            🎲 Это заглушка для Web App<br>
            Здесь будет настоящая игра в рулетку!
        </p>
        <button class="close-btn" onclick="closeWebApp()">Закрыть</button>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();

        function closeWebApp() {
            tg.close();
        }
    </script>
</body>
</html>
"""

# Обработчик команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    logger.info(f"🎯 Получена команда /start от: {update.effective_user.first_name}")
    
    username = update.effective_user.first_name
    chat_id = update.effective_chat.id
    
    welcome_message = f"""🎰 Добро пожаловать в *Nimble Roulette*, {username}! 🎰

🎲 Готов испытать удачу? Нажми на кнопку ниже, чтобы открыть игру!

🎮 *Nimble Roulette* - это захватывающая игра, где каждый может стать победителем!"""

    # Создаем кнопку Web App
    webapp_button = InlineKeyboardButton(
        text="🎮 Открыть Nimble Roulette",
        web_app={"url": WEBAPP_URL}
    )
    
    keyboard = InlineKeyboardMarkup([[webapp_button]])
    
    try:
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        logger.info(f"✅ Сообщение отправлено пользователю: {username}")
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке сообщения: {e}")

# Обработчик callback_query
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

# Обработчик Web App данных
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик данных от Web App"""
    logger.info("📱 Получены данные от Web App")
    chat_id = update.effective_chat.id
    
    try:
        await update.message.reply_text("🎉 Данные получены! Скоро здесь будет обработка результатов игры.")
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке Web App данных: {e}")

# Обработчик ошибок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"❌ Ошибка бота: {context.error}")

# Функция запуска бота
def run_bot():
    """Запуск Telegram бота"""
    try:
        logger.info("🤖 Запуск Telegram бота...")
        
        # Добавляем обработчики
        telegram_app.add_handler(CommandHandler("start", start_command))
        telegram_app.add_handler(CallbackQueryHandler(button_callback))
        
        # Запускаем бота
        telegram_app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")

# Flask маршруты
@app.route('/')
def home():
    """Главная страница Web App"""
    return WEBAPP_HTML

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook для Telegram"""
    try:
        update = Update.de_json(request.get_json(), telegram_app.bot)
        telegram_app.process_update(update)
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"❌ Ошибка webhook: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/health')
def health():
    """Проверка здоровья сервиса"""
    return jsonify({"status": "healthy", "bot": "running"})

# Запуск бота в отдельном потоке
def start_bot_thread():
    """Запуск бота в отдельном потоке"""
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("🤖 Бот запущен в отдельном потоке")

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    start_bot_thread()
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 