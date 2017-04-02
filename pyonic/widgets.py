
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.properties import (ListProperty, NumericProperty)

class HeightButton(Button):
    pass

class HeightLabel(Label):
    pass

class HomeScreenButton(HeightButton):
    pass

class ColouredButton(ButtonBehavior, Label):
    background_normal = ListProperty([1, 1, 1, 1])
    background_down = ListProperty([0.5, 0.5, 0.5, 1])
    padding = NumericProperty(0)
    radius = NumericProperty(0)

class ColouredButtonContainer(ButtonBehavior, AnchorLayout):
    background_normal = ListProperty([1, 1, 1, 1])
    background_down = ListProperty([0.5, 0.5, 0.5, 1])
    coloured_button_padding = NumericProperty(0)
    radius = NumericProperty(0)
