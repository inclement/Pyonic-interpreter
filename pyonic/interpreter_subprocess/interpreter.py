import copy


user_locals = copy.copy(locals())
user_globals = copy.copy(globals())

import time
import ast
import sys
import os

import traceback

import threading
import ctypes
import inspect

from kivy import platform

if sys.version_info.major >= 3:
    unicode_type = str
    if platform == 'android':
        import osc
    else:
        from pyonic import osc
else:
    unicode_type = unicode
    from kivy.lib import osc

real_stdout = sys.stdout
real_stderr = sys.stderr
def real_print(*s):
    real_stdout.write(' '.join([str(item) for item in s]) + '\n')
    real_stdout.flush()


send_port = 3001
receive_port = 3000

thread = None

throttle_output = True

##########################################
# from http://stackoverflow.com/questions/5899692/how-to-terminate-a-python3-thread-correctly-while-its-reading-a-stream
##########################################
def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble, 
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
        raise SystemError("PyThreadState_SetAsyncExc failed")

def stop_thread(thread):
    _async_raise(thread.ident, KeyboardInterrupt)
##########################################

def receive_message(message, *args):
    real_stdout.write('- subprocess received' + str(message) + '\n')
    real_stdout.flush()
    address = message[0]

    osc.sendMsg(b'/interpreter', [b'received_command'], port=send_port,
                typehint='b')

    global thread
    if address == b'/interpret':
        if thread is not None:
            print('COMPUTATION FAILED: something is already running (this shouldn\'t happen)')
            complete_execution()
            return
        body = [s.decode('utf-8') for s in message[2:]]
        t = threading.Thread(target=lambda *args: interpret_code(body[0]))
        # t.daemon = True
        thread = t
        t.start()

    elif address == b'/ping':
        osc.sendMsg(b'/pong', [b'pong'], port=send_port,
                    typehint='b')

    elif address == b'/sigint':
        if thread is None:
            print('Received interrupt but there is no thread to stop - this should not happen')
        else:
            real_stdout.write('trying to stop thread {}\n'.format(thread))
            real_stdout.flush()
            stop_thread(thread)

    elif address == b'/throttling':
        global throttle_output
        body = message[2:]
        if body[0] == b'1':
            throttle_output = True
        elif body[0] == b'0':
            throttle_output = False
        else:
            print('Error changing output throttling: received value {}'.format(body[0]))

    else:
        raise ValueError('Received unrecognised address {}'.format(address))


def complete_execution():
    global thread
    thread = None
    try:
        osc.sendMsg(b'/interpreter', [b'completed_exec'], port=send_port,
                    typehint='b')
    except KeyboardInterrupt:
        complete_execution()
    

def interpret_code(code):
    try:
        sys.stdout.can_omit = True
        # The input is first parsed as ast, then if the last statement
        # is an Expr compiled partially in single mode. This means
        # that the last statement output is printed, as in the normal
        # Python interpreter

        components = ast.parse(code).body

        # print('components are', components)

        # exec all but the last ast component in exec mode
        if len(components) > 1:
            for component in components[:-1]:
                c = compile(ast.Module([component]), '<stdin>', mode='exec')
                exec(c, user_locals, user_globals)

        # if the last ast component is an Expr, compile in single mode to print it
        if isinstance(components[-1], ast.Expr):
            c = compile(ast.Interactive([components[-1]]), '<stdin>', mode='single')
        else:
            c = compile(ast.Module([components[-1]]), '<stdin>', mode='exec')
        exec(c, user_locals, user_globals)

    except KeyboardInterrupt as e:
        print('')
        traceback.print_exc()
        osc.sendMsg(b'/interpreter', [b'keyboard_interrupted'], port=send_port,
                    typehint='b')
    except Exception as e:
        print('an exception occurred')
        traceback.print_exc()
    finally:
        sys.stdout.can_omit = False

    complete_execution()

    # instructions = ast.parse(code)
    # if isinstance(instructions.body[-1], ast.Expr):
    #     exec('print({})'.format(instructions.body[-1].value.id))


class OscOut(object):
    def __init__(self, address, target_port):
        self.buffer = ''
        self.address = address
        assert isinstance(address, bytes)

        self.target_port = target_port

        self.messages_this_second = 0
        self.last_time = time.time()

        self.can_omit = False

    def write(self, s):
        if time.time() - self.last_time > 1.2:
            self.messages_this_second = 0
        try:
            self.messages_this_second += 1
            if time.time() - self.last_time > 1.:
                if self.messages_this_second > 500 and (self.can_omit and throttle_output):
                    message = 'omitted {}'.format(self.messages_this_second - 500)
                    osc.sendMsg(b'/interpreter', [message.encode('utf-8')],
                                port=self.target_port, typehint='b')
                self.messages_this_second = 0
                self.last_time = time.time()
            if self.messages_this_second > 500 and self.can_omit and throttle_output:
                return

            s = self.buffer + s
            lines = s.split('\n')
            for l in lines[:-1]:
                self.send_message(l)
            self.buffer = lines[-1]
        except KeyboardInterrupt:
            raise KeyboardInterrupt('interrupted while printing')

    def flush(self):
        return

    def send_message(self, message):
        try:
            osc.sendMsg(self.address, [
                message.encode('utf-8') if isinstance(message, unicode_type)
                else message],
                        port=self.target_port, typehint='b')
        except KeyboardInterrupt:
            raise KeyboardInterrupt('interrupted while printing')

print('got this far')

osc.init()
oscid = osc.listen(ipAddr='127.0.0.1', port=receive_port)
osc.bind(oscid, receive_message, b'/interpret')
osc.bind(oscid, receive_message, b'/ping')
osc.bind(oscid, receive_message, b'/sigint')
osc.bind(oscid, receive_message, b'/throttling')

sys.stdout = OscOut(b'/stdout', send_port)
sys.stderr = OscOut(b'/stderr', send_port)

to = os.environ.get('PYTHON_SERVICE_ARGUMENT', '')
for entry in to.split(':'):
    if entry.startswith('throttle_output='):
        throttle_output = False if entry[16:] == '0' else True

real_print('got this far4')

while True:
    osc.readQueue(oscid)
    time.sleep(.1)


