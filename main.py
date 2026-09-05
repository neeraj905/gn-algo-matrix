import sqlite3
from kivy.app import App
from kivy.uix.label import Label

class GNAlgoMatrixApp(App):
    def build(self):
        return Label(text="GN Algo Matrix Running Successfully!")

if __name__ == '__main__':
    GNAlgoMatrixApp().run()
  
