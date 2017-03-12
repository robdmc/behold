from __future__ import print_function
import contextlib
import datetime
import sys
from collections import Counter

import pandas as pd

import psutil


class OutStream(object):  # pragma no cover
    """
    This class exisist for easing testing of sys.stdout and doesn't
    need to be tested itself
    """
    header_text = '__time__,time,tag'
    header_needs_printing = True

    def write(self, *args, **kwargs):
        if self.__class__.header_needs_printing:
            sys.stdout.write('{}\n'.format(self.__class__.header_text))
            self.__class__.header_needs_printing = False
        sys.stdout.write(*args, **kwargs)


class TimerResult(object):
    def __init__(self, label, starting, ending=None, seconds=None):
        self.label = label
        self.starting = starting
        self.ending = ending
        self.seconds = seconds

    def __str__(self):
        return '__time__,{},{}'.format(self.seconds, self.label)

    def __repr__(self):
        return self.__str__()


@contextlib.contextmanager
def Timer(name='', silent=False, pretty=False, header=True):
    """
    A context manager for timing sections of code.
    :type name: str
    :param name: The name you want to give the contextified code
    :type silent: bool
    :param silent: Setting this to true will mute all printing
    :type pretty: bool
    :param pretty: When set to true, prints elapsed time in hh:mm:ss.mmmmmm
    Example
    ---------------------------------------------------------------------------
    # Example code for timing different parts of your code
    import time
    from behold import Timer
    with Timer('entire script'):
        for nn in range(3):
            with Timer('loop {}'.format(nn + 1)):
                time.sleep(.1 * nn)
    # Will generate the following output on stdout
    #     col1: a string that is easily found with grep
    #     col2: the time in seconds (or in hh:mm:ss if pretty=True)
    #     col3: the value passed to the 'name' argument of Timer

    __time__,2.6e-05,loop 1
    __time__,0.105134,loop 2
    __time__,0.204489,loop 3
    __time__,0.310102,entire script

    ---------------------------------------------------------------------------
    # Example for measuring how a piece of of code scales (measuring "big-O")
    import time
    from behold import Timer

    # initialize a list to hold results
    results = []

    # run a piece of code with different values of the var you want to scale
    for nn in range(3):
        # time each iteration
        with Timer('loop {}'.format(nn + 1), silent=True) as timer:
            time.sleep(.1 * nn)
        # add results
        results.append((nn, timer))

    # print csv compatible text for further pandashells processing/plotting
    print 'nn,seconds'
    for nn, timer in results:
        print '{},{}'.format(nn,timer.seconds)
    """
    if not header:
        OutStream.header_needs_printing = False
    stream = OutStream()
    result = TimerResult(name, starting=datetime.datetime.now())
    yield result
    result.ending = datetime.datetime.now()
    dt = result.ending - result.starting
    result.seconds = dt.total_seconds()
    dt = dt if pretty else result.seconds
    if not silent:
        stream.write('__time__,{},'.format(dt))
        if name:
            stream.write('%s\n' % name)


py_proc = psutil.Process()


def show_mem(tag=''):
    megs = int(py_proc.memory_full_info().uss / float(2 ** 20))
    print('__memory__: {}M  {}'.format(megs, tag))


class Clock(object):
    def __init__(self):
        # see the reset method for instance attributes
        self.reset()

    def start(self, name):
        if name not in self.active_start_times:
            self.active_start_times[name] = datetime.datetime.now()

    def stop(self, name):
        ending = datetime.datetime.now()
        if name in self.active_start_times:
            starting = self.active_start_times.pop(name)
            self.delta.update({name: (ending - starting).total_seconds()})

    @contextlib.contextmanager
    def timer(self, name):
        self.start(name)
        yield
        self.stop(name)

    def pause(self):
        active_names = list(self.active_start_times.keys())
        for name in active_names:
            self.stop(name)
            self.paused_set.add(name)

    def resume(self):
        for name in self.paused_set:
            self.start(name)
        self.paused_set = set()

    def reset(self):
        self.delta = Counter()
        self.active_start_times = dict()
        self.paused_set = set()

    def __str__(self):
        records = sorted(self.delta.items(), key=lambda t: t[1], reverse=True)
        records = [(r[0], '{}'.format(r[1])) for r in records]
        names, times = zip(*records)

        name_width = max([len(r[0] for r in records])) + 1
        time_width = max([len(r[1] for r in records])) + 1
        names = [name.ljust(name_width), for name in names]
        times = [time.ljust(time_width), for time in times]
        header = '{}{}'.format(
            'name'.ljust(name_width), 'seconds'.ljust(time_width))


        #max_t_width = max([len(r[0] for r in records])
        #df = pd.DataFrame(records, columns=['name', 'seconds'])
        #out = '\n'
        #out += df[['seconds', 'name']].to_string()
        return out

    def __repr__(self):
        return self.__str__()
