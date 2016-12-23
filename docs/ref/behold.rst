.. _ref-behold:


API Documentation
==================
This is the API documentation for the `behold` package.  To see examples
of how to use `behold`, visit the
`Github project page <https://github.com/robdmc/behold>`_.


Managing Context
----------------
.. autoclass:: behold.logger.in_context
.. autofunction:: behold.logger.set_context
.. autofunction:: behold.logger.unset_context
.. autofunction:: behold.logger.get_stash
.. autofunction:: behold.logger.clear_stash

Printing / Debugging
--------------------
.. autoclass:: behold.logger.Behold

.. automethod:: behold.logger.Behold.show
.. automethod:: behold.logger.Behold.when
.. automethod:: behold.logger.Behold.when_values
.. automethod:: behold.logger.Behold.when_context
.. automethod:: behold.logger.Behold.view_context
.. automethod:: behold.logger.Behold.stash
.. automethod:: behold.logger.Behold.extract


Items
-----
.. autoclass:: behold.logger.Item
    :members:

