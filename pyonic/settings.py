'''To add a new setting:
- Add a widget in the kv to display the setting
- Add a property named setting__yoursettingname to InterpreterSettingsScreen
- Bind this property in kv to your setting: `setting_yoursettingname: yoursettingwidget.value`
- Add a property named setting__yoursettingname to PyonicApp in main.py
- Add a default value class attribute setting__yoursettingname_default to PyonicApp in main.py

The other bindings, and automatically saving in the settings.json
file, will be handled automatically.

'''

from kivy.app import App
from kivy.event import EventDispatcher
from kivy.properties import (BooleanProperty, NumericProperty,
                             ObjectProperty, StringProperty,
                             ListProperty)
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
    setting__autocompletion = BooleanProperty()
    setting__autocompletion_brackets = BooleanProperty()
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
    draw_colour = ListProperty((0.2, 0.2, 0.2, 1))
    text_colour = ListProperty((0.0, 0.0, 0.0, 1))
    handle_touch = BooleanProperty(True)

    def on_touch_down(self, touch):
        if not self.handle_touch:
            return False
        return super(ButtonCheckbox, self).on_touch_down(touch)


class ButtonRadio(ButtonBehavior, Widget):
    box_size = NumericProperty()
    radio_offset = NumericProperty()
    active = BooleanProperty()

class SettingsTitle(Label):
    pass
