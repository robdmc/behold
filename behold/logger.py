from collections import defaultdict, OrderedDict
import copy
import functools
import inspect
import operator
import sys

# TODO: THINK ABOUT CHANGING ALL NON-INTERFACE METHODS TO PRIVATE

# TODO:  Maybe add a strict kwark go Behold that will fail if
#        context/values keys aren't found.

# TODO: make sure you can filter on unshown variables
# TODO: test the inquality operator


class _Sentinal(object):
    pass


class Item(object):
    """
    Item is a simple container class that sets its attributes from constructor
    kwargs.  It supports both object and dictionary access to its attributes.
    So, for example, all of the following statements are supported.

    .. code-block:: python

       item = Item(a=1, b=2)
       item['c'] = 2
       a = item['a']

    An instance of this class is created when you ask to show local variables
    with a `Behold` object. The local variables you want to show are attached as
    attributes to an `Item` object.
    """
    # I'm using unconventional "_item_self_" name here to avoid
    # conflicts when kwargs actually contain a "self" arg.

    def __init__(_item_self, **kwargs):
        for key, val in kwargs.items():
            _item_self[key] = val

    def __str__(_item_self):
        quoted_keys = [
            '\'{}\''.format(k) for k in sorted(vars(_item_self).keys())]
        att_string = ', '.join(quoted_keys)
        return 'Item({})'.format(att_string)

    def __repr__(_item_self):
        return _item_self.__str__()

    def __setitem__(_item_self, key, value):
        setattr(_item_self, key, value)

    def __getitem__(_item_self, key):
        return getattr(_item_self, key)


