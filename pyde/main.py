

from kivy.app import App
from kivy.uix.screenmanager import (ScreenManager, Screen,
                                    SlideTransition)
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import (StringProperty)
from kivy import platform

import argparse

import sys

if platform == 'android':
    import widgets
    import interpreter
else:
    import pyde.widgets  # noqa
    import pyde.interpreter  # noqa


class Manager(ScreenManager):
    back_screen_name = StringProperty('')

    def switch(self, target):
        if target not in self.screen_names:
            raise ValueError('Tried to switch to {}, but screen is not '
                             'already added')
        self.back_screen_name = self.current
        self.transition = SlideTransition(direction='left')
        self.current = target

    # def go_back(self):
    #     app = App.get_running_app()

    #     self.transition = SlideTransition(direction='right')

    #     if self.current == self.back_screen_name:
    #         self.back_screen_name = 'home'

    #     if self.back_screen_name in self.screen_names:
    #         self.current = self.back_screen_name
    #     else:
    #         self.current = 'Home'
    #     self.transition = SlideTransition(direction='left')

    def open_interpreter(self):
        if not self.has_screen('interpreter'):
            self.add_widget(InterpreterScreen())
        self.switch('interpreter')


class HomeScreen(Screen):
    pass


class PydeApp(App):
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)
        Window.softinput_mode = 'resize'
        self.parse_args()
        return Manager()

    def parse_args(self):
        print('args are', sys.argv[1:])
        parser = argparse.ArgumentParser()
        parser.add_argument('--test', choices=['interpreter'])

        args = parser.parse_args(sys.argv[1:])

        if args.test == 'interpreter':
            Clock.schedule_once(self.test_interpreter, 0)

    def test_interpreter(self, *args):
        self.root.open_interpreter()


if __name__ == "__main__":
    PydeApp().run()
