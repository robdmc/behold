Behold:  A debugging tool for large Python projects
===
[![Build Status](https://travis-ci.org/robdmc/behold.svg?branch=develop)](https://travis-ci.org/robdmc/behold)
[![Coverage Status](https://coveralls.io/repos/github/robdmc/behold/badge.svg?branch=develop)](https://coveralls.io/github/robdmc/behold?branch=develop)

Behold is a package that makes it easier to debug large Python projects. It
enables you to perform [contextual debugging](#contextual-debugging-explained)
over your entire code base.  This means that you can use the state inside one
module to control either printing or step-debugging in a completely different
module.  Given the stateful nature of many large, multi-file applications (I'm
looking at you, Django), this capability provides valuable control over your
debugging work flow.

Behold is written in pure Python with no dependencies.  It is compatible with
both Python2 and Python3.

This page shows several examples to get you started. The
<a href="http://behold.readthedocs.io/en/latest/ref/behold.html">API documentation can be found here.</a>


Installation
---
```bash
pip install behold
```

Table of Contents
---

* [API Documentation](http://behold.readthedocs.io/en/latest/ref/behold.html)
* [Simple print-style debugging](#simple-print-style-debugging)
* [Conditional printing](#conditional-printing)
* [Tagged printing](#tagged-printing)
* [Contextual debugging](#contextual-debugging-explained)
* [Printing object attributes](#printing-object-attributes)
* [Printing global variables and nested attributes](#printing-global-variables-and-nested-attributes)
* [Stashing results](#stashing-results)
* [Custom attribute extraction](#custom-attribute-extraction)


Simple Print-Style Debugging
---
Behold provides a uniform look to your print-style debugging statements.
```python
from behold import Behold

letters  = ['a', 'b', 'c', 'd', 'A', 'B', 'C', 'D']

for index, letter in enumerate(letters):
    # The following line is equivalent to
    # print('index: {}, letter: {}'.format(index, letter))
    Behold().show('index', 'letter')
```
Output:
```
index: 0, letter: a
index: 1, letter: b
index: 2, letter: c
index: 3, letter: d
index: 4, letter: A
index: 5, letter: B
index: 6, letter: C
index: 7, letter: D
```

Conditional Printing
---
You can filter your debugging statements based on scope variables.
```python
from behold import Behold

letters  = ['a', 'b', 'c', 'd', 'A', 'B', 'C', 'D']

for index, letter in enumerate(letters):
    # The following line is equivalent to
    # if letter.upper() == letter and index % 2 == 0:
    #     print('index: {}'.format(index))
    Behold().when(letter.upper() == letter and index % 2 == 0).show('index')

    # If you don't like typing, the Behold class is aliased to B
    # from behold import B  # this also works
```
Output:
```
index: 4
index: 6
```

Tagged Printing
---
Each instance of a behold object can be tagged to produce distinguishable
output.  This makes it easy to grep for specific output you want to see.
```python
from behold import Behold

letters  = ['a', 'b', 'c', 'd', 'A', 'B', 'C', 'D']

for index, letter in enumerate(letters):
    # The following two lines of code are equivalent to
    # if letter.upper() == letter and index % 2 == 0:
    #     print('index: {}, letter:, {}, even_uppercase'.format(index, letter))
    # if letter.upper() != letter and index % 2 != 0:
    #     print('index: {}, letter: {} odd_lowercase'.format(index, letter))
    Behold(tag='even_uppercase').when(letter.upper() == letter and index % 2 == 0).show('index', 'letter')
    Behold(tag='odd_lowercase').when(letter.lower() == letter and index % 2 != 0).show('index', 'letter')

```
Output:
```
index: 1, letter: b, odd_lowercase
index: 3, letter: d, odd_lowercase
index: 4, letter: A, even_uppercase
index: 6, letter: C, even_uppercase
```

Contextual Debugging Explained
---
Let's say you have a complicated code base consisting of many files spread over
many directories. In the course of chasing down bugs, you may want to print out
what is going on inside a particular function. But you only want the printing
to happen when that function is called from some other function defined in a
completely different file. Situations like this frequently arise in Django web
projects where the code can be spread across multiple apps. This is the use
case where Behold really shines. Here is a simple example.

Say you want to debug a reusable function somewhere in one of your modules.
```python
from behold import Behold

# Some function that is used everywhere in your code base
def my_function():
    x = 'hello'  # your complicated logic goes here

    # This will print the value of x, but only when in 'testing' context
    Behold().when_context(what='testing').show('x')

    # This will drop into a step debugger only when in 'debugging' context
    if Behold().when_context(what='debugging').is_true():
        import pdb; pdb.set_trace()
```

Now, from a completely different module somewhere else in your project, you can
control how your function gets debugged.
```python
from behold import in_context

# Decorate your testing function to execute in a 'testing' context
@in_context(what='testing')
def test_x():
    my_function()
test_x()  # This will print 'x: hello' to your console

# Use a context manager to set a debugging context
with in_context(what='debugging'):
    my_function()  # This will drop you into the pdb debugger.

```


Printing Object Attributes
---
Up to this point, we have only called the `.show()` method with string arguments
holding names of local variables.  What if we wanted to show attributes of some
object in our code?  The example below uses an instance of the
<a href="http://behold.readthedocs.io/en/latest/ref/behold.html#items">
Item class
</a>

```python
from behold import Behold, Item

# Define an item with three attributes.
item = Item(a=1, b=2, c=3)

# The show() method will accept up to one non-string argument.  If it detects that
# that a non-string argument has been passed, it will call getattr() on the
# non-string variable to display the str representation of the attributes listed
# in the string arguments.
Behold(tag='with_args').show(item, 'a', 'b')

# Calling show with an object and no string arguments defaults to printing all
# attributes in the object's __dict__.
Behold(tag='no_args').show(item)
```
Output:
```
a: 1, b: 2, with_args
a: 1, b: 2, c: 3, no_args
```

Printing Global Variables and Nested Attributes
---
When providing string arguments to the `.show()` method, the default behavior is
to examine the local variables for names matching the strings.  Global variables
can not be accessed in this way.  Furthermore, if you have classes with nested
attributes, those will also not be accessible with simple string arguments.
This example illustrates how to use `.show()` to access these types of
variables.

```python
from __future__ import print_function
from behold import Behold, Item

# define a global variable
g = 'global_content'

# Now set up a nested function to create a new scope
def example_func():
    employee = Item(name='Toby')
    boss = Item(employee=employee, name='Michael')

    print('# Can\'t see global variable')
    Behold().show('boss', 'employee', 'g')

    print('\n# I can see the the boss\'s name, but not employee name')
    Behold('no_employee_name').show(boss)

    print('\n# Here is how to show global variables')
    Behold().show(global_g=g, boss=boss)

    # Or if you don't like the ordering the dict keys give you,
    # you can enforce it with the order of some string arguments
    print('\n# You can force variable ordering by supplying string arguments')
    Behold().show('global_g', 'boss', global_g=g, boss=boss)

    print('\n# And a similar strategy for nested attributes')
    Behold().show(employee_name=boss.employee.name)

example_func()
```
Output:
```bash
# Can't see global variable
boss: Item('employee', 'name'), employee: Item('name'), g: None

# I can see the the boss's name, but not employee name
employee: Item('name'), name: Michael, no_employee_name

# Here is how to show global variables
boss: Item('employee', 'name'), global_g: global_content

# You can force variable ordering by supplying string arguments
global_g: global_content, boss: Item('employee', 'name')

# And a similar strategy for nested attributes
employee_name: Toby
```

Stashing Results
---
Behold provides a global stash space where you can store observed values for
later use in a top-level summary.  The stash space is global, so you need to
carefully manage it in order not to confuse yourself.  Here is an example of
using the stash feature to print summary info. The list of dicts returned by the
`.get_stash()` function was specifically designed to be passed directly to a <a
href="http://pandas.pydata.org/">Pandas</a> Dataframe constructor to help
simplify further analysis. 

```python
from __future__ import print_function
from pprint import pprint
from behold import Behold, in_context, get_stash, clear_stash

def my_function():
    out = []
    for nn in range(5):
        x, y, z = nn, 2 * nn, 3 * nn
        out.append((x, y, z))

        # You must define tags if you want to stash variables.  The tag
        # names become the keys in the global stash space

        # this will only populate when testing x
        Behold(tag='test_x').when_context(what='test_x').stash('y', 'z')

        # this will only populate when testing y
        Behold(tag='test_y').when_context(what='test_y').stash('x', 'z')

        # this will only populate when testing z
        Behold(tag='test_z').when_context(what='test_z').stash('x', 'y')
    return out


@in_context(what='test_x')
def test_x():
    assert(sum([t[0] for t in my_function()]) == 10)

@in_context(what='test_y')
def test_y():
    assert(sum([t[1] for t in my_function()]) == 20)

@in_context(what='test_z')
def test_z():
    assert(sum([t[2] for t in my_function()]) == 30)

test_x()
test_y()
test_z()


print('\n# contents of test_x stash.  Notice only y and z as expected')
pprint(get_stash('test_x'))

print('\n# contents of test_y stash.  Notice only x and z as expected')
pprint(get_stash('test_y'))

print('\n# contents of test_z stash.  Notice only x and y as expected')
pprint(get_stash('test_z'))

# With no arguments, clear_stash will delete all stashes.  You can
# select a specific set of stashes to clear by supplying their names.
clear_stash()
```
Output:
```

# contents of test_x stash.  Notice only y and z as expected
[{'y': 0, 'z': 0},
{'y': 2, 'z': 3},
{'y': 4, 'z': 6},
{'y': 6, 'z': 9},
{'y': 8, 'z': 12}]

# contents of test_y stash.  Notice only x and z as expected
[{'x': 0, 'z': 0},
{'x': 1, 'z': 3},
{'x': 2, 'z': 6},
{'x': 3, 'z': 9},
{'x': 4, 'z': 12}]

# contents of test_z stash.  Notice only x and y as expected
[{'x': 0, 'y': 0},
{'x': 1, 'y': 2},
{'x': 2, 'y': 4},
{'x': 3, 'y': 6},
{'x': 4, 'y': 8}]
```

Custom Attribute Extraction
---
When working with database applications, you frequently encounter objects that
are referenced by id numbers.  These ids serve as record keys from which you can
extract human-readable information.  When you are debugging, it can often get
confusing if your screen dump involves just a bunch of id numbers.  What you
would actually like to see is some meaningful name corresponding to that id.  By
simply overriding one method of the Behold class, this behavior is quite easy to
implement.  This example shows how.
```python
from __future__ import print_function
from behold import Behold, Item


# Subclass Behold to enable custom attribute extraction
class CustomBehold(Behold):
    @classmethod
    def load_state(cls):
        # Notice this is a class method so that the loaded state will be
        # available to all instances of CustomBehold.  A common use case would
        # be to load state like this once from a database and then be able to
        # reuse it at will without invoking continual database activity.  In
        # this example, imagine the numbers are database ids and you have 
        # constructed a mapping from id to some human-readable description.
        cls.name_lookup = {
            1: 'John',
            2: 'Paul',
            3: 'George',
            4: 'Ringo'
        }
        cls.instrument_lookup = {
            1: 'Rhythm Guitar',
            2: 'Bass Guitar',
            3: 'Lead Guitar',
            4: 'Drums'
        }

    def extract(self, item, name):
        """
        I am overriding the extract() method of the behold class.  This method
        is responsible for taking an object and turning it into a string.  The
        default behavior is to simply call str() on the object.
        """
        # if the lookup state hasn't been loaded, do so now.
        if not hasattr(self.__class__, 'name_lookup'):
            self.__class__.load_state()

        # extract the value from the behold item
        val = getattr(item, name)

        # If this is a Item object, enable name translation
        if isinstance(item, Item) and name == 'name':
            return self.__class__.name_lookup.get(val, None)

        # If this is a Item object, enable instrument translation
        elif isinstance(item, Item) and name == 'instrument':
            return self.__class__.instrument_lookup.get(val, None)

        # otherwise, just call the default extractor
        else:
            return super(CustomBehold, self).extract(item, name)


# define a list of items where names and instruments are given by id numbers
items = [Item(name=nn, instrument=nn) for nn in range(1, 5)]

print('\n# Show items using standard Behold class')
for item in items:
    Behold().show(item)


print('\n# Show items using CustomBehold class with specialized extractor')
for item in items:
    CustomBehold().show(item, 'name', 'instrument')
```
Output:
```bash
# Show items using standard Behold class
instrument: 1, name: 1
instrument: 2, name: 2
instrument: 3, name: 3
instrument: 4, name: 4

# Show items using CustomBehold class with specialized extractor
name: John, instrument: Rhythm Guitar
name: Paul, instrument: Bass Guitar
name: George, instrument: Lead Guitar
name: Ringo, instrument: Drums
```

___
Projects by [robdmc](https://www.linkedin.com/in/robdecarvalho).
* [Pandashells](https://github.com/robdmc/pandashells) Pandas at the bash command line
* [Consecution](https://github.com/robdmc/consecution) Pipeline abstraction for Python
* [Behold](https://github.com/robdmc/behold) Helping debug large Python projects
* [Crontabs](https://github.com/robdmc/crontabs) Simple scheduling library for Python scripts
* [Switchenv](https://github.com/robdmc/switchenv) Manager for bash environments



