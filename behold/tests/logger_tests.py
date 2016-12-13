import sys
from unittest import TestCase
try:
    from cStringIO import StringIO
except:
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
    def test_show_item_with_args_no_kwargs(self):
        item = Item(a=1, b=2)
        with print_catcher() as catcher:
            Behold().show(item, 'a', 'b')
        self.assertTrue('a: 1, b: 2' in catcher.txt)

    def test_no_auto(self):
        item = Item(a=1, b=2)
        with print_catcher() as catcher:
            behold = Behold(auto=False)
            passed = behold.show(item, 'a', 'b')

        out = str(behold)
        self.assertTrue(passed)
        self.assertTrue('a: 1, b: 2' in out)
        self.assertEqual('', catcher.txt)

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
        self.assertFalse('B: 2, A: 1' in catcher.txt)
        self.assertTrue('B: 2' in catcher.txt)

    def test_show_obj_and_data(self):
        item = Item(a=1, b=2)
        with self.assertRaises(ValueError):
            Behold().show(item, 'a', 'b', item=item)

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

    def test_arg_exclude(self):
        a, b = 1, 2
        with print_catcher() as catcher:
            passed = Behold().excluding(a == 3).show('a', 'b')
        self.assertEqual(catcher.txt, 'a: 1, b: 2\n')
        self.assertTrue(passed)

        with print_catcher() as catcher:
            passed = Behold().excluding(a == 1, b == 7).show('a', 'b')
        self.assertEqual(catcher.txt, '')
        self.assertFalse(passed)

    def test_context_exclude(self):
        a, b = 1, 2  # flake8: noqa
        set_context(z=0, s=0)
        set_context(z=6, s=2)
        with print_catcher() as catcher:
            passed = Behold().excluding_context(z=3, s=2).show('a', 'b')
        self.assertEqual(catcher.txt, 'a: 1, b: 2\n')
        self.assertTrue(passed)

        with print_catcher() as catcher:
            passed = Behold().excluding_context(z=6, s=2).show('a', 'b')
        self.assertEqual(catcher.txt, '')
        self.assertFalse(passed)

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