class Behold(object):
    """
    :type tag: str
    :param tag: A tag with which to label all output (default: None)

    :type strict: Bool
    :param strict: When set to true, will only only allow existing keys to be
                   used in the ``when_contex()`` and ``when_values()``
                   methods.

    :type stream: FileObject
    :param stream:  Any write-enabled python FileObject  (default: sys.stdout)

    :ivar stream: sys.stdout: The stream that will be written to
    :ivar tag: None: A string with which to tag output
    :ivar strict: False: A Bool that sets whether or not only existing keys
                         allowed in ``when_contex()`` and ``when_values()``
                         methods.

    ``Behold`` objects are used to probe state within your code base.  They can
    be used to log output to the console or to trigger entry points for step
    debugging.

    Because it is used so frequently, the behold class has a couple of aliases.
    The following three statements are equivalent

    .. code-block:: python

       from behold import Behold  # Import using the name of the class

       from behold import B       # If you really hate typing

       from behold import BB      # If you really hate typing but would
                                  # rather use a name that's easier to
                                  # search for in your editor.

       from behold import *       # Although bad practice in general, since
                                  # you'll usually be using behold just for
                                  # debugging, this is pretty convenient.


    """
    # class variable to hold all context values
    _context = {}
    _stash = defaultdict(list)

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
    # TODO; maybe add __contains and __startwith
    # And if you do, add it to the when*() methods docstrings

    def __init__(self, tag=None, strict=False, stream=None):
        self.tag = tag
        self.strict = strict

        #: Doc comment for class attribute Foo.bar.
        #: It can have multiple lines.
        self.stream = None
        if stream is None:
            self.stream = sys.stdout
        else:
            self.stream = stream

        # these filters apply to context variables
        self.passes = True
        self.context_filters = []
        self.value_filters = []
        self._viewed_context_keys = []

        # a list of fields that will be printed if filters pass
        self.print_keys = []

        # holds a string rep for this object
        self._str = ''

        # a bool to hold whether or not all filters have passed
        self._passes_all = False

    def reset(self):
        self.passes = False
        self.context_filters = []
        self.value_filters = []
        self._viewed_context_keys = []

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
        cls._context.update(kwargs)

    @classmethod
    def unset_context(cls, *keys):
        for key in keys:
            if key in cls._context:
                cls._context.pop(key)

    def when(self, *bools):
        """
        :type bools: bool
        :param bools: Boolean arguments

        All boolean arguments passed to this method must evaluate to `True` for
        printing to be enabled.

        So for example, the following code would print ``x: 1``

        .. code-block:: python

           for x in range(10):
               Behold().when(x == 1).show('x')
        """
        self.passes = self.passes and all(bools)
        return self

    def view_context(self, *context_keys):
        """
        :type context_keys: string arguments
        :param context_keys: Strings with context keys

        Supply this method with any context keys you would like to show.
        """
        self._viewed_context_keys.extend(context_keys)
        return self

    def when_context(self, **criteria):
        """
        :type criteria: kwargs
        :param criteria: Key word arguments of var_name=var_value

        The key-word arguments passed to this method specify the context
        constraints that must be met in order for printing to occur.  The
        syntax of these constraints is reminiscent of that used in Django
        querysets.  All specified criteria must be met for printing to occur.

        The following syntax is supported.

        * ``x__lt=1`` means ``x < 1``
        * ``x__lte=1`` means ``x <= 1``
        * ``x__le=1`` means ``x <= 1``
        * ``x__gt=1`` means ``x > 1``
        * ``x__gte=1`` means ``x >= 1``
        * ``x__ge=1`` means ``x >= 1``
        * ``x__ne=1`` means ``x != 1``
        * ``x__in=[1, 2, 3]`` means ``x in [1, 2, 3]``

        The reason this syntax is needed is that the context values being
        compared are not available in the local scope.  This renders the normal
        Python comparison operators useless.
        """
        self._add_context_filters(**criteria)
        return self

    def when_values(self, **criteria):
        """
        By default, ``Behold`` objects call ``str()`` on all variables before
        sending them to the output stream.  This method enables you to filter on
        those extracted string representations.  The syntax is exactly like that
        of the ``when_context()`` method.  Here is an example.

        .. code-block:: python

           from behold import Behold, Item

           items = [
              Item(a=1, b=2),
              Item(c=3, d=4),
           ]

           for item in items:
              # You can filter on the string representation
              Behold(tag='first').when_values(a='1').show(item)

              # Behold is smart enough to transform your criteria to strings
              # so this also works
              Behold(tag='second').when_values(a=1).show(item)

              # Because the string representation is not present in the local
              # scope, you must use Django-query-like syntax for logical
              # operations.
              Behold(tag='third').when_values(a__gte=1).show(item)
        """
        criteria = {k: str(v) for k, v in criteria.items()}
        self._add_value_filters(**criteria)
        return self

    def _add_context_filters(self, **criteria):
        for key, val in criteria.items():
            op, field = self._key_to_field_op(key)
            self.context_filters.append((op, field, val))

    def _add_value_filters(self, **criteria):
        for key, val in criteria.items():
            op, field = self._key_to_field_op(key)
            self.value_filters.append((op, field, val))

    def _passes_filter(self, filter_list, value_extractor, default_when_missing=True):
        passes = True
        for (op, field, filter_val) in filter_list:
            # _Sentinal object means current value couldn't be extraced
            current_val = value_extractor(field)
            no_value_found = isinstance(current_val, _Sentinal)

            # if you couldn't extract a value, do the default thing
            if no_value_found:
                passes = default_when_missing
            # otherwise update whether or not this passes
            else:
                passes = passes and op(current_val, filter_val)

            if not passes:
                return False
        return True

    def _passes_value_filter(self, item, name):
        if not self.value_filters:
            return True

        def value_extractor(field):
            return self.extract(item, field)

        return self._passes_filter(self.value_filters, value_extractor)

    def _strict_checker(self, names, item=None):
        if self.strict:
            names = set(names)
            if item is None:
                allowed_names = set(self.__class__._context.keys())
            else:
                allowed_names = set(item.__dict__.keys())
            bad_names = names - allowed_names
            if bad_names:
                msg = (
                    '\n\nKeys {} not found.\n'
                    'Allowed keys: {}'
                ).format(
                    list(sorted(bad_names)),
                    list(sorted(allowed_names))
                )

                raise ValueError(msg)

    def _passes_context_filter(self):
        if not self.context_filters:
            return True
        else:

            def value_extractor(field):
                return self.__class__._context.get(field, _Sentinal())

            return self._passes_filter(
                self.context_filters, value_extractor,
                default_when_missing=False)

    def passes_all(self, item=None, att_names=None):
        if not self.passes or not self._passes_context_filter():
            self._passes_all = False

        elif item is not None and att_names is not None:
            self._passes_all = all([
                self._passes_value_filter(item, name)
                for name in att_names
            ])
        else:
            self._passes_all = True
        return self._passes_all

    def _separate_names_objects(self, values):
        att_names = []
        objs = []
        for val in values:
            if isinstance(val, str):
                att_names.append(val)
            else:
                objs.append(val)
        return att_names, objs

    def _validate_objs(self, objs):
        has_obj = bool(objs)
        has_multi_objs = len(objs) > 1

        # only allow at most one object
        if has_multi_objs:
            raise ValueError(
                '\n\nYou can pass at most one non-string argument.'
            )

        if has_obj:
            # make sure object is useable
            if not hasattr(objs[0], '__dict__'):
                raise ValueError(
                    'Error in Behold() The object you passed has '
                    'no __dict__ attribute'
                )

    def _get_item_and_att_names(self, *values, **data):
        if not self.passes_all():
            return None, None

        att_names, objs = self._separate_names_objects(values)
        all_att_names = set(att_names)

        # gather information about the inputs
        has_data = bool(data)
        has_obj = bool(objs)

        # make sure objs are okay
        self._validate_objs(objs)

        # If an object was provided, create a dict with its attributes
        if has_obj:
            att_dict = objs[0].__dict__

        # If no object was provided, construct an item from the calling local
        # scope
        else:
            # this try/else block is needed to breake reference cycles
            try:
                att_dict = {}
                calling_frame = inspect.currentframe().f_back.f_back

                # update with local variables of the calling frame
                att_dict.update(calling_frame.f_locals)
            finally:
                # delete the calling frame to avoid reference cycles
                del calling_frame

        # If data was passed, it gets priority
        if has_data:
            att_dict.update(data)
            att_names.extend(sorted(data.keys()))

        # if no attribute names supplied, use all of them
        if not att_names:
            att_names = sorted(att_dict.keys())
            all_att_names = all_att_names.union(set(att_names))

        # do strict check if requested
        if self.strict:
            self._strict_checker(att_names, item=Item(**att_dict))

        # check for values passing
        if not self.passes_all(Item(**att_dict), list(all_att_names)):
            return None, None

        # Limit the att_dict to have only requested attributes.
        # Using an ordered dict here to preserve attribute order
        # while deduplicating
        ordered_atts = OrderedDict()
        for att_name in att_names:
            ordered_atts[att_name] = att_dict.get(att_name, None)

        # Make an item out of the att_dict (might lose order, but don't care)
        item = Item(**ordered_atts)

        # make an ordered list of attribute names
        ordered_att_names = list(ordered_atts.keys())
        return item, ordered_att_names

    @classmethod
    def get_stash(cls, stash_name):
        if stash_name in cls._stash:
            return copy.deepcopy(cls._stash[stash_name])
        else:
            raise ValueError(
                '\n\nRequested name \'{}\' not in {}'.format(
                    stash_name, list(cls._stash.keys()))
            )

    @classmethod
    def clear_stash(cls, *names):
        if names:
            for name in names:
                if name in cls._stash:
                    del cls._stash[name]
                else:
                    raise ValueError(
                        '\n\nName \'{}\' not in {}'.format(
                            name, list(cls._stash.keys())
                        )
                    )
        else:
            cls._stash = defaultdict(list)

    def stash(self, *values, **data):
        """
        The stash method allows you to stash values for later analysis.  The
        arguments are identical to the ``show()`` method.  Instead of writing
        outpout, however, the ``stash()`` method populates a global list with
        the values that would have been printed.  This allows them to be
        accessed later in the debugging process.

        Here is an example.

        .. code-block:: python

           from behold import Behold, get_stash

           for nn in range(10):
               # You can only invoke ``stash()`` on behold objects that were
               # created with tag.  The tag becomes the global key for the stash
               # list.
               behold = Behold(tag='my_stash_key')
               two_nn = 2 * nn

               behold.stash('nn' 'two_nn')

           # You can then run this in a completely different file of your code
           # base.
           my_stashed_list = get_stash('my_stash_key')
        """
        if not self.tag:
            raise ValueError(
                'You must instantiate Behold with a tag name if you want to '
                'use stashing'
            )

        item, att_names = self._get_item_and_att_names(*values, **data)
        if not item:
            self.reset()
            return False

        out = {name: item.__dict__.get(name, None) for name in att_names}

        self.__class__._stash[self.tag].append(out)
        self.reset()
        return True

    def get(self, *values, **data):
        item, att_names = self._get_item_and_att_names(*values, **data)
        if not item:
            self.reset()
            return None
        out = {name: item.__dict__.get(name, None) for name in att_names}
        return out

    def is_true(self, item=None):
        """
        If you are filtering on object values, you need to pass that object here.
        """
        if item:
            values = [item]
        else:
            values = []
        self._get_item_and_att_names(*values)
        return self._passes_all

    def show(self, *values, **data):
        """
        :type values: str arguments
        :param values: A list of variable or attribute names you want to print.
                       At most one argument can be something other than a
                       string.  Strings are interpreted as the
                       variable/attribute names you want to print. If a single
                       non-string argument is provided, it must be an object
                       having attributes named in the string variables.  If no
                       object is provided, the strings must be the names of
                       variables in the local scope.

        :type data: keyword args
        :param data: A set of keyword arguments.  The key provided will be the
                     name of the printed variables.  The value associated with
                     that key will have its str() representation printed. You
                     can think of these keyword args as attatching additional
                     attributes to any object that was passed in args.  If no
                     object was passed, then these kwargs will be used to create
                     an object.

        This method will return ``True`` if all the filters passed, otherwise it
        will return ``False``.  This allows you to perform additional logic in
        your debugging code if you wish.  Here are some examples.

        .. code-block:: python

           from behold import Behold, Item
           a, b = 1, 2
           my_list = [a, b]

           # show arguments from local scope
           Behold().show('a', 'b')

           # show values from local scope using keyword arguments
           Behold.show(a=my_list[0], b=my_list[1])

           # show values from local scope using keyword arguments, but
           # force them to be printed in a specified order
           Behold.show('b', 'a', a=my_list[0], b=my_list[1])

           # show attributes on an object
           item = Item(a=1, b=2)
           Behold.show(item, 'a', 'b')

           # use the boolean return by show to control more debugging
           a = 1
           if Behold.when(a > 1).show('a'):
               import pdb; pdb.set_trace()
        """
        item, att_names = self._get_item_and_att_names(*values, **data)
        if not item:
            self.reset()
            return False

        self._strict_checker(att_names, item=item)

        # set the string value
        self._str = self.stringify_item(item, att_names)
        self.stream.write(self._str + '\n')

        passes_all = self._passes_all
        self.reset()
        return passes_all

    def stringify_item(self, item, att_names):
        if not att_names:
            raise ValueError(
                'Error in Behold.  Could not determine attributes/'
                'variables to show.')

        out = []
        for ind, key in enumerate(att_names):
            out.append(key + ': ')
            has_more = ind < len(att_names) - 1
            has_more = has_more or self.tag or self._viewed_context_keys
            if has_more:
                ending = ', '
            else:
                ending = ''
            val = self.extract(item, key)
            out.append(val + ending)

        self._strict_checker(self._viewed_context_keys)

        for ind, key in enumerate(self._viewed_context_keys):
            has_more = ind < len(self._viewed_context_keys) - 1
            has_more = has_more or self.tag
            if has_more:
                ending = ', '
            else:
                ending = ''
            out.append(
                '{}: {}{}'.format(
                    key,
                    self.__class__._context.get(key, ''),
                    ending
                )
            )

        if self.tag:
            out.append(self.tag)
        return ''.join(out)

    def extract(self, item, name):
        """
        You should never need to call this method when you are debugging.  It is
        an internal method that is nevertheless exposed to allow you to
        implement custom extraction logic for variables/attributes.

        This method is responsible for turning attributes into string for
        printing.  The default implementation is shown below, but for custom
        situations, you inherit from `Behold` and override this method to obtain
        custom behavior you might find useful.  A common strategy is to load up
        class-level state to help you make the necessary transformation.

        :type item: Object
        :param item: The object from which to print attributes.  If you didn't
                     explicitly provide an object to the `.show()` method,
                     then `Behold` will attach the local variables you
                     specified as attributes to an :class:`.Item` object.

        :type name: str
        :param name: The attribute name to extract from item

        Here is the default implementation.

        .. code-block:: python

           def extract(self, item, name):
               val = ''
               if hasattr(item, name):
                   val = getattr(item, name)
               return str(val)

        Here is an example of transforming Django model ids to names.

        .. code-block:: python

           class CustomBehold(Behold):
               def load_state(self):
                   # Put logic here to load your lookup dict.
                   self.lookup = your_lookup_code()

               def extract(self, item, name):
                   if hasattr(item, name):
                       val = getattr(item, name)
                       if isinstance(item, Model) and name == 'client_id':
                           return self.lookup.get(val, '')
                       else:
                           return super(CustomBehold, self).extract(name, item)
                    else:
                        return ''
        """
        val = ''
        if hasattr(item, name):
            val = getattr(item, name)
        return str(val)

    def __str__(self):
        return self._str

    def __repr__(self):
        return self.__str__()


