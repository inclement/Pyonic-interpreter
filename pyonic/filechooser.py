
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.recycleview import RecycleView
from kivy.properties import (StringProperty, OptionProperty,
                             BooleanProperty, NumericProperty)
from kivy.lang import Builder

import os
from os.path import isdir, join

Builder.load_file('filechooser.kv')

class FileLabel(BoxLayout):
    file_type = OptionProperty('file', options=('folder', 'file'))
    filename = StringProperty()
    shade = BooleanProperty(False)

class FileView(RecycleView):
    folder = StringProperty('.')
    python_only = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        super(FileView, self).__init__(*args, **kwargs)
        self.on_folder(self, self.folder)

    def on_folder(self, instance, value):
        filens = os.listdir(self.folder)
        filens.append('..')

        if self.python_only:
            filens = [filen for filen in filens if filen.endswith('.py')]

        file_types = ['folder' if isdir(join(self.folder, filen)) else 'file' for filen in filens]

        files = zip(filens, file_types)
        files = sorted(files, key=lambda row: row[0].lower())
        files = sorted(files, key=lambda row: (row[1] != 'folder'))

        indices = range(len(files))

        files = [(filen[0], filen[1], index) for filen, index in zip(files, indices)]

        self.data = [{'filename': name,
                      'file_type': file_type,
                      'shade': index % 2}
                     for (name, file_type, index) in files]
        print('data is', self.data)



class PyonicFileChooser(BoxLayout):
    folder = StringProperty('.')
    python_only = BooleanProperty(False)

    current_selection = StringProperty('.')

class FileChooserScreen(Screen):
    pass
