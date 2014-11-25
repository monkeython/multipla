.. image:: https://travis-ci.org/monkeython/pluggable_package.svg?branch=master
    :target: https://travis-ci.org/monkeython/pluggable_package
    :alt: Build status

.. image:: https://coveralls.io/repos/monkeython/pluggable_package/badge.png?branch=master
    :target: https://coveralls.io/r/monkeython/pluggable_package?branch=master
    :alt: Test coverage

.. image:: https://readthedocs.org/projects/pluggable-package/badge/?version=latest&style=default
    :target: http://pluggable_package.readthedocs.org/en/latest/
    :alt: Documentation status

.. image:: https://pypip.in/download/pluggable_package/badge.svg?period=month
    :target: https://pypi.python.org/pypi/pluggable_package/
    :alt: Downloads

.. image:: https://pypip.in/version/pluggable_package/badge.svg?text=pypi
    :target: https://pypi.python.org/pypi/pluggable_package/
    :alt: Latest Version

.. image:: https://pypip.in/status/pluggable_package/badge.svg
    :target: https://pypi.python.org/pypi/pluggable_package/
    :alt: Development Status

.. image:: https://pypip.in/py_versions/pluggable_package/badge.svg
    :target: https://pypi.python.org/pypi/pluggable_package/
    :alt: Supported Python versions

.. image:: https://pypip.in/egg/pluggable_package/badge.svg
    :target: https://pypi.python.org/pypi/pluggable_package/
    :alt: Egg Status

.. image:: https://pypip.in/wheel/pluggable_package/badge.svg
    :target: https://pypi.python.org/pypi/pluggable_package/
    :alt: Wheel Status

.. .. image:: https://pypip.in/license/pluggable_package/badge.svg
..     :target: https://pypi.python.org/pypi/pluggable_package/
..     :alt: License
.. 
.. .. image:: https://pypip.in/implementation/pluggable_package/badge.svg
..     :target: https://pypi.python.org/pypi/pluggable_package/
..     :alt: Supported Python implementations

The purpose of this module is to setup a package/sub-package for a dead simple
plugin system. Is there a way to quickly setup your package for plugins?  Is it
also easy to use for you and third party developers? I don't know, but I know
what I like: package and modules as namespaces or containers. So a
``pluggable_package`` is namespace package which also is an entry point for
plugins.

I wanted something that let me write code like this:

.. code-block:: python

   import pluggable_package
   content_types = pluggable_package.import_package('cereal.content_types')

   def to_json(object):
       content_type = content_types.get('application/json')
       return content_type.format(ojbect)

   def to_tar(objects):
       return content_types.get('application_x_tar').format(objects)

   def to_user_supplied_type(object, content_type):
       return content_types.get(content_type).format(object)

or:

.. code-block:: python

   from loremipsum import generator
   import pluggable_package

   samples = pluggable_package.import_package('loremipsum.samples')
   vaporware = generator.Generator(samples.get('vaporware'))

You can read more on `Pythonhosted`_ or `Read the Docs`_. Since this package
has en extensive docstring documentation as well as code comments, you can
read more browsing the source code or in the python interactive shell.

.. _`Pythonhosted`: http://pythonhosted.org/pluggable_package
.. _`Read the Docs`: http://pluggable-package.readthedocs.org
