
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.carousel import Carousel
from kivy.uix.gridlayout import GridLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.modalview import ModalView
from kivy.properties import (ObjectProperty, NumericProperty,
                             OptionProperty, BooleanProperty,
                             StringProperty, ListProperty)
from kivy.animation import Animation
from kivy.app import App
from kivy import platform

from kivy.clock import Clock

from kivy.lib import osc

from time import time

if platform != 'android':
    import subprocess

import sys

import signal

from os.path import realpath, join, dirname


class InitiallyFullGridLayout(GridLayout):
    '''A GridLayout that always contains at least one Widget, then makes
    that Widget as small as possible for self.minimum_height to exceed
    self.height by 1 pixel.

    '''
    filling_widget_height = NumericProperty()

    def on_parent(self, instance, value):
        self.parent.bind(height=self.calculate_filling_widget_height)

    # def on_height(self, instance, value):
    #     if self.filling_widget_height > 1.5:
    #         self.calculate_filling_widget_height()

    def on_minimum_height(self, instance, value):
        self.calculate_filling_widget_height()

    def calculate_filling_widget_height(self, *args):
        child_sum = sum([c.height for c in self.children[:-1]])
        self.filling_widget_height = max(0, self.parent.height - child_sum) + 1.

    def on_filling_widget_height(self, instance, value):
        print('filling height', self.filling_widget_height)



class NoTouchCarousel(Carousel):
    '''A carousel that doesn't let the user scroll with touch.'''
    def on_touch_down(self, touch):
        for child in self.children[:]:
            if child.dispatch('on_touch_down', touch):
                return True

    def _start_animation(self, *args, **kwargs):
        # compute target offset for ease back, next or prev
        new_offset = 0
        direction = kwargs.get('direction', self.direction)
        is_horizontal = direction[0] in ['r', 'l']
        extent = self.width if is_horizontal else self.height
        min_move = kwargs.get('min_move', self.min_move)
        _offset = kwargs.get('offset', self._offset)

        if _offset < min_move * -extent:
            new_offset = -extent
        elif _offset > min_move * extent:
            new_offset = extent

        if 'new_offset' in kwargs:
            new_offset = kwargs['new_offset']
            print('yay')

        # if new_offset is 0, it wasnt enough to go next/prev
        dur = self.anim_move_duration
        if new_offset == 0:
            dur = self.anim_cancel_duration

        # detect edge cases if not looping
        len_slides = len(self.slides)
        index = self.index
        if not self.loop or len_slides == 1:
            is_first = (index == 0)
            is_last = (index == len_slides - 1)
            if direction[0] in ['r', 't']:
                towards_prev = (new_offset > 0)
                towards_next = (new_offset < 0)
            else:
                towards_prev = (new_offset < 0)
                towards_next = (new_offset > 0)
            if (is_first and towards_prev) or (is_last and towards_next):
                new_offset = 0

        anim = Animation(_offset=new_offset, d=dur, t=self.anim_type)
        anim.cancel_all(self)

        def _cmp(*l):
            if self._skip_slide is not None:
                self.index = self._skip_slide
                self._skip_slide = None

        anim.bind(on_complete=_cmp)
        anim.start(self)

class OutputLabel(Label):
    stream = OptionProperty('stdout', options=['stdout', 'stderr'])


class InputLabel(Label):
    index = NumericProperty(0)
    root = ObjectProperty()

    blue_shift = NumericProperty(0.)

    blue_anim = Animation(blue_shift=0., t='out_expo',
                          duration=0.5)

    def flash(self):
        self.blue_shift = 1.
        self.blue_anim.start(self)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super(InputLabel, self).on_touch_down(touch)

        self.flash()
        self.root.insert_previous_code(self.index)
        return True


class UserMessageLabel(Label):
    pass


class NotificationLabel(Label):
    background_colour = ListProperty([1, 0, 0, 0.5])



class ColouredButton(ButtonBehavior, Label):
    background_normal = ListProperty([1, 1, 1, 1])
    background_down = ListProperty([0.5, 0.5, 0.5, 1])
    padding = NumericProperty(0)
    radius = NumericProperty(0)

class NonDefocusingButton(ColouredButton):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            FocusBehavior.ignored_touch.append(touch)
        return super(NonDefocusingButton, self).on_touch_down(touch)

class KeyboardButton(ColouredButton):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            FocusBehavior.ignored_touch.append(touch)
        return super(KeyboardButton, self).on_touch_down(touch)


