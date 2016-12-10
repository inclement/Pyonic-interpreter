
from jedi import Script, settings
settings.case_insensitive_completion = False

from kivy.event import EventDispatcher
from kivy.properties import ListProperty, ObjectProperty
from kivy.clock import mainthread

from functools import partial

from time import time

import threading


###########################################################
# python2.7.2 compatible partial from http://stackoverflow.com/questions/20594193/dynamic-create-method-and-decorator-got-error-functools-partial-object-has-no
###########################################################
class WrappablePartial(partial):

    @property
    def __module__(self):
        return self.func.__module__

    @property
    def __name__(self):
        return "functools.partial({}, *{}, **{})".format(
            self.func.__name__,
            self.args,
            self.keywords
        )

    @property
    def __doc__(self):
        return self.func.__doc__
############################################################


def get_completions(source, func, line=None, col=None):

    print('============')
    print('asked to complete for:')
    print(source)
    print('row', line, 'col', col)
    print('============')

    func = partial(func, time=time())

    t = threading.Thread(target=WrappablePartial(_get_completions, source, func, line=line, column=col))
    t.start()

def _get_completions(source, func, line=None, column=None):
    num_lines = len(source.split('\n'))
    if line is None:
        line = num_lines
    s = Script(source, line=line, column=column)
    completions = s.completions()
    print('### input:')
    print(source)
    print('### completions:')
    print('\n'.join([c.name for c in completions]))

    mainthread(WrappablePartial(func, [c for c in completions]))()


def get_defs(source, func, line=None, col=None):
    t = threading.Thread(target=WrappablePartial(_get_defs, source, func, line=line, column=col))
    t.start()

def _get_defs(source, func, line=None, column=None):
    num_lines = len(source.split('\n'))
    if line is None:
        line = num_lines
    s = Script(source, line=line, column=column)
    defs = s.goto_definitions()

    mainthread(WrappablePartial(func, defs))()