class in_context(object):
    """
    :type context_vars: key-work arguments
    :param context_vars: Key-word arguments specifying the context variables
                         you would like to set.

    You can define arbitrary context in which to perform your debugging.  A
    common use case for this is when you have a piece of code that is called
    from many different places in your code base, but you are only interested in
    what happens when it's called from a particular location.  You can just wrap
    that location in a context and only debug when in that context.  Here is an
    example.

    .. code-block:: python

       from behold import BB  # this is an alias for Behold
       from behold import in_context

       # A function that can get called from anywhere
       def my_function():
           for nn in range(5):
               x, y = nn, 2 * nn

               # this will only print for testing
               BB().when_context(what='testing').show('x')

               # this will only print for prodution
               BB().when_context(what='production').show('y')

       # Set a a testing context using a decorator
       @in_context(what='testing')
       def test_x():
          my_function()

       # Now run the function under a test
       test_x()

       # Set a production context using a context-manager and call the function
       with in_context(what='production'):
          my_function()
    """
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
    """
    :type context_vars: key-work arguments
    :param context_vars: Key-word arguments specifying the context variables
                         you would like to set.

    This function lets you manually set context variables without using
    decorators or with statements.

    .. code-block:: python

       from behold import Behold
       from behold import set_context, unset_context


       # manually set a context
       set_context(what='my_context')

       # print some variables in that context
       Behold().when_context(what='my_context').show(x='hello')

       # manually unset the context
       unset_context('what')
    """
    Behold.set_context(**kwargs)


def unset_context(*keys):
    """
    :type keys: string arguments
    :param keys: Arguments specifying the names of context variables you
                 would like to unset.

    See the ``set_context()`` method for an example of how to use this.
    """
    Behold.unset_context(*keys)


def get_stash(name):
    """
    :type name: str
    :param name: The name of the stash you want to retrieve

    :rtype: list
    :return: A list of dictionaries holding stashed records for each time the
             ``behold.stash()`` method was called.

    For examples, see documentation for ``Behold.stash()`` as well as the stash
    `examples on Github <https://github.com/robdmc/behold#stashing-results>`_.
    """
    return Behold.get_stash(name)


def clear_stash(*names):
    """
    :type names: string arguments
    :param name: The names of stashes you would like to clear.

    This method removes all global data associated with a particular stash name.
    """
    Behold.clear_stash(*names)
