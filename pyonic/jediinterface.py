
from jedi import Script, settings
settings.case_insensitive_completion = False

from os.path import abspath, join
settings.cache_directory = join(abspath('.'), '.cache', 'jedi')

from kivy.event import EventDispatcher
from kivy.properties import ListProperty, ObjectProperty
from kivy.clock import mainthread

from functools import partial

from time import time

import threading

import traceback

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

    func = WrappablePartial(func, time=time())

    t = threading.Thread(target=WrappablePartial(_get_completions, source, func, line=line, column=col))
    t.start()

    return t

def _get_completions(source, func, line=None, column=None):
    try:
        num_lines = len(source.split('\n'))
        if line is None:
            line = num_lines
        s = Script(source, line=line, column=column)
        completions = s.completions()
        # print('### input:')
        # print(source)
        # print('### completions:')
        # print('\n'.join([c.name for c in completions]))
    except:
        print('Exception in completions thread')
        traceback.print_exc()
        completions = []

    mainthread(WrappablePartial(func, [c for c in completions]))()


def get_defs(source, func, line=None, col=None):
    t = threading.Thread(target=WrappablePartial(_get_defs, source, func, line=line, column=col))
    t.start()

def _get_defs(source, func, line=None, column=None):
    error = None
    try:
        num_lines = len(source.split('\n'))
        if line is None:
            line = num_lines
        s = Script(source, line=line, column=column)
        defs = s.goto_definitions()
        sigs = s.call_signatures()
    except:
        print('Exception in defs thread')
        traceback.print_exc()
        defs = []
        sigs = []
        error = 'Could not retrieve docstring'

    mainthread(WrappablePartial(func, defs, sigs, error=error))()
