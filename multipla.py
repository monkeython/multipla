"""
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


_multi_plug = dict()
_locked_multi_plugs = thread.allocate_lock()


def powerup(label):
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
    with _locked_multi_plugs:
        try:
            return _multi_plug[label]
        except KeyError:
            _multi_plug[label] = MultiPlug(label)
            return _multi_plug[label]


# If it walks like a duck and quacks like a duck then it is a duck.
class MultiPlug(object):
    """The PluggablePackage must be a package.

    :param module package:  The package object.

    This class mimic :py:class:`types.ModuleType`, but also imports and let you
    access all the plugins associated with that package. It uses the
    :py:func:`pkg_resources.iter_entry_points` to retrive all the third party
    plugins. Each entry point must be a ``(plugin_name, plugin_object)`` tuple.
    """

    def __init__(self, label):
        self.label = label
        self._sockets = dict(pkg_resources.iter_entry_points(self.name))

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
        maketrans = getattr(str, 'maketrans', None)
        maketrans = getattr(string, 'maketrans', maketrans)
        label = name.translate(maketrans('!#$&^/+-.', '_________'))

        plug = self._sockets.get(label, default)
        if plug is NotImplemented:
            plug = '{}.{}:{}'.format(self.label, label, name)
            raise NotImplementedError(plug)
        return plug

    def setdefault(self, label, plug):
        """Set a default plugin ``value``` for a given plugin ``label``.

        :param str label:        The plugin actual (i.e. not translated) name.
                                See also py:meth:`PluggablePackage.get`.
        :param module value:    The plugin module.
        :returns:               The plugged in module.

        Set a default plugin with the same philosofy of
        :py:meth:`dict.setdefault`. So, if plugin ``label`` has already been
        set, it returns the already set value. If you want to override a plugin
        ``label`` with your own ``value``, you must explicitly set the attribute
        ``label`` of the :py:class:`PluggablePackage` instance:

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
        return self._sockets.setdefault(label, plug)

    @property
    def sockets(self):
        return self._sockets.copy()

    def __str__(self):
        return "<MultiPlug '{}'>".format(self.label)
