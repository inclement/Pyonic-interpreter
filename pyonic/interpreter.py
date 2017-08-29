from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.carousel import Carousel
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.modalview import ModalView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.properties import (ObjectProperty, NumericProperty,
                             OptionProperty, BooleanProperty,
                             StringProperty, ListProperty)
from kivy.animation import Animation
from kivy.app import App
from kivy import platform
from kivy.lang import Builder

from kivy.clock import Clock


from time import time
import traceback

if platform == 'android':
    from interpreterwrapper import InterpreterWrapper
    import pydoc_data
    from jediinterface import get_completions, get_defs
else:
    from pyonic.interpreterwrapper import InterpreterWrapper
    from pyonic.jediinterface import get_completions, get_defs

import menu

Builder.load_file('interpreter.kv')

from widgets import ColouredButton

import sys
from os.path import realpath, join, dirname

    
class NonDefocusingBehavior(object):
    def on_touch_down(self, touch):
        if self.collide_point(*self.to_parent(*touch.pos)):
            FocusBehavior.ignored_touch.append(touch)
        return super(NonDefocusingBehavior, self).on_touch_down(touch)


class InitiallyFullGridLayout(GridLayout):
    '''A GridLayout that always contains at least one Widget, then makes
    that Widget as small as possible for self.minimum_height to exceed
    self.height by at least self.filling_widget_minimum_height + 1 pixel.

    '''
    filling_widget_height = NumericProperty()

    filling_widget_minimum_height = NumericProperty(0)

    def on_parent(self, instance, value):
        self.parent.bind(height=self.calculate_filling_widget_height)

    # def on_height(self, instance, value):
    #     if self.filling_widget_height > 1.5:
    #         self.calculate_filling_widget_height()

    def on_minimum_height(self, instance, value):
        self.calculate_filling_widget_height()

    def calculate_filling_widget_height(self, *args):
        child_sum = sum([c.height for c in self.children[:-1]])
        self.filling_widget_height = max(self.filling_widget_minimum_height,
                                         self.parent.height - child_sum) + 1.

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


class NonDefocusingScrollView(NonDefocusingBehavior, ScrollView):
    pass


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
    background_colour = ListProperty([1, 1, 0, 1])

class DocLabel(Label):
    background_colour = ListProperty([1, 0.922, 0.478, 1])

    double_opacity = NumericProperty(1)

    def remove(self):
        anim = Animation(height=0, double_opacity=0, d=0.9, t='out_expo')
        anim.bind(on_complete=self._remove)
        anim.start(self)

    def _remove(self, *args):
        self.parent.remove_widget(self)

class NotificationLabel(Label):
    background_colour = ListProperty([1, 0, 0, 0.5])


class NonDefocusingButton(NonDefocusingBehavior, ColouredButton):
    pass
    # def on_touch_down(self, touch):
    #     if self.collide_point(*touch.pos):
    #         FocusBehavior.ignored_touch.append(touch)
    #     return super(NonDefocusingButton, self).on_touch_down(touch)

class KeyboardButton(NonDefocusingBehavior, ColouredButton):
    pass
    # def on_touch_down(self, touch):
    #     if self.collide_point(*touch.pos):
    #         FocusBehavior.ignored_touch.append(touch)
    #     return super(KeyboardButton, self).on_touch_down(touch)


class InterpreterScreen(Screen):
    pass


