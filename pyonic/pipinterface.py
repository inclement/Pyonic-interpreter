
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.lang import Builder
from kivy.properties import (StringProperty, OptionProperty,
                             ObjectProperty, ListProperty)
from kivy import platform


from os import path, mkdir

if platform == 'android':
    from interpreter import InterpreterWrapper
    from utils import site_packages_path
else:
    from pyonic.interpreter import InterpreterWrapper
    from pyonic.utils import site_packages_path

Builder.load_file('pipinterface.kv')

# if platform == 'android':
#     site_packages_path = '../fake_site_packages'
# else:
#     site_packages_path = path.join(path.abspath(path.dirname(__file__)), '..', 'fake_site_packages')

if not path.exists(site_packages_path):
    mkdir(site_packages_path)


class PipScreen(Screen):
    pass


class PipOutputLabel(Label):
    stream = OptionProperty('stdout', options=['stdout', 'stderr'])


class PipGui(BoxLayout):
    output_window = ObjectProperty()
    scrollview = ObjectProperty()

    output_lines = ListProperty([])

    def __init__(self, *args, **kwargs):
        print('args kwargs', args, kwargs)
        super(PipGui, self).__init__(*args, **kwargs)
        self.interpreter = InterpreterWrapper('Pip', throttle_output=False, use_thread=False,
                                              thread_name='pip')

        self.interpreter.bind(on_stdout=self.on_stdout)
        self.interpreter.bind(on_stderr=self.on_stderr)
        self.interpreter.bind(on_complete=self.execution_complete)

    def on_stdout(self, instance, text):
        print('PIP STDOUT:', text)
        self.output_lines.append(text)

        # l = PipOutputLabel(text=text, stream='stdout')
        # self.output_window.add_widget(l)
        # self.scrollview.scroll_to(l)
        # return l

    def on_stderr(self, instance, text):
        print('PIP STDERR:', text)
        self.output_lines.append(text)
        # l = PipOutputLabel(text=text, stream='stderr')
        # self.output_window.add_widget(l)
        # self.scrollview.scroll_to(l)
        # return l

    def execution_complete(self, *args):
        '''Called when execution is complete so the TextInput should be
        unlocked etc., but first this is delayed until messages finish
        printing.
        '''
        pass

    def do_install(self, package):
        self.clear_output()

        self.interpreter.interpret_line(
            "import pip; pip.main(['install', '{}', '--target', '{}', '--no-cache-dir', '--upgrade'])".format(
                package, site_packages_path))

    def do_search(self, package):
        self.clear_output()
        self.interpreter.interpret_line(
            "import pip; pip.main(['search', '{}'])".format(
                package))

    def clear_output(self):
        self.output_lines = []
        # for child in self.output_window.children[:-1]:
        #     self.output_window.remove_widget(child)

