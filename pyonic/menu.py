
from kivy.uix.dropdown import DropDown
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.properties import (ObjectProperty, NumericProperty)
from kivy.animation import Animation
from kivy.lang import Builder


from widgets import ColouredButton

class MenuDropDown(DropDown):
    shift = NumericProperty(dp(30))
    anim_progress = NumericProperty(1)

    parent_obj = ObjectProperty()

    def open(self, *args, **kwargs):
        super(MenuDropDown, self).open(*args, **kwargs)
        self.animate_open()

    def dismiss(self, *args, **kwargs):
        if kwargs.get('immediate', False):
            kwargs.pop('immediate')
            super(MenuDropDown, self).dismiss(*args, **kwargs)
        else:
            self.animate_dismiss()

    def animate_open(self):
        Animation.cancel_all(self)
        self.anim_progress = 1

        Animation(anim_progress=0, d=0.4, t='out_cubic').start(self)

    def animate_dismiss(self):
        Animation.cancel_all(self)
        anim = Animation(anim_progress=1, d=0.2, t='out_cubic')
        anim.bind(on_complete=self.immediate_dismiss)
        anim.start(self)


    def immediate_dismiss(self, *args, **kwargs):
        self.dismiss(immediate=True)

class MenuButton(ColouredButton):

    dropdown_holder = ObjectProperty()
    dropdown_holder_width = NumericProperty()

    dropdown_cls = ObjectProperty(MenuDropDown)

    def __init__(self, *args, **kwargs):
        super(MenuButton, self).__init__(*args, **kwargs)

        self.dropdown = self.dropdown_cls(parent_obj=self)

    def on_release(self):
        if self.dropdown.parent is None:
            self.dropdown.open(self)

class DropDownButton(ColouredButton):
    pass
