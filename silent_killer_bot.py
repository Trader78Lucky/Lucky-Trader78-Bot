import time
import requests
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode

# === Tvoj Telegram bot token ===
BOT_TOKEN = '7701011442:AAEdy5RkdBadlnNNQmvEEuimqfNO6Ll-Z5M'

# === Anti-spam limiter ===
last_sent_time = 0
def throttle():
    global last_sent_time
    now = time.time()
    if now - last_sent_time < 10:
        return False
    last_sent_time = now
    return True

# === Komande bota ===

def start(update, context):
    if throttle():
        update.message.reply_text("Lucky_Trader78_Bot je aktivan! Spreman za akciju!")

def cena(update, context):
    if not throttle():
        return
    try:
        response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
        data = response.json()
        cena_btc = data['price']
        update.message.reply_text(f"Trenutna cena BTC-a: *{cena_btc}* USDT", parse_mode=ParseMode.MARKDOWN)
    except:
        update.message.reply_text("Greška pri dohvatanju cene BTC-a.")

def pozdrav(update, context):
    if throttle():
        update.message.reply_text("Nikad ne odustaj, Srećko! Idemo jako!")

def status(update, context):
    if throttle():
        update.message.reply_text("Pratim: BTCUSDT, GUNUSDT, TSTUSDT, KAITOUSDT...")

def get_top_movers(limit=5):
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    try:
        response = requests.get(url)
        data = response.json()
        usdt_pairs = [coin for coin in data if coin['symbol'].endswith('USDT')]
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['priceChangePercent']), reverse=True)
        top_movers = sorted_pairs[:limit]
        result = []
        for coin in top_movers:
            symbol = coin['symbol']
            change = float(coin['priceChangePercent'])
            price = float(coin['lastPrice'])
            result.append(f"{symbol}: {price} USDT ({change:+.2f}%)")
        return result
    except:
        return ["Greška pri dohvatanju podataka."]

def skener(update, context):
    if not throttle():
        return
    movers = get_top_movers()
    poruka = "Top Movers na Binance Futures:\n\n" + "\n".join(movers)
    update.message.reply_text(poruka)

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("cena", cena))
    dp.add_handler(CommandHandler("pozdrav", pozdrav))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("skener", skener))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()