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

__all__ = ['power_up']

import collections
import importlib

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


class Lock(object):
    def __init__(self):
        self.__lock = thread.allocate_lock()

    def __nonzero__(self):
        return self.__lock.locked()

    def __enter__(self):
        self.__lock.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__lock.release()


class RatedDict(object):
    """A :py:class:`dict`-like class that lets you to rate its objects.

    This implementation is meant to be thread-safe. Actually, it only supports
    the following :py:class:`dict`-like methods:

    * ``__setitem__``
    * ``__getitem__``
    * ``__str__``
    """
    def __init__(self):
        self._ratings = collections.OrderedDict()
        self._dict = dict()
        self.locked = Lock()

    def __str__(self):
        try:
            name = self.name
        except AttributeError:
            name = id(self)
        return "<{} '{}'>".format(self.__class__.__name__, name)

    def _setitem_(self, key, value):
        self._dict[key] = value
        self._ratings.setdefault(key, 0)
        return value

    def __setitem__(self, key, value):
        with self.locked:
            self._setitem_(key, value)

    def __getitem__(self, key):
        return self._dict[key]

    def __delitem__(self, key):
        with self.locked:
            del self._dict[key]
            del self._ratings[key]

    def __contains__(self, key):
        return self._dict.__contains__(key)

    def __iter__(self):
        return self._ratings.__iter__()

    def __reversed__(self):
        return self._ratings.__reversed__()

    def __len__(self):
        return self._dict.__len__()

    def update(self, other=(), **updated):
        with self.locked:
            try:
                for key, value in other.items():
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

#     def setdefault(self, key, value):
#         with self.locked:
#             try:
#                 default = self._dict[key]
#             except KeyError:
#                 default = self._setitem_(key, value)
#         return default

    def rate(self, updates=(), **args):
        """Rate the items into the dictionary.

        :param updates:                 A ``key: rating`` dictionary or an
                                        iterable yielding ``(key, rating)``.
        :param dict args:               Anyway, variable keyword arguments
                                        ``args`` will be used to update the
                                        item ratings.
        :raises KeyError:               If unexpected keys are found.

        This method behave like the :py:meth:`dict.update`, but affects only
        items ratings. At the end of the update, dictionary keys are sorted by
        rating, from greater to lower rating value. Rating is supposed to be
        any kind of number equal or greater than 0. Default item rating is 0.
        """

        ratings = dict(updates, **args)
        with self.locked:
            unexpected = set(ratings.keys()) - set(self._dict.keys())
            if unexpected:
                error = '{}.rate: unexpected keys {}'
                raise KeyError(error.format(self, unexpected))
            self._ratings.update(ratings)
            # Here we take advantage of the ordering of
            # :py:class:`collections.OrderedDict` and stability of
            # :py:func:`sorted`
            by_rate = sorted(self._ratings.items(), key=lambda kv: -kv[1])
            self._ratings = collections.OrderedDict(by_rate)

    def top(self, amount=None):
        """Returns the top rated items.

        :param int amount:              The number of items to return. Defaults
                                        to all items.
        :returns:                       A list of ``key``-``value`` pairs,
                                        sorted by key ratings.
        :raises ValueError:             If ``amount`` is greater than the
                                        available items.
        """
        top_rated = list()
        with self.locked:
            if amount is None:
                amount = len(self._ratings)
            item = iter(self._ratings)
            try:
                for counter in range(amount):
                    key = next(item)
                    top_rated.append((key, self._dict[key]))
            except StopIteration:
                error = '{}.top: asked {} items, got {}'
                raise ValueError(error.format(self, amount, counter))
        return top_rated

    @property
    def highest_rated(self):
        """The value of the highest rated item.

        :raises ValueError:             If container is empty.
        """
        with self.locked:
            try:
                return self._dict[self._ratings.__iter__().next()]
            except StopIteration:
                error = '{}.highest_rated: empty container'
                raise ValueError(error.format(self))


