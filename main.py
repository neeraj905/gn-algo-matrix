from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
import threading
import time
import requests
from datetime import datetime

class TradingEngine:
    def __init__(self):
        self.indices = ["Nifty 50", "Bank Nifty", "Sensex"]
        self.signals = {index: "HOLD / MONITOR" for index in self.indices}
        self.prices = {index: 25000.0 for index in self.indices}
        self.colors = {index: "ffffff" for index in self.indices}
        
        # Telegram Credentials (Aapke wale fit hain)
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

    def manual_refresh(self):
        import random
        for idx in self.indices:
            change = random.uniform(-150, 150)
            self.prices[idx] += change
            if change < -80:
                self.signals[idx] = "⚠️ CRASH WARNING! BUY PUT"
                self.colors[idx] = "ff3333"
            elif change > 80:
                self.signals[idx] = "🚀 SPIKE SURGE! BUY CALL"
                self.colors[idx] = "00ff00"
            else:
                self.signals[idx] = "HOLD / MONITOR"
                self.colors[idx] = "ffffff"

    def run_simulation(self):
        import random
        last_sent_signals = {idx: "" for idx in self.indices}
        
        while self.running:
            for idx in self.indices:
                change = random.uniform(-180, 180)
                self.prices[idx] += change
                
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

                if current_signal != last_sent_signals[idx]:
                    if "WARNING" in current_signal or "SURGE" in current_signal:
                        self.send_telegram_alert(idx, current_signal, self.prices[idx])
                    last_sent_signals[idx] = current_signal
            
            time.sleep(10)

class TradingDashboard(BoxLayout):
    def __init__(self, **kwargs):
        super(TradingDashboard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 15

        # Top Header Layout with Title & Big Refresh Button
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=65)
        
        header_layout.add_widget(Label(
            text='[b][color=00ffff]GN ALGO MATRIX[/color][/b]', 
            markup=True, 
            font_size=24,
            halign='left'
        ))

        self.refresh_btn = Button(
            text='[b]🔄 REFRESH[/b]',
            markup=True,
            font_size=18,
            size_hint_x=None,
            width=130,
            background_color=(0, 0.8, 0.8, 1)
        )
        self.refresh_btn.bind(on_press=self.trigger_refresh)
        header_layout.add_widget(self.refresh_btn)
        
        self.add_widget(header_layout)

        self.engine = TradingEngine()
        self.thread = threading.Thread(target=self.engine.run_simulation, daemon=True)
        self.thread.start()

        # EKDAM GIANT FONT LABELS (Aapke circle jitne bade aur saaf blocks)
        self.index_labels = {}
        for idx in self.engine.indices:
            lbl = Label(
                text=f'[b]{idx}[/b]\n[size=50]--[/size]\nLoading...', 
                markup=True, 
                font_size=26,
                halign='center',
                valign='middle'
            )
            self.index_labels[idx] = lbl
            self.add_widget(lbl)

        Clock.schedule_interval(self.update_ui, 1.0)

    def trigger_refresh(self, instance):
        self.refresh_btn.text = '[b]⏳ 🔄[/b]'
        self.engine.manual_refresh()
        self.update_ui(0)
        Clock.schedule_once(lambda dt: setattr(self.refresh_btn, 'text', '[b]🔄 REFRESH[/b]'), 0.5)

    def update_ui(self, dt):
        for idx in self.engine.indices:
            price = self.engine.prices[idx]
            signal = self.engine.signals[idx]
            color = self.engine.colors[idx]
            
            # Font size ko aur bada (52 size) kar diya hai taaki door se ekdum saaf dikhe
            self.index_labels[idx].text = (
                f'[b][color=ffff00]{idx}[/color][/b]\n'
                f'[size=52][b]⚡ {price:,.2f}[/b][/size]\n'
                f'[b][color={color}]{signal}[/color][/b]'
            )

class GNAlgoMatrixApp(App):
    def build(self):
        return TradingDashboard()

if __name__ == '__main__':
    GNAlgoMatrixApp().run()
                