from kivy.uix.codeinput import CodeInput as InputWidget
class InterpreterInput(InputWidget):
    '''TextInput styled for the app. This also overrides normal disabled
    behaviour to allow the widget to retain focus even when disabled,
    although input is still disabled.

    '''
    root = ObjectProperty()

    trigger_completions = BooleanProperty(True)

    def __init__(self, *args, **kwargs):
        super(InterpreterInput, self).__init__(*args, **kwargs)

        self.register_event_type('on_request_completions')
        self.register_event_type('on_clear_completions')
        self.register_event_type('on_get_completions')

        if platform != 'android':
            from pygments.lexers import PythonLexer
            self.lexer = PythonLexer()

        App.get_running_app().bind(on_pause=self.on_pause)

    #     self.text = '''for i in range(5):
    # print(i)
    # time.sleep(1)'''

    def on_request_completions(self):
        pass

    def on_clear_completions(self):
        pass

    def on_get_completions(self, text):
        pass

    def on_pause(self, *args):
        self.focus = False

    def on_disabled(self, instance, value):
        if value:
            from kivy.base import EventLoop
            self._hide_handles(EventLoop.window)

    def _on_focusable(self, instance, value):
        if not self.is_focusable:
            self.focus = False

    def on_cursor(self, instance, value):
        super(InterpreterInput, self).on_cursor(instance, value)
        self.get_completions()

    def get_completions(self, extra_text=''):
        row_index, line, col_index = self.currently_edited_line()
        if col_index == 0:
            self.dispatch('on_clear_completions')
            return

        completion_breakers = [' ', '.', ',', '(', ')', ':',
                               '#', '[', ']', '{', '}', '&',
                               '\\', '/', '+', '*', '\'', '\"',
                               '|', '=', '^', '%']
        if line[col_index - 1] in completion_breakers:
            self.dispatch('on_clear_completions')
            return
        if col_index + 1 < len(line) and line[col_index] not in completion_breakers:
            self.dispatch('on_clear_completions')
            return

        if not self.trigger_completions:
            self.dispatch('on_clear_completions')
            return
        self.dispatch('on_get_completions', extra_text)

    def currently_edited_line(self):
        '''Returns the row number, line text and column number for the current cursor pos.'''
        index = self.cursor_index()
        lines = self.text.split('\n')
        cur_num = 0
        for i, line in enumerate(lines):
            line_length = len(line) + 1  # The +1 is for the deleted \n
            if cur_num + line_length > index:
                return i, line, index - cur_num
            cur_num += line_length
        raise ValueError('Could not identify currently edited line')  # TODO: make not an error

    def insert_text(self, text, from_undo=False):
        if self.disabled:
            return
        if text != '\n' or self.text == '':
            return super(InterpreterInput, self).insert_text(text,
                                                             from_undo=from_undo)

        self.dispatch('on_clear_completions')

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
    status_label_colour = StringProperty('b2ade6')

    _output_label_queue = ListProperty([])

    dequeue_scheduled = ObjectProperty(None, allownone=True)
    clear_scheduled = ObjectProperty(None, allownone=True)

    awaiting_label_display_completion = BooleanProperty(False)

    throttle_label_output = BooleanProperty()
    '''Whether to clear the output label queue regularly. If False, labels
    will always be displayed, but this *will* cause problems with
    e.g. a constantly printing while loop.
    '''

    interpreted_lines = ListProperty([])
    '''A list of the lines of code that have been executed so far.'''

    completion_threads = []
    '''The threads running jedi completion functions.'''

    most_recent_completion_time = 0.
    '''The most recent timestamp from a completion. New completions with
    older timestamps will be ignored.'''

    def __init__(self, *args, **kwargs):
        super(InterpreterGui, self).__init__(*args, **kwargs)
        self.animation = Animation(input_fail_alpha=0., t='out_expo',
                                   duration=0.5)

        self.interpreter = InterpreterWrapper(
            'Interpreter',
            use_thread=True,
            throttle_output=App.get_running_app().setting__throttle_output,
            thread_name='interpreter')
        self.interpreter.bind(interpreter_state=self.setter('interpreter_state'))
        self.interpreter.bind(lock_input=self.setter('lock_input'))

        self.interpreter.bind(on_execution_complete=self.execution_complete)
        self.interpreter.bind(on_stdout=self.on_stdout)
        self.interpreter.bind(on_stderr=self.on_stderr)
        self.interpreter.bind(on_notification=self.on_notification)
        self.interpreter.bind(on_user_message=self.on_user_message)
        self.interpreter.bind(on_missing_labels=self.on_missing_labels)
        self.interpreter.bind(on_request_input=self.on_request_input)

        # self.interpreter = DummyInterpreter()

        # Clock.schedule_interval(self._dequeue_output_label, 0.05)
        # Clock.schedule_interval(self._clear_output_label_queue, 1)

        Clock.schedule_once(self.post_init_check, 0)

    def post_init_check(self, *args):
        if App.get_running_app().ctypes_working:
            return
        self.add_user_message_label(
            ('Could not load ctypes on this device. Keyboard interrupt '
             'will not be available.'),
            background_colour=(1, 0.6, 0, 1))

    def on_lock_input(self, instance, value):
        if value:
            self.input_focus_on_disable = self.code_input.focus
            self._lock_input = True
        else:
            self._lock_input = False
            self.code_input.focus = self.input_focus_on_disable
            self.ensure_no_ctrl_c_button()
            self.halting = False

    def on_stdout(self, interpreter, text):
        self.add_output_label(text, 'stdout')

    def on_stderr(self, interpreter, text):
        self.add_output_label(text, 'stderr')

    def on_notification(self, interpreter, text):
        self.add_notification_label(text)

    def on_user_message(self, interpreter, text):
        self.add_user_message_label(text, background_colour=(1, 0.6, 0, 1))

    def on_request_input(self, interpreter, prompt):
        self.show_input_popup(prompt)
        
    def show_input_popup(self, prompt):
        # Window.softinput_mode = 'below_target'
        p = InputPopup(prompt=prompt,
                       submit_func=self.send_input)
        p.open()

    def send_input(self, text):
        '''Send the given input to the Python interpreter.'''
        self.interpreter.send_input(text)

    def ensure_ctrl_c_button(self):
        if not App.get_running_app().ctypes_working:
            return
        Clock.schedule_once(self._switch_to_ctrl_c_button, 0.4)

    def _switch_to_ctrl_c_button(self, *args):
        c = self.ids.carousel
        if c.index == 0:
            c.load_next()

    def clear_output(self):
        for child in self.output_window.children[:-1]:
            self.output_window.remove_widget(child)

    def exec_file(self):
        App.get_running_app().root.switch_to(
            'filechooser', open_method=self._exec_file,
            success_screen_name='interpreter',
            purpose='exec file')

    def _exec_file(self, filename):
        self.add_user_message_label('Executing {}...'.format(filename))
        self.ensure_ctrl_c_button()
        self.interpreter.exec_file(filename)

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
            self.status_label_colour = 'b2ade6'
        elif value == 'interpreting':
            self.status_label_colour = 'ade6b4'
        elif value == 'not_responding':
            self.status_label_colour = 'e6adad'
        elif value == 'restarting':
            self.status_label_colour = 'e6adad'

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
        self.interpreted_lines.append(text)
        index = self.interpreter.interpret_line(text)
        self.add_input_label(text, index)
        self.ensure_ctrl_c_button()

    def add_user_message_label(self, text, **kwargs):
        l = UserMessageLabel(text=text, **kwargs)
        self.output_window.add_widget(l)
        self.scrollview.scroll_to(l)

    def add_doc_label(self, text, **kwargs):
        l = DocLabel(text=text, **kwargs)
        self.output_window.add_widget(l)
        self.scrollview.scroll_to(l)

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
        print('Rendered {} labels in {}'.format(i, time() - t))
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

        if (self.awaiting_label_display_completion and
            len(self._output_label_queue) == 0):
            self.awaiting_label_display_completion = False
            self._execution_complete()

    def _clear_output_label_queue(self, dt):
        if not self.throttle_label_output:
            return
        labels = self._output_label_queue
        self._output_label_queue = []
        if labels:
            self.add_missing_labels_marker(labels=labels)

        if self.dequeue_scheduled:
            self.dequeue_scheduled.cancel()
            self.dequeue_scheduled = None

        if self.clear_scheduled:
            self.clear_scheduled.cancel()
            self.clear_scheduled = None

        if self.awaiting_label_display_completion:
            self.awaiting_label_display_completion = False
            self._execution_complete()

    def on__output_label_queue(self, instance, values):
        # print('olq', self.dequeue_scheduled, self.clear_scheduled)
        if self.dequeue_scheduled:
            return

        if not self.dequeue_scheduled:
            self.dequeue_scheduled = Clock.schedule_once(self._dequeue_output_label, 0)
        if not self.clear_scheduled:
            self.clear_scheduled = Clock.schedule_once(
                self._clear_output_label_queue, 1)

    def on_throttle_label_output(self, instance, value):
        self.interpreter.set_service_output_throttling(value)

    def on_missing_labels(self, instance, number):
        self.add_missing_labels_marker(num_labels=number)

    def add_missing_labels_marker(self, num_labels=None, labels=None):
        if labels is not None:
            num_labels = len(labels)
        self.add_user_message_label(
            '{} lines omitted (too many to render)'.format(num_labels),
            background_colour=(1, 0.6, 0, 1))
        # l.labels = labels

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
        self.interpreted_lines = []
        self.interpreter.restart()

    def query_restart(self):
        popup = RestartPopup(interpreter_gui=self)
        popup.open()

    def execution_complete(self, *args):
        '''Called when execution is complete so the TextInput should be
        unlocked etc., but first this is delayed until messages finish
        printing.
        '''
        if len(self._output_label_queue) == 0:
            self._execution_complete()
        else:
            self.awaiting_label_display_completion = True

    def _execution_complete(self):
        self.add_break()
        self.lock_input = False
        self.halting = False
        self.ensure_no_ctrl_c_button()

    def get_defs(self):
        previous_text = '\n'.join(self.interpreted_lines)
        num_previous_lines = len(previous_text.split('\n'))

        text = self.code_input.text
        row_index, line, col_index = self.code_input.currently_edited_line()

        get_defs('\n'.join([previous_text, text]),
                 self.show_defs,
                 line=row_index + num_previous_lines + 1,
                 col=col_index)

    def show_defs(self, defs, sigs, error=None):
        print('docs are', defs)
        if error is not None:
            self.add_doc_label(error)
            return
        if not defs and not sigs:
            self.add_doc_label('No definition found at cursor')
            return

        if defs:
            d = defs[0]
        else:
            d = sigs[0]
        if hasattr(d, 'params'):
            text = '{}({})\n{}'.format(d.desc_with_module,
                                            ', '.join([p.description for p in d.params]),
                                            d.doc)
        else:
            text = '{}\n{}'.format(d.desc_with_module,
                                   d.doc)
            
        self.add_doc_label(text)

    def check_completion_threads(self):
        for thread in self.completion_threads:
            if not thread.is_alive():
                self.completion_threads.remove(thread)

    def get_completions(self, extra_text=''):
        if not self.enable_autocompletion:
            return
        
        previous_text = '\n'.join(self.interpreted_lines)
        num_previous_lines = len(previous_text.split('\n'))

        text = self.code_input.text
        row_index, line, col_index = self.code_input.currently_edited_line()
        self.check_completion_threads()
        if len(self.completion_threads) > 3:
            return

        thread = get_completions('\n'.join([previous_text, text + extra_text]),
                                 self.show_completions,
                                 line=row_index + num_previous_lines + 1,
                                 col=col_index)
        self.completion_threads.append(thread)

    def show_completions(self, completions, time=None):
        if time is not None:
            if time < self.most_recent_completion_time:
                return
            self.most_recent_completion_time = time

        self.ids.completions.completions = completions
        # self.ids.completions.text = ', '.join(completions[:5])
        # print('set text')

    def clear_completions(self):
        self.most_recent_completion_time = time()  # block running completions
        self.ids.completions.completions = []


