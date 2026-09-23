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

def get_market_status():
    """Check karta hai ki abhi Indian Stock Market (NSE) khula hai ya nahi (9:15 AM - 3:30 PM IST)"""
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    
    # Weekend check (Saturday = 5, Sunday = 6)
    if now_ist.weekday() >= 5:
        return False, "Market is CLOSED (Weekend)"
    
    current_time = now_ist.time()
    market_open = dtime(9, 15)
    market_close = dtime(15, 30)
    
    if market_open <= current_time <= market_close:
        return True, "Market is OPEN"
    else:
        return False, "Market is CLOSED (Timing: 09:15 AM - 03:30 PM)"

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
    # 1. Check ON/OFF Status
    status = check_bot_status()
    print(f"Current Bot Status: {status}")

    if status == "ON":
        ist = pytz.timezone('Asia/Kolkata')
        current_time_str = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
        
        # Market timing & live data fetch
        market_open, market_msg = get_market_status()
        market_data = get_live_market_data()
        
        msg = "🚨 *GN ALGO MATRIX - REAL-TIME TRADING SYSTEM* 🚨\n"
        msg += f"⏰ *Time (IST):* `{current_time_str}`\n"
        msg += f"📌 *Market State:* {market_msg}\n\n"
        
        if market_data:
            for symbol, data in market_data.items():
                price = data['price']
                prev_close = data['prev_close']
                change = price - prev_close
                change_pct = (change / prev_close) * 100
                
                # Trading Logic & Signal Decision
                if change >= 0:
                    signal = "🟢 *BUY CALL (BULLISH)*"
                    trend_icon = "📈"
                else:
                    signal = "🔴 *BUY PUT (BEARISH)*"
                    trend_icon = "📉"
                
                # Drop / Jump alert logic (Agar market tezi se upar/niche ho)
                alert_note = ""
                if abs(change_pct) > 0.5:
                    alert_note = f"\n⚠️ *HIGH VOLATILITY ALERT:* Mov by {change_pct:.2f}%!"

                msg += f"📊 *Index:* {symbol}\n"
                msg += f"💰 *Live Price:* `{price:,.2f}`\n"
                msg += f"📊 *Change:* `{change:+.2f} ({change_pct:+.2f}%)` {trend_icon}\n"
                msg += f"🎯 *Signal:* {signal}{alert_note}\n"
                msg += "-----------------------------------\n"
            
            send_message(msg)
        else:
            print("Failed to fetch market data.")
    else:
        print("Bot is currently OFF via config.json.")
    
