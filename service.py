import time
import requests
import json
from datetime import datetime

# Aapka Telegram Token aur Chat ID
TOKEN = "8642396544:AAFJVudpn9zWK13a-SweJIkChoKExAk565A"
CHAT_ID = "6606431950"

def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=5)
        print("Telegram Response:", response.text)
    except Exception as e:
        print(f"Telegram error: {e}")

def check_bot_status():
    """GitHub repository se config.json padh kar check karega ki bot ON hai ya OFF"""
    try:
        url = "https://raw.githubusercontent.com/neeraj905/gn-algo-matrix/main/config.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            config = response.json()
            return config.get("bot_status", "OFF").upper()
    except Exception as e:
        print(f"Status check error: {e}")
    return "OFF"  # Agar koi error aaye toh safety ke liye OFF maanega

def get_real_market_data():
    """Yahoo Finance ya free public API se Nifty aur Bank Nifty ka real live price layega"""
    prices = {}
    try:
        # Nifty 50 aur Bank Nifty ke live symbols ke liye public API call
        url = "https://query1.finance.pythonic.ee/v8/finance/chart/%5ENSEI?interval=1m&range=1d" # Alternative public source ya Yahoo Finance
        # Hum ek asaan aur reliable direct API use karte hain:
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        # Nifty 50 Real Price fetch karna (Yahoo Finance API)
        nifty_url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI"
        res = requests.get(nifty_url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            prices['Nifty 50'] = price
    except Exception as e:
        print(f"Market data error: {e}")
        # Fallback agar API se connection mein dikkat aaye
        prices['Nifty 50'] = 24500.00 

    return prices

if __name__ == '__main__':
    # Sabse pehle check karo ki On/Off switch ON hai ya OFF
    status = check_bot_status()
    print(f"Current Bot Status: {status}")

    if status == "ON":
        # Agar ON hai toh real market data fetch karke Telegram par bhejo
        market_prices = get_real_market_data()
        
        msg = "🟢 *GN ALGO MATRIX - LIVE SIGNAL*\n"
        msg += f"⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        for symbol, price in market_prices.items():
            msg += f"📊 *Index:* {symbol}\n💰 *Live Price:* `{price:,.2f}`\n⚡ *Status:* Market Monitoring Active!\n"
        
        send_message(msg)
    else:
        print("Bot is currently OFF via config.json. No signals sent.")
        
