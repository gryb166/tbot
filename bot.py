# bot.py - Long/Short Switching Bot (Binance Futures) with SQLite logging
import argparse
import time
import math
import os
from datetime import datetime
from binance.client import Client
from db import init_db, save_trade, DB_PATH

# ------------------------------
# API Keys (для тесту можна залишити пусті рядки)
# ------------------------------
API_KEY = "";
API_SECRET = "";

# ------------------------------
# Аргументи командного рядка
# ------------------------------
parser = argparse.ArgumentParser(description="Long/Short Switching Bot (Binance Futures)")
parser.add_argument("--symbol", type=str, required=True, help="Trading pair e.g. BTCUSDT, SOLUSDT")
parser.add_argument("--long_tp", type=float, required=True, help="Price increase % for closing long")
parser.add_argument("--long_to_short", type=float, required=True, help="Price drop % for switching long → short")
parser.add_argument("--short_tp", type=float, required=True, help="Price drop % for closing short")
parser.add_argument("--short_to_long", type=float, required=True, help="Price increase % for switching short → long")
parser.add_argument("--start", type=float, default=1, help="Start USDT margin")
parser.add_argument("--lev", type=int, default=10, help="Leverage")
args = parser.parse_args()

SYMBOL = args.symbol.upper()
LONG_TP_PCT = args.long_tp / 100
LONG_TO_SHORT_PCT = args.long_to_short / 100
SHORT_TP_PCT = args.short_tp / 100
SHORT_TO_LONG_PCT = args.short_to_long / 100
START_USDT = args.start
LEVERAGE = args.lev

# ------------------------------
# Перевірка ключів
# ------------------------------
if not API_KEY or not API_SECRET:
    print("⚠ WARNING: API_KEY і API_SECRET не встановлені. Робимо запуск в testnet режимі.")

client = Client(API_KEY, API_SECRET, testnet=True)

# ------------------------------
# Функції для роботи з Binance
# ------------------------------
def get_mark_price():
    info = client.futures_mark_price(symbol=SYMBOL)
    return float(info["markPrice"])

def get_step(symbol):
    info = client.futures_exchange_info()
    for s in info["symbols"]:
        if s["symbol"] == symbol:
            for f in s["filters"]:
                if f["filterType"] == "LOT_SIZE":
                    return float(f["stepSize"])
    return 0.000001

def round_qty(qty):
    step = get_step(SYMBOL)
    return math.floor(qty / step) * step

def market_order(side, margin_usdt, position_counter, long_count, short_count):
    price = get_mark_price()
    qty = round_qty((margin_usdt * LEVERAGE) / price)

    if qty <= 0:
        raise ValueError("Computed quantity is 0. Adjust margin/leverage or check step size.")

    if side == "BUY":
        long_count += 1
        print(f"🟢 OPEN LONG #{long_count} | Qty: {qty} | Margin: {margin_usdt}$")
    else:
        short_count += 1
        print(f"🔴 OPEN SHORT #{short_count} | Qty: {qty} | Margin: {margin_usdt}$")

    print(f"📌 Total opened positions: {position_counter}")

    client.futures_create_order(
        symbol=SYMBOL,
        side=side,
        type="MARKET",
        quantity=qty
    )

    return qty, price, long_count, short_count

def close_position():
    print("🛑 Closing entire position!")
    pos = client.futures_position_information(symbol=SYMBOL)[0]
    amt = float(pos["positionAmt"])
    qty = abs(amt)

    if qty == 0:
        print("⚠ No position to close.")
        return None, None, None

    side = "SELL" if amt > 0 else "BUY"
    client.futures_create_order(
        symbol=SYMBOL,
        side=side,
        type="MARKET",
        quantity=qty,
        reduceOnly=True
    )

    return ("LONG" if amt > 0 else "SHORT"), qty, get_mark_price()

