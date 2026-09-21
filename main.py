from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
import threading
import time
import requests
from datetime import datetime

# Android WakeLock to prevent sleep mode
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    WindowManager = autoclass('android.view.WindowManager$LayoutParams')
    def keep_screen_on():
        try:
            window = activity.getWindow()
            window.addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
        except Exception:
            pass
except Exception:
    def keep_screen_on():
        pass

class TradingEngine:
    def __init__(self):
        self.indices = ["Nifty 50", "Bank Nifty", "Sensex"]
        self.signals = {index: "HOLD / MONITOR" for index in self.indices}
        self.prices = {index: 24500.0 for index in self.indices}
        self.colors = {index: "ffffff" for index in self.indices}
        
        # Telegram Credentials
        self.token = "8642396544:AAFJVudpn9zWK13a-SweJIkChoKExAk565A"
        self.chat_id = "6606431950"
        self.running = True

    def send_telegram_alert(self, index_name, signal_type, price):
        if self.token and self.chat_id:
            msg = (
                f"🚨 *GN ALGO MATRIX TRADING SIGNAL* 🚨\n\n"
                f"📊 *Index:* {index_name}\n"
                f"⚡ *Action Signal:* {signal_type}\n"
                f"💰 *Trigger Price:* {price:,.2f}\n"
                f"⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"🎯 _Execute trade as per your setup!_"
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
            change = random.uniform(-120, 120)
            self.prices[idx] += change
            if change < -60:
                self.signals[idx] = "📉 BUY PUT / PUT SELL"
                self.colors[idx] = "ff3333"
            elif change > 60:
                self.signals[idx] = "📈 BUY CALL / CALL BUY"
                self.colors[idx] = "00ff00"
            else:
                self.signals[idx] = "HOLD / MONITOR"
                self.colors[idx] = "ffffff"

    def run_simulation(self):
        import random
        last_sent_signals = {idx: "" for idx in self.indices}
        
        while self.running:
            for idx in self.indices:
                change = random.uniform(-150, 150)
                self.prices[idx] += change
                
                if change <= -100:
                    current_signal = "📉 BUY PUT / PUT SELL"
                    self.colors[idx] = "ff3333"
                elif change >= 100:
                    current_signal = "📈 BUY CALL / CALL BUY"
                    self.colors[idx] = "00ff00"
                else:
                    current_signal = "HOLD / MONITOR"
                    self.colors[idx] = "ffffff"

                self.signals[idx] = current_signal

                if current_signal != last_sent_signals[idx]:
                    if "BUY" in current_signal or "SELL" in current_signal:
                        self.send_telegram_alert(idx, current_signal, self.prices[idx])
                    last_sent_signals[idx] = current_signal
            
            time.sleep(10)

class TradingDashboard(BoxLayout):
    def __init__(self, **kwargs):
        super(TradingDashboard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10

        keep_screen_on()

        # Top Header Layout
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        
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

        # Giant UI Blocks for Indices
        self.index_labels = {}
        for idx in self.engine.indices:
            lbl = Label(
                text=f'[b]{idx}[/b]\n[size=45]--[/size]\nLoading...', 
                markup=True, 
                font_size=28,
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
            
            # Giant text layout: Name [32], Price [46], Signal [28]
            self.index_labels[idx].text = (
                f'[b][color=ffff00][size=32]{idx}[/size][/color][/b]\n'
                f'[b][color=ffffff][size=46]{price:,.2f}[/size][/color][/b]\n'
                f'[b][color={color}][size=28]{signal}[/size][/color][/b]'
            )

class GNAlgoMatrixApp(App):
    def build(self):
        return TradingDashboard()

if __name__ == '__main__':
    GNAlgoMatrixApp().run()
    
