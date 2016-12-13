from collections import defaultdict
import copy
import functools
import inspect
import operator
import sys


class _Sentinal(object):
    pass


class Item(object):
    def __init__(_item_self_, **kwargs):
        # I'm using unconventional "_item_self_" name here to avoid
        # conflicts when kwargs actually contain a "self" arg.
        for k, v in kwargs.items():
            setattr(_item_self_, k, v)


class Behold(object):
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

    def __init__(self, tag=None, auto=True, stream=None):
        self.tag = tag
        self.auto = auto
        if stream is None:
            self.stream = sys.stdout
        else:
            self.stream = stream

        # these filters apply to context variables
        self.passes = True
        self.context_filters = []

        # a list of fields that will be printed if filters pass
        self.print_keys = []

        # holds a string rep for this object
        self._str = ''

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

    def reset(self):
        """
        resets filtering state
        """
        self.passes = False
        self.context_filters = []

    def when(self, *bools):
        self.passes = self.passes and all(bools)
        return self

    def excluding(self, *bools):
        self.passes = self.passes and not any(bools)
        return self

    def when_context(self, **criteria):
        self._add_context_filters(False, **criteria)
        return self

    def excluding_context(self, **criteria):
        self._add_context_filters(True, **criteria)
        return self

    def _add_context_filters(self, exclude, **criteria):
        for key, val in criteria.items():
            op, field = self._key_to_field_op(key)
            self.context_filters.append((op, field, val, exclude))

    def _passes_context_filter(self):
        if not self.context_filters:
            return True

        passes = False
        for (op, field, filter_val, exclude) in self.context_filters:
            context_val = self.__class__._context.get(field, _Sentinal())
            if not isinstance(context_val, _Sentinal):
                passes = exclude ^ op(context_val, filter_val)

        return passes

    def passes_all(self):
        return self.passes and self._passes_context_filter()

    def _separate_names_objects(self, values):
        att_names = []
        objs = []
        for val in values:
            if isinstance(val, str):
                att_names.append(val)
            else:
                objs.append(val)
        return att_names, objs

    def _validate_objs_data(self, objs, data):
        # at most one object is allowed
        if len(objs) > 1:
            raise ValueError(
                'Non key-word arguments to Behold() can only have '
                'one non-string value.'
            )

        # make sure kwargs and data not simultaneously specified
        elif data and len(objs) == 1:
            raise ValueError(
                'Error in Behold().  You specified both keyword '
                'arguments and a non-string argument. You can\'t do that.'
            )

    def _get_item_and_att_names(self, *values, **data):
        if not self.passes_all():
            return None, None

        att_names, objs = self._separate_names_objects(values)

        self._validate_objs_data(objs, data)

        # handle case of no kwargs but non string in args
        if not data and len(objs) == 1:
            item = objs[0]
            if not att_names:
                if not hasattr(item, '__dict__'):
                    raise ValueError(
                        'Error in Behold() The object you passed has '
                        'no __dict__ attribute'
                    )
                att_names = sorted(item.__dict__.keys())

        # handle case of kwargs only
        elif not objs and data:
            item = Item(**data)
            if not att_names:
                att_names = sorted(data.keys())

        # if no object specified, use locals()
        else:
            try:
                att_dict = {}
                calling_frame = inspect.currentframe().f_back.f_back

                # update with local variables of the calling frame
                att_dict.update(calling_frame.f_locals)

                # populate att_names if it wasn't specified
                if not att_names:
                    att_names = sorted(att_dict.keys())

                # make sure att_dict only has requested fields
                att_dict = {k: att_dict.get(k, None) for k in att_names}

                # make an item out of those locals
                item = Item(**att_dict)
            finally:
                # delete the calling frame to avoid reference cycles
                del calling_frame

        return item, att_names

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
        if not self.tag:
            raise ValueError(
                'You must instantiate Behold with a tag name if you want to '
                'use stashing'
            )
        passes_all = self.passes_all()
        if not passes_all:
            return False

        item, att_names = self._get_item_and_att_names(*values, **data)
        if not item:
            self.reset()
            return None
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

    def show(self, *values, **data):
        """
        If data is provided, then that will be used as source.  In this case
        if values are also provided, only those values are shown, otherwise all
        in key-sorted order.

        If data is not provided, *values are searched for non-string inputs.
        Any non-string input will be treated as the data source and only
        attributes listed in the string values will be extracted.  In this
        case if values are all strings with no non-string, then
        global() + locals() will be used as the data source.
        """
        item, att_names = self._get_item_and_att_names(*values, **data)
        if not item:
            self.reset()
            return False

        # set the string value
        self._str = self.stringify_item(item, att_names)
        if self.auto:
            self.stream.write(self._str + '\n')

        passes_all = self.passes_all()
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
            if ind < len(att_names) - 1 or self.tag:
                ending = ', '
            else:
                ending = ''

            val = self.extract(item, key)
            out.append(val + ending)
        if self.tag:
            out.append(self.tag)
        return ''.join(out)

    def extract(self, item, name):
        """
        Override this to perform any custom field extraction
        """
        val = ''
        if hasattr(item, name):
            val = getattr(item, name)
        return str(val)

    def __str__(self):
        return self._str

    def __repr__(self):
        return self.__str__()

    def __bool__(self):
        return self.passes_all()


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


def unset_context(*keys):
    Behold.unset_context(*keys)


def get_stash(name):
    return Behold.get_stash(name)


def clear_stash(*names):
    Behold.clear_stash(*names)
