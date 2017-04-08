
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.recycleview import RecycleView
from kivy.uix.modalview import ModalView
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import (StringProperty, OptionProperty,
                             BooleanProperty, NumericProperty,
                             ObjectProperty)
from kivy.lang import Builder
from kivy import platform

import os
from os.path import (isdir, join, abspath, split, expanduser)

from sys import version_info
if version_info.major >= 3:
    permission_errors = (PermissionError, OSError)
else:
    permission_errors = (OSError, )

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
        selected = not self.selected
        if selected:
            self.recycleview.select(self)
            if self.file_type == 'folder':
                self.recycleview.safe_set_folder(abspath(
                    join(self.recycleview.folder, self.filename)))
        else:
            self.recycleview.select(None)
        self.selected = selected

    def on_selected(self, instance, value):
        if self.file_type == 'folder':
            self.selected = False

class PermissionError(ModalView):
    text = StringProperty()

class FileView(RecycleView):
    folder = StringProperty(abspath('.'))
    python_only = BooleanProperty(False)
    selection_instance = ObjectProperty(allownone=True)
    selection_filename = StringProperty()


    def __init__(self, *args, **kwargs):
        super(FileView, self).__init__(*args, **kwargs)
        self.go_home()
        self.on_folder(self, self.folder)

    def safe_set_folder(self, value):
        '''Function to safely set self.folder, by checking that the folder can
        be accessed.'''
        current_folder = self.folder
        try:
            self.folder = value
        except permission_errors as e:
            text = '[b]Permissions error:[/b] Could not open {}'.format(value)
            self.show_permissions_error(text)
            self.folder = current_folder

    def show_permissions_error(self, text):
        PermissionError(text=text).open()
            
    def on_python_only(self, instance, value):
        self.on_folder(self, self.folder)

    def on_folder(self, instance, value):
        filens = os.listdir(self.folder)
        filens.append('..')

        file_types = ['folder' if isdir(join(self.folder, filen)) else 'file' for filen in filens]

        filens = [filen + ('/' if file_type == 'folder' else '')
                  for filen, file_type in zip(filens, file_types)]

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

        self.reset_scroll()

    def select(self, widget):
        if self.selection_instance is not None:
            self.selection_instance.selected = False
        self.selection_instance = widget
        if widget is not None and widget.file_type == 'file':
            self.selection_filename = widget.filename
        else:
            self.selection_filename = ''

    def reset_scroll(self):
        self.scroll_y = 1

    def go_up_folder(self):
        self.select(None)
        self.safe_set_folder(abspath(self.folder + '/..'))

    def go_home(self):
        self.select(None)
        if platform == 'android':
            from jnius import autoclass
            Environment = autoclass('android.os.Environment')
            home = Environment.getExternalStorageDirectory().getAbsolutePath()
        else:
            home = expanduser('~')
        self.folder = home

    def reset(self, go_home=True):
        self.select(None)
        if go_home:
            self.go_home()
        self.scroll_y = 1


class PyonicFileChooser(BoxLayout):
    folder = StringProperty(abspath('.'))
    python_only = BooleanProperty(False)

    current_selection = ObjectProperty(allownone=True)

    open_method = ObjectProperty()
    # The open_method should accept a single filepath as an argument.
    success_screen_name = StringProperty()

    open_button_text = StringProperty('open')

    def return_selection(self):
        if self.current_selection is None:
            return
        if self.open_method is None:
            return
        self.open_method(join(self.folder, self.current_selection.filename))
        from kivy.app import App

        if self.success_screen_name:
            App.get_running_app().manager.switch_to(self.success_screen_name)
        else:
            App.get_running_app().manager.go_back()

class FileChooserScreen(Screen):
    open_method = ObjectProperty()
    success_screen_name = StringProperty()
    current_filename = StringProperty()
    purpose = StringProperty('')

    def on_pre_enter(self):
        self.ids.pyonicfilechooser.ids.fileview.reset(go_home=False)
