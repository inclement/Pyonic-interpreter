import time
import ast
import sys

import traceback

from kivy.lib import osc

with open('testfile.txt', 'a') as fileh:
    fileh.write('subprocess working ({})\n'.format(time.asctime()))

send_port = 3001
receive_port = 3000

def receive_message(message, *args):
    real_stdout.write('subprocess received' + str(message) + '\n')
    address = message[0]

    body = [s.decode('utf-8') for s in message[2:]]

    if address == b'/interpret':
        interpret_code(body[0])

    osc.sendMsg(b'/interpreter', [b'completed_exec'], port=send_port,
                typehint='b')
    

def interpret_code(code):
    try:
        exec(code, locals(), globals())
    except Exception as e:
        traceback.print_exc()
        return

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
        real_stdout.write(s)
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

real_stdout = sys.stdout
real_stderr = sys.stderr
sys.stdout = OscOut(b'/stdout', send_port)
sys.stderr = OscOut(b'/stderr', send_port)

def real_print(s):
    real_stdout.write(str(s) + '\n')
    real_stdout.flush()

while True:
    osc.readQueue(oscid)
    time.sleep(.2)