class InterpreterScreen(Screen):
    pass


from kivy.uix.codeinput import CodeInput as InputWidget
class InterpreterInput(InputWidget):
    '''TextInput styled for the app. This also overrides normal disabled
    behaviour to allow the widget to retain focus even when disabled,
    although input is still disabled.

    '''
    root = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super(InterpreterInput, self).__init__(*args, **kwargs)
        if platform != 'android':
            from pygments.lexers import PythonLexer
            self.lexer = PythonLexer()

        self.text = '''for i in range(5):
    print(i)
    time.sleep(1)'''

    def on_disabled(self, instance, value):
        if value:
            from kivy.base import EventLoop
            self._hide_handles(EventLoop.window)

    def _on_focusable(self, instance, value):
        if not self.is_focusable:
            self.focus = False

    def insert_text(self, text, from_undo=False):
        if self.disabled:
            return
        if text != '\n' or self.text == '':
            return super(InterpreterInput, self).insert_text(text,
                                                             from_undo=from_undo)

        print(self.text.split('\n'))
        last_line = self.text.split('\n')[-1].rstrip()
        if len(last_line) == 0:
            return super(InterpreterInput, self).insert_text(text,
                                                             from_undo=from_undo)

        num_spaces = len(last_line) - len(last_line.lstrip())
        if last_line[-1] == ':':
            return super(InterpreterInput, self).insert_text(text + (num_spaces + 4) * ' ',
                                                             from_undo=from_undo)
        else:
            return super(InterpreterInput, self).insert_text(text + num_spaces * ' ',
                                                             from_undo=from_undo)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] == 'enter' and 'shift' in modifiers:
            self.root.interpret_line_from_code_input()
            return
        super(InterpreterInput, self).keyboard_on_key_down(
            window, keycode, text, modifiers)


