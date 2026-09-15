import time
import asyncio
import logging
import os
import requests
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ProductionSignalEngine:
    def __init__(self, symbol="NIFTY", spike_threshold=15, time_window=2):
        self.symbol = symbol
        self.spike_threshold = spike_threshold
        self.time_window = time_window
        self.last_price = None
        self.last_time = None
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    async def start_engine(self):
        logging.info(f"GN Algo Matrix Server Active for {self.symbol}...")
        
        while True:
            try:
                # Live feed tick simulation / integration point
                current_price, current_volume = 24500.0, 1500000 
                await self.evaluate_triggers(current_price, current_volume)
            except Exception as e:
                logging.error(f"Engine exception caught: {e}. Retrying...")
                await asyncio.sleep(2)
            
            await asyncio.sleep(1)

    async def evaluate_triggers(self, price, volume):
        now = time.time()
        
        if self.last_price is not None:
            price_diff = price - self.last_price
            time_diff = now - self.last_time
            
            if abs(price_diff) >= self.spike_threshold and time_diff <= self.time_window:
                if price_diff > 0:
                    signal = "🟢 STRONG BUY CALL (CE) / BULLISH SPIKE"
                    advice = "Rapid upward momentum detected. Look for Call entry setup."
                else:
                    signal = "🔴 STRONG SELL / PUT CALL (PE) / BEARISH DROP"
                    advice = "Sharp breakdown detected. Watch for Put entry or exit positions."
                
                self.send_telegram_alert(signal, price, price_diff, advice)

        self.last_price = price
        self.last_time = now

    def send_telegram_alert(self, signal, price, diff, advice):
        msg = (
            f"🚨 *GN ALGO MATRIX ALERT* 🚨\n\n"
            f"🔹 *Signal:* {signal}\n"
            f"📊 *Symbol:* {self.symbol}\n"
            f"📈 *Movement:* {diff} Points\n"
            f"💰 *Price:* {price}\n"
            f"💡 *Action:* {advice}\n"
            f"⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        if self.token and self.chat_id:
            try:
                telegram_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
                payload = {
                    "chat_id": self.chat_id,
                    "text": msg,
                    "parse_mode": "Markdown"
                }
                requests.post(telegram_url, json=payload, timeout=5)
            except Exception as ex:
                logging.error(f"Failed to push Telegram notification: {ex}")
        else:
            print(msg)

if __name__ == "__main__":
    engine = ProductionSignalEngine()
    # To run on server/local:
    # asyncio.run(engine.start_engine())
  
