from kivy.event import EventDispatcher
from kivy.properties import (OptionProperty, BooleanProperty)
from kivy.clock import Clock
from kivy.app import App
from kivy import platform

from os.path import (join, dirname, realpath)
import sys
import os

if platform != 'android':
    import subprocess

if sys.version_info.major >= 3:
    unicode_type = str
    if platform == 'android':
        import osc
    else:
        from pyonic import osc

    package_name = 'net.inclem.pyonicinterpreter3'
else:
    unicode_type = unicode
    from kivy.lib import osc

    package_name = 'net.inclem.pyonicinterpreter'


class InterpreterWrapper(EventDispatcher):

    interpreter_state = OptionProperty('waiting', options=['waiting',
                                                           'interpreting',
                                                           'not_responding',
                                                           'restarting'])
    lock_input = BooleanProperty(False)

    interpreter_number = 0

    def __init__(self, use_thread=True):

        self.register_event_type('on_execution_complete')
        self.register_event_type('on_missing_labels')
        self.register_event_type('on_stdout')
        self.register_event_type('on_stderr')
        self.register_event_type('on_notification')
        self.register_event_type('on_user_message')

        self.subprocess = None

        self.use_thread = use_thread

        self.start_interpreter()

        self.input_index = 0  # The current input number
        self.inputs = {}  # All the inputs so far

        py_ver = sys.version_info.major
        self.interpreter_port = 3000 + 10 * py_ver
        self.receive_port = 3001 + 10 * py_ver

        Clock.schedule_interval(self.read_osc_queue, 0.05)

        self.init_osc()

        self._interpreter_state = 'waiting'

        # This check_interpreter method is not reliable enough to enable yet.
        # App.get_running_app().bind(on_resume=self.check_interpreter)

    def on_execution_complete(self):
        pass

    def on_missing_labels(self, num_labels):
        pass

    def on_stdout(self, text):
        pass

    def on_stderr(self, text):
        pass

    def on_notification(self, text):
        pass

    def on_user_message(self, text):
        pass

    def start_interpreter(self):
        interpreter_script_path = join(dirname(realpath(__file__)),
                                       'interpreter_subprocess',
                                       'interpreter.py')

        # prepare settings to send to interpreter
        throttle_output = '1' if App.get_running_app().setting__throttle_output else '0'

        use_thread = '1' if self.use_thread else '0'

        argument = 'throttle_output={}:use_thread={}'.format(throttle_output, use_thread)

        if platform == 'android':
            from jnius import autoclass
            service = autoclass('{}.ServiceInterpreter'.format(package_name))
            mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
            service.start(mActivity, argument)
        else:
            # This may not actually work everywhere, but let's assume it does
            print('starting subprocess')
            python_name = 'python{}'.format(sys.version_info.major)
            print('python name is', python_name)
            os.environ['PYTHON_SERVICE_ARGUMENT'] = argument
            s = subprocess.Popen([python_name, '{}'.format(interpreter_script_path)])
            App.get_running_app().subprocesses.append(s)
            self.subprocess = s
            pass

    def send_sigint(self):
        self.send_osc_message(b'sigint', address=b'/sigint')

    def init_osc(self):
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
                self.dispatch('on_execution_complete')
                self.interpreter_state = 'waiting'
                # self.end_osc_listen()

            elif body[0] == 'received_command':
                Clock.unschedule(self.command_not_received)

            elif body[0].startswith('omitted'):
                number = body[0].split(' ')[-1]
                self.dispatch('on_missing_labels', number)

        elif address == b'/pong':
            self.pong()

        elif address == b'/stdout':
            self.dispatch('on_stdout', body[0])

        elif address == b'/stderr':
            self.dispatch('on_stderr', body[0])

    def interpret_line(self, text):
        self.send_python_command(text.encode('utf-8'))
        self.lock_input = True
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
            service = autoclass('{}.ServiceInterpreter'.format(package_name))
            mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
            service.stop(mActivity)
            self.start_interpreter()
        else:
            self.subprocess.kill()
            self.start_interpreter()

        self.lock_input = True
        self.interpreter_state = 'restarting'
        Clock.unschedule
        Clock.schedule_interval(self.ping, 0.3)

    def finish_restart(self):
        if self.interpreter_state != 'restarting':
            raise ValueError('Tried to finish restarting, but was not restarting')
        self.interpreter_state = 'waiting'
        self.lock_input = False
        self.dispatch('on_notification', '[b]interpreter restarted: variable context lost[/b]')

    def check_interpreter(self, *args):
        print('checking interpreter')
        Clock.schedule_once(self.ping, 2)

    def restart_halted_interpreter(self):
        print('interpreter is halted')
        self.dispatch('on_user_message', 
            ('The interpreter is not responding, it may have been killed by the OS '
             'while paused. Restarting.'))
        self.restart()

    def ping(self, *args, **kwargs):
        timeout = kwargs.get('timeout', 2)
        self.send_osc_message(b'ping', address=b'/ping')
        Clock.schedule_once(self.ping_failed, timeout)

    def ping_failed(self, *args, **kwargs):
        if self.interpreter_state != 'restarting':
            self.interpreter_state = 'not_responding'

    def pong(self):
        print('Received pong')
        Clock.unschedule(self.ping_failed)
        if self.interpreter_state == 'restarting':
            self.finish_restart()
            Clock.unschedule(self.ping)

    def set_service_output_throttling(self, value):
        self.send_osc_message(b'1' if value else b'0', b'/throttling')


class DummyInterpreter(object):
    def __getattr__(self, *args, **kwargs):
        return lambda *args, **kwargs: 1
