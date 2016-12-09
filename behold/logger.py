import operator
import functools
import inspect

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

class Behold(object):
    _context = {}

    _op_for = {
        '__lt': operator.lt,
        '__lte': operator.le,
        '__le': operator.le,
        '__gt': operator.gt,
        '__gte': operator.ge,
        '__ge': operator.ge,
        '__ne': operator.ne,
        '__in': lambda value, options: value in options
    }

    def __init__(self, item=None, tag=None):
        if item is None:
            frame = inspect.currentframe()
            try:
                item = frame.f_back.f_locals
                item.update(frame.f_back.f_globals)
            finally:
                del frame

        if not isinstance(item, dict):
            try:
                item = item.__dict__
            except:
                raise ValueError(
                    'The \'Behold\' object can only process items that are '
                    'dicts or that have a .__dict__ attribute.'
                )

        self.item = item
        self.tag = tag
        self.all_filters = []
        self.any_filters = []
        self.all_context_filters = []
        self.any_context_filters = []

    def _key_to_field_op(self, key):
        op = operator.eq
        name = key
        for op_name, trial_op in self.__class__._op_for.items():
            if key.endswith(op_name):
                op = trial_op
                name = key.split('__')[0]
                break
        return op, name

    @classmethod
    def set_context(cls, **kwargs):
        cls._context.update(kwargs)

    @classmethod
    def unset_context(cls, *keys):
        for key in keys:
            if key in cls._context:
                cls._context.pop(key)

    def _add_filters(self, exclude, in_context, join_with, **criteria):

        #TODO: make sure you test all 4 combos
        # keyed on (in_context, join_with)
        filters_list = {
            (False, 'all'): self.all_filters,
            (True, 'all'): self.all_context_filters,
            (False, 'any'): self.any_filters,
            (True, 'any'): self.any_context_filters,
        }[(in_context, join_with)]

        for key, val in criteria.items():
            op, field = self._key_to_field_op(key)
            filters_list.append((op, field, val, exclude))

    def _passes_one_filter(
            self, filter_list, is_context=False, is_any_filter=False):
        # set the item you are comparing to based on whether or not this is
        # a context comparison
        if is_context:
            item = self.__class__._context
        else:
            item = self.item

        passes = not is_any_filter
        for (op, field, filter_val, exclude) in self._filters:
            # do not use the extractor for context variables
            if is_context:
                field_val = item[field]
            else:
                field_val = self.extract(item, field)
            passes = exclude ^ op(field_val, val)
            if (not is_any_filter) ^ passes:
                break
        return passes

    def _passes_filter(self):
        # tuples are (filter_list, is_context, is_any_filter)
        filter_tuples = [
            (self.all_filters, False, False),
            (self.any_filters, False, True),
            (self.all_context_filters, True, False),
            (self.any_context_filters, True, True),
        ]

        passes = True
        for filter_list, is_context, is_any_filter in filter_tuples:
            passes = self._passes_one_filter(filter_list, is_context, is_any_filter)
            if not passes:
                break
        return passes

    def when_all(self, **criteria):
        self._add_filters(
            exclude=False, in_context=False, join_with='all', **criteria)
        return self

    def when_any(self, **criteria):
        self._add_filters(
            exclude=False, in_context=False, join_with='any', **criteria)
        return self

    def exlude_when_any(self, **criteria):
        self._add_filters(
            exclude=True, in_context=False, join_with='any', **criteria)
        return self

    def exlude_when_all(self, **criteria):
        self._add_filters(
            exclude=True, in_context=False, join_with='all', **criteria)
        return self

    def when_all_in_context(self, **criteria):
        self._add_filters(
            exclude=False, in_context=True, join_with='all', **criteria)
        return self

    def when_any_in_context(self, **criteria):
        self._add_filters(
            exclude=False, in_context=True, join_with='any', **criteria)
        return self

    def exlude_when_any_in_context(self, **criteria):
        self._add_filters(
            exclude=True, in_context=True, join_with='any', **criteria)
        return self

    def exlude_when_all_in_context(self, **criteria):
        self._add_filters(
            exclude=True, in_context=True, join_with='all', **criteria)
        return self

    def values(self, *fields):
        return self

    @classmethod
    def load_global_state(cls):
        """
        Used for loading any state needed for transform method
        """

    def extract(self, item, name):
        return self.item[name]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return 'behold'

    def __bool__(self):
        return self._passes_filter()


class in_context(object):
    _behold_class = Behold

    def __init__(self, **context_vars):
        self._context_vars = context_vars

    def __call__(self, f):
        @functools.wraps(f)
        def decorated(*args, **kwds):
            with self:
                return f(*args, **kwds)
        return decorated

    def __enter__(self):
        self.__class__._behold_class.set_context(**self._context_vars)

    def __exit__(self, *args, **kwargs):
        self.__class__._behold_class.unset_context(*self._context_vars.keys())


x, y = 1, 2
def dummy():
    a, b = 1, 2
    dd = {'c': 1, 'd': 2}
    class Rob(object):
        def __init__(self):
            self.e = 1
            self.f = 2
    r = Rob()
    behold = Behold(r)
    print
    from pprint import pprint
    pprint(behold.item)
dummy()

#@in_context(what='decorator')
#def myfunc():
#    print Behold._context
#
#
#myfunc()
#print Behold._context
#
#with in_context(what='context_manager'):
#    print Behold._context

