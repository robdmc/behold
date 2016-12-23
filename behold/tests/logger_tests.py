import sys
from unittest import TestCase

try:  # pragma: no cover
    from cStringIO import StringIO
except:  # pragma: no cover
    from io import StringIO

from ..logger import (
    Behold,
    Item,
    in_context,
    set_context,
    unset_context,
    get_stash,
    clear_stash
)

from .testing_helpers import print_catcher

# a global variable to test global inclusion
g = 7


class BaseTestCase(TestCase):
    def setUp(self):
        Behold._context = {}
        clear_stash()


def module_func():
    m, n = 1, 2  # flake8: noqa
    Behold().show('m', 'n', 'g')


class BeholdCustom(Behold):
    """
    """
    def __init__(self, *args, **kwargs):
        super(BeholdCustom, self).__init__(*args, **kwargs)
        self.lookup = {
            1: 'manny',
            2: 'moe',
            3: 'jack',
        }

    def extract(self, item, name):
        """
        I am overriding the extract() method of the behold class.  This method
        is responsible for taking an object and turning it into a string.  The
        default behavior is to simply call str() on the object.
        """
        # extract the value from the behold item
        val = getattr(item, name)

        # If this is a MyItem object, enable name translation
        if isinstance(item, Item) and name == 'name':
            return self.lookup.get(val, None)
        # otherwise, just call the default extractor
        else:
            return super(BeholdCustom, self).extract(item, name)


class ItemTests(TestCase):
    def test_get_item(self):
        item = Item(a=1)
        self.assertEqual(item['a'], 1)

    def test_str(self):
        item1 = Item(a=1)
        item2 = Item(a=1, b='bbb')
        self.assertEqual(repr(item1), 'Item(\'a\')')
        self.assertEqual(repr(item2), 'Item(\'a\', \'b\')')


class TestBeholdRepr(BaseTestCase):
    def test_repr(self):
        x = 1
        with print_catcher() as catchter:
            behold = Behold()
            behold.show('x')
        self.assertEqual(repr(behold), 'x: 1')

class IsTrueTests(BaseTestCase):
    def test_when_no_item(self):
        self.assertTrue(Behold().when(True).is_true())
        self.assertFalse(Behold().when(False).is_true())

    def test_when_context_no_item(self):
        with in_context(what='yes'):
            self.assertTrue(Behold().when_context(what='yes').is_true())
        self.assertFalse(Behold().when_context(what='yes').is_true())

    def test_when_values_no_item(self):
        xx = 'xx'
        self.assertTrue(Behold().when_values(xx='xx').is_true())
        self.assertFalse(Behold().when_values(xx='yy').is_true())

    def test_when_values_item(self):
        item = Item(xx='xx')
        self.assertTrue(Behold().when_values(xx='xx').is_true(item))
        self.assertFalse(Behold().when_values(xx='yy').is_true(item))

class ViewContextTests(BaseTestCase):
    def test_good_view(self):
        xx = 1
        with print_catcher() as catcher:
            with in_context(what='this', where='here'):
                Behold().view_context('what', 'where').show('xx')
        self.assertEqual(catcher.txt, 'xx: 1, what: this, where: here\n')

    def test_missing_view(self):
        xx = 1
        with print_catcher() as catcher:
            with in_context(where='here'):
                behold = Behold()
                behold.view_context('what', 'where')
                behold.view_context('what', 'where')
                behold.show('xx')
        self.assertEqual(
            catcher.txt, 'xx: 1, what: , where: here, what: , where: here\n')

    def test_strict_missing_view(self):
        with self.assertRaises(ValueError):
            with in_context(where='here', when='now'):
                Behold(strict=True).view_context('what', 'where').show('xx')

    def test_strict_filter_on_missing_view(self):
        with in_context(where='here', when='now'):
            Behold(strict=True).when_context(
                what='this').view_context('where').is_true() #.show('xx')
            #Behold(strict=True).view_context('where').show('xx')

