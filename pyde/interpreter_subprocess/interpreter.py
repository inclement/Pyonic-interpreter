import time
import ast
import sys

import traceback

import threading
import ctypes

from kivy.lib import osc

with open('testfile.txt', 'a') as fileh:
    fileh.write('subprocess working ({})\n'.format(time.asctime()))

send_port = 3001
receive_port = 3000

thread = None

def receive_message(message, *args):
    real_stdout.write('- subprocess received' + str(message) + '\n')
    real_stdout.flush()
    address = message[0]

    osc.sendMsg(b'/interpreter', [b'received_command'], port=send_port,
                typehint='b')

    if address == b'/interpret':
        global thread
        if thread is not None:
            print('COMPUTATION FAILED: something is already running (this shouldn\'t happen)')
            complete_execution()
            return
        body = [s.decode('utf-8') for s in message[2:]]
        t = threading.Thread(target=lambda *args: interpret_code(body[0]))
        # t.daemon = True
        thread = t
        t.start()
        # interpret_code(body[0])

    elif address == b'/ping':
        osc.sendMsg(b'/pong', [b'pong'], port=send_port,
                    typehint='b')

    elif address == b'/sigint':
        pass

    else:
        raise ValueError('Received unrecognised address {}'.format(address))

    real_print('started execution thread')

def complete_execution():
    global thread
    thread = None
    osc.sendMsg(b'/interpreter', [b'completed_exec'], port=send_port,
                typehint='b')
    

def interpret_code(code):
    try:
        exec(code, locals(), globals())
    except KeyboardInterrupt as e:
        traceback.print_exc()
        osc.sendMsg(b'/interpreter', [b'keyboard_interrupted'], port=send_port,
                    typehint='b')
    except Exception as e:
        traceback.print_exc()

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

    def write(self, s):
        s = self.buffer + s
        lines = s.split('\n')
        for l in lines[:-1]:
            self.send_message(l)
        self.buffer = lines[-1]

    def flush(self):
        real_stdout.flush()
        return

    def send_message(self, message):
        osc.sendMsg(self.address, [message.encode('utf-8')],
                    port=self.target_port, typehint='b')

osc.init()
oscid = osc.listen(ipAddr='127.0.0.1', port=receive_port)
osc.bind(oscid, receive_message, b'/interpret')
osc.bind(oscid, receive_message, b'/ping')
osc.bind(oscid, receive_message, b'/sigint')

real_stdout = sys.stdout
real_stderr = sys.stderr
sys.stdout = OscOut(b'/stdout', send_port)
sys.stderr = OscOut(b'/stderr', send_port)

def real_print(s):
    real_stdout.write(str(s) + '\n')
    real_stdout.flush()

while True:
    try:
        osc.readQueue(oscid)
        time.sleep(.2)
    except KeyboardInterrupt:
        traceback.print_exc()


