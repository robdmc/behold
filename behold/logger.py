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
    # class variable to hold all context values
    _context = {}

    # operators to handle django-style querying
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
        """
        If item is None, then locals() + globals() is used.
        If its not None, then it must either be a dict or
        something with a dict attribute
        """
        # if no item, get locals() and globals() from calling frame 
        if item is None:
            self.frame = inspect.currentframe().f_back
            item = self._load_frame()
        else:
            self.frame = None

        # if the item is not a dictionary, grab its object __dict__
        if not isinstance(item, dict):
            try:
                item = item.__dict__
            except:
                raise ValueError(
                    'The \'Behold\' object can only process items that are '
                    'dicts or that have a .__dict__ attribute.'
                )

        # sore the item to work with as well as any tag for this beholder
        self.item = item
        self.tag = tag

        # these filters will apply to item or scope variables
        self.all_filters = []
        self.any_filters = []

        # these filters apply to context variables
        self.all_context_filters = []
        self.any_context_filters = []

        # a list of fields that will be printed if filters pass
        self.print_keys = []

    def _load_frame(self):
        OKAY.  HERE IS WHAT IM DOING.  IM PRETY SURE LOCAL/GLOBALS HAVE TO GET
        RELOADED EVERYTIME A BOOL IS CHECKED. SO IM TRYING TO GET THAT TO HAPPEN
        HERE, BUT ITS TRICKY TO GET A FRAME REFERENCE AND DELETE IT PROPERLY
        MAYBE I CAN SAVE THE FRAME DELETION FOR A DESTRUCTOR
            try:
                item = self.frame.f_back.f_locals
                item.update(self.frame.f_back.f_globals)
            finally:
                se
                del self.frame
                self

            return item

    def _key_to_field_op(self, key):
        # this method looks at a key and checks if it ends in any of the
        # endings that have special django-like query meanings.
        # It translates those into comparision operators and returns the
        # name of the actual key.
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
        """
        This method sets context variables
        """
        cls._context.update(kwargs)

    @classmethod
    def unset_context(cls, *keys):
        """
        This method unsets the specified context variables
        """
        for key in keys:
            if key in cls._context:
                cls._context.pop(key)

    def _add_filters(self, exclude, in_context, join_with, **criteria):
        # This is the method does all the work for creating a filter
        # list that will then be used to determine whether or not
        # this beholder passes filters.

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
        # This method does all the work for using the built-up state to
        # determine whether or not this beholder passes filters.

        # set the item you are comparing to based on whether or not this is
        # a context comparison
        if is_context:
            item = self.__class__._context
        else:
            item = self.item

        if not filter_list:
            return True

        passes = not is_any_filter
        for (op, field, filter_val, exclude) in filter_list:
            # do not use the extractor for context variables
            if is_context:
                field_val = item[field]
            else:
                field_val = self.extract(item, field)
            passes = exclude ^ op(field_val, filter_val)
            if (not is_any_filter) ^ passes:
                break
        return passes

    def _passes_filter(self):
        # This is the high-level method that determines whether or not
        # this beholder passes filters.

        # tuples are (filter_list, is_context, is_any_filter)
        filter_tuples = [
            (self.all_filters, False, False),
            (self.any_filters, False, True),
            (self.all_context_filters, True, False),
            (self.any_context_filters, True, True),
        ]

        print '=--'
        passes = True
        for filter_list, is_context, is_any_filter in filter_tuples:
            print passes
            passes = self._passes_one_filter(filter_list, is_context, is_any_filter)
            if not passes:
                break
        print passes, filter_list
        return passes

    def when_all(self, **criteria):
        """
        Beholder will evaluate to True only if all criteria are met
        """
        self._add_filters(
            exclude=False, in_context=False, join_with='all', **criteria)
        return self

    def when_any(self, **criteria):
        """
        Beholder will evaluate to True if any of the criteria are met
        """
        self._add_filters(
            exclude=False, in_context=False, join_with='any', **criteria)
        return self

    def exlude_when_all(self, **criteria):
        """
        Beholder will evaluate to False if all of the criteria are met
        """
        self._add_filters(
            exclude=True, in_context=False, join_with='all', **criteria)
        return self

    def exlude_when_any(self, **criteria):
        """
        Beholder will evaluate to False if any of the criteria are met
        """
        self._add_filters(
            exclude=True, in_context=False, join_with='any', **criteria)
        return self


    def when_all_in_context(self, **criteria):
        """
        Beholder will evaluate to True if all context criteria are met
        """
        self._add_filters(
            exclude=False, in_context=True, join_with='all', **criteria)
        return self

    def when_any_in_context(self, **criteria):
        """
        Beholder will evaluate to True if any context criteria are met
        """
        self._add_filters(
            exclude=False, in_context=True, join_with='any', **criteria)
        return self

    def exlude_when_all_in_context(self, **criteria):
        """
        Beholder will evaluate to False if all context criteria are met
        """
        self._add_filters(
            exclude=True, in_context=True, join_with='all', **criteria)
        return self

    def exlude_when_any_in_context(self, **criteria):
        """
        Beholder will evaluate to False if any context criteria are met
        """
        self._add_filters(
            exclude=True, in_context=True, join_with='any', **criteria)
        return self


    def values(self, *fields):
        """
        Sets the attributes or local variables that will be returned.
        If no arguments are specified, all attributes/variables get shown
        in key-sorted order.
        """

        return self

    @classmethod
    def load_global_state(cls):
        """
        Used for loading any state needed for the extract method
        """

    def extract(self, item, name):
        """
        Override this to perform any custom field extraction
        """
        val = self.item.get(name, None)
        if val is None:
            val = ''
        else:
            val = str(val)
        return val

    def get_str(self):
        if self.print_keys:
            print_keys = self.print_keys
        else:
            print_keys = sorted(self.item.keys())

        out = []
        for ind, key in enumerate(print_keys):
            out.append(key + ':')
            if ind < len(print_keys) - 1 or self.tag:
                ending = ', '
            else:
                ending = ''

            val = self.extract(self.item, name)
            out.append(val + ending)
        if self.tag:
            out.append(tag)
        return ''.join(out)

    def __str__(self):
        if self._passes_filter():
            return self.get_str()
        else:
            return ''

    def __repr__(self):
        return self.__str__()

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

def set_context(**kwargs):
    Behold.set_context(**kwargs)

def unset_context(cls, *keys):
    Behold.unset_context(*keys)


x, y = 1, 2

for nn in range(5):
    behold = Behold()
    behold.values('nn', 'x', 'y').when_all(nn=2)
    if behold:
        print behold




#set_context(rob='awesome')

#
#x, y = 1, 2
#def dummy():
#    a, b = 1, 2
#    dd = {'c': 1, 'd': 2}
#    class Rob(object):
#        def __init__(self):
#            self.e = 1
#            self.f = 2
#    r = Rob()
#    behold = Behold(r)
#    print
#    from pprint import pprint
#    pprint(behold.item)
#dummy()

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

