"""
"""

__author__ = "Luca De Vitis <luca at monkeython.com>"
__version__ = '0.0.3'
__copyright__ = "2014, %s " % __author__
__docformat__ = 'restructuredtext en'
__keywords__ = ['multipla', 'multi-plugs', 'multi-socket', 'plugs', 'plugin']
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

__all__ = ['switch_on', 'switch_off']

import collections
import importlib
import os
import string
import types
import warnings

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


# Grown man rule apply here on.
_multipla = collections.defaultdict(dict)
_locked_multipla = thread.allocate_lock()

def switch_on(label, working_set=None):
    """Create and/or returns a dictionary of plugins.

    :param str label:       The multi-plug label (i.e. entry point group)
    :rtype:                 :py:class:`Multipla`

    >>> import multipla
    >>>
    >>> multipla.switch_on('plugin_group')
    <Multipla 'plugin_group'>
    >>>
    >>> plugin_group = multipla.switch_on('plugin_group')
    >>> plugin_group is multipla.switch_on('plugin_group')
    True
    >>> isinstance(plugin_group, multipla.Multipla)
    True
    """
    if working_set is None:
        working_set = pkg_resources.working_set
    with _locked_multipla:
        try:
            return _multipla[working_set][label]
        except KeyError:
            _multipla[working_set][label] = Multipla(label, working_set)
            return _multipla[working_set][label]

def switch_off(label, working_set=None):
    if working_set is None:
        working_set = pkg_resources.working_set
    with _locked_multipla:
        multipla = _multipla[working_set]
        try:
            del multipla[label]
        except KeyError:
            return None

class RatedDict(object):
    """A :py:class:`dict`-like class that lets you to rate its objects.

    Implementation is meant to be thread-safe. Supports the following
    :py:class:`dict`-like methods:

    * ``__setitem__``, ``__getitem__``, ``__delitem__``
    * ``__iter__``, ``__reversed__``
    * ``__contains__``, ``__len__``, ``__str__``
    * ``update``, ``setdefault``
    """
    def __init__(self):
        self._ratings = collections.OrderedDict()
        self._dict = dict()
        self._locked = thread.allocate_lock()

    def _setitem_(self, key, value):
        self._dict[key] = value
        self._ratings.setdefault(key, 0)

    def __setitem__(self, key, value):
        with self._locked:
            self._setitem_(key, value)

    def __delitem__(self, key):
        with self._locked:
            del self._dict[key]
            del self._ratings[key]
    
    def __getitem__(self, key):
        return self._dict[key]

    def __iter__(self):
        return self._ratings.__iter__()

    def __reversed__(self):
        return self._ratings.__reversed__()

    def __contains__(self, key):
        return key in self._dict

    def __len__(self):
        return self._dict.__len__()

    def __str__(self):
        try:
            label = self.label
        except AttributeError:
            label = id(self)
        return "<{} '{}'>".format(self.__class__.__name__, label)

    def update(self, other=None, **updated):
        with self._locked:
            if other is not None:
                try:
                    for key, value in other.iteritems():
                        self._setitem_(key, value)
                except AttributeError:
                    try:
                        for key in other.keys():
                            self._setitem_(key, other[key])
                    except AttributeError:
                        for key, value in other:
                            self._setitem_(key, value)
            for key in updated:
                self._setitem_(key, updated[key])

    def setdefault(self, key, value):
        try:
            default = self._dict[key]
        except KeyError:
            self[key] = default = value
        return default

    def rate(self, ratings=(), **args):
        """Rate the items into the dictionary.
        
        :param rating:                  If ``rating`` has an ``iteritems`` or
                                        ``keys`` methods, they will be used to
                                        update the items ratings. Else,
                                        ``ratings`` is considered a
                                        :py:class:`tuple` of ``key``-``rating``
                                        pairs.
        :param dict args:               Anyway, variable keyword arguments
                                        ``args`` will be used to update the
                                        item ratings.

        This method behave like the :py:meth:`dict.update`, but affects only
        items ratings. At the end of the update, dictionary keys are sorted by
        rating, from greater to lower rating value. Rating is supposed to be
        any kind of number equal or greater than 0. Default item rating is 0.
        """
        with self._locked:
            self._ratings.update(ratings, **args)
            ratings, key = self._ratings.items(), lambda k, v: -v
            self._ratings = collections.OrderedDict(sorted(ratings, key=key))

    def top(self, amount=None):
        """Returns the ``top`` rated items.

        :param int top:                 The number of items to return, sorted by
                                        ratings. Defaults to all items.
        :rtype:                         list
                                        item is returned.
        :raises ValueError:             If ``amount`` is greater than the
                                        available items.
        """
        with self._locked:
            if amount is None:
                amount = len(self._ratings)
            item = iter(self._ratings)
            try:
                for counter in range(amount):
                    key = next(item)
                    top.append((key, self._dict[key]))
            except StopIteration:
                error = '{}.top: asked {} plugs, got {}'
                raise ValueError(error.format(self, amount, counter))
            return top

    @property
    def highest_rated(self):
        return self.top(1)[0]


