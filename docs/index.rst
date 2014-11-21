************************
A micro plugin framework
************************

:version: |version|
:author: |author|
:contact: |contact|
:copyright: |copyright|

.. include:: ../LICENSE.rst

Overview
========

.. include:: ../README.rst

.. include:: ../CHANGES.rst

Usage
=====

Now, let's say you have a ``awesome_framework.plugin_container`` module and you
want it to accept plugins that behave exactly like your ``awesome`` plugin. Of
course, each plugin would do the same awesome task, but in their own way. Let's
have a look at ``plugin_container.py``:

.. code-block:: python

   """Awesome pluggable module."""
   
   __all__ = ['awesome']
   
   # It's already Awesome ... ;)
   def awesome():
       return object()

And that is ``awesome_framework/__init__.py``:

.. code-block:: python

   """
   This awesome package will let you do awesome things, by just plugging your
   awesome module in.
   """

   __all__ = ['plugin_container']

   import pluggable_package

   import plugin_container

   pluggable_package.setup(plugin_container, 'awesome')

Let's give it a try:

.. code-block:: python

   >>> from awesome_framework import plugin_container
   >>>
   >>> plugin_container.get('awesome') is plugin_container.DEFAULT
   True
   >>>
   >>> plugin_container.registered()
   {'awesome': <function awesome at ...>}

That's not mutch, but at least you can write your plugin ready application in
a simple way, and with a simple API. Let's say that now **I** want to jump in
your package and provide my ``amazing`` plugin, so I write
``amazing_module.py``:

.. code-block:: python

   """My amazing version of the awesome plugin."""

   __all__ = ['amazing_plugin']

   def amazing_plugin():
       pass

   def get_amazing_plugin():
       return {'amazing': amazing_plugin}

and then, in my ``setup.py``:

.. code-block:: python

   import setuptools
  
   setuptools.setup(
       ...
       entry_points="""
           [awesome_framework.plugin_container]
           amazing_plugin=amazing_module:get_amazing_plugin
       """)

API
===

.. automodule:: pluggable_package
   :members: 

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