# ------------------------------
# Основна логіка бота
# ------------------------------
def main():
    print("====================================")
    print("🚀 Long/Short Switching Bot (with SQLite logging)")
    print(f"Symbol: {SYMBOL}")
    print("====================================\n")

    init_db()
    client.futures_change_leverage(symbol=SYMBOL, leverage=LEVERAGE)

    position_counter = 0
    long_count = 0
    short_count = 0
    long_win = 0
    long_loss = 0
    short_win = 0
    short_loss = 0
    position = "LONG"
    margin = START_USDT
    entry_price = None
    entry_side = None

    while True:
        try:
            # Відкриваємо LONG
            position_counter += 1
            qty, entry_price, long_count, short_count = market_order(
                "BUY", margin, position_counter, long_count, short_count
            )
            entry_side = "LONG"
            print(f"✔ Entered initial LONG at {entry_price}")

            while True:
                mark = get_mark_price()
                change_pct = (mark - entry_price) / entry_price

                print(
                    f"Mark: {mark:.4f} | Entry: {entry_price:.4f} | "
                    f"Change: {change_pct*100:.2f}% | Position: {position} | "
                    f"Total: {position_counter} | "
                    f"L+{long_win}-{long_loss} | S+{short_win}-{short_loss}"
                )

                # ===== LONG =====
                if position == "LONG":
                    if change_pct >= LONG_TP_PCT:
                        print("🎯 LONG TP reached → closing")
                        closed_side, closed_qty, exit_price = close_position()
                        if closed_side:
                            change = (exit_price - entry_price) / entry_price
                            result = "WIN" if change > 0 else "LOSS"
                            save_trade("LONG", result, entry_price, exit_price, change)
                            long_win += 1 if result == "WIN" else 0
                            long_loss += 1 if result == "LOSS" else 0
                        print("🔁 Reopening LONG")
                        position_counter += 1
                        qty, entry_price, long_count, short_count = market_order(
                            "BUY", margin, position_counter, long_count, short_count
                        )
                        continue
                    elif change_pct <= -LONG_TO_SHORT_PCT:
                        print("🔄 LONG stop hit → switching to SHORT")
                        closed_side, closed_qty, exit_price = close_position()
                        if closed_side:
                            change = (exit_price - entry_price) / entry_price
                            result = "WIN" if change > 0 else "LOSS"
                            save_trade("LONG", result, entry_price, exit_price, change)
                            long_win += 1 if result == "WIN" else 0
                            long_loss += 1 if result == "LOSS" else 0
                        position = "SHORT"
                        position_counter += 1
                        qty, entry_price, long_count, short_count = market_order(
                            "SELL", margin, position_counter, long_count, short_count
                        )
                        entry_side = "SHORT"
                        continue

                # ===== SHORT =====
                elif position == "SHORT":
                    change_pct = (mark - entry_price) / entry_price
                    if change_pct <= -SHORT_TP_PCT:
                        print("🎯 SHORT TP reached → closing")
                        closed_side, closed_qty, exit_price = close_position()
                        if closed_side:
                            change = (entry_price - exit_price) / entry_price
                            result = "WIN" if change > 0 else "LOSS"
                            save_trade("SHORT", result, entry_price, exit_price, -change)
                            short_win += 1 if result == "WIN" else 0
                            short_loss += 1 if result == "LOSS" else 0
                        print("🔁 Reopening SHORT")
                        position_counter += 1
                        qty, entry_price, long_count, short_count = market_order(
                            "SELL", margin, position_counter, long_count, short_count
                        )
                        continue
                    elif change_pct >= SHORT_TO_LONG_PCT:
                        print("🔄 SHORT stop hit → switching to LONG")
                        closed_side, closed_qty, exit_price = close_position()
                        if closed_side:
                            change = (entry_price - exit_price) / entry_price
                            result = "WIN" if change > 0 else "LOSS"
                            save_trade("SHORT", result, entry_price, exit_price, -change)
                            short_win += 1 if result == "WIN" else 0
                            short_loss += 1 if result == "LOSS" else 0
                        position = "LONG"
                        position_counter += 1
                        qty, entry_price, long_count, short_count = market_order(
                            "BUY", margin, position_counter, long_count, short_count
                        )
                        continue

                time.sleep(1)

        except Exception as e:
            print(f"❌ ERROR: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