class ValueFilterTests(BaseTestCase):
    def test_values_in(self):
        items = [
            Item(name=nn, value=nn) for nn in range(1, 4)
        ]
        with print_catcher() as catcher:
            for item in items:
                BeholdCustom().when_values(
                    name__in=['manny', 'moe'], value=2
                ).show(item, 'name', 'value')

        self.assertTrue('name: moe, value: 2' in catcher.txt)

    def test_lt(self):

        items = [
            Item(name=nn, value=nn) for nn in range(1, 4)
        ]

        with print_catcher() as catcher:
            for item in items:
                BeholdCustom().when_values(value__lt=2).show(item)
        self.assertEqual(catcher.txt, 'name: manny, value: 1\n')

    def test_lte(self):

        items = [
            Item(name=nn, value=nn) for nn in range(1, 4)
        ]

        with print_catcher() as catcher:
            for item in items:
                BeholdCustom().when_values(value__lte=2).show(item)
        self.assertTrue('manny' in catcher.txt)
        self.assertTrue('moe' in catcher.txt)

    def test_gt(self):

        items = [
            Item(name=nn, value=nn) for nn in range(1, 4)
        ]

        with print_catcher() as catcher:
            for item in items:
                BeholdCustom().when_values(value__gt=2).show(item)
        self.assertEqual(catcher.txt, 'name: jack, value: 3\n')

    def test_gte(self):

        items = [
            Item(name=nn, value=nn) for nn in range(1, 4)
        ]

        with print_catcher() as catcher:
            for item in items:
                BeholdCustom().when_values(value__gte=2).show(item)
        self.assertTrue('moe' in catcher.txt)
        self.assertTrue('jack' in catcher.txt)


class StashTests(BaseTestCase):
    def test_full_stash(self):
        for nn in range(10):
            x = nn
            Behold(tag='mystash').when(nn>=2).stash('nn', 'y')
            Behold(tag='mystash2').when(nn>=2).stash('nn', 'y')
        stash_list = get_stash('mystash')
        expected_list = [{'nn': nn, 'y': None} for nn in range(2, 10)]
        self.assertEqual(stash_list, expected_list)
        clear_stash('mystash')
        with self.assertRaises(ValueError):
            get_stash('mystash')
        stash_list = get_stash('mystash2')
        self.assertEqual(stash_list, expected_list)
        clear_stash()
        with self.assertRaises(ValueError):
            get_stash('mystash2')

    def test_stash_no_tag(self):
        nn = 1
        with self.assertRaises(ValueError):
            Behold().stash('nn')

    def test_stash_bad_item(self):
        nn = 1
        Behold(tag='bad_stash').stash('xx')
        results =  get_stash('bad_stash')
        self.assertEqual(results, [{'xx': None}])

    def test_stash_bad_delete(self):
        nn = 1
        Behold(tag='bad_stash').stash('xx')
        with self.assertRaises(ValueError):
            clear_stash('bad_name')

    def test_stash_no_pass(self):
        item = Item(nn=1)
        #passed = Behold(tag='mytag').when(False).stash('xx')
        passed = Behold(tag='mytag').when_values(nn=3).stash(item, 'nn')
        self.assertEqual(passed, False)


class GetTests(BaseTestCase):
    def test_get_okay(self):
        a, b, c = 'aaa', 'bbb', 'ccc'
        result = Behold().get('a', 'b', 'd')
        self.assertEqual({'a': 'aaa', 'b': 'bbb', 'd': None}, result)

    def test_get_all(self):
        a, b, c = 'aaa', 'bbb', 'ccc'
        self.assertEqual(set(Behold().get()), {'self', 'a', 'b', 'c'})

    def test_get_item(self):
        item = Item(a='aaa', b='bbb', c='ccc')
        self.assertEqual(set(Behold().get(item)), {'a', 'b', 'c'})

    def test_get_failing(self):
        a, b, c = 'aaa', 'bbb', 'ccc'
        result = Behold().when(a=='zzz').get('a', 'b', 'd')
        self.assertEqual(None, result)

