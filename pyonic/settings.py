'''
Menu items:
- About page
'''

from kivy.app import App
from kivy.event import EventDispatcher
from kivy.properties import (BooleanProperty, NumericProperty,
                             ObjectProperty, StringProperty)
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.lang import Builder

from functools import partial

Builder.load_file('settings.kv')


class BooleanSetting(BoxLayout):
    name = StringProperty()
    description = StringProperty()
    active = BooleanProperty()
    input_column_width_setter = NumericProperty()


class SmallIntSetting(BoxLayout):
    name = StringProperty()
    description = StringProperty()
    value = NumericProperty()

    input_column_width = NumericProperty()

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


class RotationSetting(BoxLayout):
    name = StringProperty()
    description = StringProperty()
    value = StringProperty()
    input_column_width_setter = NumericProperty()
    

    def on_value(self, instance, value):
        print('value', value)
        for bid in ['portrait_button', 'landscape_button', 'auto_button']:
            if bid.startswith(value):
                self.ids[bid].active = True
            else:
                self.ids[bid].active = False

class InterpreterSettingsScreen(Screen):
    container = ObjectProperty()

    settings_col_width = NumericProperty()

    # Properties relating to settings
    setting__throttle_output = BooleanProperty()
    setting__show_input_buttons = BooleanProperty()
    setting__text_input_height = NumericProperty()
    setting__rotation = StringProperty()

    def __init__(self, *args, **kwargs):
        super(InterpreterSettingsScreen, self).__init__(*args, **kwargs)

        for attr in dir(self):
            if attr.startswith('setting__'):
                self.bind(**{attr: partial(self.setting_updated, attr)})

    def setting_updated(self, setting, instance, value):
        setattr(App.get_running_app(), setting, value)


class ButtonCheckbox(ButtonBehavior, Label):
    active = BooleanProperty(True)
    box_size = NumericProperty()


class ButtonRadio(ButtonBehavior, Widget):
    box_size = NumericProperty()
    radio_offset = NumericProperty()
    active = BooleanProperty()

class SettingsTitle(Label):
    pass