class MultiPlugAdapter(RatedDict):
    """The multi-plug adapter that holds all the implementations

    :param label:                       The label of the plug adapter (i.e. the
                                        name of the entry point).

    This class represents all the plugins that implement the give entry point
    name. Since this class inherit from :py:class:`RatedDict`, it's possible to
    rate each implementation. The ``pkg_resources`` classes allows multiple
    packages/modules to provide their own implementation of a given plugin
    name: for example, 2 modules might provide the same ``YAML`` serialization
    functions, but each using a different ``YAML`` library.
    """
    def __init__(self, label):
        self.label = label
        super(MultiPlugAdapter, self).__init__()

    def get(self, plug_model, default=None):
        """Get a plugin or the supplied ``default`` value.
        
        :param str plug_model:          The ``plug`` implementation name.
        :param default:                 The default value to return if lookup
                                        fails.
        :returns:                       The desired plugged in object.
        """
        try:
            return self._dict[plug_model]
        except KeyError:
            return default

    def plug_in(self, plug_model, plug):
        """Try to plug an object in.
        
        :param str plug_model:          The ``plug`` implementation name.
        :param plug:                    The object to plug in.
        :raises KeyError:               If another object with the same
                                        ``plug_model`` is already plugghed in.

        If you want to override a specific plug implementation, you should use
        dictionary item setting syntax.
        """
        try:
            plugged = self[plug_model]
        except KeyError:
            self[plug_model] = plug
            return plug
        else:
            raise KeyError(plug_model)

    def plug_out(self, plug_model):
        """Plugs an object out.

        :param str plug_model:          The ``plug`` implementation name.

        If ``plug_model`` does not exists, nothing is done.  If you want an
        exception to be raised if the specific ``plug_model`` implementation is
        not set, you should use dictionary item deletion syntax.
        """
        try:
            del self[plug_model]
        except KeyError:
            return None


class Multipla(RatedDict):
    """The power strip to put the plugs into.
    
    :param label:                       The label of the power strip (i.e. the
                                        entry point group).

    This class represents the plugin group. Since this class inherit from
    :py:class:`RatedDict`, it's possible to rate each plugin.
    """

    def __init__(self, label, working_set=None):
        self.label = label
        super(Multipla, self).__init__()
        ratings = collections.defaultdict(list)
        for ep in working_set.iter_entry_points(label):
            self.switch_on(ep.name).plug_in('.'.join(ep.attrs), ep.load())

    def switch_on(self, socket_label):
        """Switch on a socket labeled ``socket_label``.

        :param str socket_label:        The socket label.
        :returns:                       The :py:class:`MultiPlugAdapter`
                                        associated with the ``socket_label``.

        If the :py:class:`MultiPlugAdapter` already exists, it is returned.
        If there is no :py:class:`MultiPlugAdapter` for the specified plugin
        set, a new one is created and returned.
        """
        try:
            adapter = self[socket_label]
        except KeyError:
            self[socket_label] = adapter = MultiPlugAdapter(socket_label)
        return adapter

    def switch_off(self, socket_label):
        """Switch off a socket labeled ``socket_label``.

        :param str socket_label:        The socket label.

        The effect of this method is to delete the specified
        :py:class:`MultiPlugAdapter`. If specified plugin set does not exists,
        nothing is done.
        """
        try:
            del self[socket_label]
        except KeyError:
            return None

    def plugs(self, name):
        """Return all the available implementation for ``name``.

        :param str name:                The plugin name.
        :rtype:                         :py:class:`MultiPlugAdapter`
        :raises KeyError:               If no ``MultiPlugAdapter`` was switched
                                        on for ``name``..

        See :py:meth:`Multipla.get` for ``name`` value.
        """
        maketrans = getattr(str, 'maketrans', None)
        maketrans = getattr(string, 'maketrans', maketrans)
        socket_label = name.translate(maketrans('!#$&^/+-.', '_________'))
        return self._dict[socket_label]
        
    def get(self, name, default=None):
        """Get the higest rated ``plug`` for the given plug ``name``.

        :param name:                    The plugin name.
        :param default:                 The default value to return if lookup
                                        fails.
        :returns:                       The highest rated plugin.

        Lookup the desired plugin and returns it. On lookup, ``name`` value is
        translated into a label: ``!#$&^/+-.`` characters are converted to
        ``_``. So, the following example should work as expected:

        >>> import multipla
        >>> content_types = multipla.switch_on('content_types')
        >>> plugin = content_types.get('application/octet-stream')
        """
        try:
            return self.plugs(name).highest_rated(1)[1]
        except KeyError:
            return default
