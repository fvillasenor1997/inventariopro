from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

class InventarioApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        label = Label(text='InventarioPro\nTest Build\nVersion 1.0')
        layout.add_widget(label)
        return layout

if __name__ == '__main__':
    InventarioApp().run()