class CompletionButton(KeyboardButton):
    interpreter_gui = ObjectProperty()

    completion_type = StringProperty()
    completion_name = StringProperty()
    completion_complete = StringProperty()

    completion = ObjectProperty()

    colour_mappings = {'keyword': (0, 0.8, 0, 0.1),
                       'instance': (0.8, 0, 0, 0.1),
                       'function': (0, 0, 0.8, 0.1),
                       'module': (0.8, 0.8, 0, 0.1)}

    def on_release(self):
        self.interpreter_gui.ids.completions.completions = []
        self.interpreter_gui.code_input.trigger_completions = False
        for letter in self.completion.complete:
            self.interpreter_gui.code_input.insert_text(letter)
        if App.get_running_app().setting__autocompletion_brackets:
            if self.completion.type in ('function', 'class'):
                if not (self.completion.name == 'print' and sys.version_info.major == 2):
                    # This check is necessary as jedi detects print as a
                    # function in Python 2 on Android (maybe because of
                    # the __future__ import in another file?)
                    self.interpreter_gui.code_input.insert_text('(')
                    self.interpreter_gui.code_input.insert_text(')')
                    self.interpreter_gui.code_input.do_cursor_movement('cursor_left')
        self.interpreter_gui.code_input.trigger_completions = True

    def on_completion(self, instance, completion):
        self.completion_type = completion.type
        self.completion_name = completion.name
        self.completion_complete = completion.complete