class MultiPlugAdapter(RatedDict):
    """The multi-plug adapter that holds the implementations.

    :param name:                        The name of the plug adapter (i.e. the
                                        name of the entry point).

    This class represents all the plugins that implement the give entry point
    name. Since this class inherit from :py:class:`RatedDict`, it's possible to
    rate each implementation. The ``pkg_resources`` classes allows each
    distribution to provide their own implementation of a given plugin name:
    for example, 2 distributions might provide the same ``YAML`` serialization
    functions, but each using a different ``YAML`` library.
    """
    def __init__(self, name):
        self.name = name
        super(MultiPlugAdapter, self).__init__()

    def plug_in(self, name, plug):
        """Try to plug an object in.

        :param str name:                The ``plug`` implementation name.
        :param plug:                    The object to plug in.
        :raises KeyError:               If another object with the same
                                        ``name`` is already plugghed in.

        If you want to explicitly overrid a plug implementation, you must use
        dictionary item setting syntax.
        """
        with self.locked:
            try:
                value = self._dict[name]
            except KeyError:
                return self._setitem_(name, plug)
        error = '{}.plug_in: {} is already set with {}'
        raise KeyError(error.format(self, name, value))


class Multipla(RatedDict):
    """The power strip to put the plugs into.

    :param name:                        The name of the power strip (i.e. the
                                        entry point group).

    This class represents the plugin group. Since this class inherit from
    :py:class:`RatedDict`, it's possible to rate each plugin. For example, you
    could rate a set of content type handler.
    """

    def __init__(self, name):
        self.name = name
        super(Multipla, self).__init__()

    def __call__(self, distribution):   # pragma: no cover
        for ep in distribution.get_entry_map(self.name).values():
            implementation = ':'.join([ep.module_name, '.'.join(ep.attrs)])
            self.switch_on(ep.name).plug_in(implementation, ep.load())

    def switch_on(self, name):
        """Switch on a socket.

        :param str name:                The socket (entry point group) name.
        :returns:                       The :py:class:`MultiPlugAdapter`
                                        associated with the ``name``.

        If the specified :py:class:`MultiPlugAdapter` already exists, it is
        returned.  If there is no :py:class:`MultiPlugAdapter` for the
        specified plugin group, a new one is created and returned.
        """
        with self.locked:
            try:
                adapter = self._dict[name]
            except KeyError:
                adapter = self._setitem_(name, MultiPlugAdapter(name))
        return adapter

    def get(self, name, default=None):
        """Get the higest rated ``plug`` for the given plug ``name``.

        :param name:                    The plugin name.
        :param default:                 The default value to return if lookup
                                        fails.
        :returns:                       The highest rated plugin.
        :raises ValueError:             See :py:data:`RatedDict.highest_rated`.
        """
        try:
            return self[name].highest_rated
        except KeyError:
            return default


_register = dict()
_locked_register = Lock()


def power_up(name, *args):
    """Creates and returns a rated dictionary of plugins.

    :param str name:                    The multi-plug name (i.e. entry point
                                        group).
    :param args:                        Variable argument list of
                                        :py:class:`pkg_resources.WorkingSet`.
    :rtype:                             :py:class:`Multipla`

    :py:class:`Multipla` instance meant to be unique, is powered up by
    subscribing (as per :py:meth:`pkg_resources.WorkingSet.subscribe`) it to
    each :py:class:`pkg_resources.WorkingSet` in the variable argument list. If
    no extra argument is provided, :py:data:`pkg_resources.working_set` is
    used.

    >>> import multipla
    >>>
    >>> multipla.power_up('plugin_group')
    <Multipla 'plugin_group'>
    >>>
    >>> plugin_group = multipla.power_up('plugin_group')
    >>> plugin_group is multipla.power_up('plugin_group')
    True
    >>> isinstance(plugin_group, multipla.Multipla)
    True
    """
    with _locked_register:
        try:
            multipla = _register[name]
        except KeyError:
            _register[name] = multipla = Multipla(name)
    if not args:
        args = [pkg_resources.working_set]
    for working_set in args:
        working_set.subscribe(multipla)
    return multipla
