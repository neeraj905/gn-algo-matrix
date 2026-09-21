from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
import threading
import time
import requests
from datetime import datetime

class TradingEngine:
    def __init__(self):
        self.indices = ["Nifty 50", "Bank Nifty", "Sensex"]
        self.signals = {index: "HOLD / MONITOR" for index in self.indices}
        self.prices = {index: 0.0 for index in self.indices}
        self.colors = {index: "ffffff" for index in self.indices}
        
        # Aapke Telegram credentials yahan fit hain
        self.token = "8642396544:AAFJVudpn9zWK13a-SweJIkChoKExAk565A"
        self.chat_id = "6606431950"
        self.running = True

    def send_telegram_alert(self, index_name, signal_type, price):
        if self.token and self.chat_id:
            msg = (
                f"🚨 *GN ALGO MATRIX ADVANCE ALERT* 🚨\n\n"
                f"📊 *Index:* {index_name}\n"
                f"⚡ *Signal:* {signal_type}\n"
                f"💰 *Price:* {price:,.2f}\n"
                f"⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"⚠️ _Demat account balance cover karein, sharp market movement detected!_"
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
        import random
        last_sent_signals = {idx: "" for idx in self.indices}
        previous_prices = {idx: 25000.0 for idx in self.indices}
        
        while self.running:
            # Market Timing Check (Subah 9:15 se Shaam 3:30 tak active)
            now = datetime.now()
            current_time_val = now.hour * 100 + now.minute
            is_market_open = 915 <= current_time_val <= 1530

            if is_market_open:
                for idx in self.indices:
                    change = random.uniform(-180, 180)
                    current_price = previous_prices[idx] + change
                    self.prices[idx] = current_price
                    
                    if change <= -120:
                        current_signal = "⚠️ CRASH WARNING! BUY PUT"
                        self.colors[idx] = "ff3333"
                    elif change >= 120:
                        current_signal = "🚀 SPIKE SURGE! BUY CALL"
                        self.colors[idx] = "00ff00"
                    else:
                        current_signal = "HOLD / MONITOR"
                        self.colors[idx] = "ffffff"

                    self.signals[idx] = current_signal
                    previous_prices[idx] = current_price

                    if current_signal != last_sent_signals[idx]:
                        if "WARNING" in current_signal or "SURGE" in current_signal:
                            self.send_telegram_alert(idx, current_signal, current_price)
                        last_sent_signals[idx] = current_signal
            else:
                for idx in self.indices:
                    self.signals[idx] = "MARKET CLOSED (OFFLINE)"
                    self.colors[idx] = "888888"

            time.sleep(10)

class TradingDashboard(BoxLayout):
    def __init__(self, **kwargs):
        super(TradingDashboard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15

        # Header Title - Bada aur Saaf
        self.add_widget(Label(
            text='[b][color=00ffff]GN ALGO MATRIX DASHBOARD[/color][/b]', 
            markup=True, 
            font_size=26, 
            size_hint_y=None, 
            height=60,
            halign='center'
        ))

        self.engine = TradingEngine()
        self.thread = threading.Thread(target=self.engine.run_simulation, daemon=True)
        self.thread.start()

        self.index_labels = {}
        for idx in self.engine.indices:
            lbl = Label(
                text=f'[b]{idx}[/b]\n[size=24]Price: --[/size]\nStatus: Loading...', 
                markup=True, 
                font_size=22,
                halign='center',
                valign='middle'
            )
            self.index_labels[idx] = lbl
            self.add_widget(lbl)

        Clock.schedule_interval(self.update_ui, 1.0)

    def update_ui(self, dt):
        for idx in self.engine.indices:
            price = self.engine.prices[idx]
            signal = self.engine.signals[idx]
            color = self.engine.colors[idx]
            
            self.index_labels[idx].text = (
                f'[b][color=ffff00]{idx}[/color][/b]\n'
                f'[size=26]⚡ {price:,.2f}[/size]\n'
                f'[b][color={color}]Status: {signal}[/color][/b]'
            )

class GNAlgoMatrixApp(App):
    def build(self):
        return TradingDashboard()

if __name__ == '__main__':
    GNAlgoMatrixApp().run()
        
