"""
The purpose of this module is to mix the namespace packages with the
:py:mod:`setuptools` plugins system.
"""

__author__ = "Luca De Vitis <luca at monkeython.com>"
__version__ = '0.0.2'
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

__all__ = ['import_package']

import collections
import importlib
import os
import string
import types

import pkg_resources

try:
    thread = importlib.import_module('thread')
except ImportError:     # pragma: no cover
    try:
        thread = importlib.import_module('_thread')
    except ImportError:
        try:
            thread = importlib.import_module('dummy_thread')
        except ImportError:
            thread = importlib.import_module('_dummy_thread')


_packages = dict()
_locked_packages = thread.allocate_lock()

_plugins = collections.defaultdict(dict)
_locked_plugins = thread.allocate_lock()


def import_package(name, package=None):
    """Returns pluggable package.

    :param str name:        See :py:func:`importlib.import_module`.
    :param str package:     See :py:func:`importlib.import_module`.
    :rtype:                 :py:class:`PluggablePackage`

    >>> import pluggable_package
    >>> import my_package
    >>> import sys
    >>> import types
    >>>
    >>> pluggable_package.import_package('my_package')
    <pluggable_package 'my_package' from 'my_package/__init__.py'>
    >>>
    >>> my_package = pluggable_package.import_package('my_package')
    >>> my_package is pluggable_package.import_package('my_package')
    True
    >>> isinstance(my_package, types.ModuleType)
    True
    >>> my_package is not sys.modules['my_package']
    True
    """
    global _packages, _locked_packages
    pluggable = importlib.import_module(name, package)
    with _locked_packages:
        try:
            return _packages[pluggable]
        except KeyError:
            _packages[pluggable] = PluggablePackage(pluggable)
            return _packages[pluggable]


# If it walks like a duck and quacks like a duck then it is a duck.
class PluggablePackage(types.ModuleType):
    """The PluggablePackage must be a package.

    :param module package:  The package object.

    This class mimic :py:class:`types.ModuleType`, but also imports and let you
    access all the plugins associated with that package. It uses the
    :py:func:`pkg_resources.iter_entry_points` to retrive all the third party
    plugins. Each entry point must be a ``(plugin_name, plugin_object)`` tuple.
    """

    def __init__(self, package):
        global _plugins, _locked_plugins
        self.__name__ = package.__name__
        self.__doc__ = getattr(package, '__doc__', None)
        self.__package__ = getattr(package, '__package__',
                                   self.__name__.split('.')[-1])
        self.__file__ = package.__file__
        self.__path__ = getattr(package, '__path__',
                                os.path.dirname(self.__file__))
        entry_points = pkg_resources.iter_entry_points(self.__name__)
        with _locked_plugins:
            _plugins[self.__name__] = dict(entry_points)

    @property
    def __all__(self):
        global _plugins, _locked_plugins
        with _locked_plugins:
            return tuple(_plugins[self.__name__])

    def get(self, name, default=NotImplemented):
        """Get the desired plugin.

        :param name:                    The plugin name.
        :param default:                 The default value to return if lookup
                                        fails.
        :raises NotImplementedError:    If flookup fails and no default value
                                        is explictly provided.
        :returns:                       The desired plugin.

        Lookup the desired plugin and returns it. On lookup, ``name`` value is
        translated: ``!#$&^/+-.`` characters are converted to ``_``. So, the
        following example should work as expected:

        >>> import pluggable_package
        >>> content_types = pluggable_package.import_package('content_types')
        >>> plugin = content_types.get('application/octet-stream')

        Note that even if ``default`` param has a declared default value, If
        lookup fails and no ``default`` value was provided on call, the method
        will raise :py:exc:`NotImplementedError`:

        >>> mediatype = 'application/vnd.mytype-v2+xml'
        >>> try:
        ...     plugin = content_types.get(mediatype)
        ... except NotImplementedError:
        ...     plugin = False
        ...
        >>> plugin
        False
        >>> content_types.get(mediatype, None) is None
        True
        """
        global _plugins, _locked_plugins
        maketrans = getattr(str, 'maketrans', None)
        maketrans = getattr(string, 'maketrans', maketrans)
        translated = name.translate(maketrans('!#$&^/+-.', '_________'))

        with _locked_plugins:
            plugin = _plugins[self.__name__].get(translated, default)
        if plugin is NotImplemented:
            plugin = '{}.{}:{}'.format(self.__name__, translated, name)
            raise NotImplementedError(plugin)
        return plugin

    def setdefault(self, name, value):
        """Set a default plugin ``value``` for a given plugin ``name``.

        :param str name:        The plugin actual (i.e. not translated) name.
                                See also py:meth:`PluggablePackage.get`.
        :param module value:    The plugin module.
        :returns:               The plugged in module.

        Set a default plugin with the same philosofy of
        :py:meth:`dict.setdefault`. So, if plugin ``name`` has already been
        set, it returns the already set value. If you want to override a plugin
        ``name`` with your own ``value``, you must explicitly set the attribute
        ``name`` of the :py:class:`PluggablePackage` instance:

        >>> import importlib
        >>> import pluggable_package
        >>> my_module = importlib.import_module('my_module')
        >>> third_party = importlib.import_module('third_party')
        >>> my_package = pluggable_package.import_package('my_package')
        >>>
        >>> my_pacakge.setdefault('my_module', my_module) is my_module
        True
        >>> my_pacakge.setdefault('my_module', third_party) is not third_party
        True
        >>> my_pacakge.setdefault('my_module', third_party) is my_module
        True
        >>> my_pacakge.my_module is my_module
        True
        >>> my_package.my_module = third_party
        >>> my_package.my_module is third_party
        """
        global _plugins, _locked_plugins
        with _locked_plugins:
            return _plugins[self.__name__].setdefault(name, value)

    def __str__(self):
        str_ = "<pluggable_package '{}' from '{}'>"
        return str_.format(self.__name__, self.__file__)
