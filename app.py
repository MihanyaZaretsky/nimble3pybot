import os
import logging
import asyncio
from flask import Flask, request, jsonify, render_template_string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
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
application = Application.builder().token(BOT_TOKEN).build()

# HTML шаблон для Web App с Telegram Mini Apps SDK
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
        .balance {
            background: rgba(255, 215, 0, 0.2);
            padding: 15px;
            border-radius: 15px;
            margin: 20px 0;
            border: 2px solid #ffd700;
        }
        .bet-controls {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin: 20px 0;
        }
        .bet-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .bet-btn:hover {
            background: #45a049;
        }
        .payment-btn {
            background: #ff9800;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            margin: 10px;
            transition: background 0.3s;
        }
        .payment-btn:hover {
            background: #f57c00;
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
        
        <div class="balance">
            <h3>💰 Баланс: <span id="balance">100</span> Stars</h3>
        </div>
        
        <div class="bet-controls">
            <button class="bet-btn" onclick="placeBet(10)">Ставка 10</button>
            <button class="bet-btn" onclick="placeBet(50)">Ставка 50</button>
            <button class="bet-btn" onclick="placeBet(100)">Ставка 100</button>
        </div>
        
        <button class="payment-btn" onclick="buyStars()">💎 Купить Stars</button>
        <button class="payment-btn" onclick="withdrawStars()">💸 Вывести Stars</button>
        
        <button class="close-btn" onclick="closeWebApp()">Закрыть</button>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        
        // Инициализация Mini App
        tg.MainButton.setText('🎰 Играть в рулетку');
        tg.MainButton.show();
        
        // Обработка нажатия главной кнопки
        tg.MainButton.onClick(() => {
            spinRoulette();
        });
        
        let balance = 100;
        
        function updateBalance() {
            document.getElementById('balance').textContent = balance;
        }
        
        function placeBet(amount) {
            if (balance >= amount) {
                balance -= amount;
                updateBalance();
                tg.showAlert(`Ставка ${amount} Stars принята!`);
            } else {
                tg.showAlert('Недостаточно Stars!');
            }
        }
        
        function spinRoulette() {
            const result = Math.floor(Math.random() * 37); // 0-36
            const win = Math.random() > 0.5; // 50% шанс выигрыша
            
            if (win) {
                const winAmount = Math.floor(Math.random() * 200) + 50;
                balance += winAmount;
                tg.showAlert(`🎉 Выигрыш! +${winAmount} Stars`);
            } else {
                tg.showAlert('😔 Попробуйте еще раз!');
            }
            
            updateBalance();
            
            // Отправляем данные в бота
            tg.sendData(JSON.stringify({
                action: 'roulette_result',
                result: result,
                win: win,
                balance: balance
            }));
        }
        
        function buyStars() {
            tg.showPopup({
                title: '💎 Купить Stars',
                message: 'Выберите количество Stars для покупки',
                buttons: [
                    {text: '100 Stars - $1', type: 'buy'},
                    {text: '500 Stars - $5', type: 'buy'},
                    {text: '1000 Stars - $10', type: 'buy'},
                    {text: 'Отмена', type: 'cancel'}
                ]
            });
        }
        
        function withdrawStars() {
            if (balance > 0) {
                tg.showPopup({
                    title: '💸 Вывести Stars',
                    message: `Доступно для вывода: ${balance} Stars`,
                    buttons: [
                        {text: 'Вывести все', type: 'withdraw'},
                        {text: 'Отмена', type: 'cancel'}
                    ]
                });
            } else {
                tg.showAlert('Нет Stars для вывода!');
            }
        }
        
        function closeWebApp() {
            tg.close();
        }
        
        // Обработка событий от Telegram
        tg.onEvent('popupClosed', () => {
            console.log('Popup closed');
        });
        
        tg.onEvent('mainButtonClicked', () => {
            spinRoulette();
        });
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

🎮 *Nimble Roulette* - это захватывающая игра с Telegram Stars!
💎 Покупайте Stars, делайте ставки и выигрывайте!"""

    # Создаем кнопку Web App с WebAppInfo
    webapp_button = InlineKeyboardButton(
        text="🎮 Открыть Nimble Roulette",
        web_app=WebAppInfo(url=WEBAPP_URL)
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
        # Парсим данные от Mini App
        web_app_data = update.message.web_app_data.data
        import json
        data = json.loads(web_app_data)
        
        if data.get('action') == 'roulette_result':
            result = data.get('result')
            win = data.get('win')
            balance = data.get('balance')
            
            if win:
                await update.message.reply_text(
                    f"🎉 Поздравляем! Вы выиграли!\n"
                    f"🎰 Результат: {result}\n"
                    f"💰 Новый баланс: {balance} Stars"
                )
            else:
                await update.message.reply_text(
                    f"😔 Попробуйте еще раз!\n"
                    f"🎰 Результат: {result}\n"
                    f"💰 Баланс: {balance} Stars"
                )
        else:
            await update.message.reply_text("🎉 Данные получены! Обрабатываем результаты игры.")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке Web App данных: {e}")
        await update.message.reply_text("❌ Ошибка обработки данных")

# Обработчик ошибок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"❌ Ошибка бота: {context.error}")

# Функция запуска бота
async def run_bot():
    """Запуск Telegram бота"""
    try:
        logger.info("🤖 Запуск Telegram бота...")
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # Запускаем бота
        await application.initialize()
        await application.start()
        await application.run_polling(drop_pending_updates=True)
        
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
        update = Update.de_json(request.get_json(), application.bot)
        asyncio.create_task(application.process_update(update))
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
    def run_bot_sync():
        asyncio.run(run_bot())
    
    bot_thread = threading.Thread(target=run_bot_sync, daemon=True)
    bot_thread.start()
    logger.info("🤖 Бот запущен в отдельном потоке")

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    start_bot_thread()
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 