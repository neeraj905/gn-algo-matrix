from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import threading
import time
import os
import requests
from datetime import datetime

class TradingEngine:
    def __init__(self):
        self.indices = ["Nifty 50", "Bank Nifty", "Sensex"]
        self.signals = {index: "WAITING FOR SIGNAL" for index in self.indices}
        self.prices = {index: "0.00" for index in self.indices}
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        self.running = True

    def send_telegram_alert(self, index_name, signal_type, price):
        if self.token and self.chat_id:
            msg = (
                f"🚨 *GN ALGO MATRIX ALERT* 🚨\n\n"
                f"📊 *Index:* {index_name}\n"
                f"⚡ *Signal:* {signal_type}\n"
                f"💰 *Price:* {price}\n"
                f"⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            try:
                url = f"https://api.telegram.org/bot{self.token}/sendMessage"
                payload = {
                    "chat_id": self.chat_id,
                    "text": msg,
                    "parse_mode": "Markdown"
                }
                requests.post(url, json=payload, timeout=5)
            except Exception as e:
                print(f"Telegram error: {e}")

    def run_simulation(self):
        # Yahan aap apna live data feed ya Tradetron/API integration jod sakte hain
        import random
        while self.running:
            for idx in self.indices:
                # Simulating live movement for testing; replace with actual feed/algo logic
                dummy_price = round(random.uniform(20000, 50000), 2)
                self.prices[idx] = str(dummy_price)
                
                # Example condition for signal generation
                rand_val = random.random()
                if rand_val > 0.8:
                    self.signals[idx] = "🟢 STRONG BUY (CALL)"
                    self.send_telegram_alert(idx, "STRONG BUY (CALL)", dummy_price)
                elif rand_val < 0.2:
                    self.signals[idx] = "🔴 STRONG SELL (PUT)"
                    self.send_telegram_alert(idx, "STRONG SELL (PUT)", dummy_price)
                else:
                    self.signals[idx] = "⚪ HOLD / MONITOR"
            
            time.sleep(10) # 10 seconds interval check

class TradingDashboard(BoxLayout):
    def __init__(self, **kwargs):
        super(TradingDashboard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15

        # Header Title
        self.add_widget(Label(
            text='[b]GN ALGO MATRIX DASHBOARD[/b]', 
            markup=True, 
            font_size=22, 
            size_hint_y=None, 
            height=50
        ))

        # Engine initialization
        self.engine = TradingEngine()
        
        # Start background thread for scanning indices and sending alerts
        self.thread = threading.Thread(target=self.engine.run_simulation, daemon=True)
        self.thread.start()

        # Labels for displaying dynamic status of each index
        self.index_labels = {}
        for idx in self.engine.indices:
            lbl = Label(
                text=f'[b]{idx}[/b]\nPrice: -- | Signal: Loading...', 
                markup=True, 
                font_size=16,
                halign='center'
            )
            self.index_labels[idx] = lbl
            self.add_widget(lbl)

        # Refresh UI via Clock schedule every 1 second
        Clock.schedule_interval(self.update_ui, 1.0)

    def update_ui(self, dt):
        for idx in self.engine.indices:
            price = self.engine.prices[idx]
            signal = self.engine.signals[idx]
            self.index_labels[idx].text = f'[b]{idx}[/b]\nPrice: {price} | Status: {signal}'

class GNAlgoMatrixApp(App):
    def build(self):
        return TradingDashboard()

if __name__ == '__main__':
    GNAlgoMatrixApp().run()
    
