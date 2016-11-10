
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.properties import (StringProperty)
from kivy import platform

from os import path, mkdir

if platform == 'android':
    from interpreter import InterpreterInput
else:
    from pyonic.interpreter import InterpreterInput

Builder.load_file('pipinterface.kv')


if platform == 'android':
    site_packages_path = '../fake_site_packages'
else:
    site_packages_path = path.join(path.abspath(path.dirname(__file__)), '..', 'fake_site_packages')

if not path.exists(site_packages_path):
    mkdir(site_packages_path)

class PipScreen(Screen):
    pass

class PipGui(BoxLayout):
    def do_install(self, package):
        import pip
        print('running pip')
        pip.main(['install', package, '--target', site_packages_path])
        print('done')

    def do_search(self, package):
        import pip 
        print('running search')
        pip.main(['search', package])
        print('done')