class CompletionsList(StackLayout):
    completions = ListProperty([])
    completion_type = StringProperty()
    completion_completion = StringProperty()

    interpreter_gui = ObjectProperty()
    def on_completions(self, instance, completions):
        # self.clear_widgets()
        
        if len(completions) > 5:
            print('too many completions, not showing options')
            self.clear_widgets()

        removals = self.children[:]
        for completion in completions[:5]:
            if not completion.complete:
                continue
            for widget in self.children:
                if widget.completion.name == completion.name:
                    widget.completion = completion
                    removals.remove(widget)
                    break
            else:
                try:
                    button = CompletionButton(
                        # text=completion.name,
                        completion=completion,
                        interpreter_gui=self.interpreter_gui)
                    self.add_widget(button)
                except:
                    print('Exception when making CompletionButton from {}'.format(
                        completion))
                    traceback.print_exc()

        for removal in removals:
            self.remove_widget(removal)

    def on_width(self, instance, value):
        self.on_minimum_width(self, self.minimum_width)

    def on_minimum_width(self, instance, value):
        while sum([c.width for c in self.children]) > self.width:
            self.remove_widget(self.children[0])



class RestartPopup(ModalView):
    interpreter_gui = ObjectProperty()


class BreakMarker(Widget):
    pass


class InputPopup(Popup):
    prompt = StringProperty()
    submit_func = ObjectProperty()

    def submit_text(self, text):
        self.submit_func(text)
        # Window.softinput_mode = 'pan'
        self.dismiss()

    # This is the normal ModalView on_touch_down, with
    # self.submit_func added to ensure that some text is submitted.
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            if self.auto_dismiss:
                self.submit_func(self.ids.ti.text)
                self.dismiss()
                return True
        super(ModalView, self).on_touch_down(touch)
        return True

    # Again, modify the normal _handle_keyboard so that
    # self.submit_func is called before self.dismiss
    def _handle_keyboard(self, window, key, *largs):
        if key == 27 and self.auto_dismiss:
            self.submit_func(self.ids.ti.text)
            self.dismiss()
            return True

class InterpreterMenuDropDown(menu.MenuDropDown):
    pass

class InterpreterMenuButton(menu.MenuButton):
    dropdown_cls = ObjectProperty(InterpreterMenuDropDown)
