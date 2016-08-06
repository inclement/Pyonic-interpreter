
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.codeinput import CodeInput
from kivy.properties import (ObjectProperty, NumericProperty,
                             OptionProperty)
from kivy.animation import Animation

from kivy.clock import Clock

from kivy.lib import osc

import subprocess

from os.path import realpath, curdir, join, dirname


class OutputLabel(Label):
    stream = OptionProperty('stdout', options=['stdout', 'stderr'])


class InputLabel(Label):
    pass
    

class InterpreterScreen(Screen):
    pass


class InterpreterInput(CodeInput):
    def insert_text(self, text, from_undo=False):
        super(InterpreterInput, self).insert_text(text, from_undo=from_undo)
        try:
            if text == '\n' and self.text.split('\n')[-2][-1].strip()[-1] == ':':
                for i in range(4):
                    self.insert_text(' ')
            elif text == '\n':
                previous_line = self.text.split('\n')[-2]
                num_spaces = len(previous_line) - len(previous_line.lstrip())
                for i in range(num_spaces):
                    self.insert_text(' ')
        except IndexError:
            pass

class InterpreterGui(BoxLayout):
    output_window = ObjectProperty()
    code_input = ObjectProperty()
    scrollview = ObjectProperty()

    input_fail_alpha = NumericProperty(0.)

    def __init__(self, *args, **kwargs):
        super(InterpreterGui, self).__init__(*args, **kwargs)
        self.animation = Animation(input_fail_alpha=0., t='out_expo',
                                   duration=0.5)

        self.interpreter = InterpreterWrapper(self)
    
    def interpret_line_from_code_input(self):
        text = self.code_input.text
        if text == '':
            self.flash_input_fail()
            return
        self.code_input.text = ''
        self.interpret_line(text)
        self.code_input.focus = True

    def flash_input_fail(self):
        self.animation.stop(self)
        self.input_fail_alpha = 1.
        self.animation.start(self)

    def interpret_line(self, text):
        self.add_input_label(text)
        self.interpreter.interpret_line(text)

    def add_input_label(self, text):
        l = InputLabel(text=text)
        self.output_window.add_widget(l)
        self.scrollview.scroll_to(l)

    def add_output_label(self, text, stream='stdout'):
        l = OutputLabel(text=text, stream=stream)
        self.output_window.add_widget(l)
        self.scrollview.scroll_to(l)

    def add_break(self):
        b = BreakMarker()
        self.output_window.add_widget(b)
        self.scrollview.scroll_to(b)

class BreakMarker(Widget):
    pass


class InterpreterWrapper(object):

    def __init__(self, gui):
        interpreter_script_path = join(dirname(realpath(__file__)),
                                       'interpreter_subprocess',
                                       'interpreter.py')
        subprocess.Popen(['python3', '{}'.format(interpreter_script_path)])

        self.gui = gui

        self.interpreter_port = 3000
        self.receive_port = 3001

        self.init_osc()

    def init_osc(self):
        from kivy.lib import osc
        osc.init()
        self.oscid = osc.listen(ipAddr='127.0.0.1', port=self.receive_port)

        osc.bind(self.oscid, self.receive_osc_message, b'/stdout')
        osc.bind(self.oscid, self.receive_osc_message, b'/stderr')
        osc.bind(self.oscid, self.receive_osc_message, b'/interpreter')

    def begin_osc_listen(self):
        Clock.schedule_interval(self.read_osc_queue, 0.1)

    def end_osc_listen(self):
        Clock.unschedule(self.read_osc_queue)
        print('not listening!')

    def read_osc_queue(self, *args):
        osc.readQueue(self.oscid)

    def receive_osc_message(self, message, *args):
        print('received message', message)
        address = message[0]
        body = [s.decode('utf-8') for s in message[2:]]
        
        if address == b'/interpreter':
            if body[0] == 'completed_exec':
                self.gui.add_break()
                self.end_osc_listen()

        elif address == b'/stdout':
            self.gui.add_output_label(body[0], 'stdout')

        elif address == b'/stderr':
            self.gui.add_output_label(body[0], 'stderr')

    def interpret_line(self, text):
        self.send_osc_message(text.encode('utf-8'))
        self.begin_osc_listen()

    def send_osc_message(self, message):
        osc.sendMsg(b'/interpret', [message], port=self.interpreter_port,
                    typehint='b')
        print('sent', message)
