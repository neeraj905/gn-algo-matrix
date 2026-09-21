from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
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

class TradingDashboard(ScrollView):
    def __init__(self, **kwargs):
        super(TradingDashboard, self).__init__(**kwargs)
        self.do_scroll_x = False
        self.do_scroll_y = True

        # Main layout inside scroll view for pull-to-refresh effect
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        # Header Title - Giant & Clear
        layout.add_widget(Label(
            text='[b][color=00ffff]GN ALGO MATRIX DASHBOARD[/color][/b]', 
            markup=True, 
            font_size=28, 
            size_hint_y=None, 
            height=60,
            halign='center'
        ))

        self.engine = TradingEngine()
        self.thread = threading.Thread(target=self.engine.run_simulation, daemon=True)
        self.thread.start()

        # GIANT FONT LABELS FOR INDICES
        self.index_labels = {}
        for idx in self.engine.indices:
            lbl = Label(
                text=f'[b]{idx}[/b]\n[size=34]Price: --[/size]\nStatus: Loading...', 
                markup=True, 
                font_size=24,
                halign='center',
                valign='middle',
                size_hint_y=None,
                height=130
            )
            self.index_labels[idx] = lbl
            layout.add_widget(lbl)

        # MODERN REFRESH BUTTON (Swipe / Pull style action)
        self.refresh_btn = Button(
            text='[b]🔄 REFRESH (PULL / TAP TO UPDATE)[/b]',
            markup=True,
            font_size=20,
            size_hint_y=None,
            height=70,
            background_color=(0, 0.7, 0.7, 1)
        )
        self.refresh_btn.bind(on_press=self.trigger_refresh)
        layout.add_widget(self.refresh_btn)

        self.add_widget(layout)
        Clock.schedule_interval(self.update_ui, 1.0)

    def trigger_refresh(self, instance):
        self.refresh_btn.text = '[b]⏳ REFRESHING...[/b]'
        self.engine.manual_refresh()
        self.update_ui(0)
        Clock.schedule_once(lambda dt: setattr(self.refresh_btn, 'text', '[b]🔄 REFRESH (PULL / TAP TO UPDATE)[/b]'), 0.5)

    def update_ui(self, dt):
        for idx in self.engine.indices:
            price = self.engine.prices[idx]
            signal = self.engine.signals[idx]
            color = self.engine.colors[idx]
            
            self.index_labels[idx].text = (
                f'[b][color=ffff00]{idx}[/color][/b]\n'
                f'[size=36]⚡ {price:,.2f}[/size]\n'
                f'[b][color={color}]Status: {signal}[/color][/b]'
            )

class GNAlgoMatrixApp(App):
    def build(self):
        return TradingDashboard()

if __name__ == '__main__':
    GNAlgoMatrixApp().run()
        