class UnfilteredTests(BaseTestCase):
    def test_strinfigy_no_names(self):
        item = Item()
        b = Behold()
        with self.assertRaises(ValueError):
            b.stringify_item(item, [])

    def test_show_item_with_args_no_kwargs(self):
        item = Item(a=1, b=2)
        with print_catcher() as catcher:
            Behold().show(item, 'a', 'b')
        self.assertTrue('a: 1, b: 2' in catcher.txt)

    def test_truthiness(self):
        item = Item(a=1, b=2)
        with print_catcher() as catcher:
            behold = Behold()
            with print_catcher() as catcher:
                passed = behold.show(item, 'a', 'b')

        out = str(behold)
        self.assertTrue(passed)
        self.assertTrue('a: 1, b: 2' in out)
        self.assertEqual('', catcher.txt)

    def test_unkown_local(self):
        c = 1
        self.assertFalse(Behold().when_values(a=1).show('a', 'c'))

    def test_show_locals_with_args_no_kwargs(self):
        a, b = 1, 2  # flake8: noqa

        def nested():
            x, y = 3, 4  # flake8: noqa
            Behold().show('a', 'b', 'x', 'y',)
        with print_catcher() as catcher:
            nested()

        self.assertTrue('a: None, b: None, x: 3, y: 4' in catcher.txt)

    def test_show_from_frame_module_func(self):
        with print_catcher() as catcher:
            module_func()
        self.assertTrue('m: 1, n: 2' in catcher.txt)

    def test_show_with_kwargs_no_args(self):
        a, b = 1, 2
        with print_catcher() as catcher:
            Behold().show(B=b, A=a)
        self.assertTrue('A: 1, B: 2' in catcher.txt)

    def test_show_with_kwargs_and_args(self):
        a, b = 1, 2

        with print_catcher() as catcher:
            Behold().show('B', 'A', B=b, A=a)
        self.assertTrue('B: 2, A: 1' in catcher.txt)

        with print_catcher() as catcher:
            Behold().show('B', B=b, A=a)
        self.assertTrue('B: 2, A: 1' in catcher.txt)

    def test_show_obj_and_data(self):
        item = Item(first='one', second='two', a=1, b=2)
        with print_catcher() as catcher:
            Behold().show(item, 'a', 'b', begin=item.first, end=item.second)
        self.assertEqual(catcher.txt, 'a: 1, b: 2, begin: one, end: two\n')

    def test_show_obj_and_data_bad_att(self):
        item = Item(a=1, b=2)
        with print_catcher() as catcher:
            Behold().show(item, 'a', 'b', 'c')
        self.assertTrue('a: 1, b: 2, c: ' in catcher.txt)

    def test_show_multiple_obj(self):
        item = Item(a=1, b=2)
        with self.assertRaises(ValueError):
            Behold().show(item, 'a', 'b', item)

    def test_show_only_args(self):
        x = ['hello']
        with self.assertRaises(ValueError):
            Behold().show(x)

    def test_show_with_stream(self):
        x, y = 1, 2  # flake8: noqa
        stream = StringIO()
        Behold(stream=stream).show('x')
        self.assertEqual('x: 1\n', stream.getvalue())

    def test_show_with_non_existing_attribute(self):
        x = 8  # flake8: noqa

        with print_catcher() as catcher:
            Behold().show('x', 'y')

        self.assertEqual(catcher.txt, 'x: 8, y: None\n')


