import sys
from contextlib import contextmanager


# These don't need to covered.  They are just tesing utilities
@contextmanager
def print_catcher(buff='stdout'):  # pragma: no cover
    if buff == 'stdout':
        sys.stdout = Printer()
        yield sys.stdout
        sys.stdout = sys.__stdout__
    elif buff == 'stderr':
        sys.stderr = Printer()
        yield sys.stderr
        sys.stderr = sys.__stderr__
    else:  # pragma: no cover  This is just to help testing. No need to cover.
        raise ValueError('buff must be either \'stdout\' or \'stderr\'')


class Printer(object):  # pragma: no cover
    def __init__(self):
        self.txt = ""

    def write(self, txt):
        self.txt += txt

    def lines(self):
        for line in self.txt.split('\n'):
            yield line.strip()
