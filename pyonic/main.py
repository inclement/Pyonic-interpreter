from kivy.app import App
from kivy.uix.screenmanager import (ScreenManager, Screen,
                                    SlideTransition)
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import (StringProperty, BooleanProperty,
                             ObjectProperty, NumericProperty)
from kivy.storage.jsonstore import JsonStore
from kivy import platform

from android_runnable import run_on_ui_thread

import argparse
import sys
from functools import partial

from os.path import abspath, join, dirname


if platform == 'android':
    import widgets
    import interpreter
    import settings
    import menu
else:
    import pyonic.widgets  # noqa
    import pyonic.interpreter  # noqa
    import pyonic.settings  # noqa
    import pyonic.menu  # noqa


class Manager(ScreenManager):
    back_screen_name = StringProperty('')

    def switch_to(self, target):
        if target not in self.screen_names:
            raise ValueError('Tried to switch to {}, but screen is not '
                             'already added')
        self.back_screen_name = self.current
        self.transition = SlideTransition(direction='left')
        self.current = target

    def go_back(self):
        app = App.get_running_app()

        if self.current == 'interpreter':  # current top level screen
            app.back_button_leave_app()

        self.transition = SlideTransition(direction='right')

        if self.current == self.back_screen_name:
            self.back_screen_name = 'interpreter'

        if self.back_screen_name in self.screen_names:
            self.current = self.back_screen_name
        else:
            self.current = 'interpreter'
        self.transition = SlideTransition(direction='left')

    def open_interpreter(self):
        if not self.has_screen('interpreter'):
            self.add_widget(InterpreterScreen())
        self.switch('interpreter')


class HomeScreen(Screen):
    pass


class SettingsStore(JsonStore):
    def get(self, name, default=None):
        try:
            result = super(SettingsStore, self).get(name)
            return result
        except KeyError:
            if default is not None:
                print('default not None')
                return default
            raise


class PyonicApp(App):

    subprocesses = []

    ctypes_working = BooleanProperty(True)

    manager = ObjectProperty()

    # Properties relating to settings in the Settings screen
    setting__throttle_output = BooleanProperty()
    setting__throttle_output_default = True
    setting__show_input_buttons = BooleanProperty()
    setting__show_input_buttons_default = True
    setting__text_input_height = NumericProperty()
    setting__text_input_height_default = 3
    
    def build(self):
        self.settings_retrieved = False  # used to prevent setting
                                         # updates until they have
                                         # been fetched from the file

        Window.clearcolor = (1, 1, 1, 1)
        Window.softinput_mode = 'pan'

        self.parse_args()
        Clock.schedule_once(self.android_setup, 0)
        Clock.schedule_once(self.retrieve_settings, 0)

        if platform == 'android':
            settings_path = '../settings.json'
        else:
            settings_path = join(abspath(dirname(__file__)), '..', 'settings.json')
        self.store = SettingsStore(settings_path)

        # Retrieve the input throttling argument so that it can be
        # passed to the service immediately
        self.setting__throttle_output = self.store.get(
            'setting__throttle_output',
            {'value': self.setting__throttle_output_default})['value']

        Window.bind(on_keyboard=self.key_input)

        for attr in dir(self):
            if attr.startswith('setting__') and not attr.endswith('_default'):
                self.bind(**{attr: partial(self.setting_updated, attr)})

        self.manager = Manager()

        return self.manager

    def retrieve_settings(self, *args):
        '''Tries to load each setting from the settings.json, or otherwise
        uses the default value. These values are passed to the settings
        screen. This is the only time the file is loaded (not written to)
        during each run.

        '''

        settings_screen = self.manager.get_screen('settings')

        for attr in dir(self):
            if attr.startswith('setting__') and not attr.endswith('_default'):
                default = getattr(self, attr + '_default')
                value = self.store.get(attr, default={'value': default})
                value = value['value']
                assert hasattr(settings_screen, attr)
                setattr(settings_screen, attr, value)
        self.settings_retrieved = True


    def android_setup(self, *args):
        if platform != 'android':
            return
        self.remove_android_splash()
        self.set_softinput_mode()

        import ctypes
        try:
            setasyncexc = ctypes.pythonapi.PyThreadState_SetAsyncExc
        except AttributeError:
            self.ctypes_working = False

    def key_input(self, window, key, scancode, codepoint, modifier):
        if key == 27:
            self.manager.go_back()
            return True  # back button now does nothing on Android
        return False

    def back_button_leave_app(self):
        if platform != 'android':
            return
        from jnius import autoclass
        activity = autoclass('org.kivy.android.PythonActivity')
        activity.moveTaskToBack(True)

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

    def setting_updated(self, setting, instance, value):
        if not self.settings_retrieved:
            return
        self.store.put(setting, value=value)

    def test_interpreter(self, *args):
        self.root.open_interpreter()

    def on_pause(self):
        return True

    def on_stop(self):
        for subprocess in self.subprocesses:
            subprocess.kill()


if __name__ == "__main__":
    PyonicApp().run()
