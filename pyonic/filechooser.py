
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.recycleview import RecycleView
from kivy.properties import (StringProperty, OptionProperty,
                             BooleanProperty)
from kivy.lang import Builder

import os
from os.path import isdir, join

Builder.load_file('filechooser.kv')

class FileLabel(BoxLayout):
    file_type = OptionProperty('file', options=('folder', 'file'))
    filename = StringProperty()

class FileView(RecycleView):
    folder = StringProperty('.')
    python_only = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        super(FileView, self).__init__(*args, **kwargs)
        self.on_folder(self, self.folder)

    def on_folder(self, instance, value):
        filens = os.listdir(self.folder)

        if self.python_only:
            filens = [filen for filen in filens if filen.endswith('.py')]

        file_types = ['folder' if isdir(join(self.folder, filen)) else 'file' for filen in filens]

        files = zip(filens, file_types)
        files = sorted(files, key=lambda row: row[0].lower())
        files = sorted(files, key=lambda row: (row[1] != 'folder'))

        self.data = [{'filename': name, 'file_type': file_type}
                     for (name, file_type) in files]
        print('data is', self.data)



class PyonicFileChooser(BoxLayout):
    folder = StringProperty('.')
    python_only = BooleanProperty(False)

    current_selection = StringProperty('.')

class FileChooserScreen(Screen):
    pass
