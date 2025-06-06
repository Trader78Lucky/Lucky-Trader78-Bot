import time
import threading
import requests
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode

# === TOKEN TVOG BOTA ===
BOT_TOKEN = '7701011442:AAEdy5RkdBadlnNNQmveEuimqfNO6Ll-Z5M'

# === Globalne promenljive ===
last_sent_time = 0
price_alerts = {}
volume_alerts = {}

# === Anti-spam limiter ===
def throttle():
    global last_sent_time
    now = time.time()
    if now - last_sent_time < 10:
        return False
    last_sent_time = now
    return True

# === Komande ===

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
        update.message.reply_text(f"Trenutna cena BTC-a: {cena_btc} USDT")
    except:
        update.message.reply_text("Greška pri dohvatanju cene.")

def pozdrav(update, context):
    update.message.reply_text("Pozdrav, legendo!")

def status(update, context):
    pairs = list(price_alerts.keys()) + list(volume_alerts.keys())
    poruka = f"Pratim: {', '.join(pairs)}" if pairs else "Nema aktivnih parova za praćenje."
    update.message.reply_text(poruka)

def get_top_movers(limit=5):
    try:
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        response = requests.get(url)
        data = response.json()
        usdt_pairs = [coin for coin in data if coin["symbol"].endswith("USDT")]
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x["priceChangePercent"]), reverse=True)
        top_movers = sorted_pairs[:limit]
        result = []
        for coin in top_movers:
            symbol = coin['symbol']
            change = float(coin['priceChangePercent'])
            price = float(coin['lastPrice'])
            result.append(f"{symbol}: {price:.5f} USDT ({change:+.2f}%)")
        return result
    except:
        return ["Greška pri dohvatanju podataka."]

def skener(update, context):
    if not throttle():
        return
    movers = get_top_movers()
    poruka = "Top Movers na Binance Futures:\n\n" + "\n".join(movers)
    update.message.reply_text(poruka)

def alert(update, context):
    if not throttle():
        return
    try:
        symbol = context.args[0].upper()
        target = float(context.args[1])
        chat_id = update.message.chat_id
        if symbol not in price_alerts:
            price_alerts[symbol] = []
        price_alerts[symbol].append((chat_id, target))
        update.message.reply_text(f"Alert postavljen: {symbol} kada pređe {target}")
    except:
        update.message.reply_text("Koristi komandu ovako:\n/alert BTCUSDT 68000")

def volumen(update, context):
    if not throttle():
        return
    try:
        symbol = context.args[0].upper()
        target_vol = float(context.args[1])
        chat_id = update.message.chat_id
        if symbol not in volume_alerts:
            volume_alerts[symbol] = []
        volume_alerts[symbol].append((chat_id, target_vol))
        update.message.reply_text(f"Volumen alert postavljen: {symbol} kada pređe {target_vol} USDT.")
    except:
        update.message.reply_text("Koristi komandu ovako:\n/volumen BTCUSDT 100000000")

# === Provera alertova ===

def check_alerts(updater):
    while True:
        # --- Provera volumena ---
        for symbol in list(volume_alerts):
            try:
                url = f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}"
                response = requests.get(url)
                volume = float(response.json()["quoteVolume"])
                triggered = []
                for chat_id, target_vol in volume_alerts[symbol]:
                    if volume >= target_vol:
                        updater.bot.send_message(
                            chat_id=chat_id,
                            text=f"ALERT: Volumen za {symbol} je sada {volume:,.3f} USDT (prešao {target_vol:,}!)"
                        )
                        triggered.append((chat_id, target_vol))
                volume_alerts[symbol] = [
                    entry for entry in volume_alerts[symbol] if entry not in triggered
                ]
            except:
                pass

        # --- Provera cene ---
        for symbol in list(price_alerts):
            try:
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
                response = requests.get(url)
                price = float(response.json()["price"])
                triggered = []
                for chat_id, target in price_alerts[symbol]:
                    if price >= target:
                        updater.bot.send_message(
                            chat_id=chat_id,
                            text=f"ALERT: Cena za {symbol} je sada {price} USDT (prešla {target})"
                        )
                        triggered.append((chat_id, target))
                price_alerts[symbol] = [
                    entry for entry in price_alerts[symbol] if entry not in triggered
                ]
            except:
                pass

        time.sleep(10)

# === Pokretanje bota ===

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("cena", cena))
    dp.add_handler(CommandHandler("pozdrav", pozdrav))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("skener", skener))
    dp.add_handler(CommandHandler("alert", alert))
    dp.add_handler(CommandHandler("volumen", volumen))

    threading.Thread(target=check_alerts, args=(updater,), daemon=True).start()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()