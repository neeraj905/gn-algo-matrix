import os
import requests

# ==========================================
# 1. CREDENTIALS SETUP (GitHub Secrets se uthayega)
# ==========================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ==========================================
# 2. LIVE MARKET DATA FETCH SERVICE
# ==========================================
def get_live_market_data():
    """
    Yahoo Finance se Nifty 50, Nifty Next 50, aur Sensex 
    ka exact spot index data fetch karta hai.
    """
    prices = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Official Spot Index Tickers for Yahoo Finance
    indices = {
        'Nifty 50': '%5ENSEI',          # Nifty 50 Spot (^NSEI)
        'Nifty Next 50': '%5ENSEMDCP0', # Nifty Next 50 Spot (^NSEMDCP0)
        'Sensex': '%5EBSESN'            # Sensex Spot (^BSESN)
    }
    
    for name, ticker in indices.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m"
            res = requests.get(url, headers=headers, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                result = data['chart']['result'][0]
                meta = result['meta']
                
                price = meta.get('regularMarketPrice')
                prev_close = meta.get('chartPreviousClose') or meta.get('previousClose')
                
                if price and prev_close:
                    change = price - prev_close
                    change_pct = (change / prev_close) * 100
                    prices[name] = {
                        'price': price,
                        'prev_close': prev_close,
                        'change': change,
                        'change_pct': change_pct
                    }
        except Exception as e:
            print(f"Error fetching {name}: {e}")

    return prices

# ==========================================
# 3. SIGNAL & STRATEGY LOGIC (CALL / PUT / SIDEWAYS)
# ==========================================
def evaluate_signal(change_pct):
    """
    Percentage change ke base par decide karta hai ki 
    Call (CE), Put (PE) ya Sideways signal bnega.
    """
    # Agar fluctuation -0.15% se +0.15% ke beech hai toh Sideways maana jayega
    if -0.15 <= change_pct <= 0.15:
        return {
            "signal": "🟡 SIDEWAYS / RANGE-BOUND",
            "action": "Market range-bound hai, filhal koi fresh trade avoid karein."
        }
    elif change_pct > 0.15:
        return {
            "signal": "🟢 BUY / CE (BULLISH)",
            "action": "Fresh Call (CE) trade le sakte hain."
        }
    else:
        return {
            "signal": "🔴 SELL / PE (BEARISH)",
            "action": "Fresh Put (PE) trade le sakte hain."
        }

# ==========================================
# 4. TELEGRAM ALERT SENDER
# ==========================================
def send_telegram_alert(message):
    """
    Telegram bot ke zariye formatted message bhejta hai.
    """
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Error: Telegram TOKEN ya CHAT_ID missing hai!")
        return None
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Telegram alert error: {e}")
        return None
        
