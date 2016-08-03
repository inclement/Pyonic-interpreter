

from kivy.app import App
from kivy.uix.screenmanager import (ScreenManager, Screen,
                                    SlideTransition)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import (StringProperty, ObjectProperty,
                             NumericProperty)
from kivy.animation import Animation
from kivy.core.window import Window
Window.clearcolor = (1, 1, 1, 1)

import pyde.widgets  # noqa

class Manager(ScreenManager):
    back_screen_name = StringProperty('')

    def switch(self, target):
        if target not in self.screen_names:
            raise ValueError('Tried to switch to {}, but screen is not '
                             'already added')
        self.back_screen_name = self.current
        self.transition = SlideTransition(direction='left')
        self.current = target

    def go_back(self):
        app = App.get_running_app()

        self.transition = SlideTransition(direction='right')

        if self.current == self.back_screen_name:
            self.back_screen_name = 'home'

        if self.back_screen_name in self.screen_names:
            self.current = self.back_screen_name
        else:
            self.current = 'Home'
        self.transition = SlideTransition(direction='left')

    def open_interpreter(self):
        if not self.has_screen('interpreter'):
            self.add_widget(InterpreterScreen())
        self.switch('interpreter')

class HomeScreen(Screen):
    pass

class InterpreterScreen(Screen):
    pass

class OutputLabel(Label):
    pass

class InterpreterGui(BoxLayout):
    output_window = ObjectProperty()
    code_input = ObjectProperty()
    scrollview = ObjectProperty()

    input_fail_alpha = NumericProperty(0.)

    def __init__(self, *args, **kwargs):
        super(InterpreterGui, self).__init__(*args, **kwargs)
        self.animation = Animation(input_fail_alpha=0., t='out_expo',
                                   duration=0.5)
    
    def interpret_line_from_code_input(self):
        text = self.code_input.text
        if text == '':
            self.flash_input_fail()
            return
        self.code_input.text = ''
        self.interpret_line(text)
        self.code_input.focus = True

    def flash_input_fail(self):
        self.animation.stop(self)
        self.input_fail_alpha = 1.
        self.animation.start(self)

    def interpret_line(self, text):
        l = OutputLabel(text=text)
        self.output_window.add_widget(l)
        self.scrollview.scroll_to(l)


class PydeApp(App):
    def build(self):
        return Manager()


if __name__ == "__main__":
    PydeApp().run()
