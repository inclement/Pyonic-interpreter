
from kivy.uix.dropdown import DropDown
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.properties import (ObjectProperty, NumericProperty)
from kivy.animation import Animation

from widgets import ColouredButton



class MenuDropDown(DropDown):
    shift = NumericProperty(dp(30))
    anim_progress = NumericProperty(1)

    def open(self, *args, **kwargs):
        super(MenuDropDown, self).open(*args, **kwargs)
        self.animate_open()

    def dismiss(self, *args, **kwargs):
        super(MenuDropDown, self).dismiss(*args, **kwargs)
        self.animate_dismiss()

    def animate_open(self):
        Animation.cancel_all(self)
        self.anim_progress = 1

        Animation(anim_progress=0, d=0.4, t='out_cubic').start(self)

    def animate_dismiss(self):
        pass

class MenuButton(ColouredButton):

    dropdown_holder = ObjectProperty()
    dropdown_holder_width = NumericProperty()

    def __init__(self, *args, **kwargs):
        super(MenuButton, self).__init__(*args, **kwargs)

        self.dropdown = MenuDropDown()

    def on_release(self):
        print('ast')
        self.dropdown.open(self)

class DropDownButton(ColouredButton):
    pass
