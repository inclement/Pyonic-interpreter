from kivy.app import App
from kivy.uix.screenmanager import (ScreenManager, Screen,
                                    SlideTransition)
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import (StringProperty, BooleanProperty)
from kivy import platform

from android_runnable import run_on_ui_thread

import argparse
import sys


if platform == 'android':
    import widgets
    import interpreter
    import settings
else:
    import pyonic.widgets  # noqa
    import pyonic.interpreter  # noqa
    import pyonic.settings  # noqa


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


class PyonicApp(App):

    subprocesses = []

    ctypes_working = BooleanProperty(True)
    
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)
        Window.softinput_mode = 'pan'
        self.parse_args()
        Clock.schedule_once(self.android_setup, 0)
        return Manager()

    def android_setup(self, *args):
        if platform != 'android':
            return

        self.remove_android_splash()
        self.set_softinput_mode()
        Window.bind(on_keyboard=self.android_key_input)

        import ctypes
        try:
            setasyncexc = ctypes.pythonapi.PyThreadState_SetAsyncExc
        except AttributeError:
            self.ctypes_working = False

    def android_key_input(self, window, key, scancode, codepoint, modifier):
        if scancode == 270:
            from jnius import autoclass
            activity = autoclass('org.kivy.android.PythonActivity')
            activity.moveTaskToBack(True)
            return True  # back button now does nothing on Android
        return False

    @run_on_ui_thread
    def set_softinput_mode(self):
        return
        # from jnius import autoclass
        # PythonActivity = autoclass('org.kivy.android.PythonActivity')
        # WindowManager = autoclass('android.view.WindowManager')
        # LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
        # activity = PythonActivity.mActivity

        # activity.getWindow().setSoftInputMode(LayoutParams.SOFT_INPUT_ADJUST_RESIZE)
        

    def remove_android_splash(self, *args):
        from jnius import autoclass
        activity = autoclass('org.kivy.android.PythonActivity').mActivity
        activity.removeLoadingScreen()

    def parse_args(self):
        print('args are', sys.argv[1:])
        parser = argparse.ArgumentParser()
        parser.add_argument('--test', choices=['interpreter'])

        args = parser.parse_args(sys.argv[1:])

        if args.test == 'interpreter':
            Clock.schedule_once(self.test_interpreter, 0)

    def test_interpreter(self, *args):
        self.root.open_interpreter()

    def on_pause(self):
        return True

    def on_stop(self):
        for subprocess in self.subprocesses:
            subprocess.kill()


if __name__ == "__main__":
    PyonicApp().run()
