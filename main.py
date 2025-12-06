import os
import logging
import json
from flask import Flask, request, abort
from aiogram import Bot

# --- НАЛАШТУВАННЯ ---
logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID") 

# Gunicorn шукає саме цей об'єкт 'app'
app = Flask(__name__) 
bot = Bot(token=TELEGRAM_TOKEN)

# --- АНАЛІЗ JSON-СИГНАЛУ ВІД TRADINGVIEW ---
def format_signal_message(data):
    """Форматує отримані дані в красиве повідомлення для Telegram."""
    signal = data.get('signal', 'N/A').upper()
    pair = data.get('pair', 'N/A')
    price = data.get('price', 'N/A')
    timeframe = data.get('timeframe', 'N/A')
    info = data.get('info', 'Webhook Signal')
    
    if signal == 'BUY':
        emo = "🟢 BUY (LONG)"
    elif signal == 'SELL':
        emo = "🔴 SELL (SHORT)"
    else:
        emo = "🟡 Signal"

    message_text = (
        f"🔔 **НОВИЙ СИГНАЛ!**\n\n"
        f"📈 **СИГНАЛ:** {emo}\n"
        f"📊 **АКТИВ:** `{pair}`\n"
        f"⏱️ **ТАЙМФРЕЙМ:** `{timeframe}`\n"
        f"💰 **ЦІНА ВХОДУ:** `{price}`\n\n"
        f"📝 **СТРАТЕГІЯ:** {info}\n"
        f"⏳ **ЕКСПІРАЦІЯ:** 2-3 хвилини\n\n"
        "*(Підтверджено: EMA200, MACD, RSI, ADX)*"
    )
    return message_text

# --- ENDPOINT ДЛЯ WEBHOOK ---
@app.route('/webhook', methods=['POST'])
async def webhook():
    if request.method == 'POST':
        try:
            data = request.get_json(force=True)
            logging.info(f"Отримано Webhook: {data}")

            message_text = format_signal_message(data)
            await bot.send_message(
                chat_id=TARGET_CHAT_ID,
                text=message_text,
                parse_mode="Markdown"
            )
            return 'OK', 200
            
        except Exception as e:
            logging.error(f"Помилка обробки Webhook: {e}")
            return 'Error', 400
    else:
        abort(400) 

# Заглушка для Health Check Render
@app.route('/', methods=['GET'])
def health_check():
    return 'Bot is running and ready for webhooks.', 200
