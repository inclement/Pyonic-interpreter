'''

Settings:
- control what buttons are displayed

Menu items:
- settings menu
- clear output
- About page
'''

from kivy.event import EventDispatcher
from kivy.properties import (BooleanProperty, NumericProperty,
                             ObjectProperty, StringProperty)
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.lang import Builder

Builder.load_file('settings.kv')


class BooleanSetting(BoxLayout):
    name = StringProperty()
    description = StringProperty()
    active = BooleanProperty()

class SmallIntSetting(BoxLayout):
    name = StringProperty()
    description = StringProperty()
    value = NumericProperty()

    min = NumericProperty(0)
    max = NumericProperty(10)

    def decrement(self):
        l = self.ids.number_label
        if not l.text:
            return
        num = int(l.text)
        new_num = num - 1
        if new_num < self.min:
            return
        l.text = str(new_num)

    def increment(self):
        l = self.ids.number_label
        if not l.text:
            return
        num = int(l.text)
        new_num = num + 1
        if new_num > self.max:
            return
        l.text = str(new_num)

class InterpreterSettingsScreen(Screen):
    container = ObjectProperty()


class ButtonCheckbox(ButtonBehavior, Label):
    active = BooleanProperty(True)
    box_size = NumericProperty()


class SettingsTitle(Label):
    pass