class InterpreterGui(BoxLayout):
    output_window = ObjectProperty()
    code_input = ObjectProperty()
    scrollview = ObjectProperty()

    input_fail_alpha = NumericProperty(0.)

    lock_input = BooleanProperty(False)
    _lock_input = BooleanProperty(False)

    halting = BooleanProperty(False)
    '''True when the interpreter has been asked to stop but has not yet
    done so.'''

    interpreter_state = OptionProperty('waiting', options=['waiting',
                                                           'interpreting',
                                                           'not_responding',
                                                           'restarting'])
    status_label_colour = StringProperty('0000ff')

    _output_label_queue = ListProperty([])

    dequeue_scheduled = None
    clear_scheduled = None

    def __init__(self, *args, **kwargs):
        super(InterpreterGui, self).__init__(*args, **kwargs)
        self.animation = Animation(input_fail_alpha=0., t='out_expo',
                                   duration=0.5)

        self.interpreter = InterpreterWrapper(self)

        # Clock.schedule_interval(self._dequeue_output_label, 0.05)
        # Clock.schedule_interval(self._clear_output_label_queue, 1)

    def on_lock_input(self, instance, value):
        if value:
            self.input_focus_on_disable = self.code_input.focus
            self._lock_input = True
        else:
            self._lock_input = False
            self.code_input.focus = self.input_focus_on_disable
            self.ensure_no_ctrl_c_button()
            self.halting = False

    def ensure_ctrl_c_button(self):
        Clock.schedule_once(self._switch_to_ctrl_c_button, 0.4)

    def _switch_to_ctrl_c_button(self, *args):
        c = self.ids.carousel
        if c.index == 0:
            c.load_next()

    def ensure_no_ctrl_c_button(self):
        Clock.unschedule(self._switch_to_ctrl_c_button)
        c = self.ids.carousel
        if c.index == 1:
            c.load_previous()
        else:
            Animation.cancel_all(c)
            c._start_animation(new_offset=0)

    def on_interpreter_state(self, instance, value):
        if value == 'waiting':
            self.status_label_colour = '0000ff'
        elif value == 'interpreting':
            self.status_label_colour = '00ff00'
        elif value == 'not_responding':
            self.status_label_colour = 'ff0000'
        elif value == 'restarting':
            self.status_label_colour = 'ffA500'

    def interpret_line_from_code_input(self):
        text = self.code_input.text
        if text == '':
            self.flash_input_fail()
            return
        self.code_input.text = ''
        self.interpret_line(text)

    def flash_input_fail(self):
        self.animation.stop(self)
        self.input_fail_alpha = 1.
        self.animation.start(self)

    def interpret_line(self, text):
        index = self.interpreter.interpret_line(text)
        self.add_input_label(text, index)

    def add_input_label(self, text, index):
        l = InputLabel(text=text, index=index, root=self)
        self.output_window.add_widget(l)
        self.scrollview.scroll_to(l)

    def add_output_label(self, text, stream='stdout'):
        self._output_label_queue.append((text, stream))
        # self._dequeue_output_label(0)

    def _add_output_label(self, text, stream='stdout', scroll_to=True):
        l = OutputLabel(text=text, stream=stream)
        self.output_window.add_widget(l)
        if scroll_to:
            self.scrollview.scroll_to(l)
        return l

    def _dequeue_output_label(self, dt):
        if not self._output_label_queue:
            return

        # print('dequeueing', self._output_label_queue)

        t = time()
        i = 0
        while (time() - t) < 0.005:
            i += 1
            if not self._output_label_queue:
                break
            label_text = self._output_label_queue.pop(0)
            label = self._add_output_label(*label_text, scroll_to=False)
        print('did {} labels in {}'.format(i, time() - t))
        Animation.stop_all(self.scrollview, 'scroll_x', 'scroll_y')
        self.scrollview.scroll_to(label)

        self.dequeue_scheduled.cancel()
        self.dequeue_scheduled = None

        if len(self._output_label_queue) == 0 and self.clear_scheduled:
            self.clear_scheduled.cancel()
            self.clear_scheduled = None
        elif len(self._output_label_queue) > 0:
            self.dequeue_scheduled = Clock.schedule_once(
                self._dequeue_output_label, 0.05)

    def _clear_output_label_queue(self, dt):
        print('CLEARING')
        labels = self._output_label_queue
        self._output_label_queue = []
        if labels:
            self.add_missing_labels_marker(labels)

        if self.dequeue_scheduled:
            self.dequeue_scheduled.cancel()
            self.dequeue_scheduled = None

        if self.clear_scheduled:
            self.clear_scheduled.cancel()
            self.clear_scheduled = None

    def on__output_label_queue(self, instance, values):
        # print('olq', self.dequeue_scheduled, self.clear_scheduled)
        if self.dequeue_scheduled:
            return

        if not self.dequeue_scheduled:
            self.dequeue_scheduled = Clock.schedule_once(self._dequeue_output_label, 0)
        if not self.clear_scheduled:
            self.clear_scheduled = Clock.schedule_once(
                self._clear_output_label_queue, 1)

    def add_missing_labels_marker(self, labels):
        l = UserMessageLabel(
            text='{} lines omitted (too many to render)'.format(len(labels)),
            background_colour=(1, 0.6, 0, 1))
        l.labels = labels
        self.output_window.add_widget(l)
        self.scrollview.scroll_to(l)

    def add_notification_label(self, text):
        self.add_break()
        l = NotificationLabel(text=text)
        self.output_window.add_widget(l)
        self.scrollview.scroll_to(l)
        self.add_break()

    def add_break(self):
        b = BreakMarker()
        self.output_window.add_widget(b)
        self.scrollview.scroll_to(b)

    def insert_previous_code(self, index, clear=False):
        if clear:
            self.code_input.text = ''
        code = self.interpreter.inputs[index]
        if self.code_input.text == '':
            self.code_input.text = code
        else:
            self.code_input.text += '\n' + code

    def send_sigint(self):
        self.halting = True
        self.interpreter.send_sigint()

    def restart_interpreter(self):
        self.interpreter.restart()

    def query_restart(self):
        popup = RestartPopup(interpreter_gui=self)
        popup.open()

class RestartPopup(ModalView):
    interpreter_gui = ObjectProperty()


class BreakMarker(Widget):
    pass


