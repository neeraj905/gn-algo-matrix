from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
import platform

# App khulte hi Android Foreground Service start karne ka code
if platform.platform() == 'android':
    from jnius import autoclass
    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        Intent = autoclass('android.content.Intent')
        service_intent = Intent(activity, autoclass('org.kivy.android.PythonService'))
        service_intent.putExtra('android.intent.extra.PYTHON_SERVICE_ARGUMENT', '')
        activity.startForegroundService(service_intent)
    except Exception as e:
        print(f"Foreground service start error: {e}")

class TradingDashboard(BoxLayout):
    def __init__(self, **kwargs):
        super(TradingDashboard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 20

        self.add_widget(Label(
            text='[b][color=00ffff]GN ALGO MATRIX[/color][/b]\n[size=20]Live Trading & Background Service ON[/size]',
            markup=True,
            font_size=28,
            halign='center'
        ))

class GNAlgoMatrixApp(App):
    def build(self):
        return TradingDashboard()

if __name__ == '__main__':
    GNAlgoMatrixApp().run()
        