class FilteredTests(BaseTestCase):
    def test_strict_context_filtering(self):
        with in_context(what='testing'):
            is_true = Behold(strict=True).when_context(
                what='testing').is_true()
            self.assertTrue(is_true)

        with in_context(what='testing'):
            is_false = Behold(strict=True).when_context(where='here').is_true()
            self.assertFalse(is_false)

        with self.assertRaises(ValueError):
            with in_context(what='testing'):
                x = 1
                Behold(strict=True).when_context(what='testing').view_context(
                    'where').show('x')

        with print_catcher() as catcher:
            with in_context(what='testing'):
                x = 1
                Behold(strict=True).when_context(what='testing').view_context(
                    'what').show('x')
        self.assertEqual(catcher.txt, 'x: 1, what: testing\n')

    def test_strict_value_filtering(self):
        item = Item(a=1, b=2)
        with print_catcher() as catcher:
            Behold(strict=True).show(item, 'a', 'b')
        self.assertEqual(catcher.txt, 'a: 1, b: 2\n')

        with self.assertRaises(ValueError):
            Behold(strict=True).show(item, 'c')

        with self.assertRaises(ValueError):
            Behold(strict=True).show('w', 'z')

    def test_arg_filtering(self):
        a, b = 1, 2  # flake8: noqa
        with print_catcher() as catcher:
            passed = Behold().when(a == 1).show('a', 'b')
        self.assertEqual(catcher.txt, 'a: 1, b: 2\n')
        self.assertTrue(passed)

        with print_catcher() as catcher:
            behold = Behold()
            passed = behold.when(a == 2).show('a', 'b')
        self.assertEqual(catcher.txt, '')
        self.assertFalse(passed)
        self.assertEqual(repr(behold), '')

    def test_context_filtering_equal(self):
        var = 'first'  # flake8: noqa
        with in_context(what=10):
            with print_catcher() as catcher:
                passed = Behold(tag='tag').when_context(what=10).show('var')

        self.assertTrue(passed)
        self.assertEqual('var: first, tag\n', catcher.txt)

        with in_context(what=10):
            with print_catcher() as catcher:
                passed = Behold(tag='tag').when_context(what=11).show('var')

        self.assertFalse(passed)
        self.assertEqual('', catcher.txt)

        with print_catcher() as catcher:
            passed = Behold(tag='tag').when_context(what=11).show('var')

        self.assertFalse(passed)
        self.assertEqual('', catcher.txt)

    def test_context_filtering_inequality(self):
        var = 'first'  # flake8: noqa
        with in_context(what=10):
            with print_catcher() as catcher:
                passed = Behold(tag='tag').when_context(what__gt=5).show('var')

        self.assertTrue(passed)
        self.assertEqual('var: first, tag\n', catcher.txt)

        with in_context(what=10):
            with print_catcher() as catcher:
                passed = Behold(tag='tag').when_context(what__lt=5).show('var')

        self.assertFalse(passed)
        self.assertEqual('', catcher.txt)

    def test_context_filtering_membership(self):
        var = 'first'  # flake8: noqa
        with in_context(what=10):
            with print_catcher() as catcher:
                passed = Behold(
                    tag='tag').when_context(what__in=[5, 10]).show('var')

        self.assertTrue(passed)
        self.assertEqual('var: first, tag\n', catcher.txt)

        with in_context(what=10):
            with print_catcher() as catcher:
                passed = Behold(
                    tag='tag').when_context(what__in=[7, 11]).show('var')

        self.assertFalse(passed)
        self.assertEqual('', catcher.txt)

    def test_context_decorator(self):
        @in_context(what='hello')
        def my_func():
            x = 1  # flake8: noqa
            Behold().when_context(what='hello').show('x')

        def my_out_of_context_func():
            x = 1  # flake8: noqa
            Behold().when_context(what='hello').show('x')

        with print_catcher() as catcher:
            my_func()
        self.assertEqual(catcher.txt, 'x: 1\n')

        with print_catcher() as catcher:
            my_out_of_context_func()
        self.assertEqual(catcher.txt, '')

    def test_explicit_context_setting(self):
        def printer():
            Behold().when_context(what='hello').show(x='yes')

        set_context(what='hello')
        with print_catcher() as catcher:
            printer()
        self.assertEqual(catcher.txt, 'x: yes\n')

        unset_context('what')
        with print_catcher() as catcher:
            printer()
        self.assertEqual(catcher.txt, '')

        set_context(what='not_hello')
        with print_catcher() as catcher:
            printer()
        self.assertEqual(catcher.txt, '')

    def test_unset_non_existing(self):
        def printer():
            Behold().when_context(what='hello').show(x='yes')

        set_context(what='hello')
        unset_context('what_else')

        with print_catcher() as catcher:
            printer()
        self.assertEqual(catcher.txt, 'x: yes\n')
