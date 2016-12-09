import operator

"""
Input defaults to locals().  If it's a dict, then kwargs will reference keys.  Otherwise, kwargs will reference
attributes.

logger = DBLog(locals(), tag='mytag')  # see if I can pop stack frame to get locals

DBLog.set_global(gx=1, gy=2) # can just set class attributes

logger.when_all(x=1, y=2)
logger.when_any(z=1, f=4)

logger.when_all_global(x=1, y=2)
logger.when_any_gobal(z=2, z=3)

logger.values('x', 'y', 'z')
if logger:
    print logger

    If values is set, then print in order of values.  Otherwise just print ordered keys.
    maybe have a format option that allows 'keyvalue',  'csv', 'json'


    Think about using this
    http://stackoverflow.com/questions/6618795/get-locals-from-calling-namespace-in-python

    Call the project behold and the class Behold

    I also want context managers and decorators for setting global state

    with Behold.using_global(x=1, y=2):
        my_func_here()

    with using_global(x=1, y=2):
        my_func_here()

    @Behold.using_global(x=1, y=2)
    def my func():
        pass

    @using_global(x=1, y=2)
    def my func():
        pass


Look at this for multiple python versions
https://gist.github.com/pombredanne/72130ee6f202e89c13bb

"""

class in_global_context(object):
    def __call__(self, f):
        @functools.wraps(f)
        def decorated(*args, **kwds):
            with self:
                return f(*args, **kwds)
        return decorated

    def __enter__(self):
        pass

    def __exit__(self):
        pass




#class Behold(object):
#   _global_state = {}
#
#    _op_for = {
#        '__lt': operator.lt,
#        '__lte': operator.le,
#        '__le': operator.le,
#        '__gt': operator.gt,
#        '__gte': operator.ge,
#        '__ge': operator.ge,
#        '__ne': operator.ne,
#        '__in': lambda value, options: value in options
#    }
#
#    def __init__(self, item, tag=None):
#        self.item = item
#        self.tag = tag
#        self.all_filters = []
#        self.any_filters = []
#
#    def _key_to_field_op(self, key):
#        op = operator.eq
#        name = key
#        for op_name, trial_op in self.__class__._op_for.items():
#            if key.endswith(op_name):
#                op = trial_op
#                name = key.split('__')[0]
#                break
#        return op, name
#
#    def update_global_context(self, **kwargs):
#        self.__class__.global_state.update(kwargs)
#
#    def when_all_global(self, **criteria):
#        return self
#
#    def when_any_global(self, **criteria):
#        return self
#
#    def when_all(self, **criteria):
#        return self
#
#    def when_any(self, **criteria):
#        return self
#
#    def values(self, *fields):
#        return self
#
#    def load_global_context(self):
#        # method to load any state required by pretty stuff
#        return self
#
#    def load_local_context(self):
#        # method to load any state required by pretty stuff
#        return self
#
#    def pretty(self, item, key, value):
#        # hook to transorm printed stuff
#        return self
#
#    def __repr__(self):
#        return self.__str__()
#
#    def __str__(self):
#        return 'behold'






