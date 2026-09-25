import time
import requests
import json
from datetime import datetime, time as dtime
import pytz

# Aapka Telegram Token aur Chat ID
TOKEN = "8642396544:AAFJVudpn9zWK13a-SweJIkChoKExAk565A"
CHAT_ID = "6606431950"

def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=10)
        print("Telegram Response:", response.text)
    except Exception as e:
        print(f"Telegram error: {e}")

def check_bot_status():
    """GitHub repository se config.json check karega ki bot ON hai ya OFF"""
    try:
        url = "https://raw.githubusercontent.com/neeraj905/gn-algo-matrix/main/config.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            config = response.json()
            return config.get("bot_status", "OFF").upper()
    except Exception as e:
        print(f"Status check error: {e}")
    return "ON"

def get_live_market_data():
    """Yahoo Finance se Nifty aur Sensex ka real live price layega"""
    prices = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # Nifty 50
        nifty_url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1m"
        res = requests.get(nifty_url, headers=headers, timeout=8)
        if res.status_code == 200:
            data = res.json()
            result = data['chart']['result'][0]
            price = result['meta']['regularMarketPrice']
            previous_close = result['meta']['chartPreviousClose']
            prices['Nifty 50'] = {'price': price, 'prev_close': previous_close}
    except Exception as e:
        print(f"Nifty fetch error: {e}")

    try:
        # Sensex
        sensex_url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EBSESN?interval=1m"
        res = requests.get(sensex_url, headers=headers, timeout=8)
        if res.status_code == 200:
            data = res.json()
            result = data['chart']['result'][0]
            price = result['meta']['regularMarketPrice']
            previous_close = result['meta']['chartPreviousClose']
            prices['Sensex'] = {'price': price, 'prev_close': previous_close}
    except Exception as e:
        print(f"Sensex fetch error: {e}")

    return prices

if __name__ == '__main__':
    status = check_bot_status()
    print(f"Current Bot Status: {status}")

    if status == "ON":
        ist = pytz.timezone('Asia/Kolkata')
        current_time_str = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
        
        market_data = get_live_market_data()
        
        msg = "🚨 *GN ALGO MATRIX - TRADING SIGNAL* 🚨\n"
        msg += f"⏰ *Time (IST):* `{current_time_str}`\n\n"
        
            if market_data:
                if market_data:
        for symbol, data in market_data.items():
            price = data['price']
            prev_close = data['prev_close']
            change = price - prev_close
            change_pct = (change / prev_close) * 100
            
            # Signal Generation & Exit Logic
            if change_pct > 0.15:
                signal = "🟢 *BUY / CE (BULLISH)*"
                action = "💡 *Action:* Fresh Call trade le sakte hain."
            elif change_pct < -0.15:
                signal = "🔴 *SELL / PE (BEARISH)*"
                action = "💡 *Action:* Fresh Put trade le sakte hain."
            else:
                signal = "⚪ *EXIT / SQUARE OFF (URGENT)*"
                action = "⚠️ *Action:* Market sideways/reverse ho raha hai, apna purana maal turant SELL / exit kar dein!"
            
            msg += f"📊 *Index:* {symbol}\n"
            msg += f"💰 *Live Price:* `{price:.2f}`\n"
            msg += f"📈 *Change:* `{change:+.2f} ({change_pct:+.2f}%)`\n"
            msg += f"🎯 *Signal:* {signal}\n"
            msg += f"{action}\n"
            msg += f"-------------------\n"
        
        send_message(msg)
    else:
        print("Failed to fetch market data.")
        send_message("⚠️ Test message: Bot is running but market data fetch failed.")
            
             
