
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.recycleview import RecycleView
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import (StringProperty, OptionProperty,
                             BooleanProperty, NumericProperty,
                             ObjectProperty)
from kivy.lang import Builder

import os
from os.path import isdir, join, abspath

Builder.load_file('filechooser.kv')

class FileLabel(ButtonBehavior, BoxLayout):
    file_type = OptionProperty('file', options=('folder', 'file'))
    filename = StringProperty()
    shade = BooleanProperty(False)
    selected = BooleanProperty(False)
    
    @property
    def recycleview(self):
        return self.parent.parent

    def on_release(self):
        self.selected = not self.selected
        if self.selected:
            self.recycleview.select(self)
            if self.file_type == 'folder':
                self.recycleview.folder = abspath(
                    join(self.recycleview.folder, self.filename))
        else:
            self.recycleview.select(None)

class FileView(RecycleView):
    folder = StringProperty('.')
    python_only = BooleanProperty(False)
    selection_instance = ObjectProperty(allownone=True)
    selection_filename = StringProperty()


    def __init__(self, *args, **kwargs):
        super(FileView, self).__init__(*args, **kwargs)
        self.on_folder(self, self.folder)

    def on_python_only(self, instance, value):
        self.on_folder(self, self.folder)

    def on_folder(self, instance, value):
        filens = os.listdir(self.folder)
        filens.append('..')

        file_types = ['folder' if isdir(join(self.folder, filen)) else 'file' for filen in filens]

        files = zip(filens, file_types)
        if self.python_only:
            files = [filen for filen in files if filen[0].endswith('.py') or filen[1] == 'folder']
        files = sorted(files, key=lambda row: row[0].lower())
        files = sorted(files, key=lambda row: (row[1] != 'folder'))

        indices = range(len(files))

        files = [(filen[0], filen[1], index) for filen, index in zip(files, indices)]

        self.data = [{'filename': name,
                      'file_type': file_type,
                      'shade': index % 2}
                     for (name, file_type, index) in files]
        print('data is', self.data)

        self.reset_scroll()

    def select(self, widget):
        if self.selection_instance is not None:
            self.selection_instance.selected = False
        self.selection_instance = widget
        if widget is not None:
            self.selection_filename = widget.filename
        else:
            self.selection_filename = ''

    def reset_scroll(self):
        self.scroll_y = 1


class PyonicFileChooser(BoxLayout):
    folder = StringProperty('.')
    python_only = BooleanProperty(False)

    current_selection = StringProperty('.')

class FileChooserScreen(Screen):
    pass
