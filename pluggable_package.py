"""
By default, a package/module that has been setup for plugin
management, will have the following attributes and functions available:

* :py:attr:`package.DEFAULT`
* :py:func:`package.get`
* :py:func:`package.set_default`
* :py:func:`package.registered`

Unfortunately, it may happen to have these names already set with other
objects. In that case, the :py:func:`setup` lets you personalise your internal
APIs.

.. py:data:: package.DEFAULT

   The package default plugin. Initial value is :py:obj:`None`.

.. py:function:: package.get(name, default=_DEFAULT)

   :param str name:     The ``object`` name.
   :param default:      The value to return if lookup fails.
   :raises KeyError:    If lookup fails and no ``default`` value is provided.
   :returns:            The plugged in ``object``.

   Returns the desired plugged in ``object``.  On lookup, ``name`` value is
   translated: ``/`` and ``-`` characters are converted to ``_``. So, the
   following example should work as expected:

   >>> import content_type_plugins
   >>> plugin = content_type_plugins.get('application/octet-stream')

   Also, note that even if ``default`` param has a default value itself, if it
   is not passed on call, the function will raise :py:exc:`KeyError` on lookup
   failure:

   >>> try:
   ...     plugin = plugins.get('doesn_t_exists')
   ... except KeyError:
   ...     plugin = False
   ...
   >>> plugin
   False
   >>> plugins.get('doesn_t_exists', None) is None
   True

.. py:function:: package.set_default(name)

   :param str name:     The ``object`` name.

   Lookup plugin named ``name`` and set it in ``package.DEFAULT``.

.. py:function:: package.registered()

   :returns:            Registered plugins dictionary
   :rtype:              :py:class:`dict`

   Returns a ``name: value`` dictionary of the registered ``object``s.
   ``name`` is the actual registered name: see :py:func:`package.get` above.
"""

__author__ = "Luca De Vitis <luca@monkeython.com>"
__version__ = '0.0.1'
__copyright__ = "2014, %s " % __author__
__docformat__ = 'restructuredtext en'
__keywords__ = ['plugs', 'pluggable', 'package', 'module']
# 'Development Status :: 5 - Production/Stable',
__classifiers__ = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: Implementation :: CPython',
    'Programming Language :: Python :: Implementation :: Jython',
    'Programming Language :: Python :: Implementation :: PyPy',
    'Topic :: Software Development :: Libraries :: Python Modules']

__all__ = ['setup']

import collections
import functools
import importlib
import string

import pkg_resources

# Plugin register
_REGISTERED = collections.defaultdict(dict)

_SETUP = collections.defaultdict(dict)

_DEFAULT = object()


def _get(name, default=_DEFAULT, package=None):
    global _REGISTERED, _DEFAULT
    maketrans = getattr(string, 'maketrans', getattr(str, 'maketrans', None))
    name = name.translate(maketrans("/-", "__"))
    try:
        return _REGISTERED[package.__name__][name]
    except KeyError:
        if default is not _DEFAULT:
            return default
        raise


def _set_default(name, DEFAULT_name=None, package=None):
    setattr(package, DEFAULT_name, _get(name, package=package))


def _registered(package=None):
    global _REGISTERED
    return _REGISTERED[package.__name__].copy()


def setup(package, default=None, **kwargs):
    """Set the package/module up for plugins management.

    :param module package:  The package/module object to setup for plugins.
    :param str default:     The identifier of the default plugin to set into
                            ``DEFAULT`` data variable. See also
                            :py:func:`package.get`.
    :param kwargs:          A dictionary of function names, and default value
                            remapping:

                            get
                                The name to use for the ``get`` function.
                            set_default
                                The name to use for the ``set_default``
                                function.
                            registered
                                The name to use for the ``registered``
                                function.
                            DEFAULT
                                The name to use for the ``DEFAULT`` data
                                variable referencing the default plugin.

    This function adds all the object listed in the package/module ``__all__``
    variable. Names listed in ``__all__`` are converted removing trailinig
    (right) ``_``: after all, you are not supposed to list objects whose name
    starts with an ``_``. Also, it uses the
    :py:func:`pkg_resources.iter_entry_points` to register all the third party
    plugins. Objects returned by :py:func:`pkg_resources.iter_entry_points`
    must be callables which return a ``(plugin_name, plugin_object)`` tuple.

    >>> import pluggable_package
    >>> import my_package
    >>>
    >>> my_package.__all__
    ['example', 'type_']
    >>> pluggable_package.setup(my_package)
    >>>
    >>> example = my_package.get('example')
    >>> type_ = my_package.get('type')
    >>> my_package.get('maybe', None) is None
    True

    So, what if your package already exposes a ``DEFAULT`` variable, or any of
    ``get``, ``set_default`` or ``registered`` function? You can rename any of
    them like in the following example:

    >>> import pluggable_package
    >>> import my_package
    >>>
    >>> pluggable_package.setup(my_package, 'example',
    ...                         get='get_plugin',
    ...                         set_default='set_default_plugin',
    ...                         registered='registered_plugins',
    ...                         DEFAULT='DEFAULT_PLUGIN')
    ...
    >>> my_package.get_plugin('example') is my_package.DEFAULT_PLUGIN
    True
    >>>
    >>> 'example' in my_package.registered_plugins()
    True
    """

    global _get, _set_default, _registered, _REGISTERED, _SETUP

    # Getting / overriding default names.
    DEFAULT_name = kwargs.get('DEFAULT', 'DEFAULT')
    get_name = kwargs.get('get', 'get')
    registered_name = kwargs.get('registered', 'registered')
    set_default_name = kwargs.get('set_default', 'set_default')

    partial = functools.partial

    # Registering the setup, for later use in cleaning/testing
    # :py:func:`_teardown`.
    _SETUP[package][get_name] = partial(_get, package=package)
    _SETUP[package][registered_name] = partial(_registered, package=package)
    _SETUP[package][set_default_name] = partial(_set_default,
                                                DEFAULT_name=DEFAULT_name,
                                                package=package)
    # Setting up the package.
    setattr(package, get_name, _SETUP[package][get_name])
    setattr(package, registered_name, _SETUP[package][registered_name])
    setattr(package, set_default_name, _SETUP[package][set_default_name])

    # Registering the bundled plugins.
    package_name = package.__name__
    for plugin_name in package.__all__:
        try:
            plugin_module = '.'.join([package_name, plugin_name])
            plugin_object = importlib.import_module(plugin_module)
        except ImportError:
            plugin_object = getattr(package, plugin_name)

        _REGISTERED[package_name][plugin_name.rstrip('_')] = plugin_object

    # Setting up the default plugin.
    default = default if default is None else _get(default, package=package)
    _SETUP[package][DEFAULT_name] = default
    setattr(package, DEFAULT_name, _SETUP[package][DEFAULT_name])

    # Registering third parties plugins.
    entry_points = pkg_resources.iter_entry_points(package_name)
    _REGISTERED[package_name].update(e() for e in entry_points)


def _teardown(package):
    global _SETUP
    for attribute in _SETUP[package]:
        delattr(package, attribute)
    del _SETUP[package]
