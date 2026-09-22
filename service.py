import time
import requests
from datetime import datetime

# Telegram Credentials
TOKEN = "8642396544:AAFJVudpn9zWK13a-SweJIkChoKExAk565A"
CHAT_ID = "6606431950"

def send_alert(index_name, signal_type, price):
    msg = (
        f"🚨 *GN ALGO MATRIX FOREGROUND ALERT* 🚨\n\n"
        f"📊 *Index:* {index_name}\n"
        f"⚡ *Signal:* {signal_type}\n"
        f"💰 *Price:* {price:,.2f}\n"
        f"⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"🎯 _Background Service Active!_"
    )
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Service Telegram error: {e}")

if __name__ == '__main__':
    import random
    prices = {"Nifty 50": 24500.0, "Bank Nifty": 45000.0, "Sensex": 75000.0}
    
    while True:
        for idx in prices:
            change = random.uniform(-150, 150)
            prices[idx] += change
            if change <= -100:
                send_alert(idx, "📉 BUY PUT / PUT SELL", prices[idx])
            elif change >= 100:
                send_alert(idx, "📈 BUY CALL / CALL BUY", prices[idx])
        time.sleep(10)
  
