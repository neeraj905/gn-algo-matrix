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
        self.prices = {index: "0.00" for index in self.indices}
        self.colors = {index: "ffffff" for index in self.indices}
        
        # Aapke credentials yahan seedha fit kar diye gaye hain
        self.token = "8642396544:AAFJVudpn9zWK13a-SweJIkChoKExAk565A"
        self.chat_id = "6606431950"
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
        import random
        while self.running:
            for idx in self.indices:
                dummy_price = round(random.uniform(20000, 50000), 2)
                self.prices[idx] = f"{dummy_price:,.2f}"
                
                rand_val = random.random()
                if rand_val > 0.75:
                    self.signals[idx] = "STRONG BUY (CALL)"
                    self.colors[idx] = "00ff00" # Bright Green
                    self.send_telegram_alert(idx, "STRONG BUY (CALL)", self.prices[idx])
                elif rand_val < 0.25:
                    self.signals[idx] = "STRONG SELL (PUT)"
                    self.colors[idx] = "ff3333" # Bright Red
                    self.send_telegram_alert(idx, "STRONG SELL (PUT)", self.prices[idx])
                else:
                    self.signals[idx] = "HOLD / MONITOR"
                    self.colors[idx] = "ffffff" # White
            
            time.sleep(10)

class TradingDashboard(BoxLayout):
    def __init__(self, **kwargs):
        super(TradingDashboard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 30
        self.spacing = 20

        # Header Title
        self.add_widget(Label(
            text='[b][color=00ffff]GN ALGO MATRIX[/color][/b]', 
            markup=True, 
            font_size=28, 
            size_hint_y=None, 
            height=70,
            halign='center'
        ))

        # Engine initialization
        self.engine = TradingEngine()
        self.thread = threading.Thread(target=self.engine.run_simulation, daemon=True)
        self.thread.start()

        # Large Labels for indices
        self.index_labels = {}
        for idx in self.engine.indices:
            lbl = Label(
                text=f'[b]{idx}[/b]\n[size=22]Price: --[/size]\nStatus: Loading...', 
                markup=True, 
                font_size=20,
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
                f'[size=24]⚡ {price}[/size]\n'
                f'[b][color={color}]Status: {signal}[/color][/b]'
            )

class GNAlgoMatrixApp(App):
    def build(self):
        return TradingDashboard()

if __name__ == '__main__':
    GNAlgoMatrixApp().run()
