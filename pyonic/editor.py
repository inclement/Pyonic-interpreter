
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.properties import (StringProperty)
from kivy import platform

if platform == 'android':
    from interpreter import InterpreterInput
else:
    from pyonic.interpreter import InterpreterInput

Builder.load_file('editor.kv')


class EditorInput(InterpreterInput):
    def keyboard_on_key_down(self, *args):
        return super(InterpreterInput, self).keyboard_on_key_down(*args)

class EditorScreen(Screen):
    pass

class EditorGui(BoxLayout):
    filename = StringProperty('testfilename.py')