class InterpreterWrapper(object):

    def __init__(self, gui):
        self.gui = gui

        self.subprocess = None

        self.start_interpreter()

        self.input_index = 0  # The current input number
        self.inputs = {}  # All the inputs so far

        self.interpreter_port = 3000
        self.receive_port = 3001

        Clock.schedule_interval(self.read_osc_queue, 0.05)

        self.init_osc()

        self._interpreter_state = 'waiting'

        # Clock.schedule_interval(self.ping, 5)

    @property
    def interpreter_state(self):
        return self._interpreter_state

    @interpreter_state.setter
    def interpreter_state(self, value):
        self._interpreter_state = value
        if self.gui is not None:
            self.gui.interpreter_state = self.interpreter_state

    def start_interpreter(self):
        interpreter_script_path = join(dirname(realpath(__file__)),
                                       'interpreter_subprocess',
                                       'interpreter.py')

        if platform == 'android':
            from jnius import autoclass
            service = autoclass('net.inclem.pyde.ServiceInterpreter')
            mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
            argument = ''
            service.start(mActivity, argument)
        else:
            # This may not actually work everywhere, but let's assume it does
            print('starting subprocess')
            python_name = 'python{}'.format(sys.version_info.major)
            s = subprocess.Popen([python_name, '{}'.format(interpreter_script_path)])
            App.get_running_app().subprocesses.append(s)
            self.subprocess = s
            pass

    def send_sigint(self):
        self.send_osc_message(b'sigint', address=b'/sigint')

    def init_osc(self):
        from kivy.lib import osc
        osc.init()
        self.oscid = osc.listen(ipAddr='127.0.0.1', port=self.receive_port)

        osc.bind(self.oscid, self.receive_osc_message, b'/stdout')
        osc.bind(self.oscid, self.receive_osc_message, b'/stderr')
        osc.bind(self.oscid, self.receive_osc_message, b'/interpreter')
        osc.bind(self.oscid, self.receive_osc_message, b'/pong')

    # def begin_osc_listen(self):
    #     Clock.schedule_interval(self.read_osc_queue, 0.1)

    # def end_osc_listen(self):
    #     Clock.unschedule(self.read_osc_queue)

    def read_osc_queue(self, *args):
        osc.readQueue(self.oscid)

    def receive_osc_message(self, message, *args):
        print('received message', message, args)
        address = message[0]
        body = [s.decode('utf-8') for s in message[2:]]

        if address == b'/interpreter':
            if body[0] == 'completed_exec':
                self.gui.add_break()
                self.gui.lock_input = False
                self.gui.halting = False
                self.gui.ensure_no_ctrl_c_button()
                self.interpreter_state = 'waiting'
                # self.end_osc_listen()

            elif body[0] == 'received_command':
                Clock.unschedule(self.command_not_received)

        elif address == b'/pong':
            self.pong()

        elif address == b'/stdout':
            self.gui.add_output_label(body[0], 'stdout')

        elif address == b'/stderr':
            self.gui.add_output_label(body[0], 'stderr')

    def interpret_line(self, text):
        self.send_python_command(text.encode('utf-8'))
        self.gui.lock_input = True
        self.gui.ensure_ctrl_c_button()
        self.interpreter_state = 'interpreting'
        input_index = self.input_index
        self.inputs[input_index] = text
        self.input_index += 1
        # self.begin_osc_listen()
        return input_index

    def send_python_command(self, message):
        Clock.schedule_once(self.command_not_received, 1)
        self.send_osc_message(message, address=b'/interpret')

    def send_osc_message(self, message, address=b'/interpret'):
        osc.sendMsg(address, [message], port=self.interpreter_port,
                    typehint='b')
        print('sent', message)

    def command_not_received(self, *args):
        print('command not received? something is wrong!?')

    def restart(self):
        if platform == 'android':
            from jnius import autoclass
            service = autoclass('net.inclem.pyde.ServiceInterpreter')
            mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
            service.stop(mActivity)
            self.start_interpreter()
        else:
            self.subprocess.kill()
            self.start_interpreter()

        self.gui.lock_input = True
        self.interpreter_state = 'restarting'
        Clock.unschedule
        Clock.schedule_interval(self.ping, 0.5)

    def finish_restart(self):
        if self.interpreter_state != 'restarting':
            raise ValueError('Tried to finish restarting, but was not restarting')
        self.interpreter_state = 'waiting'
        self.gui.lock_input = False
        self.gui.add_notification_label('[b]interpreter restarted: variable context lost[/b]')

    def ping(self, *args, **kwargs):
        timeout = kwargs.get('timeout', 2)
        self.send_osc_message('ping', address=b'/ping')
        Clock.schedule_once(self.ping_failed, timeout)

    def ping_failed(self, *args):
        if self.interpreter_state != 'restarting':
            self.interpreter_state = 'not_responding'

    def pong(self):
        print('Received pong')
        Clock.unschedule(self.ping_failed)
        if self.interpreter_state == 'restarting':
            self.finish_restart()
            Clock.unschedule(self.ping)
