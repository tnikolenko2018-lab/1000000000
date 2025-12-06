import os
import logging
import json
import asyncio # Добавлен для синхронного запуска асинхронной функции
from flask import Flask, request, abort
from aiogram import Bot

# --- НАЛАШТУВАННЯ ---
logging.basicConfig(level=logging.INFO)

# Получение переменных среды (настроены в Render)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID") 

# Gunicorn ищет именно этот объект 'app'
app = Flask(__name__) 
# Создаем объект бота
bot = Bot(token=TELEGRAM_TOKEN)

# --- АНАЛИЗ JSON-СИГНАЛУ ВІД TRADINGVIEW ---
def format_signal_message(data):
    """Форматирует полученные данные в красивое сообщение для Telegram."""
    signal = data.get('signal', 'N/A').upper()
    pair = data.get('pair', 'N/A')
    price = data.get('price', 'N/A')
    timeframe = data.get('timeframe', 'N/A')
    info = data.get('info', 'Webhook Signal')
    
    # Определение эмодзи
    if signal == 'BUY':
        emo = "🟢 BUY (LONG)"
    elif signal == 'SELL':
        emo = "🔴 SELL (SHORT)"
    else:
        emo = "🟡 Signal"

    # Формируем текст сообщения
    message_text = (
        f"🔔 **НОВЫЙ СИГНАЛ!**\n\n"
        f"📈 **СИГНАЛ:** {emo}\n"
        f"📊 **АКТИВ:** `{pair}`\n"
        f"⏱️ **ТАЙМФРЕЙМ:** `{timeframe}`\n"
        f"💰 **ЦЕНА ВХОДА:** `{price}`\n\n"
        f"📝 **СТРАТЕГИЯ:** {info}\n"
        f"⏳ **ЭКСПИРАЦИЯ:** 2-3 минуты\n\n"
        "*(Подтверждено: EMA200, MACD, RSI, ADX)*"
    )
    return message_text

# --- ENDPOINT ДЛЯ WEBHOOK ---
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        try:
            data = request.get_json(force=True)
            logging.info(f"Получен Webhook: {data}")

            message_text = format_signal_message(data)
            
            # ВАЖНО: Выполняем асинхронную отправку сообщения синхронно через asyncio.run
            asyncio.run(
                bot.send_message(
                    chat_id=TARGET_CHAT_ID,
                    text=message_text,
                    parse_mode="Markdown"
                )
            )
            return 'OK', 200
            
        except Exception as e:
            logging.error(f"Ошибка обработки Webhook: {e}")
            return 'Error', 400
    else:
        # Отклоняем запросы, кроме POST
        abort(400) 

# Заглушка для Health Check Render
@app.route('/', methods=['GET'])
def health_check():
    # Проверка, что бот может создать соединение с Telegram
    if not bot.token:
        return 'Bot token is missing in Environment Variables.', 500
    return 'Bot is running and ready for webhooks.', 200
